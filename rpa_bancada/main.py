# -*- coding: utf-8 -*-
import time
from io import StringIO
from pathlib import Path
import threading
import sys
import os
import json

import pyautogui as pag
import pyperclip
import pandas as pd

# Importar Google Sheets manager
print("=" * 80)
print("DEBUG: Tentando importar google_sheets_manager...")
print(f"DEBUG: sys.frozen = {getattr(sys, 'frozen', False)}")
print(f"DEBUG: _MEIPASS = {getattr(sys, '_MEIPASS', 'N/A')}")
print(f"DEBUG: __file__ = {__file__}")
print("=" * 80)

try:
    print("DEBUG: Executando 'from google_sheets_manager import enviar_para_google_sheets'...")
    from google_sheets_manager import enviar_para_google_sheets
    GOOGLE_SHEETS_AVAILABLE = True
    print("=" * 80)
    print("✅ [OK] Google Sheets manager importado com sucesso!")
    print("=" * 80)
except ImportError as e:
    print("=" * 80)
    print(f"❌ [ERRO] Google Sheets ImportError: {e}")
    print("=" * 80)
    import traceback
    traceback.print_exc()
    GOOGLE_SHEETS_AVAILABLE = False
except Exception as e:
    print("=" * 80)
    print(f"❌ [ERRO] Google Sheets Exception: {type(e).__name__}: {e}")
    print("=" * 80)
    import traceback
    traceback.print_exc()
    GOOGLE_SHEETS_AVAILABLE = False

print(f"DEBUG: GOOGLE_SHEETS_AVAILABLE = {GOOGLE_SHEETS_AVAILABLE}")
print("=" * 80)

# Focar janela por título (opcional)
try:
    from pygetwindow import getWindowsWithTitle
except Exception:
    getWindowsWithTitle = None

# =================== CONFIG ===================
# Compatível com .exe
BASE = Path(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))))
OUT = (BASE / "out"); OUT.mkdir(exist_ok=True)


# Carregar configurações do config.json
CONFIG = None
try:
    config_path = BASE / "config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        CONFIG = json.load(f)
    print(f"[OK] Configurações carregadas de {config_path}")
except Exception as e:
    print(f"[WARN] Erro ao carregar config.json: {e}")
    CONFIG = None

# ===== COORDENADAS (carregadas do config.json ou fixas) =====
if CONFIG:
    COORD_BANCADA_ABRIR = (CONFIG["coordenadas"]["tela_07_bancada_material"]["x"],
                           CONFIG["coordenadas"]["tela_07_bancada_material"]["y"])
    COORD_BANCADA_FECHAR = (CONFIG["coordenadas"]["tela_08_fechar_bancada"]["x"],
                            CONFIG["coordenadas"]["tela_08_fechar_bancada"]["y"])
    COORD_DETALHADO = (CONFIG["coordenadas"]["bancada_detalhado"]["x"],
                       CONFIG["coordenadas"]["bancada_detalhado"]["y"])
    COORD_LOCALIZAR = (CONFIG["coordenadas"]["bancada_localizar"]["x"],
                       CONFIG["coordenadas"]["bancada_localizar"]["y"])
    COORD_ORG_CELL = (CONFIG["coordenadas"]["bancada_celula_org"]["x"],
                      CONFIG["coordenadas"]["bancada_celula_org"]["y"])
    TEMPO_ENTRE_CLIQUES = CONFIG["tempos_espera"]["entre_cliques"]
    TEMPO_APOS_MODAL = CONFIG["tempos_espera"]["apos_modal"]
    TEMPO_APOS_ABRIR = CONFIG["tempos_espera"]["apos_abrir_bancada"]
    TEMPO_APOS_LOCALIZAR = CONFIG["tempos_espera"].get("apos_localizar", 120)
else:
    # Fallback para coordenadas fixas
    COORD_BANCADA_ABRIR = (598, 284)
    COORD_BANCADA_FECHAR = (746, 90)
    COORD_DETALHADO = (273, 358)
    COORD_LOCALIZAR = (524, 689)
    COORD_ORG_CELL = (318, 174)
    TEMPO_ENTRE_CLIQUES = 1.5
    TEMPO_APOS_MODAL = 5.0
    TEMPO_APOS_ABRIR = 3.0
    TEMPO_APOS_LOCALIZAR = 120


# ===== CONFIGURAÇÕES DE TIMING =====
pag.FAILSAFE = True              # Mover mouse para canto superior esquerdo para parar
pag.PAUSE = 0.35                 # Pausa entre comandos PyAutoGUI
MOUSE_MOVE_DUR = 0.45            # Duração do movimento do mouse
TIMEOUT_UI = 60                  # Timeout para elementos UI aparecerem
POLL = 0.7                       # Intervalo de polling
POPUP_MAX = 15 * 60              # Timeout máximo para popup (15 minutos)
SLEEP_POS_CLIQUE = 0.8           # Pausa após clique
SLEEP_ABERTURA = 1.2             # Pausa após abrir janela

# =================== HELPERS ===================

def focus_oracle():
    """Tenta focar a janela do Oracle Applications"""
    if not getWindowsWithTitle:
        return
    titles = [
        "Aplicativos Oracle", "Oracle Applications",
        "Tecumseh PROD Upgraded", "Bancada de Material"
    ]
    for t in titles:
        wins = getWindowsWithTitle(t)
        if wins:
            try:
                wins[0].activate()
                time.sleep(0.8)
                return
            except Exception:
                pass



def abrir_bancada() -> bool:
    """Abre a Bancada de Material com duplo clique"""
    if not _rpa_running:
        return False

    focus_oracle()
    gui_log("📂 Abrindo Bancada de Material (duplo clique)...")

    try:
        x, y = COORD_BANCADA_ABRIR
        pag.moveTo(x, y, duration=MOUSE_MOVE_DUR)
        pag.doubleClick()
        gui_log(f"   ✓ Duplo clique em ({x}, {y})")
        time.sleep(TEMPO_APOS_ABRIR)

        focus_oracle()
        gui_log("   ✅ Bancada aberta!")
        return True
    except Exception as e:
        gui_log(f"   ❌ Erro ao abrir bancada: {e}")
        return False

def fechar_bancada() -> bool:
    """Fecha a Bancada de Material clicando no X"""
    if not _rpa_running:
        return False

    focus_oracle()
    gui_log("🔴 Fechando Bancada de Material...")

    try:
        x, y = COORD_BANCADA_FECHAR
        pag.moveTo(x, y, duration=MOUSE_MOVE_DUR)
        pag.click()
        gui_log(f"   ✓ Clique em ({x}, {y})")
        time.sleep(TEMPO_ENTRE_CLIQUES)

        gui_log("   ✅ Bancada fechada!")
        return True
    except Exception as e:
        gui_log(f"   ❌ Erro ao fechar bancada: {e}")
        return False

def move_click(x, y, right=False):
    """Move o mouse e clica na coordenada especificada"""
    pag.moveTo(x, y, duration=MOUSE_MOVE_DUR)
    pag.click(button='right' if right else 'left')
    time.sleep(SLEEP_POS_CLIQUE)

def mapear_colunas_oracle(df):
    """
    Mapeia colunas do Oracle para nomes padronizados.
    Garante que as 8 colunas principais sejam identificadas.
    """
    import re

    gui_log(f"⚙️ Mapeando colunas Oracle. Colunas recebidas: {list(df.columns)}")

    # Mapeamento exato das colunas Oracle para padronizadas
    mapeamento_exato = {
        'Org.': 'ORG.',
        'Sub.': 'SUB.',
        'Endereço': 'ENDEREÇO',
        'Item': 'ITEM',
        'Descrição do Item': 'DESCRIÇÃO ITEM',
        'Rev.': 'REV.',
        'UDM Principal': 'UDM PRINCIPAL',
        'Em Estoque': 'EM ESTOQUE',
        'Em Estoque ': 'EM ESTOQUE',  # Com espaço extra
    }

    colunas_mapeadas = {}

    for col_original in df.columns:
        # Primeiro tenta mapeamento direto
        if col_original in mapeamento_exato:
            colunas_mapeadas[col_original] = mapeamento_exato[col_original]
            gui_log(f"   ✓ Mapeado direto: '{col_original}' -> '{mapeamento_exato[col_original]}'")
        else:
            # Tenta mapeamento por similaridade (removendo acentos)
            col_clean = re.sub(r'[^\w\s]', '', col_original.strip())
            encontrado = False
            for key, value in mapeamento_exato.items():
                key_clean = re.sub(r'[^\w\s]', '', key.strip())
                if col_clean.lower() == key_clean.lower():
                    colunas_mapeadas[col_original] = value
                    gui_log(f"   ✓ Mapeado fuzzy: '{col_original}' -> '{value}'")
                    encontrado = True
                    break
            if not encontrado:
                gui_log(f"   ✗ NÃO mapeado: '{col_original}'")

    gui_log(f"📊 Total de colunas mapeadas: {len(colunas_mapeadas)}")

    # Se nenhuma coluna foi mapeada, retorna DataFrame original
    if len(colunas_mapeadas) == 0:
        gui_log("⚠️ NENHUMA coluna foi mapeada! Retornando DataFrame original")
        return df

    # Renomear colunas
    df_renamed = df.rename(columns=colunas_mapeadas)

    # Manter apenas as 8 colunas desejadas (incluindo REV temporariamente)
    colunas_finais = ['ORG.', 'SUB.', 'ENDEREÇO', 'ITEM', 'DESCRIÇÃO ITEM', 'REV.', 'UDM PRINCIPAL', 'EM ESTOQUE']
    colunas_disponiveis = [col for col in colunas_finais if col in df_renamed.columns]

    gui_log(f"📋 Colunas finais selecionadas: {colunas_disponiveis}")

    if len(colunas_disponiveis) == 0:
        gui_log("⚠️ Nenhuma coluna disponível após filtro! Retornando DataFrame original")
        return df

    df_final = df_renamed[colunas_disponiveis]

    # REMOVER COLUNA REV (não é mais usada na tabela de produção)
    if 'REV.' in df_final.columns:
        gui_log("🗑️ Removendo coluna REV. (não mais utilizada)")
        df_final = df_final.drop(columns=['REV.'])
        gui_log(f"✅ Coluna REV removida. Colunas finais: {list(df_final.columns)}")

    return df_final

def texto_para_df(tsv_texto: str) -> pd.DataFrame:
    """
    Converte o texto copiado do Oracle (TSV) em DataFrame limpo.
    """
    gui_log(f"🔍 Processando clipboard: {len(tsv_texto):,} caracteres")

    if not tsv_texto or len(tsv_texto) < 10:
        gui_log("⚠️ Clipboard vazio ou muito pequeno")
        return pd.DataFrame()

    try:
        # Normaliza quebras de linha
        tsv = tsv_texto.replace("\r\n", "\n").replace("\r", "\n")

        gui_log(f"📊 Lendo dados como TSV...")
        df = pd.read_csv(StringIO(tsv), sep="\t", engine="python", on_bad_lines='skip')

        gui_log(f"✅ DataFrame inicial: {df.shape[0]:,} linhas x {df.shape[1]} colunas")

        # Se realmente parece uma tabela
        if df.shape[1] >= 2:
            # Remove colunas totalmente vazias
            df = df.dropna(axis=1, how="all")
            gui_log(f"🧹 Após remover colunas vazias: {df.shape[1]} colunas")

            # Remove linhas completamente vazias
            linhas_antes = df.shape[0]
            df = df.dropna(how="all")
            gui_log(f"🧹 Após remover linhas vazias: {df.shape[0]:,} linhas (removidas: {linhas_antes - df.shape[0]:,})")

            # Se a primeira linha for igual ao cabeçalho, descarta
            if len(df) > 0 and df.iloc[0].tolist() == list(df.columns):
                df = df.iloc[1:]
                gui_log(f"🧹 Removida linha duplicada do cabeçalho")

            gui_log(f"⚙️ Aplicando mapeamento de colunas Oracle...")
            # Aplicar mapeamento inteligente de colunas
            df_mapeado = mapear_colunas_oracle(df)

            # Limpar dados (substituir NaN por string vazia)
            df_mapeado = df_mapeado.fillna('')

            gui_log(f"✅ Dados processados: {df_mapeado.shape[0]:,} linhas x {df_mapeado.shape[1]} colunas")
            gui_log(f"📋 Colunas: {list(df_mapeado.columns)}")
            return df_mapeado.reset_index(drop=True)
        else:
            gui_log(f"⚠️ DataFrame tem apenas {df.shape[1]} coluna(s), esperado >= 2")
            return pd.DataFrame()

    except Exception as e:
        gui_log(f"❌ ERRO parseando TSV: {type(e).__name__}: {e}")
        import traceback
        gui_log(f"Stack trace: {traceback.format_exc()}")

        # Se o texto é muito grande, pode ser limitação de processamento
        if len(tsv_texto) > 50000:  # Mais de 50k caracteres
            gui_log(f"🔄 Texto grande ({len(tsv_texto):,} chars), tentando processamento direto com engine C...")
            try:
                tsv_simples = tsv_texto.replace("\r\n", "\n").replace("\r", "\n")
                df_direto = pd.read_csv(StringIO(tsv_simples), sep="\t", engine="c", low_memory=False, on_bad_lines='skip')

                gui_log(f"✅ DataFrame direto: {df_direto.shape[0]:,} linhas x {df_direto.shape[1]} colunas")

                if df_direto.shape[1] >= 2:
                    df_mapeado_direto = mapear_colunas_oracle(df_direto)
                    df_final_direto = df_mapeado_direto.fillna('')

                    gui_log(f"✅ Processamento direto bem-sucedido: {df_final_direto.shape[0]:,} linhas x {df_final_direto.shape[1]} colunas")
                    return df_final_direto.reset_index(drop=True)
                else:
                    gui_log(f"⚠️ Processamento direto: apenas {df_direto.shape[1]} coluna(s)")

            except Exception as e2:
                gui_log(f"❌ Processamento direto também falhou: {type(e2).__name__}: {e2}")

    # Fallback: retorna DataFrame vazio
    gui_log("⚠️ Usando fallback - DataFrame vazio")
    return pd.DataFrame()

def salvar(df: pd.DataFrame):
    """
    Salva o DataFrame em XLSX limpo (um arquivo por dia).
    Retorna o caminho do arquivo salvo.
    """
    hoje = pd.Timestamp.now().strftime("%Y-%m-%d")
    xlsx = OUT / f"export-{hoje}.xlsx"

    try:
        gui_log(f"💾 Preparando para salvar {df.shape[0]:,} linhas x {df.shape[1]} colunas")

        if xlsx.exists():
            gui_log(f"📂 Arquivo existente encontrado, concatenando dados...")
            old = pd.read_excel(xlsx, engine='openpyxl')
            df = pd.concat([old, df], ignore_index=True)
            gui_log(f"📊 Total após concatenação: {df.shape[0]:,} linhas")

        # Salva apenas as colunas de interesse
        if not df.empty:
            gui_log(f"💾 Salvando arquivo Excel em {xlsx}...")

            # Converter todas as colunas para string para evitar interpretação como data
            df_to_save = df.astype(str)

            df_to_save.to_excel(xlsx, index=False, engine='openpyxl')
            gui_log(f"✅ XLSX salvo: {xlsx} ({df.shape[0]:,} linhas, {df.shape[1]} colunas)")
            return str(xlsx)
        else:
            gui_log("⚠️ Nenhum dado válido para salvar.")
            return None
    except MemoryError as e:
        gui_log(f"❌ ERRO DE MEMÓRIA ao salvar Excel: {e}")
        gui_log("💡 Tente fechar outros programas e executar novamente")
        return None
    except ImportError as e:
        gui_log(f"❌ ERRO: Biblioteca openpyxl não encontrada: {e}")
        gui_log("💡 Execute: pip install openpyxl")
        return None
    except Exception as e:
        gui_log(f"❌ Erro salvando XLSX: {type(e).__name__}: {e}")
        import traceback
        gui_log(f"Stack trace: {traceback.format_exc()}")
        return None

# =================== KEEP-AWAKE E MONITORAMENTO ===================
_keep_awake_stop = threading.Event()
_keep_awake_thread = None

def keep_awake_loop(stop_event, interval=50):
    """
    Thread que pressiona Shift periodicamente para evitar bloqueio por inatividade.
    """
    while not stop_event.is_set():
        pag.keyDown('shift'); pag.keyUp('shift')
        for _ in range(int(interval * 10)):
            if stop_event.is_set():
                break
            time.sleep(0.1)

def iniciar_movimento_mouse_continuo(intervalo_mouse=1, intervalo_teclado=15):
    """
    Inicia movimento contínuo do mouse e teclado para ULTRA-proteção anti-hibernação.

    Args:
        intervalo_mouse: Intervalo entre movimentos do mouse em segundos (padrão: 1)
        intervalo_teclado: Intervalo entre pressões de Shift em segundos (padrão: 15)

    Returns:
        threading.Event: Event para parar o movimento
    """
    stop_event = threading.Event()

    def movimento_loop():
        contador_teclado = 0
        while not stop_event.is_set():
            try:
                # Movimento do mouse (5px para cima/baixo alternando)
                if not stop_event.is_set():
                    pos_atual = pag.position()
                    offset = 5 if (contador_teclado % 2 == 0) else -5
                    pag.moveTo(pos_atual.x, pos_atual.y + offset, duration=0.1)
                    time.sleep(intervalo_mouse)

                # Pressionar Shift periodicamente
                contador_teclado += intervalo_mouse
                if contador_teclado >= intervalo_teclado:
                    if not stop_event.is_set():
                        pag.keyDown('shift')
                        pag.keyUp('shift')
                    contador_teclado = 0

            except Exception:
                pass

    thread = threading.Thread(target=movimento_loop, daemon=True)
    thread.start()
    return stop_event

def monitorar_clipboard_inteligente(max_tempo=15*60, intervalo_check=3, estabilidade_segundos=30):
    """
    Monitora o clipboard de forma inteligente e detecta quando Oracle terminou de copiar.

    Estratégia:
    - Oracle abre modal "Exportação em andamento" quando começa a copiar
    - Modal fecha automaticamente quando termina
    - Detectamos observando quando clipboard para de crescer

    Args:
        max_tempo: Tempo máximo de espera em segundos (padrão: 15 minutos = 900s)
        intervalo_check: Intervalo entre verificações em segundos (padrão: 3)
        estabilidade_segundos: Tempo sem mudança para considerar completo (padrão: 30)

    Returns:
        str: Conteúdo do clipboard ou string vazia se falhar
    """
    import hashlib

    gui_log("=" * 70)
    gui_log("🔍 MONITORAMENTO INTELIGENTE DO CLIPBOARD")
    gui_log("=" * 70)
    gui_log(f"⏱️ Tempo máximo: {max_tempo//60} minutos")
    gui_log(f"🔄 Verificação a cada: {intervalo_check} segundos")
    gui_log(f"✅ Estabilidade requerida: {estabilidade_segundos} segundos")
    gui_log("")

    inicio = time.time()
    ultimo_hash = ""
    ultimo_tamanho = 0
    tempo_sem_mudanca = 0
    verificacoes = 0

    while (time.time() - inicio) < max_tempo:
        if not _rpa_running:
            gui_log("🛑 RPA interrompido durante monitoramento")
            return ""

        try:
            # Ler clipboard atual
            conteudo_atual = pyperclip.paste() or ""
            tamanho_atual = len(conteudo_atual)

            # Calcular hash para detectar mudanças
            hash_atual = hashlib.md5(conteudo_atual.encode('utf-8')).hexdigest() if conteudo_atual else ""

            verificacoes += 1
            tempo_decorrido = int(time.time() - inicio)

            # Se conteúdo mudou
            if hash_atual != ultimo_hash:
                if tamanho_atual > ultimo_tamanho:
                    # Clipboard cresceu - Oracle ainda está copiando
                    delta = tamanho_atual - ultimo_tamanho
                    gui_log(f"📊 [{tempo_decorrido}s] Clipboard cresceu +{delta:,} chars (total: {tamanho_atual:,} chars)")

                ultimo_hash = hash_atual
                ultimo_tamanho = tamanho_atual
                tempo_sem_mudanca = 0  # Resetar contador
            else:
                # Conteúdo não mudou
                tempo_sem_mudanca += intervalo_check

                if tamanho_atual > 100:  # Só considerar se tiver conteúdo
                    gui_log(f"⏸️ [{tempo_decorrido}s] Clipboard estável por {tempo_sem_mudanca}s ({tamanho_atual:,} chars)")

                    # Se estável pelo tempo requerido, consideramos concluído
                    if tempo_sem_mudanca >= estabilidade_segundos:
                        linhas = conteudo_atual.count('\n')
                        tamanho_kb = len(conteudo_atual.encode('utf-8')) / 1024

                        gui_log("")
                        gui_log("=" * 70)
                        gui_log("✅ CLIPBOARD ESTABILIZADO - CÓPIA COMPLETA!")
                        gui_log("=" * 70)
                        gui_log(f"📊 Linhas: {linhas:,}")
                        gui_log(f"📦 Tamanho: {tamanho_kb:.2f} KB ({tamanho_atual:,} caracteres)")
                        gui_log(f"⏱️ Tempo total: {tempo_decorrido}s ({tempo_decorrido//60}min {tempo_decorrido%60}s)")
                        gui_log(f"🔍 Verificações: {verificacoes}")
                        gui_log("=" * 70)

                        return conteudo_atual
                else:
                    gui_log(f"⏳ [{tempo_decorrido}s] Aguardando Oracle começar a copiar...")

            # Aguardar próxima verificação
            time.sleep(intervalo_check)

        except Exception as e:
            gui_log(f"⚠️ Erro ao monitorar clipboard: {e}")
            time.sleep(intervalo_check)

    # Timeout atingido
    gui_log("")
    gui_log("=" * 70)
    gui_log(f"⏰ TIMEOUT ATINGIDO ({max_tempo//60} minutos)")
    gui_log("=" * 70)

    # Retornar o que tiver no clipboard mesmo com timeout
    conteudo_final = pyperclip.paste() or ""
    if len(conteudo_final) > 100:
        gui_log(f"⚠️ Retornando conteúdo parcial: {len(conteudo_final):,} caracteres")
        return conteudo_final
    else:
        gui_log("❌ Clipboard vazio após timeout")
        return ""

# =================== CONTROLE GLOBAL PARA GUI ===================
_rpa_running = False
_gui_log_callback = None

def set_gui_log_callback(callback):
    """Define callback para enviar logs para a GUI"""
    global _gui_log_callback
    _gui_log_callback = callback

def gui_log(msg):
    """Envia log para GUI se callback estiver definido"""
    if _gui_log_callback:
        _gui_log_callback(msg)
    else:
        print(msg)

def stop_rpa():
    """Para o RPA externamente (para ser chamado pela GUI)"""
    global _rpa_running
    _rpa_running = False
    _keep_awake_stop.set()

def is_rpa_running():
    """Verifica se RPA está rodando"""
    return _rpa_running

# =================== UM CICLO ===================
def run_once() -> bool:
    """
    Executa um ciclo completo do RPA.
    Retorna True se bem-sucedido, False caso contrário.
    SEMPRE fecha a bancada no final (try/finally).
    """
    if not _rpa_running:
        return False

    # AUTENTICAR GOOGLE SHEETS (primeira vez)
    global _google_authenticated
    if not hasattr(run_once, '_google_authenticated'):
        run_once._google_authenticated = False

    if not run_once._google_authenticated and GOOGLE_SHEETS_AVAILABLE:
        gui_log("=" * 70)
        gui_log("🔐 AUTENTICANDO GOOGLE SHEETS (PRIMEIRA VEZ)")
        gui_log("=" * 70)

        try:
            from google_sheets_manager import get_sheets_service
            gui_log("   Verificando autenticação...")

            # Isso vai abrir o navegador se não tiver token
            service = get_sheets_service()

            gui_log("   ✅ GOOGLE SHEETS AUTENTICADO!")
            run_once._google_authenticated = True
        except Exception as e:
            gui_log(f"   ⚠️ Erro na autenticação: {e}")
            gui_log("   Continuando sem Google Sheets...")

        gui_log("=" * 70)
        gui_log("")

    # ABRIR BANCADA
    if not abrir_bancada():
        gui_log("❌ Falha ao abrir bancada")
        return False

    # Flag para controlar se conseguimos processar os dados
    sucesso_ciclo = False

    try:

            # 1) Clicar em "Detalhado" usando coordenadas fixas
        gui_log("📍 [1/9] Clicando em 'Detalhado'...")
        move_click(*COORD_DETALHADO)

        if not _rpa_running:
            return False

        # 2) PRESSIONAR ENTER (ao invés de clicar em Localizar)
        gui_log("⌨️ [2/9] Pressionando Enter...")
        pag.press('enter')
        time.sleep(1.2)  # SLEEP_ABERTURA

        if not _rpa_running:
            return False

        # 3) Aguardar grid carregar (~2 minutos)
        gui_log(f"⏳ [3/9] Aguardando {TEMPO_APOS_LOCALIZAR} segundos para grid carregar dados...")
        time.sleep(TEMPO_APOS_LOCALIZAR)
        focus_oracle()

        if not _rpa_running:
            return False

        # 4) Clicar na primeira célula da coluna 'Org.'
        gui_log("📍 [4/9] Clicando na célula Org...")
        move_click(*COORD_ORG_CELL)

        if not _rpa_running:
            return False

        # 5) Limpar clipboard ANTES de copiar (garantir dados novos)
        gui_log("🧹 [5/9] Limpando clipboard antes de copiar...")
        pyperclip.copy('')
        time.sleep(0.3)

        # 6) Abrir menu via teclado (mais estável que botão direito)
        gui_log("⌨️ [6/9] Abrindo menu de contexto (Shift+F10)...")
        pag.hotkey('shift', 'f10')
        time.sleep(1.5)
        focus_oracle()

        # 7) Selecionar "Copiar Todas as Linhas" via teclado
        gui_log("⌨️ [7/9] Navegando menu para 'Copiar Todas as Linhas'...")
        for i in range(3):  # Ajuste se a ordem do menu for diferente
            pag.press('down')
            time.sleep(0.25)
            gui_log(f"   Seta para baixo {i+1}/3")

        gui_log("   Pressionando Enter para copiar...")
        pag.press('enter')
        time.sleep(0.6)

        if not _rpa_running:
            return False

        # 8) MONITORAMENTO INTELIGENTE DO CLIPBOARD
        # Oracle abre modal "Exportação em andamento" que fecha quando termina
        gui_log("")
        gui_log("🎯 [8/9] Iniciando monitoramento inteligente do clipboard...")
        gui_log("💡 Modal 'Exportação em andamento' indica que cópia está em progresso")
        gui_log("💡 Sistema detectará automaticamente quando modal fechar (cópia completa)")
        gui_log("")

        # 🖱️ INICIAR MOVIMENTO CONTÍNUO DO MOUSE (anti-hibernação ULTRA-AGRESSIVA)
        gui_log("🖱️ Iniciando proteção anti-hibernação ULTRA-AGRESSIVA...")
        gui_log("   → Mouse: Move 5px a cada 1 segundo")
        gui_log("   → Teclado: Pressiona Shift a cada 15 segundos")
        gui_log("💡 Protege contra hibernação, screensaver e bloqueio de tela")
        stop_mouse_event = iniciar_movimento_mouse_continuo()

        texto = monitorar_clipboard_inteligente(
            max_tempo=15 * 60,        # Máximo 15 minutos
            intervalo_check=3,        # Verificar a cada 3 segundos (mais rápido)
            estabilidade_segundos=30  # Considerar completo após 30s sem mudança
        )

        if not texto or len(texto) < 50:
            gui_log("❌ ERRO: Clipboard vazio após todas as tentativas")
            gui_log("💡 O Oracle pode não ter conseguido copiar os dados")
            gui_log("💡 Verifique se a grid tem dados e tente novamente")

            # 🖱️ PARAR MOVIMENTO CONTÍNUO DO MOUSE (clipboard falhou)
            try:
                stop_mouse_event.set()
                gui_log("🖱️ Movimento contínuo do mouse parado (clipboard vazio)")
            except:
                pass

            return False

        # Dados copiados com sucesso!
        linhas = texto.count('\n')
        tamanho_kb = len(texto.encode('utf-8')) / 1024
        gui_log("=" * 70)
        gui_log("✅ DADOS COPIADOS COM SUCESSO!")
        gui_log(f"📊 Total: {linhas:,} linhas")
        gui_log(f"📦 Tamanho: {tamanho_kb:.2f} KB ({len(texto):,} caracteres)")
        gui_log("=" * 70)

        # Mostrar preview dos primeiros 500 caracteres
        preview = texto[:500].replace('\n', '\\n').replace('\t', '\\t')
        gui_log(f"👀 Preview (500 chars): {preview}...")

        # 9) PROCESSAR DADOS COPIADOS
        gui_log("")
        gui_log("=" * 70)
        gui_log("📋 [9/9] PROCESSANDO DADOS DA BANCADA")
        gui_log("=" * 70)

        df = texto_para_df(texto)
        gui_log(f"✅ Dados processados: {df.shape[0]:,} linhas x {df.shape[1]} colunas")

        # Validar dados antes de prosseguir
        if df.empty or df.shape[0] == 0:
            gui_log("⚠️ DataFrame vazio - nenhum dado para processar")

            # 🖱️ PARAR MOVIMENTO CONTÍNUO DO MOUSE (dados vazios)
            try:
                stop_mouse_event.set()
                gui_log("🖱️ Movimento contínuo do mouse parado (dados vazios)")
            except:
                pass

            return False

        # SALVAR EM EXCEL LOCAL
        gui_log("")
        gui_log("💾 Salvando dados em Excel local...")
        arquivo_salvo = salvar(df)

        if arquivo_salvo:
            gui_log(f"✅ Excel salvo: {arquivo_salvo}")
        else:
            gui_log("⚠️ Excel local falhou, mas continuando para Google Sheets...")

        # ENVIAR PARA GOOGLE SHEETS
        gui_log("")
        gui_log("=" * 70)
        gui_log("DEBUG: Verificando envio para Google Sheets...")
        gui_log(f"DEBUG: GOOGLE_SHEETS_AVAILABLE = {GOOGLE_SHEETS_AVAILABLE}")
        gui_log(f"DEBUG: df.empty = {df.empty}")
        gui_log(f"DEBUG: df.shape = {df.shape}")
        gui_log(f"DEBUG: df.columns = {list(df.columns)}")
        gui_log("=" * 70)

        if GOOGLE_SHEETS_AVAILABLE and not df.empty:
            gui_log("")
            gui_log("☁️ Enviando dados para Google Sheets...")

            try:
                gui_log(f"📤 Chamando enviar_para_google_sheets()...")
                gui_log(f"   DataFrame: {df.shape[0]:,} linhas x {df.shape[1]} colunas")

                sucesso_sheets = enviar_para_google_sheets(df)

                gui_log("")
                gui_log("=" * 70)
                gui_log(f"📊 RETORNO da função: {sucesso_sheets} (tipo: {type(sucesso_sheets)})")
                gui_log("=" * 70)

                if sucesso_sheets:
                    gui_log("✅ Dados enviados com sucesso para Google Sheets (com Codigo e Data)!")
                    sucesso_ciclo = True
                else:
                    gui_log("❌ Envio para Google Sheets retornou False")
                    gui_log("💡 Verifique os logs acima da função enviar_para_google_sheets()")
                    sucesso_ciclo = (arquivo_salvo is not None)
            except Exception as e:
                gui_log("")
                gui_log("=" * 70)
                gui_log(f"❌ EXCEÇÃO ao enviar para Google Sheets")
                gui_log("=" * 70)
                gui_log(f"Tipo: {type(e).__name__}")
                gui_log(f"Mensagem: {e}")
                import traceback
                gui_log("Stack trace completo:")
                gui_log(traceback.format_exc())
                gui_log("=" * 70)
                sucesso_ciclo = (arquivo_salvo is not None)
        else:
            if not GOOGLE_SHEETS_AVAILABLE:
                gui_log("=" * 70)
                gui_log("⚠️ Google Sheets NÃO DISPONÍVEL")
                gui_log("=" * 70)
                gui_log(f"GOOGLE_SHEETS_AVAILABLE = {GOOGLE_SHEETS_AVAILABLE}")
                gui_log("💡 O módulo google_sheets_manager não foi importado corretamente")
                gui_log("💡 Verifique os logs de import no início da execução")
                gui_log("=" * 70)
            elif df.empty:
                gui_log("⚠️ DataFrame está vazio - pulando envio para Google Sheets")
            sucesso_ciclo = (arquivo_salvo is not None)

        gui_log("")
        gui_log("=" * 70)
        gui_log("✅ PROCESSAMENTO DA BANCADA CONCLUÍDO")
        gui_log("=" * 70)

        # 🖱️ PARAR MOVIMENTO CONTÍNUO DO MOUSE (sucesso)
        try:
            stop_mouse_event.set()
            gui_log("🖱️ Movimento contínuo do mouse parado")
        except:
            pass

    except Exception as e:
        gui_log("=" * 70)
        gui_log(f"❌ ERRO ao extrair dados da Bancada: {e}")
        gui_log("=" * 70)
        import traceback
        gui_log(traceback.format_exc())

        # 🖱️ PARAR MOVIMENTO CONTÍNUO DO MOUSE (erro)
        try:
            stop_mouse_event.set()
            gui_log("🖱️ Movimento contínuo do mouse parado (erro)")
        except:
            pass

        sucesso_ciclo = False

    finally:
        # SEMPRE FECHAR BANCADA no final do ciclo (sucesso ou falha)
        if _rpa_running:
            gui_log("")
            gui_log("🔄 Finalizando ciclo - fechando bancada...")
            fechar_bancada()
            gui_log("")

    return sucesso_ciclo

# =================== LOOP ===================
def main(single_run=False):
    """Função principal do RPA - pode ser chamada pela GUI ou linha de comando"""
    global _rpa_running
    _rpa_running = True

    gui_log("🤖 Robô iniciado. FAILSAFE: canto sup/esq. Ctrl+C para parar.")

    if single_run:
        gui_log("🎯 Modo execução única ativado - finalizar após sucesso")
    else:
        gui_log("🔄 MODO LOOP INFINITO ATIVADO")
        gui_log("   → Abrir bancada → Extrair dados → Fechar bancada → Repetir")
        gui_log("")

    # Iniciar keep-awake
    global _keep_awake_thread
    _keep_awake_stop.clear()
    _keep_awake_thread = threading.Thread(target=keep_awake_loop, args=(_keep_awake_stop,), daemon=True)
    _keep_awake_thread.start()

    backoff = 5
    ciclo = 0
    try:
        while _rpa_running:
            ciclo += 1
            gui_log(f"{'='*60}")
            gui_log(f"🔄 CICLO #{ciclo}")
            gui_log(f"{'='*60}")
            ok = run_once()
            if ok:
                gui_log("✅ Ciclo concluído com sucesso!")
                if single_run:
                    gui_log("🎉 Execução única finalizada. Encerrando RPA...")
                    _rpa_running = False
                    break
                backoff = 5
            else:
                if _rpa_running:
                    gui_log("❌ Ciclo falhou.")
                    if single_run:
                        gui_log("⚠️ Modo single run - Encerrando mesmo com falha...")
                        _rpa_running = False
                        break
                    time.sleep(backoff)
                    backoff = min(backoff*2, 90)

            if _rpa_running and not single_run:
                time.sleep(2)

    except KeyboardInterrupt:
        gui_log("🛑 Interrompido pelo usuário.")
    except pag.FailSafeException:
        gui_log("🛑 FAILSAFE acionado (mouse no canto sup/esq).")
    except Exception as e:
        gui_log(f"❌ Erro inesperado: {e}")
        import traceback
        gui_log(f"Stack trace: {traceback.format_exc()}")
    finally:
        # Parar keep-awake
        _rpa_running = False
        _keep_awake_stop.set()
        gui_log("")
        gui_log("="*60)
        gui_log("🏁 RPA FINALIZADO - Thread encerrada")
        gui_log("="*60)
        gui_log("💡 Clique em 'Iniciar RPA' para executar novamente")

if __name__ == "__main__":
    main()