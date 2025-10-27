# -*- coding: utf-8 -*-
"""
RPA CICLO - Módulo Principal (Versão para GUI)
Orquestra a execução sequencial de processos no Oracle
"""

import json
import os
import sys
import time
import threading
import hashlib
from pathlib import Path
from datetime import datetime
import pyautogui
import keyboard  # Para monitorar tecla ESC
import re
from io import StringIO

# Importar notificador Telegram
try:
    from telegram_notifier import inicializar_telegram
    TELEGRAM_DISPONIVEL = True
except ImportError:
    TELEGRAM_DISPONIVEL = False
    print("[WARN] telegram_notifier não disponível - notificações desabilitadas")

# Configurar encoding UTF-8 para o console Windows
if sys.platform.startswith('win'):
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass

# Importar pandas
try:
    import pandas as pd
    PANDAS_DISPONIVEL = True
except ImportError:
    PANDAS_DISPONIVEL = False
    print("[WARN] pandas não disponível - processamento de bancada desabilitado")

# Importar OpenCV e numpy para detecção de imagens
try:
    import cv2
    import numpy as np
    OPENCV_DISPONIVEL = True
    print("[OK] OpenCV disponível para detecção de imagens")
except ImportError:
    OPENCV_DISPONIVEL = False
    print("[WARN] OpenCV não disponível - usando pyautogui para detecção")

# =================== OCR COM TESSERACT ===================
try:
    import pytesseract
    from PIL import ImageGrab, ImageEnhance

    # Configurar caminho do Tesseract (compatível com executável)
    if getattr(sys, 'frozen', False):
        # Se estiver rodando como .exe
        tesseract_path = os.path.join(sys._MEIPASS, 'tesseract', 'tesseract.exe')
    else:
        # Se estiver rodando como script Python
        tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    if os.path.isfile(tesseract_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        PYTESSERACT_DISPONIVEL = True
        print(f"[OK] Tesseract OCR habilitado: {tesseract_path}")
    else:
        PYTESSERACT_DISPONIVEL = False
        print(f"[WARN] Tesseract não encontrado em: {tesseract_path}")
except ImportError as e:
    PYTESSERACT_DISPONIVEL = False
    print(f"[WARN] pytesseract não disponível: {e}")

# Importar módulo Google Sheets (para ciclo)
try:
    from google_sheets_ciclo import registrar_ciclo, atualizar_ciclo
    GOOGLE_SHEETS_DISPONIVEL = True
except ImportError:
    GOOGLE_SHEETS_DISPONIVEL = False
    print("⚠️ Google Sheets (ciclo) não disponível")

# Importar módulo Google Sheets (para bancada)
try:
    from google_sheets_manager import enviar_para_google_sheets
    GOOGLE_SHEETS_BANCADA_DISPONIVEL = True
    print("[OK] Google Sheets (bancada) importado com sucesso")
except ImportError as e:
    GOOGLE_SHEETS_BANCADA_DISPONIVEL = False
    print(f"[WARN] Google Sheets (bancada) não disponível: {e}")

# Importar validador híbrido (substitui OCR)
try:
    from validador_hibrido import (
        validar_campo_oracle_hibrido,
        validar_campos_oracle_completo,
        detectar_erro_oracle
    )
    VALIDADOR_HIBRIDO_DISPONIVEL = True
    print("[OK] Validador Híbrido importado com sucesso")
except ImportError as e:
    VALIDADOR_HIBRIDO_DISPONIVEL = False
    print(f"[WARN] Validador Híbrido não disponível: {e}")

# =================== CONFIGURAÇÕES GLOBAIS ===================
BASE_DIR = Path(__file__).parent.resolve() if not getattr(sys, 'frozen', False) else Path(sys.executable).parent
CONFIG_FILE = BASE_DIR / "config.json"

# Compatibilidade com .exe
base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

# ─── CONFIGURAÇÕES DE MODO ──────────────────────────────────────────────────
# IMPORTANTE: Altere para True para testes, False para PRODUÇÃO
MODO_TESTE = False  # True = simula movimentos sem pyautogui | False = PRODUÇÃO
PARAR_QUANDO_VAZIO = False  # True = para quando vazio (teste) | False = continua rodando (PRODUÇÃO)
SIMULAR_FALHA_SHEETS = False  # True = força falhas para testar retry | False = PRODUÇÃO
LIMITE_ITENS_TESTE = 50  # Limite de itens por ciclo no modo teste

# Controle de execução
_rpa_running = False
_gui_log_callback = None
_ciclo_atual = 0
_data_inicio_ciclo = None
_dados_inseridos_oracle = False  # Rastreia se dados foram inseridos no Oracle neste ciclo
_telegram_notifier = None  # Instância do notificador Telegram

# ─── CACHE LOCAL ANTI-DUPLICAÇÃO (IGUAL AO RPA_ORACLE) ──────────────────────
class CacheLocal:
    """Cache persistente para evitar duplicações no Oracle"""

    def __init__(self, arquivo="processados.json"):
        # Usar data_path (diretório do executável) igual ao RPA_Oracle
        data_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        self.arquivo = os.path.join(data_path, arquivo)
        self.dados = self._carregar()
        self.lock = threading.Lock()
        # Criar arquivo vazio se não existir
        if not os.path.exists(self.arquivo) and not self.dados:
            self._salvar()

    def _carregar(self):
        """Carrega cache do disco (persiste entre execuções)"""
        if os.path.exists(self.arquivo):
            try:
                with open(self.arquivo, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                gui_log(f"Erro ao carregar cache: {e}")
                return {}
        return {}

    def _salvar(self):
        """Salva cache no disco SEM lock para evitar deadlock (igual RPA_Oracle)"""
        try:
            # Converter dados para JSON string primeiro (para detectar erros de serialização)
            json_str = json.dumps(self.dados, indent=2, ensure_ascii=False)

            # Salvar em arquivo temporário primeiro
            temp_arquivo = self.arquivo + ".tmp"
            with open(temp_arquivo, 'w', encoding='utf-8') as f:
                f.write(json_str)
                f.flush()
                os.fsync(f.fileno())  # Garantir que foi escrito no disco

            # Substituir arquivo original pelo temporário
            if os.path.exists(self.arquivo):
                os.replace(temp_arquivo, self.arquivo)
            else:
                os.rename(temp_arquivo, self.arquivo)

        except Exception as e:
            gui_log(f"[ERRO] Falha ao salvar cache: {e}")
            # Tentar limpar arquivo temporário se existir
            try:
                temp_arquivo = self.arquivo + ".tmp"
                if os.path.exists(temp_arquivo):
                    os.remove(temp_arquivo)
            except:
                pass

    def ja_processado(self, id_item):
        """Verifica se ID já foi processado"""
        with self.lock:
            return id_item in self.dados

    def adicionar(self, id_item, linha_atual, item, quantidade, referencia, status="pendente"):
        """Adiciona ao cache APÓS Ctrl+S (status pendente)"""
        # VALIDAÇÃO: não permitir IDs vazios no cache
        if not id_item or str(id_item).strip() == "":
            gui_log(f"[ERRO CACHE] Tentativa de adicionar ID vazio ao cache! Linha: {linha_atual}, Item: {item}")
            return False

        # Preparar dados antes do lock
        dados_item = {
            "linha_atual": linha_atual,
            "item": item,
            "quantidade": quantidade,
            "referencia": referencia,
            "timestamp_processamento": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status_sheets": status
        }

        # Adicionar aos dados com lock
        with self.lock:
            self.dados[id_item] = dados_item

        # Salvar sem lock para evitar deadlock
        self._salvar()
        return True

    def marcar_concluido(self, id_item):
        """Remove do cache quando Sheets for atualizado com sucesso (igual RPA_Oracle)"""
        # Verificar e remover com lock
        removido = False
        with self.lock:
            if id_item in self.dados:
                del self.dados[id_item]
                removido = True

        # Salvar sem lock para evitar deadlock
        if removido:
            self._salvar()

        return removido

    def get_pendentes(self):
        """Retorna lista de Data Hora Sep. pendentes para retry"""
        with self.lock:
            return [
                data_hora for data_hora, dados in self.dados.items()
                if dados.get("status_sheets") == "pendente"
            ]

# =================== CALLBACKS PARA GUI ===================
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
    gui_log("🛑 Solicitação de parada recebida")

    # 🔧 CORREÇÃO CRÍTICA: Forçar parada após 3 segundos se não parar naturalmente
    import threading
    def forcar_parada():
        import time
        time.sleep(3)  # Aguarda 3s para parada natural
        if not _rpa_running:  # Se ainda está marcado como parado
            gui_log("⚠️ RPA não parou naturalmente em 3s - FORÇANDO sys.exit()")
            import sys
            sys.exit(0)  # Força parada do programa

    thread_forcada = threading.Thread(target=forcar_parada, daemon=True)
    thread_forcada.start()

def is_rpa_running():
    """Verifica se RPA está rodando"""
    return _rpa_running

# =================== CARREGAMENTO DE CONFIGURAÇÃO ===================
def carregar_config():
    """Carrega as configurações do arquivo config.json"""
    try:
        config_path = os.path.join(base_path, "config.json")
        if not os.path.exists(config_path):
            config_path = CONFIG_FILE

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        gui_log("✅ Configurações carregadas")
        return config
    except FileNotFoundError:
        gui_log(f"❌ Arquivo de configuração não encontrado: {CONFIG_FILE}")
        raise
    except json.JSONDecodeError as e:
        gui_log(f"❌ Erro ao decodificar JSON: {e}")
        raise

# =================== FUNÇÕES AUXILIARES ===================
def indice_para_coluna(idx):
    """Converte índice numérico (0-based) para letra de coluna do Google Sheets
    0 -> A, 1 -> B, 25 -> Z, 26 -> AA, 27 -> AB, 28 -> AC, etc.
    """
    resultado = ""
    idx += 1  # Google Sheets é 1-based
    while idx > 0:
        idx -= 1
        resultado = chr(65 + (idx % 26)) + resultado
        idx //= 26
    return resultado

def corrigir_confusao_ocr(texto):
    """
    Corrige caracteres comumente confundidos pelo OCR.

    Confusões comuns:
    - A ↔ 4
    - B ↔ 8
    - O ↔ 0 (letra o ↔ zero)
    - I ↔ 1
    - S ↔ 5
    - Z ↔ 2

    MELHORIAS IMPLEMENTADAS:
    1. Correção de símbolos especiais: £→E, €→E (ex: "£20298" → "E20298")
    2. Correção de o→0 em qualquer posição (ex: "E2o294" → "E20294")
    3. Validação contextual para padrões letra+dígitos+letra
    4. Correção do último caractere (ex: "E20294" → "E2029A", "E20298" → "E2029B")

    Args:
        texto: Texto lido pelo OCR

    Returns:
        str: Texto com correções aplicadas
    """
    if not texto:
        return texto

    import re

    texto_original = texto
    texto_corrigido = texto.upper().strip()

    # ═══════════════════════════════════════════════════════════════
    # PASSO 0: Corrigir símbolos especiais confundidos (£ → E)
    # ═══════════════════════════════════════════════════════════════
    # OCR frequentemente confunde E com £ no início de códigos
    if texto_corrigido.startswith('£'):
        texto_corrigido = 'E' + texto_corrigido[1:]
        gui_log(f"🔧 [OCR SÍMBOLO] '£' → 'E' (início de código)")

    # Corrigir outros símbolos comuns
    texto_corrigido = texto_corrigido.replace('€', 'E')  # Euro → E
    texto_corrigido = texto_corrigido.replace('£', 'E')  # Libra → E (qualquer posição)

    # ═══════════════════════════════════════════════════════════════
    # PASSO 1: Corrigir confusões letra↔número em QUALQUER POSIÇÃO
    # ═══════════════════════════════════════════════════════════════
    # Detectar padrão: Começa com LETRA (contexto alfanumérico)
    if re.match(r'^[A-Z]', texto_corrigido):
        # Mapa de correções bidirecionais
        correcoes_posicao = {
            'o': '0',  # letra o minúscula → zero (CRÍTICO para "E2o294" → "E20294")
            'O': '0',  # letra O maiúscula → zero
            'l': '1',  # letra l minúscula → um
            'I': '1',  # letra I maiúscula → um (em contexto numérico)
            's': '5',  # letra s minúscula → cinco
            'S': '5',  # letra S maiúscula → cinco
            'z': '2',  # letra z minúscula → dois
            'Z': '2',  # letra Z maiúscula → dois
        }

        # Aplicar correções em todo o texto (exceto primeiro caractere que é letra)
        resultado = texto_corrigido[0]  # Preserva primeira letra
        for i, char in enumerate(texto_corrigido[1:], start=1):
            # Se encontrar letra minúscula em contexto numérico, corrigir
            if char in correcoes_posicao:
                # Verificar se há dígitos ao redor (contexto numérico)
                tem_digito_antes = i > 1 and texto_corrigido[i-1].isdigit()
                tem_digito_depois = i < len(texto_corrigido)-1 and texto_corrigido[i+1].isdigit()

                if tem_digito_antes or tem_digito_depois:
                    resultado += correcoes_posicao[char]
                else:
                    resultado += char
            else:
                resultado += char

        texto_corrigido = resultado

    # ═══════════════════════════════════════════════════════════════
    # PASSO 2: Correção do ÚLTIMO CARACTERE (letra confundida com número)
    # ═══════════════════════════════════════════════════════════════
    # Padrão: Letra + dígitos + NÚMERO_FINAL que pode ser letra
    # Ex: E20294 → E2029A (4→A), E20298 → E2029B (8→B)
    match = re.match(r'^([A-Z]+\d+)([0-9])$', texto_corrigido)

    if match:
        prefixo = match.group(1)  # Ex: "E2029"
        ultimo = match.group(2)    # Ex: "4" ou "8"

        # Mapa de confusão comum no final de códigos
        mapa_final = {
            '4': 'A',
            '8': 'B',
            '0': 'O',
            '1': 'I',
            '5': 'S',
            '2': 'Z'
        }

        if ultimo in mapa_final:
            texto_corrigido = prefixo + mapa_final[ultimo]

    # Log apenas se houve correção
    if texto_corrigido != texto_original.upper().strip():
        return texto_corrigido

    return texto

def verificar_campo_ocr(x, y, largura, altura, valor_esperado, nome_campo="Campo", salvar_debug=False):
    """
    Captura região da tela e usa OCR para verificar se o valor está correto.

    Args:
        x, y: Coordenadas do canto superior esquerdo do campo
        largura, altura: Dimensões da região a capturar
        valor_esperado: Texto que deveria estar no campo
        nome_campo: Nome do campo para logs
        salvar_debug: Se True, salva screenshot para debug (apenas em modo teste)

    Returns:
        tuple: (sucesso: bool, texto_lido: str, confianca: float)
    """
    if not PYTESSERACT_DISPONIVEL:
        gui_log("⚠️ [OCR] pytesseract não disponível, pulando validação visual")
        return (True, "", 0.0)

    try:
        # Capturar região específica
        screenshot = ImageGrab.grab(bbox=(x, y, x + largura, y + altura))

        if salvar_debug and MODO_TESTE:
            screenshot.save(f"debug_ocr_{nome_campo}.png")
            gui_log(f"[DEBUG] Screenshot salvo: debug_ocr_{nome_campo}.png")

        # Processar imagem (escala de cinza + contraste)
        screenshot_processado = screenshot.convert('L')
        enhancer = ImageEnhance.Contrast(screenshot_processado)
        screenshot_processado = enhancer.enhance(2.0)

        # Extrair texto com pytesseract
        texto = pytesseract.image_to_string(screenshot_processado, config='--psm 7').strip()

        # Tentar obter confiança (se disponível)
        try:
            ocr_data = pytesseract.image_to_data(screenshot_processado, output_type=pytesseract.Output.DICT)
            confiancas = [int(c) for c in ocr_data['conf'] if c != -1]
            confianca = sum(confiancas) / len(confiancas) if confiancas else 0
        except:
            confianca = 0

        return (True, texto, confianca)

    except Exception as e:
        gui_log(f"⚠️ [OCR] Erro ao ler campo {nome_campo}: {e}")
        return (False, "", 0.0)

def validar_campos_oracle_ocr(coords, item, quantidade, referencia, sub_o, end_o, sub_d, end_d, salvar_debug=False):
    """
    Valida visualmente se os campos do Oracle foram preenchidos (NÃO VAZIOS) usando OCR.

    SIMPLIFICADO: Apenas verifica se os campos contêm ALGUM texto, sem comparar valores.
    Isso evita falsos positivos de OCR (£ vs E, o vs 0, 4 vs A, etc).

    Args:
        coords: Dicionário com coordenadas dos campos
        item, quantidade, referencia, sub_o, end_o, sub_d, end_d: Valores esperados (apenas para referência COD)
        salvar_debug: Se True, salva screenshots

    Returns:
        tuple: (validacao_ok: bool, tipo_erro: str)
            - validacao_ok: True se passou, False se falhou
            - tipo_erro: "COD_VAZIO" se COD com campos DESTINO vazios, "" se passou
    """
    if not PYTESSERACT_DISPONIVEL:
        gui_log("⚠️ [OCR] pytesseract não disponível, pulando validação visual")
        return (True, "")

    gui_log("🔍 [OCR] Iniciando validação visual - APENAS verificando se campos NÃO estão VAZIOS...")
    gui_log("ℹ️  [OCR] Modo simplificado ativo:")
    gui_log("    ✓ Verifica presença de texto em cada campo (sem comparar valores)")
    gui_log("    ✓ Detecta campos vazios que deveriam estar preenchidos")
    gui_log("    ✓ Para referência COD: valida campos DESTINO preenchidos")

    try:
        # Detectar se é referência COD (precisa validar campos DESTINO)
        eh_cod = referencia and referencia.upper().strip().startswith("COD")

        if eh_cod:
            gui_log("[OCR] 📋 Referência COD detectada - validando campos DESTINO (não devem estar vazios)")
        else:
            gui_log("[OCR] 📋 Referência MOV/OUTRO - validando campos ORIGEM (não devem estar vazios)")

        # ════════════════════════════════════════════════════════════════════
        # CAPTURA E OCR DA REGIÃO DOS CAMPOS
        # ════════════════════════════════════════════════════════════════════
        X_INICIO = 67
        Y_INICIO = 50
        LARGURA_TOTAL = 1236
        ALTURA_TOTAL = 130

        # Capturar imagem
        screenshot = ImageGrab.grab(bbox=(X_INICIO, Y_INICIO, X_INICIO + LARGURA_TOTAL, Y_INICIO + ALTURA_TOTAL))
        if salvar_debug:
            screenshot.save("debug_ocr_campos.png")

        # Processar imagem
        from PIL import ImageEnhance
        screenshot_processado = screenshot.convert('L')
        enhancer = ImageEnhance.Contrast(screenshot_processado)
        screenshot_processado = enhancer.enhance(2.0)

        # OCR com detecção de posição
        import pandas as pd
        ocr_data = pytesseract.image_to_data(screenshot_processado, config='--psm 6', output_type=pytesseract.Output.DICT)
        df_ocr = pd.DataFrame(ocr_data)
        df_ocr = df_ocr[df_ocr['conf'] != -1]
        df_ocr['text'] = df_ocr['text'].str.strip()
        df_ocr = df_ocr[df_ocr['text'] != '']

        gui_log(f"[OCR] 📊 Total de palavras detectadas: {len(df_ocr)}")

        # Log simplificado (apenas primeiras 10 palavras)
        textos_sample = df_ocr['text'].head(10).tolist()
        textos_formatados = ', '.join([f"'{t}'" for t in textos_sample])
        gui_log(f"[OCR] Exemplo de textos: {textos_formatados}...")

        # ════════════════════════════════════════════════════════════════════
        # FUNÇÃO AUXILIAR: Buscar header no OCR
        # ════════════════════════════════════════════════════════════════════
        def encontrar_header(df, texto_header):
            """Busca header no DataFrame OCR (busca aproximada)"""
            texto_norm = texto_header.upper().replace(" ", "")
            for _, row in df.iterrows():
                texto_lido = str(row['text']).upper().replace(" ", "")
                if texto_norm in texto_lido or texto_lido in texto_norm:
                    return row
            return None

        # ════════════════════════════════════════════════════════════════════
        # VALIDAÇÃO HÍBRIDA: Campos essenciais + Validação por maioria
        # ════════════════════════════════════════════════════════════════════

        # CAMPOS CRÍTICOS (devem SEMPRE estar preenchidos)
        campos_criticos = ["Item", "Quantidade", "Referência"]

        # CAMPOS OPCIONAIS (validação por maioria)
        campos_opcionais = ["Subinvent.", "Endereço"]

        # CAMPOS DESTINO (validação especial para COD)
        campos_destino = ["Para Subinv.", "Para Loc."]

        # Contadores
        erros_criticos = []
        campos_validados = []  # Lista de (campo, passou)

        # ════════════════════════════════════════════════════════════════════
        # 1. VALIDAR CAMPOS CRÍTICOS (Item, Quantidade, Referência)
        # ════════════════════════════════════════════════════════════════════
        gui_log("[OCR] 🎯 Validando campos CRÍTICOS (devem estar preenchidos):")

        for header_nome in campos_criticos:
            header_row = encontrar_header(df_ocr, header_nome)

            if header_row is not None:
                header_x = header_row['left']
                header_y = header_row['top']
                margem_x = 40

                valores_abaixo = df_ocr[
                    (df_ocr['top'] > header_y) &
                    (df_ocr['left'].between(header_x - margem_x, header_x + margem_x)) &
                    (df_ocr['text'].str.strip() != '')
                ]

                if len(valores_abaixo) > 0:
                    textos = valores_abaixo['text'].tolist()
                    gui_log(f"  ✅ '{header_nome}': OK (valores: {textos[:2]})")
                    campos_validados.append((header_nome, True))
                else:
                    gui_log(f"  ❌ '{header_nome}': VAZIO!")
                    erros_criticos.append(f"{header_nome} está vazio (CRÍTICO)")
                    campos_validados.append((header_nome, False))
            else:
                gui_log(f"  ⚠️ '{header_nome}': Header não encontrado")
                erros_criticos.append(f"{header_nome} não encontrado")
                campos_validados.append((header_nome, False))

        # ════════════════════════════════════════════════════════════════════
        # 2. VALIDAR CAMPOS OPCIONAIS (Subinvent., Endereço)
        # ════════════════════════════════════════════════════════════════════
        gui_log("[OCR] 📋 Validando campos OPCIONAIS:")

        for header_nome in campos_opcionais:
            header_row = encontrar_header(df_ocr, header_nome)

            if header_row is not None:
                header_x = header_row['left']
                header_y = header_row['top']
                margem_x = 40

                valores_abaixo = df_ocr[
                    (df_ocr['top'] > header_y) &
                    (df_ocr['left'].between(header_x - margem_x, header_x + margem_x)) &
                    (df_ocr['text'].str.strip() != '')
                ]

                if len(valores_abaixo) > 0:
                    textos = valores_abaixo['text'].tolist()
                    gui_log(f"  ✅ '{header_nome}': OK (valores: {textos[:2]})")
                    campos_validados.append((header_nome, True))
                else:
                    gui_log(f"  ⚠️ '{header_nome}': VAZIO (não crítico)")
                    campos_validados.append((header_nome, False))
            else:
                gui_log(f"  ⚠️ '{header_nome}': Header não encontrado")
                campos_validados.append((header_nome, False))

        # ════════════════════════════════════════════════════════════════════
        # 3. VALIDAR CAMPOS DESTINO (Para Subinv., Para Loc.)
        # ════════════════════════════════════════════════════════════════════
        if eh_cod:
            gui_log("[OCR] 🔍 REFERÊNCIA COD - Validando campos DESTINO (devem estar preenchidos):")
        else:
            gui_log("[OCR] 🔍 REFERÊNCIA MOV/OUTRO - Validando campos DESTINO:")

        erros_destino = []

        for header_nome in campos_destino:
            header_row = encontrar_header(df_ocr, header_nome)

            if header_row is not None:
                header_x = header_row['left']
                header_y = header_row['top']
                margem_x = 40

                # Buscar textos abaixo, EXCLUINDO o próprio header
                valores_abaixo = df_ocr[
                    (df_ocr['top'] > header_y + 5) &  # +5 pixels para evitar pegar o header
                    (df_ocr['left'].between(header_x - margem_x, header_x + margem_x)) &
                    (df_ocr['text'].str.strip() != '')
                ]

                # Filtrar textos que não sejam parte do header
                textos_validos = []
                for _, row in valores_abaixo.iterrows():
                    texto = str(row['text']).strip().upper()
                    # Ignorar se for parte do header
                    if texto not in ['PARA', 'SUBINV', 'SUBINV.', 'LOC', 'LOC.']:
                        textos_validos.append(row['text'])

                if len(textos_validos) > 0:
                    gui_log(f"  ✅ '{header_nome}': OK (valores: {textos_validos[:2]})")
                    campos_validados.append((header_nome, True))
                else:
                    if eh_cod:
                        # Para COD: campo destino vazio é ERRO CRÍTICO
                        gui_log(f"  ❌ '{header_nome}': VAZIO (COD precisa destino preenchido)!")
                        erros_destino.append(f"{header_nome} está vazio (COD)")
                        campos_validados.append((header_nome, False))
                    else:
                        # Para MOV/OUTRO: campo destino vazio é OK
                        gui_log(f"  ⚠️ '{header_nome}': VAZIO (OK para MOV)")
                        campos_validados.append((header_nome, False))
            else:
                gui_log(f"  ⚠️ '{header_nome}': Header não encontrado")
                campos_validados.append((header_nome, False))

        # ════════════════════════════════════════════════════════════════════
        # RESULTADO DA VALIDAÇÃO: Decisão inteligente
        # ════════════════════════════════════════════════════════════════════
        gui_log("[OCR] 📊 RESULTADO DA VALIDAÇÃO:")

        # Calcular estatísticas
        total_campos = len(campos_validados)
        campos_ok = sum(1 for _, passou in campos_validados if passou)
        taxa_aprovacao = (campos_ok / total_campos * 100) if total_campos > 0 else 0

        gui_log(f"  Total de campos: {total_campos}")
        gui_log(f"  Campos OK: {campos_ok}")
        gui_log(f"  Taxa de aprovação: {taxa_aprovacao:.1f}%")

        # REGRAS DE DECISÃO:
        # 1. Se TEM erros CRÍTICOS → FALHA
        # 2. Se COD com campos DESTINO vazios → FALHA
        # 3. Se taxa aprovação >= 70% → PASSA
        # 4. Caso contrário → FALHA

        erros_finais = []

        # Regra 1: Erros críticos
        if erros_criticos:
            gui_log(f"  ❌ FALHA: {len(erros_criticos)} erro(s) CRÍTICO(S)")
            erros_finais.extend(erros_criticos)

        # Regra 2: COD com destino vazio
        if eh_cod and erros_destino:
            gui_log(f"  ❌ FALHA: COD com campos DESTINO vazios")
            erros_finais.extend(erros_destino)

        # Regra 3: Taxa de aprovação
        if not erros_finais:  # Só verifica se não tem erros críticos
            if taxa_aprovacao >= 70:
                gui_log(f"  ✅ APROVADO: Taxa de aprovação >= 70% ({taxa_aprovacao:.1f}%)")
            else:
                gui_log(f"  ❌ FALHA: Taxa de aprovação < 70% ({taxa_aprovacao:.1f}%)")
                erros_finais.append(f"Taxa de aprovação insuficiente ({taxa_aprovacao:.1f}%)")

        # Decisão final
        if erros_finais:
            gui_log(f"❌ [OCR] Validação FALHOU - {len(erros_finais)} problema(s) encontrado(s):")
            for erro in erros_finais:
                gui_log(f"   - {erro}")

            # Detectar tipo de erro
            tipo_erro = "COD_VAZIO" if eh_cod and any("vazio" in e.lower() for e in erros_finais) else "OUTRO"
            return (False, tipo_erro)
        else:
            gui_log(f"✅ [OCR] Validação APROVADA! ({campos_ok}/{total_campos} campos OK)")
            return (True, "")

    except Exception as e:
        gui_log(f"⚠️ [OCR] Erro na validação: {e}")
        import traceback
        gui_log(traceback.format_exc())
        return (True, "")  # Em caso de erro, não bloqueia

# =================== FUNÇÕES DE AUTOMAÇÃO ===================
def clicar_coordenada(x, y, duplo=False, clique_pausa_duplo=False, descricao=""):
    """Clica em uma coordenada específica na tela"""
    if descricao:
        gui_log(f"🖱️ {descricao}")

    if MODO_TESTE:
        gui_log(f"[MODO TESTE] Simulando clique em ({x}, {y})")
        time.sleep(0.2)
        return

    pyautogui.moveTo(x, y, duration=0.8)
    time.sleep(0.5)

    if clique_pausa_duplo:
        # Bancada: click → espera 2s → doubleClick (igual você faz manualmente)
        pyautogui.click()
        gui_log("⏳ Aguardando 2s...")
        time.sleep(2.0)
        gui_log("🖱️ Executando doubleClick()...")
        pyautogui.doubleClick()
    elif duplo:
        # Duplo clique nativo do pyautogui
        pyautogui.doubleClick()
    else:
        pyautogui.click()

    time.sleep(1.0)

def digitar_texto(texto, pressionar_teclas=None):
    """Digita um texto e opcionalmente pressiona teclas adicionais"""
    gui_log(f"⌨️ Digitando: {texto}")

    if MODO_TESTE:
        gui_log(f"[MODO TESTE] Simulando digitação de '{texto}'")
        if pressionar_teclas:
            gui_log(f"[MODO TESTE] Simulando teclas: {', '.join(pressionar_teclas)}")
        time.sleep(0.2)
        return

    pyautogui.write(texto)
    time.sleep(0.3)

    if pressionar_teclas:
        for tecla in pressionar_teclas:
            gui_log(f"⌨️ Pressionando: {tecla.upper()}")
            pyautogui.press(tecla)
            time.sleep(0.3)

def iniciar_movimento_mouse_continuo():
    """
    Inicia uma thread que move o mouse continuamente a cada 1 segundo
    para evitar hibernação durante operações longas (processamento, upload)

    Returns:
        threading.Event: Evento para parar a thread quando necessário
    """
    import threading
    import time as time_module

    stop_event = threading.Event()

    def mover_mouse_loop():
        global _rpa_running
        contador = 0
        inicio_thread = time_module.time()

        while not stop_event.is_set() and _rpa_running:  # 🔧 CORREÇÃO: Verificar _rpa_running
            try:
                if not MODO_TESTE:
                    # A cada 15 segundos, pressiona Shift (mais efetivo contra bloqueio de tela)
                    if contador > 0 and contador % 15 == 0:
                        pyautogui.press('shift')
                        gui_log(f"⌨️ [Thread] Shift pressionado (anti-bloqueio de tela)")
                    else:
                        # Pegar posição atual
                        x_atual, y_atual = pyautogui.position()

                        # SEGURANÇA: Se mouse estiver perto do FAILSAFE, move para posição segura
                        if x_atual < 100 or y_atual < 100:
                            pyautogui.moveTo(400, 400, duration=0.1)
                        else:
                            # Move 5 pixels para direita e volta
                            pyautogui.moveRel(5, 0, duration=0.1)
                            pyautogui.moveRel(-5, 0, duration=0.1)

                contador += 1

                # Log a cada 30 movimentos (30 segundos)
                if contador % 30 == 0:
                    tempo_decorrido = int(time_module.time() - inicio_thread)
                    gui_log(f"🖱️ [Thread Anti-Hibernação] {contador} movimentos em {tempo_decorrido}s | Mouse + Shift")
            except Exception as e:
                pass  # Ignora erros silenciosamente na thread

            # Aguardar 1 segundo antes do próximo movimento
            stop_event.wait(1)

        # 🔧 CORREÇÃO: Log quando thread parar
        if not _rpa_running:
            gui_log("🛑 [Thread Anti-Hibernação] Parada por _rpa_running=False")

    # Iniciar thread em background
    thread = threading.Thread(target=mover_mouse_loop, daemon=True)
    thread.start()

    return stop_event

def aguardar_com_pausa(segundos, mensagem="Aguardando", evitar_hibernar=False):
    """
    Aguarda um tempo com possibilidade de interrupção

    Args:
        segundos: Tempo em segundos para aguardar
        mensagem: Mensagem a exibir
        evitar_hibernar: Se True, move o mouse periodicamente para evitar hibernação da tela
    """
    gui_log(f"⏳ {mensagem} ({segundos}s)...")
    if evitar_hibernar:
        gui_log("🖱️ Movendo mouse periodicamente para evitar hibernação da tela...")

    inicio = time.time()
    ultimo_movimento = time.time()

    while time.time() - inicio < segundos:
        if not _rpa_running:
            return False

        # Se evitar_hibernar está ativo, move o mouse a cada 5 segundos (mais agressivo)
        if evitar_hibernar and (time.time() - ultimo_movimento) >= 5:
            try:
                if not MODO_TESTE:
                    # Pega posição atual do mouse
                    x_atual, y_atual = pyautogui.position()

                    # SEGURANÇA: Se mouse estiver muito perto do canto (0,0) FAILSAFE, move para posição segura
                    if x_atual < 100 or y_atual < 100:
                        pyautogui.moveTo(400, 400, duration=0.1)
                        gui_log(f"⚠️ Mouse estava perto do FAILSAFE ({x_atual}, {y_atual}) - movido para posição segura")
                    else:
                        # Move um pouco (5 pixels) e volta
                        pyautogui.moveRel(5, 0, duration=0.1)
                        pyautogui.moveRel(-5, 0, duration=0.1)

                ultimo_movimento = time.time()
                gui_log("🖱️ Mouse movido para evitar hibernação")
            except Exception as e:
                gui_log(f"⚠️ Erro ao mover mouse: {e}")
                ultimo_movimento = time.time()

        time.sleep(0.5)

    return True

def aguardar_salvamento_concluido(timeout_travamento=120, intervalo_check=0.5):
    """
    Aguarda o salvamento ser concluído após Ctrl+S.

    Verifica se a tela voltou ao estado correto (tela_transferencia_subinventory.png).

    Lógica:
    - Aguarda 5s após Ctrl+S
    - Verifica se imagem da tela está correta
    - Se NÃO: aguarda mais 30s e verifica novamente
    - Se ainda NÃO: FALHOU ❌

    Args:
        timeout_travamento: Tempo máximo de espera (padrão: 120s) - NÃO USADO MAIS
        intervalo_check: Intervalo entre verificações (padrão: 0.5s) - NÃO USADO MAIS

    Returns:
        tuple: (sucesso: bool, tipo_resultado: str, tempo_espera: float)

        Tipos de resultado:
        - "SALVO_OK": Tela voltou ao estado correto
        - "TRAVADO": Tela não voltou após 2 tentativas (5s + 30s)
        - "RPA_PARADO": Usuário apertou botão PARAR
        - "QUEDA_REDE": Internet caiu
        - "IMAGEM_NAO_EXISTE": Imagem de validação não existe
    """
    global _rpa_running

    gui_log("⏳ [SALVAMENTO] Aguardando confirmação de salvamento...")
    gui_log(f"   Método: DETECÇÃO DE IMAGEM (tela_transferencia_subinventory.png)")
    gui_log(f"   Estratégia: 5s + (se falhar) 30s + (se falhar) ERRO")

    caminho_tela_transferencia = os.path.join(base_path, "informacoes", "tela_transferencia_subinventory.png")

    # Verificar se imagem existe
    if not os.path.isfile(caminho_tela_transferencia):
        gui_log(f"❌ [SALVAMENTO] Imagem não encontrada: {caminho_tela_transferencia}")
        return False, "IMAGEM_NAO_EXISTE", 0.0

    tempo_inicio = time.time()

    # ═══════════════════════════════════════════════════════════════
    # TENTATIVA 1: Verificar após 5 segundos
    # ═══════════════════════════════════════════════════════════════
    gui_log("⏳ [SALVAMENTO] Aguardando 5 segundos...")
    time.sleep(5)

    # Verificar se RPA foi parado
    if not _rpa_running:
        tempo_total = time.time() - tempo_inicio
        gui_log(f"🛑 [SALVAMENTO] RPA PARADO pelo usuário após {tempo_total:.1f}s")
        return False, "RPA_PARADO", tempo_total

    # Verificar queda de rede
    if verificar_queda_rede():
        tempo_total = time.time() - tempo_inicio
        gui_log(f"❌ [SALVAMENTO] QUEDA DE REDE detectada após {tempo_total:.1f}s")
        return False, "QUEDA_REDE", tempo_total

    gui_log("🔍 [SALVAMENTO] Verificando tela (tentativa 1/2)...")
    tela_correta = detectar_imagem_opencv(caminho_tela_transferencia, confidence=0.8, timeout=3)

    if tela_correta:
        tempo_total = time.time() - tempo_inicio
        gui_log(f"✅ [SALVAMENTO] Tela correta detectada! Salvamento confirmado em {tempo_total:.1f}s")
        return True, "SALVO_OK", tempo_total

    # ═══════════════════════════════════════════════════════════════
    # TENTATIVA 2: Aguardar mais 30 segundos e verificar novamente
    # ═══════════════════════════════════════════════════════════════
    gui_log("⚠️ [SALVAMENTO] Tela não detectada na tentativa 1")
    gui_log("⏳ [SALVAMENTO] Aguardando mais 30 segundos...")
    time.sleep(30)

    # Verificar se RPA foi parado
    if not _rpa_running:
        tempo_total = time.time() - tempo_inicio
        gui_log(f"🛑 [SALVAMENTO] RPA PARADO pelo usuário após {tempo_total:.1f}s")
        return False, "RPA_PARADO", tempo_total

    # Verificar queda de rede
    if verificar_queda_rede():
        tempo_total = time.time() - tempo_inicio
        gui_log(f"❌ [SALVAMENTO] QUEDA DE REDE detectada após {tempo_total:.1f}s")
        return False, "QUEDA_REDE", tempo_total

    gui_log("🔍 [SALVAMENTO] Verificando tela (tentativa 2/2)...")
    tela_correta = detectar_imagem_opencv(caminho_tela_transferencia, confidence=0.8, timeout=3)

    if tela_correta:
        tempo_total = time.time() - tempo_inicio
        gui_log(f"✅ [SALVAMENTO] Tela correta detectada! Salvamento confirmado em {tempo_total:.1f}s")
        return True, "SALVO_OK", tempo_total

    # ═══════════════════════════════════════════════════════════════
    # FALHA: Tela não voltou ao estado correto
    # ═══════════════════════════════════════════════════════════════
    tempo_total = time.time() - tempo_inicio
    gui_log(f"❌ [SALVAMENTO] FALHOU - Tela não voltou ao estado correto após {tempo_total:.1f}s")

    # Notificar via Telegram
    try:
        if _telegram_notifier and _telegram_notifier.enabled:
            _telegram_notifier.notificar_erro_critico(
                f"TELA DIVERGENTE\n\n"
                f"A tela não voltou ao estado esperado após salvamento.\n"
                f"Tempo esperado: {tempo_total:.1f}s\n\n"
                f"Verifique os arquivos debug_*.png para análise."
            )
    except:
        pass

    return False, "TRAVADO", tempo_total

def detectar_imagem_opencv(caminho_imagem, confidence=0.8, timeout=5, salvar_debug=True):
    """
    Detecta imagem na tela usando OpenCV com MULTI-ESCALA
    Procura a imagem mesmo se estiver em tamanho diferente

    Args:
        caminho_imagem: Caminho da imagem a ser detectada
        confidence: Confiança mínima (0.0 a 1.0)
        timeout: Tempo máximo de tentativas em segundos
        salvar_debug: Se True, salva screenshots para debug

    Returns:
        bool: True se encontrou a imagem, False caso contrário
    """
    if not OPENCV_DISPONIVEL:
        return False

    if not os.path.isfile(caminho_imagem):
        return False

    try:
        # Carregar a imagem de referência
        template = cv2.imread(caminho_imagem)
        if template is None:
            return False

        template_h, template_w = template.shape[:2]
        nome_imagem = os.path.basename(caminho_imagem)

        gui_log(f"[OPENCV] 🔍 Iniciando detecção de: {nome_imagem}")
        gui_log(f"[OPENCV]    Dimensões template: {template_w}x{template_h}")
        gui_log(f"[OPENCV]    Confiança mínima: {confidence:.2%}")

        inicio = time.time()
        tentativa = 0
        ultima_screenshot = None
        ultimo_template_usado = None
        melhor_score_global = 0

        while time.time() - inicio < timeout:
            tentativa += 1

            # Capturar screenshot da tela
            screenshot = ImageGrab.grab()
            screenshot_np = np.array(screenshot)
            screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

            screen_h, screen_w = screenshot_bgr.shape[:2]

            if tentativa == 1:
                gui_log(f"[OPENCV]    Dimensões tela: {screen_w}x{screen_h}")

            # Guardar screenshot para debug
            ultima_screenshot = screenshot_bgr.copy()

            # Verificar se template é maior que a tela
            if template_w > screen_w or template_h > screen_h:
                # Redimensionar template para caber na tela
                scale = min(screen_w / template_w, screen_h / template_h) * 0.95
                new_w = int(template_w * scale)
                new_h = int(template_h * scale)
                template_scaled = cv2.resize(template, (new_w, new_h))
                if tentativa == 1:
                    gui_log(f"[OPENCV] ⚠️ Template redimensionado: {template_w}x{template_h} -> {new_w}x{new_h}")
            else:
                template_scaled = template

            ultimo_template_usado = template_scaled.copy()

            # Fazer o template matching
            result = cv2.matchTemplate(screenshot_bgr, template_scaled, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val > melhor_score_global:
                melhor_score_global = max_val

            # Se a confiança for maior que o threshold
            if max_val >= confidence:
                gui_log(f"[OPENCV] ✅ Imagem detectada! Confiança: {max_val:.2%} (tentativa {tentativa})")

                # Salvar debug apenas em caso de SUCESSO (se habilitado)
                if salvar_debug:
                    try:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        debug_path_tela = f"debug_tela_atual_SUCESSO_{timestamp}.png"
                        cv2.imwrite(debug_path_tela, ultima_screenshot)
                        gui_log(f"[DEBUG] ✅ Tela salva em: {debug_path_tela}")
                    except:
                        pass

                return True

            # Se não encontrou mas template é diferente do tamanho da tela, tentar multi-escala
            if max_val < confidence and (template_w != screen_w or template_h != screen_h):
                # Tentar diferentes escalas
                melhor_score = max_val
                melhor_escala = 1.0

                for escala in [0.7, 0.8, 0.9, 1.0, 1.1, 1.2]:
                    new_w = int(template_w * escala)
                    new_h = int(template_h * escala)

                    # Pular se ficar maior que a tela
                    if new_w > screen_w or new_h > screen_h:
                        continue

                    template_test = cv2.resize(template, (new_w, new_h))
                    result_test = cv2.matchTemplate(screenshot_bgr, template_test, cv2.TM_CCOEFF_NORMED)
                    _, max_val_test, _, _ = cv2.minMaxLoc(result_test)

                    if max_val_test > melhor_score:
                        melhor_score = max_val_test
                        melhor_escala = escala
                        ultimo_template_usado = template_test.copy()

                    if max_val_test >= confidence:
                        gui_log(f"[OPENCV] ✅ Imagem detectada (escala {escala:.1f})! Confiança: {max_val_test:.2%}")

                        # Salvar debug apenas em caso de SUCESSO (se habilitado)
                        if salvar_debug:
                            try:
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                debug_path_tela = f"debug_tela_atual_SUCESSO_{timestamp}.png"
                                cv2.imwrite(debug_path_tela, ultima_screenshot)
                                gui_log(f"[DEBUG] ✅ Tela salva em: {debug_path_tela}")
                            except:
                                pass

                        return True

                if melhor_score > melhor_score_global:
                    melhor_score_global = melhor_score

                if tentativa == 1 or tentativa % 5 == 0:
                    gui_log(f"[OPENCV] Tentativa {tentativa}: Melhor score = {melhor_score:.2%} (esperado >= {confidence:.2%})")

            # Aguardar um pouco antes da próxima tentativa
            time.sleep(0.3)

        # ═══════════════════════════════════════════════════════════════
        # NÃO ENCONTROU - SALVAR DEBUG
        # ═══════════════════════════════════════════════════════════════
        gui_log(f"[OPENCV] ❌ Imagem NÃO detectada após {timeout}s")
        gui_log(f"[OPENCV] 📊 Melhor confiança alcançada: {melhor_score_global:.2%} (esperado >= {confidence:.2%})")

        if salvar_debug and ultima_screenshot is not None:
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                # Salvar tela capturada
                debug_path_tela = f"debug_tela_atual_{timestamp}.png"
                cv2.imwrite(debug_path_tela, ultima_screenshot)
                gui_log(f"[DEBUG] 💾 Tela capturada salva: {debug_path_tela}")

                # Salvar template usado
                if ultimo_template_usado is not None:
                    debug_path_template = f"debug_template_usado_{timestamp}.png"
                    cv2.imwrite(debug_path_template, ultimo_template_usado)
                    gui_log(f"[DEBUG] 💾 Template usado salvo: {debug_path_template}")

                # Criar imagem comparativa lado a lado
                try:
                    # Redimensionar para mesma altura
                    h1, w1 = ultima_screenshot.shape[:2]
                    h2, w2 = ultimo_template_usado.shape[:2]

                    if h1 > h2:
                        scale = h1 / h2
                        new_w2 = int(w2 * scale)
                        template_resized = cv2.resize(ultimo_template_usado, (new_w2, h1))
                        comparacao = np.hstack([ultima_screenshot, template_resized])
                    else:
                        scale = h2 / h1
                        new_w1 = int(w1 * scale)
                        screen_resized = cv2.resize(ultima_screenshot, (new_w1, h2))
                        comparacao = np.hstack([screen_resized, ultimo_template_usado])

                    debug_path_comp = f"debug_comparacao_{timestamp}.png"
                    cv2.imwrite(debug_path_comp, comparacao)
                    gui_log(f"[DEBUG] 💾 Comparação salva: {debug_path_comp}")
                except Exception as e:
                    gui_log(f"[DEBUG] ⚠️ Erro ao criar comparação: {e}")

                gui_log(f"[DEBUG] 📁 Verifique os arquivos debug_*.png na pasta do executável")

            except Exception as e:
                gui_log(f"[DEBUG] ⚠️ Erro ao salvar debug: {e}")

        return False

    except Exception as e:
        gui_log(f"[OPENCV] ⚠️ Erro na detecção: {e}")
        import traceback
        gui_log(f"[OPENCV] Stack: {traceback.format_exc()}")
        return False

def verificar_e_fechar_modal_qtd_negativa(timeout=3, fazer_ctrl_s=False):
    """
    Verifica se o modal de quantidade negativa apareceu e fecha com ENTER

    Args:
        timeout: Tempo máximo para procurar o modal (padrão: 3 segundos)
        fazer_ctrl_s: Se True, faz Ctrl+S após fechar modal (padrão: False)

    Returns:
        bool: True se modal foi detectado e fechado, False caso contrário

    IMPORTANTE: Quantidade negativa NÃO é erro! É uma operação válida.
    O Oracle exibe um modal de CONFIRMAÇÃO que precisa ser fechado.
    """
    global _rpa_running

    caminho = os.path.join(base_path, "informacoes", "qtd_negativa.png")

    if not os.path.isfile(caminho):
        return False

    # Tentar detectar com OpenCV (múltiplas tentativas durante timeout)
    encontrado = detectar_imagem_opencv(caminho, confidence=0.75, timeout=timeout)

    if encontrado:
        gui_log("✅ [QTD NEG] Modal de confirmação detectado!")

        # Aguardar 0.5 segundos antes de pressionar Enter
        time.sleep(0.5)

        gui_log("[QTD NEG] >> Pressionando ENTER (fechar modal)...")
        pyautogui.press("enter")
        gui_log("[QTD NEG] << ENTER pressionado")

        # Aguardar 1 segundo para o modal fechar
        time.sleep(1)

        if fazer_ctrl_s:
            gui_log("[QTD NEG] >> Pressionando CTRL+S (salvar)...")
            pyautogui.hotkey("ctrl", "s")
            gui_log("[QTD NEG] << CTRL+S pressionado")
            time.sleep(1)
            gui_log("✅ [QTD NEG] Modal fechado e registro salvo!")
        else:
            gui_log("✅ [QTD NEG] Modal fechado! Continuando preenchimento...")

        return True
    else:
        return False

def tratar_erro_oracle():
    """
    DEPRECATED - Use verificar_e_fechar_modal_qtd_negativa() com fazer_ctrl_s=True

    Mantido para compatibilidade - chama a nova função
    """
    gui_log("[QTD NEG] 🔍 Verificando modal após Ctrl+S...")
    if verificar_e_fechar_modal_qtd_negativa(timeout=5, fazer_ctrl_s=True):
        gui_log("✅ [QTD NEG] Quantidade negativa confirmada e salva com sucesso!")
    else:
        gui_log("[QTD NEG] ✅ Nenhum modal de confirmação detectado")

def verificar_erro_produto(service, range_str, linha_atual):
    """
    Verifica se há erro de produto (ErroProduto.png) que PARA a aplicação
    Usa OpenCV para detecção mais confiável

    Returns:
        bool: True se detectou erro de produto (aplicação deve parar)
    """
    global _rpa_running

    erro_produto_path = os.path.join(base_path, "informacoes", "ErroProduto.png")

    if not os.path.isfile(erro_produto_path):
        return False

    # Detectar com OpenCV (timeout de 3 segundos, confidence 0.8 igual RPA_Oracle)
    encontrado = detectar_imagem_opencv(erro_produto_path, confidence=0.8, timeout=3)

    if encontrado:
        gui_log("⚠️ [ERRO PRODUTO] DETECTADO erro de produto!")

        # Atualizar status no Sheets
        try:
            service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=range_str,
                valueInputOption="RAW",
                body={"values": [["PD"]]}
            ).execute()
            gui_log(f"[ERRO] Linha {linha_atual} marcada como 'PD' (pendente) por erro detectado.")
        except:
            pass

        _rpa_running = False
        gui_log("🛑 [ERRO PRODUTO] Detectado - Robô parado!")
        return True

    return False

def verificar_queda_rede():
    """
    Verifica se houve queda de rede/internet
    Se detectar queda_rede.png, PARA o robô imediatamente

    Returns:
        bool: True se detectou queda de rede (aplicação deve parar)
    """
    global _rpa_running

    caminho_queda_rede = os.path.join(base_path, "informacoes", "queda_rede.png")

    if not os.path.isfile(caminho_queda_rede):
        return False

    # Detectar com OpenCV (timeout curto - 1s)
    encontrado = detectar_imagem_opencv(caminho_queda_rede, confidence=0.8, timeout=1)

    if encontrado:
        gui_log("=" * 70)
        gui_log("❌❌❌ [QUEDA DE REDE] DETECTADA! ❌❌❌")
        gui_log("=" * 70)
        gui_log("🌐 Internet caiu ou conexão perdida com servidor!")
        gui_log("🛑 PARANDO ROBÔ IMEDIATAMENTE!")
        gui_log("⚠️ Verifique sua conexão de internet antes de reiniciar")
        gui_log("=" * 70)

        # Parar flag do RPA
        _rpa_running = False

        # IMPORTANTE: Raise exception para forçar parada IMEDIATA
        # Isso garante que o RPA pare independente de onde estiver no código
        raise Exception("QUEDA DE REDE DETECTADA - Robô parado por segurança")

    return False

def verificar_tempo_oracle_rapido():
    """
    Verificação RÁPIDA de timeout do Oracle (sem logs detalhados).
    Usada em loops e pontos frequentes.

    Returns:
        bool: True se detectou timeout do Oracle (aplicação deve parar)
    """
    global _rpa_running

    # Procurar em ambos os caminhos
    caminho_raiz = os.path.join(base_path, "tempo_oracle.png")
    caminho_info = os.path.join(base_path, "informacoes", "tempo_oracle.png")

    caminho_tempo_oracle = caminho_raiz if os.path.isfile(caminho_raiz) else caminho_info

    if os.path.isfile(caminho_tempo_oracle):
        try:
            encontrado = pyautogui.locateOnScreen(caminho_tempo_oracle, confidence=0.8)
            if encontrado:
                gui_log("⏱️⏱️⏱️ [TIMEOUT ORACLE] DETECTADO! Sistema Oracle expirou!")
                gui_log("🛑 PARANDO A APLICAÇÃO - O sistema Oracle deve ser REABERTO!")
                _rpa_running = False
                return True
        except:
            pass

    return False

def verificar_tempo_oracle(service, range_str, linha_atual):
    """
    Verifica se há timeout do Oracle (tempo_oracle.png) que PARA a aplicação

    Args:
        service: Serviço do Google Sheets
        range_str: Range da célula Status Oracle
        linha_atual: Número da linha atual

    Returns:
        bool: True se detectou timeout do Oracle (aplicação deve parar)
    """
    global _rpa_running

    # Procurar em ambos os caminhos
    caminho_raiz = os.path.join(base_path, "tempo_oracle.png")
    caminho_info = os.path.join(base_path, "informacoes", "tempo_oracle.png")

    caminho_tempo_oracle = caminho_raiz if os.path.isfile(caminho_raiz) else caminho_info

    gui_log(f"[TEMPO_ORACLE] Verificando tempo_oracle.png...")
    gui_log(f"[TEMPO_ORACLE] Caminho raiz: {caminho_raiz} - Existe: {os.path.isfile(caminho_raiz)}")
    gui_log(f"[TEMPO_ORACLE] Caminho info: {caminho_info} - Existe: {os.path.isfile(caminho_info)}")
    gui_log(f"[TEMPO_ORACLE] Usando: {caminho_tempo_oracle}")

    if os.path.isfile(caminho_tempo_oracle):
        try:
            gui_log("[TEMPO_ORACLE] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            gui_log("[TEMPO_ORACLE] Iniciando verificação de timeout do Oracle...")

            # Salvar screenshot ANTES de procurar (para debug)
            try:
                screenshot_path = "debug_tempo_oracle_tela.png"
                from PIL import ImageGrab
                screenshot = ImageGrab.grab()
                screenshot.save(screenshot_path)
                gui_log(f"[TEMPO_ORACLE] 📸 Screenshot salvo: {screenshot_path}")
            except Exception as e_screenshot:
                gui_log(f"[TEMPO_ORACLE] ⚠️ Não conseguiu salvar screenshot: {e_screenshot}")

            gui_log(f"[TEMPO_ORACLE] 🔍 Procurando imagem na tela (confidence=0.8)...")
            gui_log(f"[TEMPO_ORACLE] 📂 Caminho da imagem: {caminho_tempo_oracle}")

            encontrado = None
            try:
                encontrado = pyautogui.locateOnScreen(caminho_tempo_oracle, confidence=0.8)
                gui_log(f"[TEMPO_ORACLE] 🔎 Resultado da busca: {encontrado}")
            except Exception as e_locate:
                gui_log(f"[TEMPO_ORACLE] ⚠️ Exceção no locateOnScreen: {type(e_locate).__name__}: {e_locate}")
                import traceback
                gui_log(f"[TEMPO_ORACLE] Traceback:\n{traceback.format_exc()}")

            if encontrado:
                gui_log("[TEMPO_ORACLE] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                gui_log(f"[TEMPO_ORACLE] ⚠️⚠️⚠️ IMAGEM ENCONTRADA NA TELA! ⚠️⚠️⚠️")
                gui_log("[TEMPO_ORACLE] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                gui_log(f"[TEMPO_ORACLE] 📍 Localização completa: {encontrado}")
                gui_log(f"[TEMPO_ORACLE] 📊 Detalhes:")
                gui_log(f"[TEMPO_ORACLE]    - left (X): {encontrado.left}")
                gui_log(f"[TEMPO_ORACLE]    - top (Y): {encontrado.top}")
                gui_log(f"[TEMPO_ORACLE]    - width: {encontrado.width}")
                gui_log(f"[TEMPO_ORACLE]    - height: {encontrado.height}")
                gui_log("[TEMPO_ORACLE] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                gui_log("⏱️ [TIMEOUT ORACLE] Detectado TIMEOUT DO ORACLE!")
                gui_log("🛑 O sistema Oracle deve ser REABERTO!")
                gui_log("🛑 PARANDO A APLICAÇÃO conforme solicitado")

                # Marcar linha como "Timeout Oracle - Reabrir sistema" no Google Sheets
                try:
                    gui_log(f"[TEMPO_ORACLE] 📝 Marcando linha {linha_atual} como 'Timeout Oracle - Reabrir sistema'...")
                    service.spreadsheets().values().update(
                        spreadsheetId=SPREADSHEET_ID,
                        range=range_str,
                        valueInputOption="RAW",
                        body={"values": [["Timeout Oracle - Reabrir sistema"]]}
                    ).execute()
                    gui_log(f"[TEMPO_ORACLE] ✅ Linha {linha_atual} marcada como 'Timeout Oracle - Reabrir sistema'")
                except Exception as err_up:
                    gui_log(f"[TEMPO_ORACLE] ⚠️ Erro ao marcar linha {linha_atual} no Sheets: {err_up}")
                    import traceback
                    gui_log(f"[TEMPO_ORACLE] Traceback Sheets:\n{traceback.format_exc()}")

                # PARAR A APLICAÇÃO
                gui_log("[TEMPO_ORACLE] 🛑 Definindo _rpa_running = False...")
                _rpa_running = False
                gui_log("[TEMPO_ORACLE] 🛑 Aplicação será parada!")
                gui_log("[TEMPO_ORACLE] 🔄 AÇÃO NECESSÁRIA: Reabra o sistema Oracle e execute novamente")
                return True
            else:
                gui_log("[TEMPO_ORACLE] ✅ Nenhum timeout detectado (imagem não encontrada)")
                gui_log("[TEMPO_ORACLE] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        except Exception as e:
            gui_log("[TEMPO_ORACLE] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            gui_log(f"[TEMPO_ORACLE] ❌ EXCEÇÃO CAPTURADA: {type(e).__name__}: {e}")
            import traceback
            gui_log(f"[TEMPO_ORACLE] Traceback completo:\n{traceback.format_exc()}")
            gui_log("[TEMPO_ORACLE] ✅ Continuando normalmente (tratando como 'não encontrado')")
            gui_log("[TEMPO_ORACLE] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            pass
    else:
        gui_log("[TEMPO_ORACLE] ❌ Arquivo tempo_oracle.png NÃO ENCONTRADO em nenhum caminho!")

    return False

# =================== ETAPAS DO PROCESSO ===================
def etapa_01_transferencia_subinventario(config):
    """Etapa 1: Duplo clique em Transferência de Subinventário"""
    gui_log("📋 ETAPA 1: Transferência de Subinventário")

    coord = config["coordenadas"]["tela_01_transferencia_subinventario"]
    clicar_coordenada(coord["x"], coord["y"], duplo=True, descricao=coord["descricao"])

    tempo_espera = config["tempos_espera"]["apos_modal"]
    return aguardar_com_pausa(tempo_espera, "Aguardando abertura do modal")

def etapa_02_preencher_tipo(config):
    """Etapa 2: Preencher campo Tipo com SUB"""
    gui_log("📋 ETAPA 2: Preenchimento do Tipo")

    coord = config["coordenadas"]["tela_02_campo_tipo"]
    clicar_coordenada(coord["x"], coord["y"], descricao=coord["descricao"])

    time.sleep(0.5)
    digitar_texto(coord["digitar"], pressionar_teclas=coord["acoes"])

    tempo_espera = config["tempos_espera"]["entre_cliques"]
    return aguardar_com_pausa(tempo_espera, "Aguardando processamento")

def etapa_03_selecionar_funcionario(config):
    """Etapa 3: Selecionar funcionário Wallatas Moreira usando setas"""
    gui_log("📋 ETAPA 3: Seleção de Funcionário")

    # Clicar na pastinha
    coord_pastinha = config["coordenadas"]["tela_03_pastinha_funcionario"]
    clicar_coordenada(coord_pastinha["x"], coord_pastinha["y"], descricao=coord_pastinha["descricao"])

    tempo_espera = config["tempos_espera"]["apos_modal"]
    if not aguardar_com_pausa(tempo_espera, "Aguardando modal de funcionários"):
        return False

    # Método 1: Navegar com setas para baixo (9x) + Enter
    gui_log("⌨️ Navegando até Wallatas Moreira (9 setas para baixo)...")

    if MODO_TESTE:
        gui_log("[MODO TESTE] Simulando navegação e seleção de funcionário")
        time.sleep(0.5)
    else:
        time.sleep(1.0)

        # Pressionar 9 vezes a seta para baixo
        for i in range(9):
            pyautogui.press('down')
            time.sleep(0.2)
            gui_log(f"   Seta {i+1}/9")

        time.sleep(0.5)

        # Pressionar Enter para selecionar
        gui_log("⌨️ Pressionando Enter para selecionar Wallatas")
        pyautogui.press('enter')
        time.sleep(1.0)

        # Pressionar Enter novamente para confirmar o modal "Sim"
        gui_log("⌨️ Pressionando Enter para confirmar (Sim)")
        pyautogui.press('enter')
        time.sleep(1.0)

    tempo_espera = config["tempos_espera"]["entre_cliques"]
    return aguardar_com_pausa(tempo_espera, "Aguardando confirmação")

def etapa_05_executar_rpa_oracle(config, primeiro_ciclo=False):
    """Etapa 5: Processar linhas do Google Sheets no Oracle

    Args:
        config: Configurações do RPA
        primeiro_ciclo: Se True, após 2 tentativas sem itens, pula para Bancada
    """
    global _dados_inseridos_oracle
    _dados_inseridos_oracle = False  # Resetar flag no início

    gui_log("🤖 ETAPA 5: Processamento no Oracle")

    try:
        # Importar Google Sheets
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        # Autenticar Google Sheets
        SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
        SPREADSHEET_ID = "14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk"  # PLANILHA PRODUÇÃO ORACLE
        SHEET_NAME = "Separação"

        token_path = os.path.join(BASE_DIR, "token.json")
        creds_path = os.path.join(base_path, "CredenciaisOracle.json")

        creds = None
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, "w") as token:
                token.write(creds.to_json())

        service = build("sheets", "v4", credentials=creds)

        # Inicializar cache anti-duplicação
        cache = CacheLocal()  # Usa "processados.json" por padrão
        gui_log(f"💾 Cache carregado: {len(cache.dados)} itens processados anteriormente")
        gui_log(f"📂 Arquivo de cache: {cache.arquivo}")

        # Coordenadas dos campos no Oracle (para digitação - apenas x, y)
        coords = {
            "item": (101, 156),
            "sub_origem": (257, 159),
            "end_origem": (335, 159),
            "sub_destino": (485, 159),
            "end_destino": (553, 159),
            "quantidade": (672, 159),
            "Referencia": (768, 159),
        }

        # Coordenadas completas para validação híbrida (x, y, largura, altura)
        coords_validacao = {}
        if "campos_oracle_validacao" in config:
            campos_val = config["campos_oracle_validacao"]
            gui_log("✅ Coordenadas de validação carregadas do config.json")
            coords_validacao = {
                "campo_item": tuple(campos_val["campo_item"]),
                "campo_quantidade": tuple(campos_val["campo_quantidade"]),
                "campo_referencia": tuple(campos_val["campo_referencia"]),
                "campo_sub_o": tuple(campos_val["campo_sub_o"]),
                "campo_end_o": tuple(campos_val["campo_end_o"]),
                "campo_sub_d": tuple(campos_val["campo_sub_d"]),
                "campo_end_d": tuple(campos_val["campo_end_d"]),
            }
        else:
            # Fallback: usar coordenadas hardcoded (caso config.json esteja desatualizado)
            gui_log("⚠️ Usando coordenadas padrão (config.json antigo)")
            coords_validacao = {
                "campo_item": (67, 155, 118, 22),
                "campo_quantidade": (639, 155, 89, 22),
                "campo_referencia": (737, 155, 100, 22),
                "campo_sub_o": (208, 155, 101, 22),
                "campo_end_o": (316, 155, 101, 22),
                "campo_sub_d": (422, 155, 103, 22),
                "campo_end_d": (530, 155, 100, 22),
            }

        # Loop de espera até encontrar pelo menos 1 item para processar
        itens_processados = 0
        tentativas_verificacao = 0
        MAX_TENTATIVAS_PRIMEIRO_CICLO = 2  # Apenas 2 tentativas no primeiro ciclo

        while itens_processados == 0 and _rpa_running:
            # ═══════════════════════════════════════════════════════════════
            # 🔍 VERIFICAR TIMEOUT DO ORACLE (INÍCIO DO LOOP)
            # ═══════════════════════════════════════════════════════════════
            if verificar_tempo_oracle_rapido():
                gui_log("⏱️ TIMEOUT ORACLE DETECTADO no início do loop. Parando RPA.")
                return False

            tentativas_verificacao += 1

            # Buscar linhas para processar (Status = "CONCLUÍDO" e Status Oracle vazio)
            # IMPORTANTE: Buscar até coluna AC (ID está na coluna AC)
            res = service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{SHEET_NAME}!A1:AC"
            ).execute()

            valores = res.get("values", [])
            if not valores:
                gui_log("⚠️ Nenhuma linha encontrada no Google Sheets")
                if not aguardar_com_pausa(30, "Aguardando novas linhas no Google Sheets"):
                    return False
                continue

            headers, dados = valores[0], valores[1:]

            # Log de debug para verificar se ID está nos headers
            if "ID" in headers:
                idx_id = headers.index("ID")
                gui_log(f"✅ Coluna ID encontrada no índice {idx_id} (coluna {chr(65 + idx_id)})")
            else:
                gui_log(f"⚠️ AVISO: Coluna ID não encontrada nos headers!")
                gui_log(f"📋 Headers disponíveis: {', '.join(headers[:10])}... (total: {len(headers)})")

            # Filtrar linhas para processar
            # 🔒 TRAVA 4: Ignorar linhas com "PROCESSANDO..." APENAS se estiverem no cache
            linhas_processar = []
            for i, row in enumerate(dados):
                if len(row) < len(headers):
                    row += [''] * (len(headers) - len(row))
                idx_status_oracle = headers.index("Status Oracle")
                idx_status = headers.index("Status")
                idx_id = headers.index("ID") if "ID" in headers else -1

                status_oracle = row[idx_status_oracle].strip()
                status = row[idx_status].strip().upper()
                id_linha_temp = row[idx_id].strip() if idx_id >= 0 and len(row) > idx_id else f"linha_{i+2}"

                # Só processa se:
                # 1. Status Oracle estiver VAZIO E Status contém "CONCLUÍDO"
                # 2. OU Status Oracle = "Erro OCR - Tentar novamente" (retry de erros de OCR)
                # 3. OU Status Oracle = "PROCESSANDO..." MAS NÃO está no cache (retry de timeouts/crashes)
                # 4. OU Status Oracle = "Timeout Oracle - Reabrir sistema" (retry após reabrir)
                # 5. OU Status Oracle = mensagens de erro que precisam retry
                processar = False
                motivo = ""

                # Lista de mensagens de erro que permitem retry
                # IMPORTANTE: "Tela incorreta" NÃO está aqui porque PARA o robô
                # Mas permite retry na PRÓXIMA EXECUÇÃO (não adiciona ao cache)
                mensagens_erro_retry = [
                    # Erros gerais
                    "Campo vazio encontrado",
                    "Transação não autorizada",
                    "Não concluído no Oracle",

                    # Erros de dados
                    "Erro Oracle: dados faltantes por item não cadastrado",
                    "Dados não conferem",
                    "OCR - Dados não conferem",

                    # Erros de validação
                    "Erro validação: valor divergente",
                    "Erro OCR",
                    "Erro OCR - Tentar novamente",
                    "CAMPO_VAZIO",

                    # Erros de salvamento
                    "Sistema travado no Ctrl+S",
                    "Timeout salvamento",
                    "Erro salvamento"
                ]

                # ═══════════════════════════════════════════════════════════════
                # 🚫 FILTRO: Ignorar linhas com Quantidade = 0 (Quantidade Zero)
                # ═══════════════════════════════════════════════════════════════
                idx_quantidade = headers.index("Quantidade") if "Quantidade" in headers else -1
                quantidade_valor = None
                if idx_quantidade >= 0 and len(row) > idx_quantidade:
                    try:
                        quantidade_valor = float(row[idx_quantidade])
                    except:
                        quantidade_valor = None

                # Se quantidade for ZERO, NÃO processar (mesmo com erro de retry)
                if quantidade_valor is not None and quantidade_valor == 0:
                    # Linha com quantidade zero - IGNORAR completamente
                    continue

                # ═══════════════════════════════════════════════════════════════
                # 🚫 FILTRO: Ignorar linhas com "REVER" no Status Oracle
                # ═══════════════════════════════════════════════════════════════
                if "REVER" in status_oracle.upper():
                    # Linha marcada como REVER - NÃO REPROCESSAR
                    continue

                if status_oracle == "" and "CONCLUÍDO" in status:
                    processar = True
                    motivo = "Status vazio + Concluído"
                elif status_oracle == "Erro OCR - Tentar novamente":
                    processar = True
                    motivo = "Retry de erro OCR"
                elif status_oracle == "Timeout Oracle - Reabrir sistema":
                    # Retry de timeout Oracle (mas vai PARAR quando processar)
                    processar = True
                    motivo = "Retry após timeout Oracle (sistema reaberto)"
                    gui_log(f"🔄 [RETRY] Linha {i+2} (ID: {id_linha_temp}) com timeout Oracle - será reprocessada")
                elif "Tela incorreta" in status_oracle or "tela incorreta" in status_oracle.lower():
                    # Retry de erro de tela incorreta (mas vai PARAR quando processar)
                    processar = True
                    motivo = "Retry de erro de tela incorreta (corrigido manualmente)"
                    gui_log(f"🔄 [RETRY] Linha {i+2} (ID: {id_linha_temp}) com erro de tela - será reprocessada")
                elif status_oracle in mensagens_erro_retry:
                    # Match exato
                    processar = True
                    motivo = f"Retry de erro: {status_oracle}"
                    gui_log(f"🔄 [RETRY] Linha {i+2} (ID: {id_linha_temp}) com erro '{status_oracle}' - será reprocessada")
                elif any(erro in status_oracle for erro in mensagens_erro_retry):
                    # 🔧 CORREÇÃO: Match parcial (CONTÉM alguma palavra-chave de erro)
                    processar = True
                    motivo = f"Retry de erro (parcial): {status_oracle}"
                    gui_log(f"🔄 [RETRY] Linha {i+2} (ID: {id_linha_temp}) com erro '{status_oracle}' - será reprocessada")
                elif status_oracle == "PROCESSANDO...":
                    # Verificar se está no cache
                    if not cache.ja_processado(id_linha_temp):
                        processar = True
                        motivo = "PROCESSANDO mas não está no cache (retry de crash/timeout)"
                        gui_log(f"🔄 [RETRY] Linha {i+2} (ID: {id_linha_temp}) está PROCESSANDO mas não está no cache - será reprocessada")
                    else:
                        gui_log(f"⏭️ [SKIP] Linha {i+2} (ID: {id_linha_temp}) está PROCESSANDO e está no cache - atualizando status")

                        # Atualizar status no Google Sheets para "Processo Oracle Concluído"
                        try:
                            coluna_letra = indice_para_coluna(idx_status_oracle)
                            range_str = f"{SHEET_NAME}!{coluna_letra}{i+2}"

                            service.spreadsheets().values().update(
                                spreadsheetId=SPREADSHEET_ID,
                                range=range_str,
                                valueInputOption="RAW",
                                body={"values": [["Processo Oracle Concluído"]]}
                            ).execute()
                            gui_log(f"✅ Status atualizado no Sheets: 'Processo Oracle Concluído' (linha {i+2})")
                        except Exception as e_update:
                            gui_log(f"❌ ERRO ao atualizar status de item em cache (linha {i+2}): {e_update}")

                if processar:
                    linha_dict = dict(zip(headers, row))
                    linhas_processar.append((i + 2, linha_dict))
                    gui_log(f"✅ Linha {i+2} adicionada para processar - Motivo: {motivo}")

            if not linhas_processar:
                gui_log(f"⏳ Nenhuma linha nova para processar (verificação #{tentativas_verificacao})")

                # LÓGICA DIFERENTE PARA PRIMEIRO CICLO
                if primeiro_ciclo and tentativas_verificacao >= MAX_TENTATIVAS_PRIMEIRO_CICLO:
                    gui_log(f"✅ Primeiro ciclo: Após {MAX_TENTATIVAS_PRIMEIRO_CICLO} tentativas sem itens, prosseguindo para Bancada")

                    # ⚡ FORÇAR TAB PARA GARANTIR FLUXO ÚNICO DE FECHAMENTO
                    # Quando não há dados para processar, forçamos um TAB para que
                    # o Oracle entre no estado que exige confirmação ao fechar (modais)
                    # Isso garante um fluxo único e consistente, sempre fechando com os modais
                    gui_log("⌨️ Forçando TAB para garantir fluxo único de fechamento...")
                    if not MODO_TESTE:
                        pyautogui.press("tab")
                        time.sleep(0.5)
                    else:
                        gui_log("[MODO TESTE] Simulando TAB")

                    # Retornar sucesso para continuar o fluxo (ir para Bancada)
                    tempo_espera = config["tempos_espera"]["apos_rpa_oracle"]
                    aguardar_com_pausa(tempo_espera, "Aguardando estabilização pós-Oracle")
                    return True

                gui_log("⏳ Aguardando 30 segundos antes de verificar novamente...")
                if not aguardar_com_pausa(30, "Aguardando novos itens"):
                    return False
                continue

            gui_log(f"📋 {len(linhas_processar)} linhas encontradas para processar")

            # Processar cada linha
            for i, linha in linhas_processar:
                if not _rpa_running:
                    return False

                item = linha.get("Item", "").strip()
                sub_o = linha.get("Sub.Origem", "").strip()
                end_o = linha.get("End. Origem", "").strip()
                sub_d = linha.get("Sub. Destino", "").strip()
                end_d = linha.get("End. Destino", "").strip()
                quantidade = linha.get("Quantidade", "")
                referencia = linha.get("Cód Referencia", "")

                # Usar ID (coluna AC) como identificador único
                id_linha = linha.get("ID", "").strip()

                # Log de debug para ver o ID encontrado
                gui_log(f"🔍 Linha {i}: ID encontrado = '{id_linha}'")

                # Se ID estiver vazio, usar número da linha como fallback
                if not id_linha:
                    id_linha = f"linha_{i}"
                    gui_log(f"⚠️ Linha {i}: ID vazio, usando fallback: {id_linha}")
                else:
                    gui_log(f"✅ Linha {i}: Usando ID = {id_linha}")

                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                # 📊 MOSTRAR TODOS OS DADOS QUE SERÃO INSERIDOS
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                gui_log("=" * 70)
                gui_log(f"📋 DADOS DA LINHA {i} DO GOOGLE SHEETS:")
                gui_log("=" * 70)
                gui_log(f"  🔹 Linha no Sheets: {i}")
                gui_log(f"  🔹 ID: {id_linha}")
                gui_log(f"  🔹 Item: {item}")
                gui_log(f"  🔹 Sub.Origem: {sub_o}")
                gui_log(f"  🔹 End. Origem: {end_o}")
                gui_log(f"  🔹 Sub. Destino: {sub_d}")
                gui_log(f"  🔹 End. Destino: {end_d}")
                gui_log(f"  🔹 Quantidade: {quantidade}")
                gui_log(f"  🔹 Cód Referencia: {referencia}")
                gui_log("=" * 70)

                # Notificar início do item no Telegram
                if _telegram_notifier:
                    try:
                        if _telegram_notifier.enabled:
                            resultado = _telegram_notifier.notificar_inicio_item(i, item, quantidade, sub_o, sub_d)
                            gui_log(f"📱 [TELEGRAM] Notificação de início enviada: {resultado}")
                        else:
                            gui_log("⚠️ [TELEGRAM] Notificador desabilitado (token/chat_id não configurados)")
                    except Exception as e:
                        gui_log(f"⚠️ [TELEGRAM] Erro ao notificar início: {e}")
                else:
                    gui_log("⚠️ [TELEGRAM] Notificador não inicializado")

                # ═══════════════════════════════════════════════════════════════
                # 🔍 VERIFICAR TIMEOUT DO ORACLE (ANTES DE PROCESSAR ITEM)
                # ═══════════════════════════════════════════════════════════════
                gui_log("🔍 Verificando timeout do Oracle antes de processar item...")
                if verificar_tempo_oracle_rapido():
                    gui_log("⏱️ TIMEOUT DETECTADO! Parando antes de processar este item.")
                    # Marcar linha no Sheets
                    try:
                        idx_status_oracle = headers.index("Status Oracle")
                        coluna_letra = indice_para_coluna(idx_status_oracle)
                        range_str = f"{SHEET_NAME}!{coluna_letra}{i}"
                        service.spreadsheets().values().update(
                            spreadsheetId=SPREADSHEET_ID,
                            range=range_str,
                            valueInputOption="RAW",
                            body={"values": [["Timeout Oracle - Reabrir sistema"]]}
                        ).execute()
                        gui_log(f"✅ Linha {i} marcada como 'Timeout Oracle - Reabrir sistema'")
                    except:
                        pass
                    return False

                # ✅ VERIFICAR CACHE ANTI-DUPLICAÇÃO
                if cache.ja_processado(id_linha):
                    gui_log(f"⏭️ Linha {i} (ID: {id_linha}) já processada anteriormente. Pulando.")

                    # Atualizar status no Google Sheets para indicar que foi pulado
                    try:
                        idx_status_oracle = headers.index("Status Oracle")
                        coluna_letra = indice_para_coluna(idx_status_oracle)
                        range_str = f"{SHEET_NAME}!{coluna_letra}{i}"

                        gui_log(f"[CACHE SKIP] Tentando atualizar linha {i}, coluna {coluna_letra}")
                        gui_log(f"[CACHE SKIP] Range: {range_str}")
                        gui_log(f"[CACHE SKIP] Spreadsheet ID: {SPREADSHEET_ID}")

                        service.spreadsheets().values().update(
                            spreadsheetId=SPREADSHEET_ID,
                            range=range_str,
                            valueInputOption="RAW",
                            body={"values": [["Processo Oracle Concluído"]]}
                        ).execute()
                        gui_log(f"✅ Status atualizado no Sheets: 'Processo Oracle Concluído' (linha {i})")

                        # Notificar skip no Telegram
                        if _telegram_notifier:
                            try:
                                _telegram_notifier.notificar_skip_item(i, item, "Já processado anteriormente (encontrado no cache)")
                            except:
                                pass

                    except Exception as e_cache_skip:
                        import traceback
                        gui_log(f"❌ ERRO ao atualizar status de item em cache:")
                        gui_log(f"   Tipo do erro: {type(e_cache_skip).__name__}")
                        gui_log(f"   Mensagem: {e_cache_skip}")
                        gui_log(f"   Traceback completo:")
                        gui_log(traceback.format_exc())

                    continue

                # 🔒 TRAVA 4: LOCK TEMPORÁRIO - Marcar como "PROCESSANDO..." antes de processar
                # Isso evita que outras instâncias peguem a mesma linha
                try:
                    idx_status_oracle = headers.index("Status Oracle")
                    coluna_letra = indice_para_coluna(idx_status_oracle)
                    range_str = f"{SHEET_NAME}!{coluna_letra}{i}"

                    # Verificar se já estava como PROCESSANDO (retry de crash/timeout)
                    status_atual = linha.get("Status Oracle", "").strip()
                    if status_atual == "PROCESSANDO...":
                        gui_log(f"🔄 [RETRY] Linha {i} estava como PROCESSANDO mas não está no cache - REPROCESSANDO")
                    elif status_atual == "Timeout Oracle - Reabrir sistema":
                        gui_log(f"🔄 [RETRY] Linha {i} com timeout - REPROCESSANDO após reabrir Oracle")
                    elif status_atual == "Erro OCR - Tentar novamente":
                        gui_log(f"🔄 [RETRY] Linha {i} com erro OCR - REPROCESSANDO")

                    gui_log(f"🔒 [LOCK] Marcando linha {i} como 'PROCESSANDO...' (coluna {coluna_letra})")
                    service.spreadsheets().values().update(
                        spreadsheetId=SPREADSHEET_ID,
                        range=range_str,
                        valueInputOption="RAW",
                        body={"values": [["PROCESSANDO..."]]}
                    ).execute()
                    gui_log(f"✅ [LOCK] Linha {i} bloqueada com sucesso")
                except Exception as e_lock:
                    gui_log(f"⚠️ [LOCK] Erro ao marcar linha {i} como PROCESSANDO: {e_lock}")
                    # Se não conseguir fazer o lock, pula para próxima linha (segurança)
                    continue

                # REGRA 3: Validar campos vazios
                if not item or not sub_o or not end_o or not sub_d or not end_d:
                    gui_log(f"⚠️ Linha {i} PULADA - Campo vazio encontrado")
                    service.spreadsheets().values().update(
                        spreadsheetId=SPREADSHEET_ID,
                        range=f"{SHEET_NAME}!T{i}",
                        valueInputOption="RAW",
                        body={"values": [["Campo vazio encontrado"]]}
                    ).execute()
                    continue

                # REGRA 1: Validar quantidade = 0 (IMPORTANTE: quantidade negativa é PERMITIDA)
                try:
                    qtd_float = float(str(quantidade).replace(",", ".").replace(" ", ""))
                    if qtd_float == 0:
                        gui_log(f"⚠️ Linha {i} PULADA - Quantidade Zero")
                        service.spreadsheets().values().update(
                            spreadsheetId=SPREADSHEET_ID,
                            range=f"{SHEET_NAME}!T{i}",
                            valueInputOption="RAW",
                            body={"values": [["Quantidade Zero"]]}
                        ).execute()
                        continue
                    # ✅ QUANTIDADE NEGATIVA É PERMITIDA - Oracle apenas pede confirmação
                    if qtd_float < 0:
                        gui_log(f"ℹ️ Linha {i} - Quantidade NEGATIVA ({quantidade}) - será processada normalmente")
                except ValueError:
                    continue

                # Definir lista de subinventários proibidos
                subs_proibidos = ["RAWINDIR", "RAWMANUT", "RAWWAFIFE"]
                sub_o_upper = sub_o.upper()
                sub_d_upper = sub_d.upper()

                # REGRA 2: Validar combinação proibida: origem proibida → RAWCENTR
                if sub_o_upper in subs_proibidos and sub_d_upper == "RAWCENTR":
                    gui_log(f"⚠️ Linha {i} PULADA - Transação não autorizada: {sub_o} → {sub_d}")
                    service.spreadsheets().values().update(
                        spreadsheetId=SPREADSHEET_ID,
                        range=f"{SHEET_NAME}!T{i}",
                        valueInputOption="RAW",
                        body={"values": [["Transação não autorizada"]]}
                    ).execute()
                    continue

                # REGRA 4: Validar origem proibida → destino deve ser igual à origem
                if sub_o_upper in subs_proibidos and sub_o_upper != sub_d_upper:
                    gui_log(f"⚠️ Linha {i} PULADA - Transação não autorizada: {sub_o} → {sub_d} (origem proibida deve ir para si mesma)")
                    service.spreadsheets().values().update(
                        spreadsheetId=SPREADSHEET_ID,
                        range=f"{SHEET_NAME}!T{i}",
                        valueInputOption="RAW",
                        body={"values": [["Transação não autorizada"]]}
                    ).execute()
                    continue

                gui_log(f"▶ Linha {i}: {item} | Qtd={quantidade} | Ref={referencia}")

                # 🌐 VERIFICAR QUEDA DE REDE NO INÍCIO DO PROCESSAMENTO
                if verificar_queda_rede():
                    gui_log("❌ QUEDA DE REDE detectada no início do processamento da linha!")
                    return False

                # 🔒 TRAVA 5: TIMEOUT DE SEGURANÇA - Registrar início do processamento
                inicio_processamento = time.time()
                TIMEOUT_PROCESSAMENTO = 60  # 60 segundos por linha

                if MODO_TESTE:
                    gui_log("[MODO TESTE] Simulando preenchimento no Oracle (sem pyautogui)...")
                    time.sleep(0.5)  # Simula tempo de preenchimento
                else:
                    # ═══════════════════════════════════════════════════════════════
                    # 🖼️ VERIFICAR TELA DE TRANSFERÊNCIA SUBINVENTORY
                    # ═══════════════════════════════════════════════════════════════
                    gui_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                    gui_log("🔍 VERIFICANDO TELA DE TRANSFERÊNCIA SUBINVENTORY...")

                    caminho_tela_transferencia = os.path.join(base_path, "informacoes", "tela_transferencia_subinventory.png")

                    if not os.path.isfile(caminho_tela_transferencia):
                        gui_log(f"⚠️ Imagem de validação não encontrada: {caminho_tela_transferencia}")
                        gui_log("⚠️ CONTINUANDO sem verificação de tela (imagem não existe)")
                    else:
                        tela_correta = detectar_imagem_opencv(caminho_tela_transferencia, confidence=0.8, timeout=5)

                        if not tela_correta:
                            gui_log("❌ TELA DE TRANSFERÊNCIA NÃO DETECTADA!")
                            gui_log("❌ A tela atual NÃO corresponde à tela esperada de Transferência Subinventory")
                            gui_log("🛑 PARANDO ROBÔ - Verifique se está na tela correta do Oracle")

                            # Atualizar status no Sheets
                            try:
                                service.spreadsheets().values().update(
                                    spreadsheetId=SPREADSHEET_ID,
                                    range=range_str,
                                    valueInputOption="RAW",
                                    body={"values": [["Tela incorreta - verificar Oracle"]]}
                                ).execute()
                                gui_log(f"✅ Status atualizado no Sheets: 'Tela incorreta - verificar Oracle'")
                            except Exception as e_tela:
                                gui_log(f"⚠️ Erro ao atualizar status: {e_tela}")

                            gui_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                            return False
                        else:
                            gui_log("✅ TELA CORRETA DETECTADA - Transferência Subinventory OK!")

                    gui_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

                    # ═══════════════════════════════════════════════════════════════
                    # PREENCHER ITEM
                    # ═══════════════════════════════════════════════════════════════
                    gui_log(f"[ITEM] >> Clicando no campo Item: {coords['item']}")
                    pyautogui.click(coords["item"])
                    gui_log(f"[ITEM] << Click executado")
                    gui_log(f"[ITEM] Aguardando 0.3 segundos...")
                    time.sleep(0.3)
                    gui_log(f"[ITEM] >> Pressionando DELETE...")
                    pyautogui.press("delete")
                    gui_log(f"[ITEM] << DELETE pressionado")
                    gui_log(f"[ITEM] Aguardando 0.2 segundos...")
                    time.sleep(0.2)
                    gui_log(f"[ITEM] >> Digitando Item: '{item}'")
                    pyautogui.write(item)
                    gui_log(f"[ITEM] << Item digitado")
                    gui_log(f"[ITEM] Aguardando 0.2 segundos...")
                    time.sleep(0.2)
                    gui_log(f"[ITEM] >> Pressionando TAB...")
                    pyautogui.press("tab")
                    gui_log(f"[ITEM] << TAB pressionado")
                    gui_log(f"[ITEM] Aguardando 1 segundo...")
                    time.sleep(1)
                    gui_log(f"[ITEM] ✅ Item preenchido")

                    # ═══════════════════════════════════════════════════════════════
                    # VERIFICAR ERRO DE PRODUTO (LOGO APÓS ITEM) - IGUAL RPA_ORACLE
                    # ═══════════════════════════════════════════════════════════════
                    gui_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                    gui_log("🔍 INICIANDO VERIFICAÇÃO DE ERRO DE PRODUTO...")
                    gui_log(f"📊 Contexto: Linha {i}, Item: {item}, Referência: {referencia}")
                    gui_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

                    erro_detectado = verificar_erro_produto(service, range_str, i)

                    gui_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                    gui_log(f"🔍 RESULTADO VERIFICAÇÃO: {erro_detectado}")
                    gui_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

                    if erro_detectado:
                        gui_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                        gui_log("❌❌❌ ERRO DE PRODUTO DETECTADO - APLICAÇÃO SERÁ PARADA ❌❌❌")
                        gui_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                        gui_log(f"📋 Linha {i} marcada como 'PD' (Pendente)")
                        gui_log("🔄 Corrija o erro e execute novamente a aplicação")
                        gui_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                        return False
                    else:
                        gui_log("✅✅✅ Nenhum erro de produto - CONTINUANDO PROCESSAMENTO ✅✅✅")

                    # ═══════════════════════════════════════════════════════════════
                    # VERIFICAR TIMEOUT DO ORACLE (LOGO APÓS VERIFICAÇÃO DE ERRO)
                    # ═══════════════════════════════════════════════════════════════
                    gui_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                    gui_log("🔍 INICIANDO VERIFICAÇÃO DE TIMEOUT DO ORACLE...")
                    gui_log(f"📊 Contexto: Linha {i}, Item: {item}, Referência: {referencia}")
                    gui_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

                    timeout_detectado = verificar_tempo_oracle(service, range_str, i)

                    gui_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                    gui_log(f"🔍 RESULTADO VERIFICAÇÃO TIMEOUT: {timeout_detectado}")
                    gui_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

                    if timeout_detectado:
                        gui_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                        gui_log("⏱️⏱️⏱️ TIMEOUT DO ORACLE DETECTADO - APLICAÇÃO SERÁ PARADA ⏱️⏱️⏱️")
                        gui_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                        gui_log(f"📋 Linha {i} marcada como 'Timeout Oracle - Reabrir sistema'")
                        gui_log("🔄 REABRA o sistema Oracle e execute novamente a aplicação")
                        gui_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                        return False
                    else:
                        gui_log("✅✅✅ Nenhum timeout detectado - CONTINUANDO PROCESSAMENTO ✅✅✅")

                    # ═══════════════════════════════════════════════════════════════
                    # PREENCHER REFERÊNCIA, SUB ORIGEM, END ORIGEM
                    # ═══════════════════════════════════════════════════════════════
                    gui_log(f"[REFERENCIA] >> Clicando em coords: {coords['Referencia']}")
                    pyautogui.click(coords["Referencia"])
                    gui_log(f"[REFERENCIA] << Click executado")
                    gui_log(f"[REFERENCIA] >> Digitando '{referencia}'...")
                    pyautogui.write(referencia)
                    gui_log(f"[REFERENCIA] << Digitado")
                    gui_log(f"[REFERENCIA] >> Pressionando TAB...")
                    pyautogui.press("tab")
                    gui_log(f"[REFERENCIA] << TAB pressionado")
                    gui_log(f"[REFERENCIA] Aguardando 1 segundo...")
                    time.sleep(1)

                    gui_log(f"[SUB_ORIGEM] >> Clicando em coords: {coords['sub_origem']}")
                    pyautogui.click(coords["sub_origem"])
                    gui_log(f"[SUB_ORIGEM] << Click executado")
                    gui_log(f"[SUB_ORIGEM] Aguardando 0.2 segundos...")
                    time.sleep(0.2)
                    gui_log(f"[SUB_ORIGEM] >> Digitando '{sub_o}'...")
                    pyautogui.write(sub_o)
                    gui_log(f"[SUB_ORIGEM] << Digitado")
                    gui_log(f"[SUB_ORIGEM] >> Pressionando TAB...")
                    pyautogui.press("tab")
                    gui_log(f"[SUB_ORIGEM] << TAB pressionado")
                    gui_log(f"[SUB_ORIGEM] Aguardando 1 segundo...")
                    time.sleep(1)

                    gui_log(f"[END_ORIGEM] >> Pressionando DELETE...")
                    pyautogui.press("delete")
                    gui_log(f"[END_ORIGEM] << DELETE pressionado")
                    gui_log(f"[END_ORIGEM] >> Clicando em coords: {coords['end_origem']}")
                    pyautogui.click(coords["end_origem"])
                    gui_log(f"[END_ORIGEM] << Click executado")
                    gui_log(f"[END_ORIGEM] Aguardando 0.2 segundos...")
                    time.sleep(0.2)
                    gui_log(f"[END_ORIGEM] >> Digitando '{end_o}'...")
                    pyautogui.write(end_o)
                    gui_log(f"[END_ORIGEM] << Digitado")
                    gui_log(f"[END_ORIGEM] >> Pressionando TAB...")
                    pyautogui.press("tab")
                    gui_log(f"[END_ORIGEM] << TAB pressionado")
                    time.sleep(1.5)  # Aumentar delay para Oracle processar

                    # Verifica se referencia inicia com "COD"
                    if str(referencia).strip().upper().startswith("COD"):
                        gui_log(f"[COD] Referencia '{referencia}' detectada como tipo COD. Pulando campos destino.")
                        if not MODO_TESTE:
                            gui_log(f"[COD] Cursor deve estar em SUB_DESTINO. Dando TAB para pular...")
                            pyautogui.press("tab")
                            time.sleep(1.2)
                            gui_log(f"[COD] Cursor deve estar em END_DESTINO. Dando TAB para pular...")
                            pyautogui.press("tab")
                            time.sleep(1.2)
                            gui_log(f"[COD] Cursor deve estar em QUANTIDADE agora.")
                        else:
                            gui_log(f"[MODO TESTE] Simulando TAB TAB para COD...")
                    else:
                        gui_log(f"[MOV] Referencia '{referencia}' tratada como MOV. Preenchendo normalmente.")
                        gui_log(f"[SUB_DESTINO] Preenchendo: {sub_d}")
                        gui_log(f"[SUB_DESTINO] >> Pressionando DELETE...")
                        pyautogui.press("delete")
                        gui_log(f"[SUB_DESTINO] << DELETE pressionado")
                        gui_log(f"[SUB_DESTINO] >> Clicando em coords: {coords['sub_destino']}")
                        pyautogui.click(coords["sub_destino"])
                        gui_log(f"[SUB_DESTINO] << Click executado")
                        gui_log(f"[SUB_DESTINO] Aguardando 0.2 segundos...")
                        time.sleep(0.2)
                        gui_log(f"[SUB_DESTINO] >> Digitando '{sub_d}'...")
                        pyautogui.write(sub_d)
                        gui_log(f"[SUB_DESTINO] << Digitado")
                        gui_log(f"[SUB_DESTINO] >> Pressionando TAB...")
                        pyautogui.press("tab")
                        gui_log(f"[SUB_DESTINO] << TAB pressionado")
                        gui_log(f"[SUB_DESTINO] Aguardando 1 segundo...")
                        time.sleep(1)
                        gui_log(f"[SUB_DESTINO] ✅ Preenchido")

                        gui_log(f"[END_DESTINO] Preenchendo: {end_d}")
                        gui_log(f"[END_DESTINO] >> Pressionando DELETE...")
                        pyautogui.press("delete")
                        gui_log(f"[END_DESTINO] << DELETE pressionado")
                        gui_log(f"[END_DESTINO] >> Clicando em coords: {coords['end_destino']}")
                        pyautogui.click(coords["end_destino"])
                        gui_log(f"[END_DESTINO] << Click executado")
                        gui_log(f"[END_DESTINO] Aguardando 0.2 segundos...")
                        time.sleep(0.2)
                        gui_log(f"[END_DESTINO] >> Digitando '{end_d}'...")
                        pyautogui.write(end_d)
                        gui_log(f"[END_DESTINO] << Digitado")
                        gui_log(f"[END_DESTINO] >> Pressionando TAB...")
                        pyautogui.press("tab")
                        gui_log(f"[END_DESTINO] << TAB pressionado")
                        gui_log(f"[END_DESTINO] Aguardando 1 segundo...")
                        time.sleep(1)
                        gui_log(f"[END_DESTINO] ✅ Preenchido")

                    # ═══════════════════════════════════════════════════════════════
                    # PREENCHER QUANTIDADE
                    # ═══════════════════════════════════════════════════════════════
                    gui_log(f"[QUANTIDADE] Preenchendo quantidade: {quantidade}")
                    gui_log("[QUANTIDADE] >> Pressionando DELETE...")
                    pyautogui.press("delete")
                    gui_log("[QUANTIDADE] << DELETE pressionado")
                    gui_log(f"[QUANTIDADE] >> Clicando em coords quantidade: {coords['quantidade']}")
                    pyautogui.click(coords["quantidade"])
                    gui_log("[QUANTIDADE] << Click executado")
                    gui_log("[QUANTIDADE] Aguardando 0.2 segundos...")
                    time.sleep(0.2)
                    gui_log(f"[QUANTIDADE] >> Digitando '{quantidade}'...")
                    pyautogui.write(quantidade)
                    gui_log("[QUANTIDADE] << Digitação concluída")

                    # Pressionar TAB para sair do campo quantidade (ou clicar fora)
                    gui_log("[QUANTIDADE] >> Pressionando TAB para sair do campo...")
                    pyautogui.press("tab")
                    gui_log("[QUANTIDADE] << TAB pressionado")

                    gui_log("[QUANTIDADE] Aguardando 1 segundo...")
                    time.sleep(1)
                    gui_log(f"[QUANTIDADE] ✅ Quantidade preenchida")

                    # ═══════════════════════════════════════════════════════════════
                    # ⚠️ VERIFICAR MODAL #1 - AO SAIR DO CAMPO QUANTIDADE
                    # O modal pode aparecer quando sai do foco do campo quantidade
                    # Apenas fecha o modal com ENTER, NÃO faz Ctrl+S
                    # Confidence 0.8 (80%) - IGUAL ao RPA_Oracle
                    # ═══════════════════════════════════════════════════════════════
                    gui_log("[QTD NEG] 🔍 Verificando modal após sair do campo quantidade...")
                    caminho_modal = os.path.join(base_path, "informacoes", "qtd_negativa.png")
                    if os.path.isfile(caminho_modal):
                        modal_encontrado = detectar_imagem_opencv(caminho_modal, confidence=0.8, timeout=3)
                        if modal_encontrado:
                            gui_log("✅ [QTD NEG] Modal detectado ao sair do campo!")
                            time.sleep(0.5)
                            gui_log("[QTD NEG] >> Pressionando ENTER (fechar modal)...")
                            pyautogui.press("enter")
                            gui_log("[QTD NEG] << ENTER pressionado")
                            time.sleep(1)
                            gui_log("✅ [QTD NEG] Modal fechado! Continuando...")
                        else:
                            gui_log("[QTD NEG] ✅ Nenhum modal detectado")

                    # ═══════════════════════════════════════════════════════════════
                    # 🔍 VERIFICAR TIMEOUT (APÓS PREENCHER QUANTIDADE)
                    # ═══════════════════════════════════════════════════════════════
                    if verificar_tempo_oracle_rapido():
                        gui_log("⏱️ TIMEOUT DETECTADO após preencher quantidade. Parando RPA.")
                        try:
                            service.spreadsheets().values().update(
                                spreadsheetId=SPREADSHEET_ID,
                                range=range_str,
                                valueInputOption="RAW",
                                body={"values": [["Timeout Oracle - Reabrir sistema"]]}
                            ).execute()
                        except:
                            pass
                        return False

                    # ═══════════════════════════════════════════════════════════════
                    # 🔍 VALIDAÇÃO HÍBRIDA - Verificar se campos foram preenchidos
                    # ═══════════════════════════════════════════════════════════════
                    if VALIDADOR_HIBRIDO_DISPONIVEL:
                        gui_log("[VALIDADOR] ═══════════════════════════════════════════════")

                        # 🌐 VERIFICAR QUEDA DE REDE ANTES DA VALIDAÇÃO
                        if verificar_queda_rede():
                            gui_log("❌ QUEDA DE REDE detectada antes da validação!")
                            return False

                        gui_log("[VALIDADOR] Aguardando 3 segundos para campos estabilizarem...")
                        time.sleep(3)  # Timeout maior para dar tempo da tela estabilizar

                        validacao_ok, tipo_erro = validar_campos_oracle_completo(
                            coords_validacao, item, quantidade, referencia,
                            sub_o, end_o, sub_d, end_d
                        )

                        # ═══════════════════════════════════════════════════════════════
                        # ⚠️ VERIFICAR MODAL DE QUANTIDADE NEGATIVA (aparece DURANTE validação!)
                        # O validador COPIA os valores dos campos, e nesse momento
                        # o Oracle pode exibir o modal de quantidade negativa
                        # Apenas fecha o modal com ENTER, NÃO faz Ctrl+S
                        # Confidence 0.8 (80%) - IGUAL ao RPA_Oracle
                        # ═══════════════════════════════════════════════════════════════
                        gui_log("[QTD NEG] 🔍 Verificando se modal apareceu durante validação...")
                        caminho_modal = os.path.join(base_path, "informacoes", "qtd_negativa.png")
                        if os.path.isfile(caminho_modal):
                            modal_encontrado = detectar_imagem_opencv(caminho_modal, confidence=0.8, timeout=3)
                            if modal_encontrado:
                                gui_log("✅ [QTD NEG] Modal de confirmação detectado durante validação!")
                                time.sleep(0.5)
                                gui_log("[QTD NEG] >> Pressionando ENTER (fechar modal)...")
                                pyautogui.press("enter")
                                gui_log("[QTD NEG] << ENTER pressionado")
                                time.sleep(1)
                                gui_log("✅ [QTD NEG] Modal fechado! Continuando validação...")
                            else:
                                gui_log("[QTD NEG] ✅ Nenhum modal detectado durante validação")

                        if not validacao_ok:
                            gui_log("❌ [VALIDADOR] Validação FALHOU - dados não conferem!")

                            # Definir mensagem baseada no tipo de erro
                            if tipo_erro == "COD_VAZIO" or tipo_erro == "CAMPO_VAZIO":
                                mensagem_status = "Erro Oracle: dados faltantes por item não cadastrado"
                                gui_log(f"[VALIDADOR] Tipo de erro: {tipo_erro} - campos vazios")
                            elif tipo_erro == "VALOR_ERRADO":
                                mensagem_status = "Erro validação: valor divergente"
                                gui_log(f"[VALIDADOR] Tipo de erro: Valor digitado diferente do esperado")
                            elif tipo_erro == "QTD_NEGATIVA":
                                # ✅ QUANTIDADE NEGATIVA NÃO É ERRO! Considera validação OK
                                gui_log(f"✅ [VALIDADOR] Quantidade negativa detectada - É PERMITIDA, validação OK")
                                validacao_ok = True
                                mensagem_status = "Processo Oracle Concluído"
                            elif tipo_erro == "PRODUTO_INVALIDO":
                                mensagem_status = "Erro Oracle: produto inválido"
                                gui_log(f"[VALIDADOR] Tipo de erro: Produto não encontrado")
                            else:
                                mensagem_status = "Não concluído no Oracle"
                                gui_log(f"[VALIDADOR] Tipo de erro: {tipo_erro}")

                            gui_log(f"[VALIDADOR] Marcando linha como '{mensagem_status}'")

                            # ═══════════════════════════════════════════════════════════════
                            # 🧹 LIMPAR FORMULÁRIO COM F6 (OBRIGATÓRIO ANTES DE CONTINUAR)
                            # ═══════════════════════════════════════════════════════════════
                            gui_log("[VALIDADOR] ═══════════════════════════════════════════════")
                            gui_log("[VALIDADOR] 🧹 Pressionando F6 para limpar formulário...")

                            limpar_sucesso = False
                            try:
                                if MODO_TESTE:
                                    gui_log("[VALIDADOR] [MODO TESTE] Simulando pressionar F6")
                                    limpar_sucesso = True
                                else:
                                    # 🔧 CORREÇÃO: Pausar hook do teclado temporariamente
                                    gui_log("[VALIDADOR] Pausando hook do teclado para evitar interceptação...")
                                    try:
                                        keyboard.unhook_all()
                                        gui_log("[VALIDADOR] ✅ Hook pausado")
                                    except:
                                        pass

                                    # Tentar F6 com múltiplas tentativas
                                    for tentativa in range(3):
                                        try:
                                            gui_log(f"[VALIDADOR] >> Tentativa {tentativa+1}/3: Pressionando F6...")
                                            time.sleep(0.3)  # Pequeno delay antes de pressionar
                                            pyautogui.press('f6')
                                            time.sleep(0.5)  # Aguardar tecla ser processada
                                            gui_log(f"[VALIDADOR] << F6 pressionado (tentativa {tentativa+1})")
                                            limpar_sucesso = True
                                            break
                                        except Exception as e_tentativa:
                                            gui_log(f"[VALIDADOR] ⚠️ Tentativa {tentativa+1} falhou: {e_tentativa}")
                                            if tentativa < 2:
                                                time.sleep(0.5)

                                    # Reativar hook do teclado
                                    try:
                                        def parar_callback_reativado(event):
                                            global _rpa_running
                                            if event.name == 'esc' and event.event_type == 'down':
                                                gui_log("⚠️ [ESC] TECLA ESC PRESSIONADA - PARANDO RPA...")
                                                _rpa_running = False
                                                keyboard.unhook_all()
                                        keyboard.hook(parar_callback_reativado)
                                        gui_log("[VALIDADOR] ✅ Hook do teclado reativado")
                                    except:
                                        pass

                                    if limpar_sucesso:
                                        gui_log("[VALIDADOR] ✅ Tecla F6 pressionada com sucesso")
                                        gui_log("[VALIDADOR] Aguardando 3 segundos para formulário limpar...")
                                        time.sleep(3)  # Aguardar formulário limpar
                                        gui_log("[VALIDADOR] ✅ Formulário deve estar limpo agora")
                                    else:
                                        # 🔧 FALLBACK: Usar botão Limpar se F6 falhar
                                        gui_log("[VALIDADOR] ⚠️ F6 falhou após 3 tentativas, usando botão Limpar...")
                                        coord_limpar = config["coordenadas"].get("tela_06_limpar")
                                        if coord_limpar:
                                            pyautogui.click(coord_limpar["x"], coord_limpar["y"])
                                            time.sleep(3)
                                            gui_log("[VALIDADOR] ✅ Botão Limpar clicado como fallback")
                                        else:
                                            gui_log("[VALIDADOR] ❌ Botão Limpar não configurado em config.json")

                            except Exception as e_limpar:
                                gui_log(f"[VALIDADOR] ❌ ERRO CRÍTICO ao limpar formulário: {e_limpar}")
                                gui_log(f"[VALIDADOR] Tipo do erro: {type(e_limpar).__name__}")
                                import traceback
                                gui_log(f"[VALIDADOR] Traceback: {traceback.format_exc()}")

                            gui_log("[VALIDADOR] ═══════════════════════════════════════════════")

                            # Marcar no Sheets com mensagem específica (NÃO adicionar ao cache)
                            try:
                                service.spreadsheets().values().update(
                                    spreadsheetId=SPREADSHEET_ID,
                                    range=range_str,
                                    valueInputOption="RAW",
                                    body={"values": [[mensagem_status]]}
                                ).execute()
                                gui_log(f"✅ Status atualizado: '{mensagem_status}'")

                                # Notificar erro no Telegram
                                if _telegram_notifier:
                                    try:
                                        if _telegram_notifier.enabled:
                                            resultado = _telegram_notifier.notificar_erro_item(i, item, mensagem_status)
                                            gui_log(f"📱 [TELEGRAM] Notificação de erro enviada: {resultado}")
                                    except Exception as e:
                                        gui_log(f"⚠️ [TELEGRAM] Erro ao notificar: {e}")

                            except Exception as e_validador:
                                gui_log(f"⚠️ Erro ao atualizar status: {e_validador}")

                            # NÃO adicionar ao cache - linha será reprocessada no próximo ciclo
                            gui_log("[VALIDADOR] Item marcado para retry na próxima execução")

                            # 🛑 VERIFICAR SE É ERRO QUE REQUER PARADA DO ROBÔ
                            if "Tela incorreta" in mensagem_status or "tela incorreta" in mensagem_status.lower():
                                gui_log("🛑 ERRO DE TELA INCORRETA DETECTADO!")
                                gui_log("⚠️ PARANDO EXECUÇÃO para correção manual")
                                gui_log("✅ Item ficará marcado para retry na próxima execução")
                                return False  # PARA O ROBÔ

                            gui_log("[VALIDADOR] Pulando para próxima linha (esta será reprocessada)")
                            continue
                        else:
                            gui_log("[VALIDADOR] ✅ Validação passou - campos corretos!")

                        gui_log("[VALIDADOR] ═══════════════════════════════════════════════")

                    # ═══════════════════════════════════════════════════════════════
                    # SALVAR COM Ctrl+S (APÓS VALIDAÇÃO HÍBRIDA)
                    # ═══════════════════════════════════════════════════════════════
                    gui_log("[SAVE] ═══════════════════════════════════════════════")

                    # 🌐 VERIFICAR QUEDA DE REDE ANTES DE SALVAR
                    if verificar_queda_rede():
                        gui_log("❌ QUEDA DE REDE detectada antes do salvamento!")
                        return False

                    gui_log("[SAVE] Iniciando salvamento com Ctrl+S...")
                    gui_log("[SAVE] >> Pressionando CTRL+S...")
                    pyautogui.hotkey("ctrl", "s")
                    gui_log("[SAVE] << CTRL+S pressionado")
                    gui_log("[SAVE] Aguardando 1 segundo...")
                    time.sleep(1)
                    gui_log("[SAVE] Aguardando mais 0.5 segundos...")
                    time.sleep(0.5)
                    gui_log("[SAVE] ✅ Ctrl+S executado")

                    # ═══════════════════════════════════════════════════════════════
                    # 💾 ADICIONAR AO CACHE IMEDIATAMENTE (APÓS Ctrl+S)
                    # IMPORTANTE: Adiciona ANTES de confirmar salvamento para evitar
                    # duplicação se houver falha/queda de rede durante salvamento
                    # Melhor ter no cache e não salvar, do que salvar 2x!
                    # ═══════════════════════════════════════════════════════════════
                    gui_log("💾 Adicionando ao cache ANTES de aguardar salvamento...")

                    sucesso_cache = cache.adicionar(
                        id_item=id_linha,
                        linha_atual=i,
                        item=item,
                        quantidade=quantidade,
                        referencia=referencia,
                        status="pendente"
                    )
                    if sucesso_cache:
                        gui_log(f"✅ Registrado no cache: {id_linha}")
                    else:
                        gui_log(f"⚠️ Falha ao registrar no cache (ID vazio?)")

                    # ═══════════════════════════════════════════════════════════════
                    # ⏳ AGUARDAR SALVAMENTO SER CONCLUÍDO (TELA VOLTAR AO NORMAL)
                    # Verifica se a tela voltou ao estado correto após Ctrl+S
                    # Estratégia: 5s + (se falhar) 30s + (se falhar) ERRO
                    # ═══════════════════════════════════════════════════════════════
                    gui_log("[SAVE] ═══════════════════════════════════════════════")
                    gui_log("[SAVE] Aguardando confirmação de salvamento...")

                    sucesso_save, tipo_save, tempo_save = aguardar_salvamento_concluido()

                    if not sucesso_save:
                        # FALHA: Tela não voltou ao estado normal após Ctrl+S
                        gui_log(f"❌ [SAVE] FALHA NO SALVAMENTO após {tempo_save:.1f}s - tela não voltou ao normal")
                        gui_log(f"[SAVE] Tipo de erro: {tipo_save}")

                        # ═══════════════════════════════════════════════════════════════
                        # 🧹 LIMPAR FORMULÁRIO COM F6 (OBRIGATÓRIO ANTES DE CONTINUAR)
                        # ═══════════════════════════════════════════════════════════════
                        gui_log("[SAVE] ═══════════════════════════════════════════════")
                        gui_log("[SAVE] 🧹 Pressionando F6 para forçar limpeza do formulário...")

                        limpar_sucesso = False
                        try:
                            if MODO_TESTE:
                                gui_log("[SAVE] [MODO TESTE] Simulando pressionar F6")
                                limpar_sucesso = True
                            else:
                                # 🔧 CORREÇÃO: Pausar hook do teclado temporariamente
                                gui_log("[SAVE] Pausando hook do teclado para evitar interceptação...")
                                try:
                                    keyboard.unhook_all()
                                    gui_log("[SAVE] ✅ Hook pausado")
                                except:
                                    pass

                                # Tentar F6 com múltiplas tentativas
                                for tentativa in range(3):
                                    try:
                                        gui_log(f"[SAVE] >> Tentativa {tentativa+1}/3: Pressionando F6...")
                                        time.sleep(0.3)  # Pequeno delay antes de pressionar
                                        pyautogui.press('f6')
                                        time.sleep(0.5)  # Aguardar tecla ser processada
                                        gui_log(f"[SAVE] << F6 pressionado (tentativa {tentativa+1})")
                                        limpar_sucesso = True
                                        break
                                    except Exception as e_tentativa:
                                        gui_log(f"[SAVE] ⚠️ Tentativa {tentativa+1} falhou: {e_tentativa}")
                                        if tentativa < 2:
                                            time.sleep(0.5)

                                # Reativar hook do teclado
                                try:
                                    def parar_callback_reativado(event):
                                        global _rpa_running
                                        if event.name == 'esc' and event.event_type == 'down':
                                            gui_log("⚠️ [ESC] TECLA ESC PRESSIONADA - PARANDO RPA...")
                                            _rpa_running = False
                                            keyboard.unhook_all()
                                    keyboard.hook(parar_callback_reativado)
                                    gui_log("[SAVE] ✅ Hook do teclado reativado")
                                except:
                                    pass

                                if limpar_sucesso:
                                    gui_log("[SAVE] ✅ Tecla F6 pressionada com sucesso")
                                    gui_log("[SAVE] Aguardando 3 segundos para formulário limpar...")
                                    time.sleep(3)  # Aguardar formulário limpar
                                    gui_log("[SAVE] ✅ Formulário deve estar limpo agora")
                                else:
                                    # 🔧 FALLBACK: Usar botão Limpar se F6 falhar
                                    gui_log("[SAVE] ⚠️ F6 falhou após 3 tentativas, usando botão Limpar...")
                                    coord_limpar = config["coordenadas"].get("tela_06_limpar")
                                    if coord_limpar:
                                        pyautogui.click(coord_limpar["x"], coord_limpar["y"])
                                        time.sleep(3)
                                        gui_log("[SAVE] ✅ Botão Limpar clicado como fallback")
                                    else:
                                        gui_log("[SAVE] ❌ Botão Limpar não configurado em config.json")

                        except Exception as e_limpar:
                            gui_log(f"[SAVE] ❌ ERRO CRÍTICO ao limpar formulário: {e_limpar}")
                            gui_log(f"[SAVE] Tipo do erro: {type(e_limpar).__name__}")
                            import traceback
                            gui_log(f"[SAVE] Traceback: {traceback.format_exc()}")

                        gui_log("[SAVE] ═══════════════════════════════════════════════")

                        # Marcar como erro no Google Sheets
                        try:
                            # Mensagem detalhada sobre o tipo de erro
                            if tipo_save == "TRAVADO":
                                mensagem_status = f"Tela não voltou ao normal após Ctrl+S ({tempo_save:.0f}s) - Verificar Oracle"
                            elif tipo_save == "IMAGEM_NAO_EXISTE":
                                mensagem_status = "ERRO: Imagem tela_transferencia_subinventory.png não encontrada"
                            elif tipo_save == "QUEDA_REDE":
                                mensagem_status = f"Queda de rede durante salvamento ({tempo_save:.0f}s)"
                            elif tipo_save == "RPA_PARADO":
                                mensagem_status = f"RPA parado pelo usuário durante salvamento ({tempo_save:.0f}s)"
                            else:
                                mensagem_status = f"Erro salvamento ({tempo_save:.0f}s) - {tipo_save}"

                            service.spreadsheets().values().update(
                                spreadsheetId=SPREADSHEET_ID,
                                range=range_str,
                                valueInputOption="RAW",
                                body={"values": [[mensagem_status]]}
                            ).execute()
                            gui_log(f"✅ Status atualizado no Sheets: '{mensagem_status}'")
                        except Exception as e_timeout:
                            gui_log(f"⚠️ Erro ao atualizar status no Sheets: {e_timeout}")

                        # Item JÁ está no cache - não vai duplicar
                        # Será reprocessado no próximo ciclo
                        gui_log("[SAVE] ⚠️ Item está no cache, não será duplicado")
                        gui_log("[SAVE] Pulando para próxima linha (esta será reprocessada)")
                        continue

                    # ═══════════════════════════════════════════════════════════════
                    # ✅ SALVAMENTO CONFIRMADO! (tela voltou ao estado normal)
                    # Item JÁ está no cache (adicionado após Ctrl+S)
                    # Agora apenas atualiza Sheets e remove do cache
                    # ═══════════════════════════════════════════════════════════════
                    gui_log(f"✅ [SAVE] Salvamento confirmado em {tempo_save:.1f}s!")
                    gui_log("[SAVE] Tela voltou ao estado normal - salvamento bem-sucedido")
                    gui_log("[SAVE] ═══════════════════════════════════════════════")

                    # ═══════════════════════════════════════════════════════════════
                    # 📊 ATUALIZAR GOOGLE SHEETS E REMOVER DO CACHE
                    # ═══════════════════════════════════════════════════════════════

                    # 🌐 VERIFICAR QUEDA DE REDE ANTES DE ATUALIZAR SHEETS
                    if verificar_queda_rede():
                        gui_log("❌ QUEDA DE REDE detectada antes de atualizar Google Sheets!")
                        gui_log("⚠️ Item permanece no cache para retry no próximo ciclo")
                        return False

                    try:
                        service.spreadsheets().values().update(
                            spreadsheetId=SPREADSHEET_ID,
                            range=f"{SHEET_NAME}!T{i}",
                            valueInputOption="RAW",
                            body={"values": [["Processo Oracle Concluído"]]}
                        ).execute()

                        # ✅ Marcar como concluído no cache (remove do cache)
                        cache.marcar_concluido(id_linha)
                        gui_log(f"✅ Linha {i} processada e salva no Oracle + Sheets atualizado")

                        # Notificar sucesso no Telegram
                        if _telegram_notifier:
                            try:
                                if _telegram_notifier.enabled:
                                    resultado = _telegram_notifier.notificar_sucesso_item(i, item)
                                    gui_log(f"📱 [TELEGRAM] Notificação de sucesso enviada: {resultado}")
                            except Exception as e:
                                gui_log(f"⚠️ [TELEGRAM] Erro ao notificar sucesso: {e}")

                    except Exception as err:
                        gui_log(f"⚠️ Falha ao atualizar Sheets: {err}. Permanece no cache para retry...")

                itens_processados += 1
                _dados_inseridos_oracle = True  # Marcar que dados foram inseridos
                time.sleep(0.5)

            # ✅ CONTINUA PROCESSANDO TODOS OS ITENS DISPONÍVEIS
            # (Removido break que limitava a 1 item por ciclo)

        # Verificar se processou pelo menos 1 item antes de continuar
        if itens_processados == 0:
            gui_log("⚠️ Nenhum item foi processado (RPA foi interrompido)")
            return False

        gui_log(f"✅ {itens_processados} linhas processadas com sucesso")

        tempo_espera = config["tempos_espera"]["apos_rpa_oracle"]
        return aguardar_com_pausa(tempo_espera, "Aguardando estabilização pós-Oracle")

    except Exception as e:
        gui_log(f"❌ Erro ao processar Oracle: {e}")
        import traceback
        gui_log(traceback.format_exc())
        return False

def etapa_06_navegacao_pos_oracle(config):
    """Etapa 6: Navegação após RPA_Oracle - Fechar janelas e abrir Bancada

    FLUXO CORRETO:
    1. Limpar formulário (botão Limpar)
    2. Fechar janela "Subinventory Transfer (BC2)" (X)
    3. Fechar janela "Transferencia do Subinventario (BC2)" (X)
    4. Clicar em "Janela" para dar foco
    5. Clicar no menu de navegação
    6. Duplo clique para abrir Bancada de Material
    """
    global _rpa_running, _dados_inseridos_oracle

    try:
        gui_log("📋 ETAPA 6: Fechamento de modais e abertura da Bancada")

        tempo_espera = config["tempos_espera"]["entre_cliques"]

        # Verificar se dados foram inseridos no Oracle
        if _dados_inseridos_oracle:
            gui_log("🧹 Dados foram inseridos - Limpando formulário primeiro...")
        else:
            gui_log("ℹ️ Nenhum dado foi inserido - Fechando modais...")

        # 1. Limpar formulário (botão Limpar)
        gui_log("🧹 [PASSO 1/6] Limpando formulário...")
        coord = config["coordenadas"]["tela_06_limpar"]
        clicar_coordenada(coord["x"], coord["y"], descricao=coord["descricao"])

        if not aguardar_com_pausa(tempo_espera, "Aguardando limpeza"):
            if not _rpa_running:
                gui_log("❌ [PASSO 1/6] RPA foi parado durante limpeza")
                return False

        # 2. Fechar janela "Subinventory Transfer (BC2)" - Botão X
        gui_log("🔴 [PASSO 2/6] Fechando 'Subinventory Transfer (BC2)'...")
        coord = config["coordenadas"]["tela_06_fechar_subinventory_transfer"]
        clicar_coordenada(coord["x"], coord["y"], descricao=coord["descricao"])

        if not aguardar_com_pausa(tempo_espera, "Aguardando fechar primeira janela"):
            if not _rpa_running:
                gui_log("❌ [PASSO 2/6] RPA foi parado ao fechar primeira janela")
                return False

        # 3. Fechar janela "Transferencia do Subinventario (BC2)" - Botão X
        gui_log("🔴 [PASSO 3/6] Fechando 'Transferencia do Subinventario (BC2)'...")
        coord = config["coordenadas"]["tela_06_fechar_transferencia_subinventario_bc2"]
        clicar_coordenada(coord["x"], coord["y"], descricao=coord["descricao"])

        if not aguardar_com_pausa(tempo_espera, "Aguardando fechar segunda janela"):
            if not _rpa_running:
                gui_log("❌ [PASSO 3/6] RPA foi parado ao fechar segunda janela")
                return False

        gui_log("✅ Ambas as modais foram fechadas com sucesso")

        # 4. CRÍTICO: Clicar em "Janela" para dar foco antes de navegar
        gui_log("🖱️ [PASSO 4/6] Clicando em 'Janela' para dar foco...")
        gui_log(f"[DEBUG] _rpa_running={_rpa_running} | Tentando clicar em 'Janela'")

        coord = config["coordenadas"]["navegador_janela"]
        gui_log(f"[DEBUG] Coordenadas de 'Janela': x={coord['x']}, y={coord['y']}")

        try:
            clicar_coordenada(coord["x"], coord["y"], descricao=coord["descricao"])
            gui_log(f"[DEBUG] ✅ Clique em 'Janela' executado. _rpa_running={_rpa_running}")
        except pyautogui.FailSafeException as e:
            gui_log("🛑 [PASSO 4/6] FAILSAFE ACIONADO ao clicar em 'Janela'!")
            gui_log(f"   Mouse estava no canto superior esquerdo: {e}")
            gui_log("   Mova o mouse para longe do canto (0,0) e tente novamente")
            _rpa_running = False
            return False
        except Exception as e:
            gui_log(f"❌ [PASSO 4/6] ERRO ao clicar em 'Janela': {e}")
            import traceback
            gui_log(traceback.format_exc())
            return False

        if not aguardar_com_pausa(tempo_espera, "Aguardando foco em 'Janela'"):
            if not _rpa_running:
                gui_log("❌ [PASSO 4/6] RPA foi parado após clicar em 'Janela'")
                return False

        # 5. Clicar no menu de navegação
        gui_log("🖱️ [PASSO 5/6] Clicando no menu de navegação...")
        gui_log(f"[DEBUG] _rpa_running={_rpa_running}")
        coord = config["coordenadas"]["navegador_menu"]
        gui_log(f"[DEBUG] Coordenadas do menu: x={coord['x']}, y={coord['y']}")

        try:
            clicar_coordenada(coord["x"], coord["y"], descricao=coord["descricao"])
            gui_log(f"[DEBUG] ✅ Clique no menu executado. _rpa_running={_rpa_running}")
        except pyautogui.FailSafeException:
            gui_log("🛑 [PASSO 5/6] FAILSAFE acionado ao clicar no menu")
            _rpa_running = False
            return False

        if not aguardar_com_pausa(tempo_espera, "Aguardando menu abrir"):
            if not _rpa_running:
                gui_log("❌ [PASSO 5/6] RPA foi parado após clicar no menu")
                return False

        # 6. Abrir Bancada de Material
        gui_log("📂 [PASSO 6/6] Abrindo Bancada de Material...")
        gui_log(f"[DEBUG] _rpa_running={_rpa_running}")
        coord = config["coordenadas"]["tela_07_bancada_material"]
        duplo_clique = coord.get("duplo_clique", False)
        gui_log(f"[DEBUG] Coordenadas bancada: x={coord['x']}, y={coord['y']}, duplo_clique={duplo_clique}")

        try:
            clicar_coordenada(coord["x"], coord["y"], duplo=duplo_clique, descricao=coord["descricao"])
            gui_log(f"[DEBUG] ✅ Bancada aberta. _rpa_running={_rpa_running}")
        except pyautogui.FailSafeException:
            gui_log("🛑 [PASSO 6/6] FAILSAFE acionado ao abrir bancada")
            _rpa_running = False
            return False
        except Exception as e:
            gui_log(f"❌ [PASSO 6/6] Erro ao abrir bancada: {e}")
            import traceback
            gui_log(traceback.format_exc())
            return False

        tempo_espera = config["tempos_espera"]["apos_modal"]
        resultado = aguardar_com_pausa(tempo_espera, "Aguardando abertura da Bancada")

        if not resultado:
            gui_log("⚠️ [ETAPA 6] Aguardar foi interrompido, mas etapa foi concluída")
            # Verificar se foi realmente interrompido pelo usuário ou apenas timeout
            if not _rpa_running:
                gui_log("🛑 [ETAPA 6] RPA foi parado pelo usuário")
                return False
            else:
                gui_log("✅ [ETAPA 6] Continuando ciclo (abertura da bancada concluída)")
                return True

        gui_log("✅ [ETAPA 6] Navegação concluída com sucesso")
        return True

    except Exception as e:
        gui_log(f"❌ [ETAPA 6] Erro durante navegação: {e}")
        import traceback
        gui_log(traceback.format_exc())
        return False

def mapear_colunas_oracle_bancada(df):
    """
    Mapeia colunas do Oracle para nomes padronizados.
    Garante que as 8 colunas principais sejam identificadas.
    (Baseado no main.py da bancada)
    """
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

def texto_para_df_bancada(tsv_texto):
    """
    Converte o texto copiado do Oracle (TSV) em DataFrame limpo.
    (Baseado no main.py da bancada)
    """
    if not PANDAS_DISPONIVEL:
        gui_log("❌ pandas não disponível - não é possível processar dados")
        return None

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
            df_mapeado = mapear_colunas_oracle_bancada(df)

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
                    df_mapeado_direto = mapear_colunas_oracle_bancada(df_direto)
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

def salvar_excel_bancada(df):
    """
    Salva o DataFrame em XLSX (um arquivo por dia).
    Retorna o caminho do arquivo salvo.
    (Baseado no main.py da bancada)
    """
    if not PANDAS_DISPONIVEL:
        gui_log("❌ pandas não disponível - não é possível salvar Excel")
        return None

    # Criar pasta out/ se não existir
    base_dir = Path(base_path)
    out_dir = base_dir / "out"
    out_dir.mkdir(exist_ok=True)

    hoje = pd.Timestamp.now().strftime("%Y-%m-%d")
    xlsx = out_dir / f"bancada-{hoje}.xlsx"

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
            gui_log(f"✅ Excel salvo: {xlsx} ({df.shape[0]:,} linhas, {df.shape[1]} colunas)")
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

def monitorar_clipboard_inteligente(max_tempo=15*60, intervalo_check=5, estabilidade_segundos=30):
    """
    Monitora o clipboard de forma inteligente e detecta quando Oracle terminou de copiar.

    Args:
        max_tempo: Tempo máximo de espera (padrão: 15 minutos)
        intervalo_check: Intervalo entre verificações (padrão: 5 segundos)
        estabilidade_segundos: Tempo sem mudança para considerar completo (padrão: 30 segundos)

    Returns:
        str: Conteúdo do clipboard ou string vazia se falhar
    """
    try:
        import pyperclip
    except ImportError:
        gui_log("❌ pyperclip não disponível")
        return ""

    import hashlib

    gui_log("=" * 60)
    gui_log("🔍 MONITORAMENTO INTELIGENTE DO CLIPBOARD")
    gui_log("=" * 60)
    gui_log(f"⏱️ Tempo máximo: {max_tempo//60} minutos")
    gui_log(f"🔄 Verificação a cada: {intervalo_check} segundos")
    gui_log(f"✅ Estabilidade requerida: {estabilidade_segundos} segundos")
    gui_log("")

    inicio = time.time()
    ultimo_hash = ""
    ultimo_tamanho = 0
    tempo_sem_mudanca = 0
    verificacoes = 0
    ultimo_movimento_mouse = time.time()

    while (time.time() - inicio) < max_tempo:
        if not _rpa_running:
            gui_log("⏸️ Monitoramento cancelado pelo usuário")
            return ""

        verificacoes += 1
        tempo_decorrido = int(time.time() - inicio)

        # NOTA: Movimento de mouse agora é feito pela thread em background (a cada 1s)
        # Removido daqui para evitar conflito

        # Ler clipboard atual
        texto_atual = pyperclip.paste() or ""
        tamanho_atual = len(texto_atual)

        # Calcular hash para detectar mudanças
        hash_atual = hashlib.md5(texto_atual.encode('utf-8')).hexdigest() if texto_atual else ""

        # Detectar mudança
        if hash_atual != ultimo_hash:
            # Clipboard mudou!
            linhas = texto_atual.count('\n')
            kb = tamanho_atual / 1024

            if tamanho_atual > 0:
                if ultimo_tamanho == 0:
                    # Primeira vez que detecta dados - cópia iniciou!
                    gui_log(f"✨ [{tempo_decorrido}s] 🎬 CÓPIA INICIADA! Primeiro bloco de dados detectado")
                gui_log(f"📊 [{tempo_decorrido}s] Copiando... {tamanho_atual:,} chars ({kb:.1f} KB) | {linhas:,} linhas")
            else:
                gui_log(f"🔍 [{tempo_decorrido}s] Aguardando modal 'Exportação em andamento' abrir...")

            # Resetar contador de estabilidade
            tempo_sem_mudanca = 0
            ultimo_hash = hash_atual
            ultimo_tamanho = tamanho_atual
        else:
            # Clipboard não mudou
            tempo_sem_mudanca += intervalo_check

            if tamanho_atual > 50:  # Tem dados
                gui_log(f"⏳ [{tempo_decorrido}s] Clipboard estável: {tamanho_atual:,} chars | Estável por {tempo_sem_mudanca}s")

                # VERIFICAR SE ESTABILIZOU (dados completos!)
                if tempo_sem_mudanca >= estabilidade_segundos:
                    linhas = texto_atual.count('\n')
                    kb = tamanho_atual / 1024

                    gui_log("=" * 60)
                    gui_log("✅ CÓPIA COMPLETA DETECTADA!")
                    gui_log("🎉 Modal 'Exportação em andamento' fechou - dados finalizados!")
                    gui_log(f"⏱️ Tempo total: {tempo_decorrido} segundos ({tempo_decorrido//60}m {tempo_decorrido%60}s)")
                    gui_log(f"📊 Tamanho final: {tamanho_atual:,} caracteres ({kb:.2f} KB)")
                    gui_log(f"📋 Total de linhas: {linhas:,}")
                    gui_log(f"🔄 Verificações realizadas: {verificacoes}")
                    gui_log(f"💾 Economizou: {(max_tempo - tempo_decorrido)//60} minutos de espera!")
                    gui_log("=" * 60)

                    return texto_atual
            else:
                # Clipboard ainda vazio
                if verificacoes % 10 == 0:  # Log a cada 30s (10 * 3s)
                    gui_log(f"⏳ [{tempo_decorrido}s] Modal 'Exportação em andamento' visível - aguardando dados...")

        # Aguardar próxima verificação
        time.sleep(intervalo_check)

    # Timeout atingido
    texto_final = pyperclip.paste() or ""
    tamanho_final = len(texto_final)

    gui_log("=" * 60)
    gui_log("⏱️ TIMEOUT: Tempo máximo atingido")
    gui_log(f"📊 Tamanho no timeout: {tamanho_final:,} caracteres")

    if tamanho_final > 50:
        linhas = texto_final.count('\n')
        gui_log(f"📋 Linhas no timeout: {linhas:,}")
        gui_log("⚠️ Retornando dados mesmo com timeout...")
        gui_log("=" * 60)
        return texto_final
    else:
        gui_log("❌ Clipboard vazio mesmo após timeout")
        gui_log("=" * 60)
        return ""

def etapa_07_executar_rpa_bancada(config):
    """
    Etapa 7: Extrair dados da Bancada (modo standalone)
    Baseado no main.py da bancada que funciona corretamente
    """
    gui_log("=" * 60)
    gui_log("🤖 ETAPA 7: Extração de dados da Bancada")
    gui_log("=" * 60)

    try:
        # Verificar pyperclip
        try:
            import pyperclip
            gui_log("✅ pyperclip disponível para copiar dados")
        except ImportError:
            gui_log("⚠️ pyperclip não disponível - pulando extração de dados")
            tempo_espera = config["tempos_espera"]["apos_rpa_bancada"]
            return aguardar_com_pausa(tempo_espera, "Aguardando estabilização")

        # PASSO 1: Clicar em "Detalhado"
        gui_log("📍 [1/9] Clicando em 'Detalhado'...")
        coord = config["coordenadas"]["bancada_detalhado"]
        clicar_coordenada(coord["x"], coord["y"], descricao=coord["descricao"])

        if not _rpa_running:
            return False

        # PASSO 2: Pressionar Enter (ao invés de clicar em Localizar)
        gui_log("⌨️ [2/9] Pressionando Enter...")
        if MODO_TESTE:
            gui_log("[MODO TESTE] Simulando Enter")
        else:
            pyautogui.press('enter')

        time.sleep(1.2)  # SLEEP_ABERTURA do main.py

        if not _rpa_running:
            return False

        # PASSO 3: Aguardar 2 minutos antes de clicar na célula
        gui_log("⏳ [3/9] Aguardando 2 minutos para grid carregar...")
        if not aguardar_com_pausa(120, "Carregamento da grid (2 minutos)", evitar_hibernar=True):
            return False

        # PASSO 4: Clicar na primeira célula da coluna 'Org.'
        gui_log("📍 [4/9] Clicando na célula Org...")
        coord = config["coordenadas"]["bancada_celula_org"]
        clicar_coordenada(coord["x"], coord["y"], descricao=coord["descricao"])

        if not _rpa_running:
            return False

        # PASSO 5: Limpar clipboard ANTES de copiar
        gui_log("🧹 [5/9] Limpando clipboard...")
        pyperclip.copy('')
        time.sleep(0.3)

        # PASSO 6: Abrir menu via Shift+F10
        gui_log("⌨️ [6/9] Abrindo menu de contexto (Shift+F10)...")
        if MODO_TESTE:
            gui_log("[MODO TESTE] Simulando Shift+F10")
        else:
            pyautogui.hotkey('shift', 'f10')

        time.sleep(1.5)

        # PASSO 7: Navegar menu e selecionar "Copiar Todas as Linhas"
        gui_log("⌨️ [7/9] Navegando menu para 'Copiar Todas as Linhas'...")
        if MODO_TESTE:
            gui_log("[MODO TESTE] Simulando navegação")
        else:
            for i in range(3):
                pyautogui.press('down')
                time.sleep(0.25)
                gui_log(f"   Seta para baixo {i+1}/3")

            gui_log("   Pressionando Enter para copiar...")
            pyautogui.press('enter')
            time.sleep(0.6)

        if not _rpa_running:
            return False

        # PASSO 8: MONITORAMENTO INTELIGENTE DO CLIPBOARD
        # Quando clica em "Copiar Todas as Linhas", Oracle abre modal "Exportação em andamento"
        # Modal abre = cópia iniciou | Modal fecha = cópia completa
        gui_log("")
        gui_log("🎯 [8/9] Iniciando monitoramento inteligente do clipboard...")
        gui_log("💡 Modal 'Exportação em andamento' indica que cópia está em progresso")
        gui_log("💡 Sistema detectará automaticamente quando modal fechar (cópia completa)")
        gui_log("")

        # 🖱️ INICIAR MOVIMENTO CONTÍNUO DO MOUSE (anti-hibernação durante TODA a bancada)
        gui_log("🖱️ Iniciando proteção anti-hibernação ULTRA-AGRESSIVA...")
        gui_log("   → Mouse: Move 5px a cada 1 segundo")
        gui_log("   → Teclado: Pressiona Shift a cada 15 segundos")
        gui_log("💡 Protege contra hibernação, screensaver e bloqueio de tela")
        stop_mouse_event = iniciar_movimento_mouse_continuo()

        texto_copiado = monitorar_clipboard_inteligente(
            max_tempo=15 * 60,        # Máximo 15 minutos
            intervalo_check=3,        # Verificar a cada 3 segundos (mais rápido)
            estabilidade_segundos=30  # Considerar completo após 30s sem mudança
        )

        if not texto_copiado or len(texto_copiado) < 50:
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
        linhas = texto_copiado.count('\n')
        tamanho_kb = len(texto_copiado.encode('utf-8')) / 1024
        gui_log("=" * 60)
        gui_log("✅ DADOS COPIADOS COM SUCESSO!")
        gui_log(f"📊 Total: {linhas:,} linhas")
        gui_log(f"📦 Tamanho: {tamanho_kb:.2f} KB ({len(texto_copiado):,} caracteres)")
        gui_log("=" * 60)

        # Mostrar preview dos primeiros 500 caracteres
        preview = texto_copiado[:500].replace('\n', '\\n').replace('\t', '\\t')
        gui_log(f"👀 Preview (500 chars): {preview}...")

        # PROCESSAR DADOS COPIADOS
        gui_log("")
        gui_log("=" * 60)
        gui_log("📋 PROCESSANDO DADOS DA BANCADA")
        gui_log("=" * 60)

        if not PANDAS_DISPONIVEL:
            gui_log("⚠️ pandas não disponível - pulando processamento")
            tempo_espera = config["tempos_espera"]["apos_rpa_bancada"]
            return aguardar_com_pausa(tempo_espera, "Aguardando estabilização")

        # Converter texto TSV para DataFrame
        df = texto_para_df_bancada(texto_copiado)

        if df is None or df.empty:
            gui_log("❌ Falha ao processar dados - DataFrame vazio")
            tempo_espera = config["tempos_espera"]["apos_rpa_bancada"]
            return aguardar_com_pausa(tempo_espera, "Aguardando estabilização")

        gui_log(f"✅ Dados processados: {df.shape[0]:,} linhas x {df.shape[1]} colunas")

        # SALVAR EM EXCEL LOCAL
        gui_log("")
        gui_log("💾 Salvando dados em Excel local...")
        arquivo_excel = salvar_excel_bancada(df)

        if arquivo_excel:
            gui_log(f"✅ Excel salvo: {arquivo_excel}")
        else:
            gui_log("⚠️ Falha ao salvar Excel local, mas continuando...")

        # ENVIAR PARA GOOGLE SHEETS
        if GOOGLE_SHEETS_BANCADA_DISPONIVEL and not df.empty:
            gui_log("")
            gui_log("☁️ Enviando dados para Google Sheets...")

            try:
                sucesso_sheets = enviar_para_google_sheets(df)

                if sucesso_sheets:
                    gui_log("✅ Dados enviados para Google Sheets com sucesso!")
                else:
                    gui_log("❌ Falha ao enviar para Google Sheets")
            except Exception as e:
                gui_log(f"❌ Erro ao enviar para Google Sheets: {e}")
                import traceback
                gui_log(traceback.format_exc())
        else:
            if not GOOGLE_SHEETS_BANCADA_DISPONIVEL:
                gui_log("⚠️ Google Sheets (bancada) não configurado")
                gui_log("💡 Os dados foram salvos apenas localmente")

        gui_log("")
        gui_log("=" * 60)
        gui_log("✅ PROCESSAMENTO DA BANCADA CONCLUÍDO")
        gui_log("=" * 60)

        # 🖱️ PARAR MOVIMENTO CONTÍNUO DO MOUSE
        try:
            stop_mouse_event.set()
            gui_log("🖱️ Movimento contínuo do mouse parado")
        except:
            pass

        tempo_espera = config["tempos_espera"]["apos_rpa_bancada"]
        return aguardar_com_pausa(tempo_espera, "Aguardando estabilização", evitar_hibernar=True)

    except Exception as e:
        gui_log("=" * 60)
        gui_log(f"❌ ERRO ao extrair dados da Bancada: {e}")
        gui_log("=" * 60)
        import traceback
        gui_log(traceback.format_exc())

        # 🖱️ PARAR MOVIMENTO CONTÍNUO DO MOUSE (em caso de erro)
        try:
            stop_mouse_event.set()
            gui_log("🖱️ Movimento contínuo do mouse parado (erro)")
        except:
            pass

        # Não falhar o ciclo por causa disso
        tempo_espera = config["tempos_espera"]["apos_rpa_bancada"]
        return aguardar_com_pausa(tempo_espera, "Aguardando estabilização", evitar_hibernar=True)


def etapa_08_fechar_bancada(config):
    """Etapa 8: Fechar a janela da Bancada"""
    gui_log("📋 ETAPA 8: Fechamento da Bancada")

    coord = config["coordenadas"]["tela_08_fechar_bancada"]
    clicar_coordenada(coord["x"], coord["y"], descricao=coord["descricao"])

    tempo_espera = config["tempos_espera"]["entre_cliques"]
    return aguardar_com_pausa(tempo_espera, "Aguardando fechamento")

# =================== ESPERA INTELIGENTE ENTRE CICLOS ===================
def aguardar_inteligente_entre_ciclos(config, max_minutos=15, intervalo_verificacao=60):
    """
    Aguarda entre ciclos verificando periodicamente se há novos itens no Google Sheets.

    Funcionalidades:
    - Verifica novos itens a cada {intervalo_verificacao} segundos (padrão: 60s = 1 minuto)
    - Anti-hibernação: move o mouse periodicamente
    - Se encontrar novos itens: retorna True imediatamente
    - Se atingir {max_minutos} sem novos itens: retorna False

    Args:
        config: Configurações do RPA
        max_minutos: Tempo máximo de espera em minutos (padrão: 15)
        intervalo_verificacao: Intervalo entre verificações em segundos (padrão: 60)

    Returns:
        bool: True se encontrou novos itens, False se atingiu tempo máximo
    """
    global _rpa_running

    max_segundos = max_minutos * 60
    inicio = time.time()
    verificacao_numero = 0

    gui_log("")
    gui_log("=" * 70)
    gui_log(f"⏰ ESPERA INTELIGENTE ENTRE CICLOS")
    gui_log(f"   • Tempo máximo: {max_minutos} minutos")
    gui_log(f"   • Verificação de novos itens a cada: {intervalo_verificacao//60} minuto(s)")
    gui_log(f"   • Anti-hibernação: ATIVO")
    gui_log("=" * 70)

    while _rpa_running:
        tempo_decorrido = time.time() - inicio

        # Verificar se atingiu o tempo máximo
        if tempo_decorrido >= max_segundos:
            gui_log("")
            gui_log(f"⏱️ Tempo máximo de {max_minutos} minutos atingido")
            gui_log("🔄 Retornando para atualizar bancada...")
            return False

        tempo_restante = max_segundos - tempo_decorrido
        minutos_restantes = int(tempo_restante // 60)
        segundos_restantes = int(tempo_restante % 60)

        # Verificar se há novos itens no Google Sheets
        verificacao_numero += 1
        gui_log("")
        gui_log(f"🔍 Verificação #{verificacao_numero} - Tempo restante: {minutos_restantes}m {segundos_restantes}s")

        try:
            # Verificar itens pendentes no Google Sheets
            tem_itens = verificar_tem_itens_pendentes()

            if tem_itens:
                gui_log("✅ NOVOS ITENS DETECTADOS!")
                gui_log(f"   Tempo economizado: {minutos_restantes}m {segundos_restantes}s")

                # Notificar via Telegram
                try:
                    if _telegram_notifier and _telegram_notifier.enabled:
                        _telegram_notifier.enviar_mensagem(
                            f"🎯 <b>NOVOS ITENS DETECTADOS</b>\n\n"
                            f"⏰ Verificação #{verificacao_numero}\n"
                            f"⚡ Processando imediatamente...\n"
                            f"💾 Economizou {minutos_restantes}m {segundos_restantes}s de espera"
                        )
                except:
                    pass

                return True
            else:
                gui_log("   Nenhum item novo encontrado")

        except Exception as e:
            gui_log(f"⚠️ Erro ao verificar itens: {e}")

        # Aguardar intervalo de verificação com anti-hibernação
        gui_log(f"⏳ Próxima verificação em {intervalo_verificacao//60} minuto(s)...")

        tempo_aguardado = 0
        intervalo_movimento = 30  # Mover mouse a cada 30 segundos
        ultimo_movimento = time.time()

        while tempo_aguardado < intervalo_verificacao and _rpa_running:
            time.sleep(1)
            tempo_aguardado += 1

            # Anti-hibernação: mover mouse periodicamente
            if time.time() - ultimo_movimento >= intervalo_movimento:
                try:
                    pos_atual = pyautogui.position()
                    # Mover 1 pixel para direita e voltar
                    pyautogui.moveTo(pos_atual.x + 1, pos_atual.y, duration=0.1)
                    pyautogui.moveTo(pos_atual.x, pos_atual.y, duration=0.1)
                    ultimo_movimento = time.time()
                except:
                    pass

            # Mostrar progresso a cada 10 segundos
            if tempo_aguardado % 10 == 0:
                segundos_restantes_verificacao = intervalo_verificacao - tempo_aguardado
                print(f"   {segundos_restantes_verificacao}s até próxima verificação...", end='\r')

        if not _rpa_running:
            gui_log("🛑 RPA parado pelo usuário durante espera")
            return False

    return False

def verificar_tem_itens_pendentes():
    """
    Verifica se há itens pendentes no Google Sheets para processar.

    Returns:
        bool: True se há itens pendentes, False caso contrário
    """
    if not GOOGLE_SHEETS_DISPONIVEL:
        return False

    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
        SPREADSHEET_ID = "1UgJWxmnYzv-FVTT4rrrVEx3J_MNXZsctwrPSTyyylPQ"
        SHEET_NAME = "Planilha Oracle"

        # Autenticar
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                return False

        service = build("sheets", "v4", credentials=creds)

        # Ler planilha
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A2:T1000"
        ).execute()

        values = result.get("values", [])

        if not values:
            return False

        # Verificar headers
        headers_result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A1:T1"
        ).execute()

        headers = headers_result.get("values", [[]])[0]

        if "Status Oracle" not in headers:
            return False

        idx_status = headers.index("Status Oracle")

        # Verificar se há linhas pendentes
        for row in values:
            if len(row) <= idx_status:
                return True  # Linha sem status = pendente

            status = str(row[idx_status]).strip().upper()

            # Considerar pendente se vazio ou específicos
            if not status or status == "" or "PENDENTE" in status or "AGUARDANDO" in status:
                return True

        return False

    except Exception as e:
        gui_log(f"⚠️ Erro ao verificar itens pendentes: {e}")
        return False

# =================== MONITORAMENTO DA TECLA ESC ===================
def monitorar_tecla_esc():
    """
    Monitora a tecla ESC para parar o RPA (IGUAL AO RPA_ORACLE)
    Usa keyboard.hook() para capturar TODAS as teclas e detectar ESC
    """
    global _rpa_running

    gui_log("[ESC] ⌨️  Thread de monitoramento ESC iniciada")
    gui_log("[ESC] 🔍 Pressione ESC a qualquer momento para parar o RPA")

    def parar_callback(event):
        """Callback chamado para TODAS as teclas pressionadas"""
        global _rpa_running

        # 🔧 CORREÇÃO: Apenas logar ESC para evitar spam (F6 não é relevante aqui)
        if event.name == 'esc':
            gui_log(f"[ESC] 🔘 Tecla ESC detectada | event_type: {event.event_type}")

        # Verificar se é ESC e se está em modo "down" (pressionado)
        if event.name == 'esc' and event.event_type == 'down':
            gui_log("━" * 70)
            gui_log("⚠️  [ESC] TECLA ESC PRESSIONADA - PARANDO RPA...")
            gui_log("━" * 70)
            _rpa_running = False
            try:
                keyboard.unhook_all()
                gui_log("🛑 [ESC] Hook removido com sucesso")
            except Exception as e_unhook:
                gui_log(f"⚠️ [ESC] Erro ao remover hook: {e_unhook}")

    try:
        # Registrar hook para capturar TODAS as teclas
        keyboard.hook(parar_callback)
        gui_log("[ESC] ✅ Hook do teclado registrado com sucesso")
        gui_log("[ESC] 🔄 Aguardando tecla ESC...")

        # Loop enquanto RPA está rodando
        while _rpa_running:
            time.sleep(0.1)

        gui_log("[ESC] 🏁 Thread de monitoramento ESC encerrada (_rpa_running=False)")

        # Limpar hooks ao sair
        try:
            keyboard.unhook_all()
            gui_log("[ESC] 🧹 Hooks limpos ao encerrar thread")
        except:
            pass

    except Exception as e:
        gui_log(f"[ESC] ❌ Erro no monitoramento ESC: {e}")
        import traceback
        gui_log(f"[ESC] Traceback:\n{traceback.format_exc()}")

# =================== EXECUÇÃO DO CICLO COMPLETO ===================
def executar_ciclo_completo(config):
    """Executa um ciclo completo de todas as etapas"""
    global _ciclo_atual, _data_inicio_ciclo

    _ciclo_atual += 1
    _data_inicio_ciclo = datetime.now()
    primeiro_ciclo = (_ciclo_atual == 1)  # Verificar se é o primeiro ciclo

    gui_log("=" * 60)
    gui_log(f"🔄 CICLO #{_ciclo_atual} - {_data_inicio_ciclo.strftime('%Y-%m-%d %H:%M:%S')}")
    if primeiro_ciclo:
        gui_log("🆕 PRIMEIRO CICLO - Se não houver itens após 2 tentativas, prossegue para Bancada")
    gui_log("=" * 60)

    # Notificar início do ciclo no Telegram
    if _telegram_notifier:
        try:
            _telegram_notifier.notificar_ciclo_inicio(_ciclo_atual)
        except:
            pass

    # Registrar início no Google Sheets
    if GOOGLE_SHEETS_DISPONIVEL:
        try:
            registrar_ciclo(
                ciclo_numero=_ciclo_atual,
                status="Em Execução",
                data_inicio=_data_inicio_ciclo
            )
        except Exception as e:
            gui_log(f"⚠️ Erro ao registrar no Google Sheets: {e}")

    etapas_status = {
        "RPA Oracle": "Pendente",
        "RPA Bancada": "Pendente"
    }

    try:
        # Executar todas as etapas em sequência
        etapas = [
            ("Transferência Subinventário", etapa_01_transferencia_subinventario, False),
            ("Preenchimento Tipo", etapa_02_preencher_tipo, False),
            ("Seleção e Confirmação Funcionário", etapa_03_selecionar_funcionario, False),
            ("RPA Oracle", etapa_05_executar_rpa_oracle, True),  # Aceita parâmetro primeiro_ciclo
            ("Navegação", etapa_06_navegacao_pos_oracle, False),
            ("RPA Bancada", etapa_07_executar_rpa_bancada, False),
            ("Fechamento Bancada", etapa_08_fechar_bancada, False)
        ]

        for nome_etapa, funcao_etapa, aceita_primeiro_ciclo in etapas:
            if not _rpa_running:
                gui_log("⏸️ Ciclo interrompido pelo usuário")

                # Atualizar no Google Sheets
                if GOOGLE_SHEETS_DISPONIVEL:
                    try:
                        atualizar_ciclo(_ciclo_atual, "Status", "Pausado")
                        atualizar_ciclo(_ciclo_atual, "Etapa Falha", nome_etapa)
                    except Exception:
                        pass

                return False

            # Passar parâmetro primeiro_ciclo apenas para RPA Oracle
            if aceita_primeiro_ciclo:
                sucesso = funcao_etapa(config, primeiro_ciclo=primeiro_ciclo)
            else:
                sucesso = funcao_etapa(config)

            # Atualizar status de etapas específicas
            if nome_etapa == "RPA Oracle":
                etapas_status["RPA Oracle"] = "Sucesso" if sucesso else "Falha"
            elif nome_etapa == "RPA Bancada":
                etapas_status["RPA Bancada"] = "Sucesso" if sucesso else "Falha"

            if not sucesso:
                gui_log(f"❌ Falha na etapa: {nome_etapa}")

                # Atualizar no Google Sheets
                if GOOGLE_SHEETS_DISPONIVEL:
                    try:
                        data_fim = datetime.now()
                        atualizar_ciclo(_ciclo_atual, "Status", "Falha")
                        atualizar_ciclo(_ciclo_atual, "Data/Hora Fim", data_fim.strftime("%Y-%m-%d %H:%M:%S"))
                        atualizar_ciclo(_ciclo_atual, "Etapa Falha", nome_etapa)
                        atualizar_ciclo(_ciclo_atual, "RPA Oracle", etapas_status["RPA Oracle"])
                        atualizar_ciclo(_ciclo_atual, "RPA Bancada", etapas_status["RPA Bancada"])
                    except Exception:
                        pass

                return False

        # Sucesso!
        data_fim = datetime.now()
        gui_log("=" * 60)
        gui_log(f"✅ CICLO #{_ciclo_atual} CONCLUÍDO COM SUCESSO!")
        gui_log("=" * 60)

        # Atualizar no Google Sheets
        if GOOGLE_SHEETS_DISPONIVEL:
            try:
                atualizar_ciclo(_ciclo_atual, "Status", "Sucesso")
                atualizar_ciclo(_ciclo_atual, "Data/Hora Fim", data_fim.strftime("%Y-%m-%d %H:%M:%S"))
                atualizar_ciclo(_ciclo_atual, "RPA Oracle", etapas_status["RPA Oracle"])
                atualizar_ciclo(_ciclo_atual, "RPA Bancada", etapas_status["RPA Bancada"])

                # Calcular tempo
                delta = data_fim - _data_inicio_ciclo
                minutos = delta.total_seconds() / 60
                atualizar_ciclo(_ciclo_atual, "Tempo Execução (min)", f"{minutos:.2f}")
            except Exception as e:
                gui_log(f"⚠️ Erro ao atualizar Google Sheets: {e}")

        return True

    except Exception as e:
        gui_log(f"❌ Erro durante o ciclo: {e}")
        import traceback
        gui_log(traceback.format_exc())

        # Atualizar no Google Sheets
        if GOOGLE_SHEETS_DISPONIVEL:
            try:
                atualizar_ciclo(_ciclo_atual, "Status", "Erro")
                atualizar_ciclo(_ciclo_atual, "Observações", str(e))
            except Exception:
                pass

        return False

# =================== LOOP PRINCIPAL ===================
def main(modo_continuo=True):
    """
    Função principal - executa em loop contínuo sem interrupção

    Args:
        modo_continuo: Se True, executa em loop contínuo (padrão: True)
    """
    global _rpa_running, _ciclo_atual, _telegram_notifier
    _rpa_running = True

    # Inicializar Telegram
    if TELEGRAM_DISPONIVEL:
        try:
            _telegram_notifier = inicializar_telegram()
            if _telegram_notifier and _telegram_notifier.enabled:
                gui_log("✅ [TELEGRAM] Notificador inicializado com sucesso")
                gui_log(f"   Bot Token: {_telegram_notifier.bot_token[:20]}...")
                gui_log(f"   Chat ID: {_telegram_notifier.chat_id}")
                # Enviar mensagem de teste
                resultado = _telegram_notifier.enviar_mensagem("🤖 RPA Ciclo iniciado!")
                gui_log(f"   Teste de envio: {resultado}")
            else:
                gui_log("⚠️ [TELEGRAM] Notificador criado mas desabilitado (verifique config.json)")
        except Exception as e:
            gui_log(f"⚠️ [TELEGRAM] Erro ao inicializar: {e}")
            _telegram_notifier = None
    else:
        gui_log("⚠️ [TELEGRAM] Módulo telegram_notifier não disponível")
        _telegram_notifier = None

    # Iniciar monitoramento da tecla ESC em thread separada
    thread_esc = threading.Thread(target=monitorar_tecla_esc, daemon=True)
    thread_esc.start()

    gui_log("=" * 60)
    gui_log("🤖 RPA CICLO - Iniciado")
    gui_log("⌨️ [ESC] Pressione ESC para parar o RPA a qualquer momento")
    if MODO_TESTE:
        gui_log("[MODO TESTE ATIVADO] Simulação sem movimentos físicos - apenas teste de lógica")
    gui_log("=" * 60)

    try:
        config = carregar_config()

        if modo_continuo:
            gui_log("🔄 Modo contínuo ativado - execução ininterrupta")
            gui_log("⚠️ O RPA Oracle aguardará automaticamente se não houver nada para processar")
            gui_log("🛑 Para parar: use o botão PARAR ou mova o mouse para o canto superior esquerdo")
            gui_log("⚠️ IMPORTANTE: RPA será interrompido automaticamente em caso de falha crítica")
            gui_log("")

            # Notificar início em modo contínuo no Telegram
            if _telegram_notifier:
                try:
                    mensagem = (
                        "🤖 <b>RPA CICLO INICIADO</b>\n\n"
                        "🔄 <b>Modo:</b> Contínuo (24/7)\n"
                        "✅ <b>Status:</b> Executando\n"
                        f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
                    )
                    _telegram_notifier.enviar_mensagem(mensagem)
                except:
                    pass

            while _rpa_running:
                # ═══════════════════════════════════════════════════════════════
                # ETAPA 1: Verificar se há itens pendentes no Google Sheets
                # ═══════════════════════════════════════════════════════════════
                gui_log("")
                gui_log("=" * 70)
                gui_log("🔍 VERIFICANDO ITENS PENDENTES NO GOOGLE SHEETS...")
                gui_log("=" * 70)

                tem_itens = verificar_tem_itens_pendentes()

                if tem_itens:
                    # ═══════════════════════════════════════════════════════════════
                    # TEM ITENS: Executar ciclo completo (Oracle + Bancada)
                    # ═══════════════════════════════════════════════════════════════
                    gui_log("✅ Itens pendentes encontrados!")
                    gui_log("🚀 Iniciando ciclo completo (Oracle + Bancada)...")

                    sucesso = executar_ciclo_completo(config)

                    if not sucesso:
                        # FALHA CRÍTICA: Parar imediatamente
                        gui_log("=" * 60)
                        gui_log("❌ FALHA CRÍTICA DETECTADA!")
                        gui_log("=" * 60)
                        gui_log("🛑 RPA foi interrompido automaticamente")
                        gui_log("📋 Verifique os logs acima para identificar o problema")
                        gui_log("⚠️ Pode ser:")
                        gui_log("   - Falha ao processar itens no Oracle")
                        gui_log("   - Falha ao executar RPA Bancada")
                        gui_log("   - Problema de conexão com Google Sheets")
                        gui_log("   - Erro de coordenadas/cliques")
                        gui_log("=" * 60)
                        break  # PARAR IMEDIATAMENTE

                    # Ciclo completo executado com sucesso
                    gui_log("✅ Ciclo concluído com sucesso!")

                    # Pequena pausa de 5 segundos para estabilização
                    if not aguardar_com_pausa(5, "Pausa entre ciclos", evitar_hibernar=True):
                        break

                else:
                    # ═══════════════════════════════════════════════════════════════
                    # NÃO TEM ITENS: Aguardar 15min verificando a cada 1min
                    # ═══════════════════════════════════════════════════════════════
                    gui_log("⚠️ Nenhum item pendente encontrado")
                    gui_log("")
                    gui_log("=" * 70)
                    gui_log("🔄 MODO INTELIGENTE DE ESPERA")
                    gui_log("   • Verifica novos itens a cada 1 minuto")
                    gui_log("   • Se encontrar itens: processa imediatamente")
                    gui_log("   • Após 15 minutos: atualiza bancada")
                    gui_log("   • Anti-hibernação ATIVO durante espera")
                    gui_log("=" * 70)

                    # Esperar até 15 minutos verificando novos itens a cada 1 minuto
                    tem_novos_itens = aguardar_inteligente_entre_ciclos(config, max_minutos=15, intervalo_verificacao=60)

                    if tem_novos_itens:
                        # Novos itens detectados durante espera
                        gui_log("🎯 Novos itens detectados durante espera!")
                        gui_log("🚀 Iniciando ciclo completo (Oracle + Bancada)...")

                        sucesso = executar_ciclo_completo(config)

                        if not sucesso:
                            gui_log("=" * 60)
                            gui_log("❌ FALHA CRÍTICA DETECTADA!")
                            gui_log("=" * 60)
                            break

                    else:
                        # 15 minutos completos sem novos itens
                        gui_log("⏰ 15 minutos completos sem novos itens")
                        gui_log("🔄 Atualizando bancada (executando apenas etapas de navegação + bancada)...")

                        # Executar apenas bancada (sem Oracle)
                        sucesso = executar_apenas_bancada(config)

                        if not sucesso:
                            gui_log("=" * 60)
                            gui_log("❌ FALHA ao atualizar bancada")
                            gui_log("=" * 60)
                            break

                # Verificar se RPA foi parado
                if not _rpa_running:
                    break

            # Fim do loop contínuo (saiu por falha crítica ou parada manual)
            if False:  # Placeholder para manter estrutura
                    # FALHA CRÍTICA: Parar imediatamente e avisar usuário
                    gui_log("=" * 60)
                    gui_log("❌ FALHA CRÍTICA DETECTADA!")
                    gui_log("=" * 60)
                    gui_log("🛑 RPA foi interrompido automaticamente")
                    gui_log("📋 Verifique os logs acima para identificar o problema")
                    gui_log("⚠️ Pode ser:")
                    gui_log("   - Falha ao processar itens no Oracle")
                    gui_log("   - Falha ao executar RPA Bancada")
                    gui_log("   - Problema de conexão com Google Sheets")
                    gui_log("   - Erro de coordenadas/cliques")
                    gui_log("=" * 60)
                    break  # PARAR IMEDIATAMENTE

                if not _rpa_running:
                    break
        else:
            gui_log("🎯 Modo execução única")
            executar_ciclo_completo(config)

    except KeyboardInterrupt:
        gui_log("⏸️ Interrompido pelo usuário (Ctrl+C)")
    except pyautogui.FailSafeException:
        gui_log("🛑 FAILSAFE acionado (mouse no canto superior esquerdo)")
    except Exception as e:
        gui_log(f"❌ Erro fatal: {e}")
        import traceback
        gui_log(traceback.format_exc())
    finally:
        _rpa_running = False
        # Remover hook do teclado
        try:
            keyboard.unhook_all()
            gui_log("⌨️ [ESC] Monitoramento de teclado desativado")
        except:
            pass
        gui_log("=" * 60)
        gui_log("🏁 RPA CICLO - Finalizado")
        gui_log(f"📊 Total de ciclos executados: {_ciclo_atual}")
        gui_log("=" * 60)

# =================== PONTO DE ENTRADA ===================
if __name__ == "__main__":
    # Configurar PyAutoGUI
    pyautogui.PAUSE = 0.5
    pyautogui.FAILSAFE = True

    # Executar RPA em modo contínuo
    main(modo_continuo=True)
