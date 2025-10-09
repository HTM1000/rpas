# -*- coding: utf-8 -*-
import time
from io import StringIO
from pathlib import Path
import threading
import sys
import os

import pyautogui as pag
import pyperclip
import pandas as pd

# Importar Google Sheets manager
try:
    from google_sheets_manager import enviar_para_google_sheets
    GOOGLE_SHEETS_AVAILABLE = True
    print("[OK] Google Sheets manager importado com sucesso")
except ImportError as e:
    print(f"[WARN] Google Sheets nao disponivel (ImportError): {e}")
    GOOGLE_SHEETS_AVAILABLE = False
except Exception as e:
    print(f"[WARN] Google Sheets nao disponivel (Exception): {e}")
    import traceback
    traceback.print_exc()
    GOOGLE_SHEETS_AVAILABLE = False

# Focar janela por título (opcional)
try:
    from pygetwindow import getWindowsWithTitle
except Exception:
    getWindowsWithTitle = None

# =================== CONFIG ===================
# Compatível com .exe
BASE = Path(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))))
OUT = (BASE / "out"); OUT.mkdir(exist_ok=True)

# ===== COORDENADAS FIXAS (1440x900, 100% escala) =====
COORD_DETALHADO = (273, 358)    # Botão "Detalhado"
COORD_LOCALIZAR = (524, 689)    # Botão "Localizar"
COORD_ORG_CELL  = (318, 174)    # Primeira célula da coluna Org.

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

def move_click(x, y, right=False):
    """Move o mouse e clica na coordenada especificada"""
    pag.moveTo(x, y, duration=MOUSE_MOVE_DUR)
    pag.click(button='right' if right else 'left')
    time.sleep(SLEEP_POS_CLIQUE)

def ler_clipboard_sem_ctrlc(max_tentativas=10, espera=0.8) -> str:
    """
    Lê o clipboard do sistema SEM enviar Ctrl+C.
    Aguarda o Oracle terminar a cópia em background.
    """
    for tentativa in range(max_tentativas):
        txt = (pyperclip.paste() or "").strip()
        if txt:
            gui_log(f"[CLIPBOARD] Lido na tentativa {tentativa+1}: {len(txt)} caracteres")
            return txt
        time.sleep(espera)

    gui_log("[WARN] Clipboard permanece vazio após todas as tentativas")
    return ""

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

    # Manter apenas as 8 colunas desejadas
    colunas_finais = ['ORG.', 'SUB.', 'ENDEREÇO', 'ITEM', 'DESCRIÇÃO ITEM', 'REV.', 'UDM PRINCIPAL', 'EM ESTOQUE']
    colunas_disponiveis = [col for col in colunas_finais if col in df_renamed.columns]

    gui_log(f"📋 Colunas finais selecionadas: {colunas_disponiveis}")

    if len(colunas_disponiveis) == 0:
        gui_log("⚠️ Nenhuma coluna disponível após filtro! Retornando DataFrame original")
        return df

    return df_renamed[colunas_disponiveis]

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

# =================== KEEP-AWAKE ===================
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
    """
    if not _rpa_running:
        return False

    focus_oracle()

    # 1) Clicar em "Detalhado" usando coordenadas fixas
    gui_log("🖱️ Clicando em 'Detalhado'...")
    move_click(*COORD_DETALHADO)

    if not _rpa_running:
        return False

    # 2) Clicar em "Localizar" usando coordenadas fixas
    gui_log("🖱️ Clicando em 'Localizar'...")
    move_click(*COORD_LOCALIZAR)

    # Dar tempo para a grade abrir
    time.sleep(SLEEP_ABERTURA)
    focus_oracle()

    if not _rpa_running:
        return False

    # 3) Clicar na primeira célula da coluna 'Org.' usando coordenadas fixas
    gui_log("🖱️ Clicando na célula Org...")
    move_click(*COORD_ORG_CELL)

    if not _rpa_running:
        return False

    # 4) Limpar clipboard ANTES de copiar (garantir dados novos)
    gui_log("🧹 Limpando clipboard antes de copiar...")
    pyperclip.copy('')
    time.sleep(0.3)

    # 5) Abrir menu via teclado (mais estável que botão direito)
    gui_log("⌨️ Abrindo menu de contexto (Shift+F10)...")
    pag.hotkey('shift', 'f10')
    time.sleep(1.5)
    focus_oracle()

    # 6) Selecionar "Copiar Todas as Linhas" via teclado
    gui_log("⌨️ Navegando menu para 'Copiar Todas as Linhas'...")
    for _ in range(3):  # Ajuste se a ordem do menu for diferente
        pag.press('down')
        time.sleep(0.25)
    pag.press('enter')
    time.sleep(0.6)

    if not _rpa_running:
        return False

    # 7) Dar tempo para o Oracle iniciar a cópia
    gui_log("⏳ Aguardando Oracle iniciar cópia em background...")
    time.sleep(3.0)

    # 8) Aguardar Oracle processar (15 minutos máximo)
    # Como não usamos prints, aguardamos um tempo fixo generoso
    gui_log("⏳ Aguardando Oracle processar dados (pode levar vários minutos)...")
    time.sleep(POPUP_MAX)  # Aguarda o tempo máximo configurado

    if not _rpa_running:
        return False

    # 9) Ler clipboard SEM Ctrl+C
    gui_log("📋 Lendo clipboard (sem Ctrl+C)...")
    texto = ler_clipboard_sem_ctrlc(max_tentativas=20, espera=1.5)
    if not texto:
        gui_log("❌ ERRO: Clipboard vazio (o Oracle pode não ter copiado).")
        gui_log("💡 Verifique se o Oracle conseguiu copiar os dados.")
        return False

    # 10) Processar dados
    df = texto_para_df(texto)
    gui_log(f"📊 Dados capturados: {df.shape[0]:,} linhas x {df.shape[1]} colunas")

    # Validar dados antes de prosseguir
    if df.empty or df.shape[0] == 0:
        gui_log("⚠️ DataFrame vazio - nenhum dado para processar")
        return False

    # 11) Salvar Excel local (backup)
    arquivo_salvo = salvar(df)

    if arquivo_salvo:
        gui_log("✅ Dados salvos no Excel local com sucesso!")
    else:
        gui_log("⚠️ Excel local falhou, mas continuando para Google Sheets...")

    # 12) Enviar para Google Sheets
    gui_log(f"🔍 Verificando Google Sheets... GOOGLE_SHEETS_AVAILABLE={GOOGLE_SHEETS_AVAILABLE}")

    if GOOGLE_SHEETS_AVAILABLE:
        gui_log("☁️ Google Sheets DISPONÍVEL - Iniciando envio...")
        try:
            gui_log(f"📤 Enviando DataFrame: {df.shape[0]:,} linhas x {df.shape[1]} colunas")
            sucesso_sheets = enviar_para_google_sheets(df)
            gui_log(f"📊 Resultado do envio: {sucesso_sheets}")

            if sucesso_sheets:
                gui_log("✅ Dados enviados com sucesso para Google Sheets (com Codigo e Data)!")
                return True
            else:
                gui_log("❌ Envio para Google Sheets retornou False")
                return arquivo_salvo is not None
        except Exception as e:
            gui_log(f"❌ EXCEÇÃO ao enviar para Google Sheets: {type(e).__name__}: {e}")
            import traceback
            gui_log(f"Stack trace: {traceback.format_exc()}")
            return arquivo_salvo is not None
    else:
        gui_log("⚠️ Google Sheets NÃO CONFIGURADO (GOOGLE_SHEETS_AVAILABLE=False)")
        gui_log("💡 Verifique se google_sheets_manager.py foi incluído no executável")
        return arquivo_salvo is not None

# =================== LOOP ===================
def main(single_run=True):
    """Função principal do RPA - pode ser chamada pela GUI ou linha de comando"""
    global _rpa_running
    _rpa_running = True

    gui_log("🤖 Robô iniciado. FAILSAFE: canto sup/esq. Ctrl+C para parar.")

    if single_run:
        gui_log("🎯 Modo execução única ativado - finalizar após sucesso")
    else:
        gui_log("🔄 Modo loop contínuo ativado")

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