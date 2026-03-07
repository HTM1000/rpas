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
import pyperclip  # Para digitação via clipboard (mais confiável)
import keyboard  # Para monitorar tecla ESC
import re
from io import StringIO

# =================== LOG DE TECLAS DO ROBÔ ===================
# Lista global para registrar todas as teclas pressionadas pelo robô
_teclas_log = []
_teclas_log_lock = threading.Lock()

def registrar_tecla(acao, tecla, contexto=""):
    """Registra uma ação de teclado no log"""
    global _teclas_log
    from datetime import timezone, timedelta
    brasilia_tz = timezone(timedelta(hours=-3))
    timestamp = datetime.now(brasilia_tz).strftime("%H:%M:%S.%f")[:-3]

    entrada = {
        "timestamp": timestamp,
        "acao": acao,  # "press", "keyUp", "keyDown", "hotkey", "write", "clipboard"
        "tecla": tecla,
        "contexto": contexto
    }

    with _teclas_log_lock:
        _teclas_log.append(entrada)
        # Manter apenas últimas 500 entradas
        if len(_teclas_log) > 500:
            _teclas_log = _teclas_log[-500:]

    # Log visual para debug
    if _gui_log_callback:
        _gui_log_callback(f"🔑 [{timestamp}] {acao.upper()}: {tecla} {f'({contexto})' if contexto else ''}")

def obter_log_teclas(ultimas=50):
    """Retorna as últimas N entradas do log de teclas"""
    with _teclas_log_lock:
        return _teclas_log[-ultimas:]

def limpar_log_teclas():
    """Limpa o log de teclas"""
    global _teclas_log
    with _teclas_log_lock:
        _teclas_log = []

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

# =================== CONFIGURAÇÕES DE DIRETÓRIO (DEVE VIR ANTES!) ===================
BASE_DIR = Path(__file__).parent.resolve() if not getattr(sys, 'frozen', False) else Path(sys.executable).parent
base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

# =================== DETECTAR MODO TESTE ===================
def detectar_modo_teste():
    """Detecta se está em modo TESTE verificando se existe o arquivo IS_TEST_MODE.flag"""
    # Verificar em vários locais possíveis
    locais = [
        base_path,  # _MEIPASS (dentro do executável)
        BASE_DIR,   # Diretório base
    ]

    if getattr(sys, 'frozen', False):
        locais.append(os.path.dirname(sys.executable))  # Pasta do .exe
        locais.append(os.path.join(os.path.dirname(sys.executable), "_internal"))  # _internal/

    for local in locais:
        flag_path = os.path.join(local, "IS_TEST_MODE.flag")
        if os.path.exists(flag_path):
            print(f"[TESTE] Flag detectada em: {flag_path}")
            return True

    print("[PROD] Flag de teste NÃO detectada - usando modo PRODUÇÃO")
    return False

MODO_TESTE_ATIVO = detectar_modo_teste()

# Importar módulo Google Sheets (para ciclo)
try:
    if MODO_TESTE_ATIVO:
        from google_sheets_ciclo_TESTE import registrar_ciclo, atualizar_ciclo
        print("[TESTE] Importado: google_sheets_ciclo_TESTE.py")
    else:
        from google_sheets_ciclo import registrar_ciclo, atualizar_ciclo
        print("[PROD] Importado: google_sheets_ciclo.py")
    GOOGLE_SHEETS_DISPONIVEL = True
except ImportError as e:
    print(f"❌ Erro ao importar Google Sheets: {e}")
    # Fallback: tentar importar qualquer um
    try:
        from google_sheets_ciclo import registrar_ciclo, atualizar_ciclo
        GOOGLE_SHEETS_DISPONIVEL = True
        print("[FALLBACK] Usando google_sheets_ciclo.py")
    except:
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
        detectar_erro_oracle,
        ler_campo_via_clipboard
    )
    VALIDADOR_HIBRIDO_DISPONIVEL = True
    print("="*70)
    print("✅ ✅ ✅ VALIDADOR HÍBRIDO IMPORTADO COM SUCESSO ✅ ✅ ✅")
    print("   DETECÇÃO DE MODAIS ESTÁ ATIVA!")
    print("="*70)
except ImportError as e:
    VALIDADOR_HIBRIDO_DISPONIVEL = False
    print("="*70)
    print("❌ ❌ ❌ VALIDADOR HÍBRIDO NÃO DISPONÍVEL ❌ ❌ ❌")
    print(f"   ERRO: {e}")
    print("   DETECÇÃO DE MODAIS NÃO VAI FUNCIONAR!")
    print("="*70)

# =================== CONFIGURAÇÕES GLOBAIS ===================
CONFIG_FILE = BASE_DIR / "config.json"

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
        # Usar horário de Brasília (UTC-3)
        from datetime import timezone, timedelta
        brasilia_tz = timezone(timedelta(hours=-3))
        dados_item = {
            "linha_atual": linha_atual,
            "item": item,
            "quantidade": quantidade,
            "referencia": referencia,
            "timestamp_processamento": datetime.now(brasilia_tz).strftime("%Y-%m-%d %H:%M:%S"),
            "status_sheets": status
        }

        # Adicionar aos dados com lock
        with self.lock:
            self.dados[id_item] = dados_item

        # Salvar sem lock para evitar deadlock
        self._salvar()
        return True

    def atualizar_status(self, id_item, novo_status):
        """Atualiza status de um item no cache (para máquina de estados)"""
        with self.lock:
            if id_item in self.dados:
                # Usar horário de Brasília (UTC-3)
                from datetime import timezone, timedelta
                brasilia_tz = timezone(timedelta(hours=-3))
                self.dados[id_item]["status_sheets"] = novo_status
                self.dados[id_item]["timestamp_ultima_atualizacao"] = datetime.now(brasilia_tz).strftime("%Y-%m-%d %H:%M:%S")

        # Salvar sem lock
        self._salvar()

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

def notificar_parada_telegram(motivo, detalhes=""):
    """
    Notifica parada do RPA no Telegram

    Args:
        motivo: Motivo da parada (ESC, FAILSAFE, ERRO, BOTAO_PARAR)
        detalhes: Detalhes adicionais (opcional)
    """
    global _telegram_notifier
    if _telegram_notifier and _telegram_notifier.enabled:
        try:
            icones = {
                "ESC": "⏹️",
                "FAILSAFE": "🛑",
                "ERRO": "❌",
                "BOTAO_PARAR": "⏸️",
                "ERRO_PRODUTO": "⚠️",
                "TIMEOUT": "⏱️",
                "QTD_NEGATIVA": "🔢",
                "TELA_INCORRETA": "🖥️"
            }

            icone = icones.get(motivo, "🛑")

            mensagem = f"""
{icone} <b>RPA PARADO</b>

🔴 <b>Motivo:</b> {motivo.replace('_', ' ')}
"""
            if detalhes:
                mensagem += f"📝 <b>Detalhes:</b> {detalhes}\n"

            mensagem += f"\n⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"

            _telegram_notifier.enviar_mensagem(mensagem.strip())
        except Exception as e:
            gui_log(f"[TELEGRAM] Erro ao notificar parada: {e}")

def stop_rpa():
    """Para o RPA externamente (para ser chamado pela GUI)"""
    global _rpa_running
    _rpa_running = False
    gui_log("🛑 Solicitação de parada recebida")

    # Notificar Telegram
    notificar_parada_telegram("BOTAO_PARAR", "Usuário clicou no botão PARAR")

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
    """Carrega as configurações do arquivo config.json ou config_TESTE.json"""
    # Determinar qual arquivo de config usar
    config_filename = "config_TESTE.json" if MODO_TESTE_ATIVO else "config.json"

    gui_log(f"🔍 Modo: {'TESTE' if MODO_TESTE_ATIVO else 'PRODUÇÃO'}")
    gui_log(f"🔍 Procurando arquivo: {config_filename}")

    # Tentar múltiplos caminhos
    caminhos_possiveis = [
        os.path.join(base_path, config_filename),  # _MEIPASS (interno do PyInstaller)
        os.path.join(BASE_DIR, config_filename),  # BASE_DIR
        os.path.join(os.path.dirname(sys.executable), config_filename) if getattr(sys, 'frozen', False) else None,  # Pasta do .exe
        os.path.join(os.path.dirname(sys.executable), "_internal", config_filename) if getattr(sys, 'frozen', False) else None,  # _internal
    ]

    # Remover Nones
    caminhos_possiveis = [c for c in caminhos_possiveis if c]

    gui_log(f"🔍 Caminhos que vou verificar:")
    for i, caminho in enumerate(caminhos_possiveis, 1):
        existe = "✅" if os.path.exists(caminho) else "❌"
        gui_log(f"   {i}. {existe} {caminho}")

    for config_path in caminhos_possiveis:
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                gui_log(f"✅ Configurações carregadas de: {os.path.basename(config_path)}")

                # Verificar se tem ID da planilha Oracle
                if "planilhas" in config and "oracle_itens" in config["planilhas"]:
                    planilha_id = config["planilhas"]["oracle_itens"]
                    # Mostrar apenas primeiros caracteres (não mostrar ID completo)
                    gui_log(f"📊 Planilha Oracle Itens: ...{planilha_id[-8:]}")
                else:
                    gui_log(f"⚠️ Planilha Oracle não configurada no {config_filename}")

                return config
            except json.JSONDecodeError as e:
                gui_log(f"❌ Erro ao decodificar JSON em {config_path}: {e}")
                continue

    # Se chegou aqui, não encontrou em nenhum lugar
    gui_log(f"❌ Arquivo de configuração não encontrado!")
    gui_log(f"   Arquivo procurado: {config_filename}")
    raise FileNotFoundError(f"{config_filename} não encontrado")

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
def safe_write(texto, contexto=""):
    """
    Digita texto usando CLIPBOARD (Ctrl+V) - método mais confiável.
    Evita completamente problemas como 'R10' virar 'R!0'.

    Por que clipboard é melhor:
    - Não depende do estado do teclado
    - Não é afetado por teclas modificadoras "presas"
    - Funciona com qualquer caractere (acentos, símbolos)
    - Mais rápido que digitar caractere por caractere
    """
    # Registrar no log de teclas
    registrar_tecla("clipboard", f"'{texto}'", contexto)

    # Salvar clipboard atual para restaurar depois
    try:
        clipboard_anterior = pyperclip.paste()
    except:
        clipboard_anterior = ""

    # 1. Liberar TODAS as teclas modificadoras
    for tecla in ['shift', 'ctrl', 'alt', 'win']:
        pyautogui.keyUp(tecla)
        registrar_tecla("keyUp", tecla, "liberando modificador")
    time.sleep(0.05)

    # 2. Copiar texto para clipboard
    pyperclip.copy(texto)
    time.sleep(0.05)

    # 3. Colar com Ctrl+V
    registrar_tecla("hotkey", "ctrl+v", f"colando '{texto}'")
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.1)

    # 4. Restaurar clipboard anterior (opcional, para não perder dados do usuário)
    try:
        time.sleep(0.05)
        pyperclip.copy(clipboard_anterior)
    except:
        pass

def safe_press(tecla, contexto=""):
    """Pressiona uma tecla e registra no log"""
    registrar_tecla("press", tecla, contexto)
    pyautogui.press(tecla)

def safe_hotkey(*teclas, contexto=""):
    """Executa um hotkey e registra no log"""
    registrar_tecla("hotkey", "+".join(teclas), contexto)
    pyautogui.hotkey(*teclas)

def ler_campo_atual():
    """
    Lê o valor do campo atual via clipboard (Ctrl+A, Ctrl+C).
    Retorna o texto lido ou string vazia se falhar.
    """
    try:
        # Salvar clipboard
        clipboard_backup = pyperclip.paste()
    except:
        clipboard_backup = ""

    try:
        # Limpar clipboard
        pyperclip.copy("")
        time.sleep(0.05)

        # Selecionar tudo no campo atual
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)

        # Copiar
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.1)

        # Ler valor
        valor = pyperclip.paste().strip()

        # Restaurar clipboard
        try:
            pyperclip.copy(clipboard_backup)
        except:
            pass

        return valor
    except Exception as e:
        gui_log(f"⚠️ Erro ao ler campo: {e}")
        return ""

def digitar_e_verificar(coord_x, coord_y, valor_esperado, nome_campo, max_tentativas=3):
    """
    Digita um valor no campo e VERIFICA se foi digitado corretamente.
    Se estiver errado, LIMPA e tenta novamente.

    Args:
        coord_x, coord_y: Coordenadas do campo
        valor_esperado: O valor que deve ser digitado
        nome_campo: Nome do campo (para logs)
        max_tentativas: Número máximo de tentativas

    Returns:
        tuple: (sucesso: bool, valor_final: str)
    """
    valor_esperado_str = str(valor_esperado).strip()

    for tentativa in range(1, max_tentativas + 1):
        gui_log(f"[{nome_campo}] Tentativa {tentativa}/{max_tentativas}")

        # 1. Clicar no campo
        pyautogui.click(coord_x, coord_y)
        time.sleep(0.2)

        # 2. Limpar campo (Ctrl+A + Delete)
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)
        safe_press('delete', contexto=f"limpar {nome_campo}")
        time.sleep(0.1)

        # 3. Digitar valor via clipboard
        safe_write(valor_esperado_str, contexto=f"campo {nome_campo}")
        time.sleep(0.2)

        # 4. Ler o que foi digitado
        valor_lido = ler_campo_atual()

        # 5. Normalizar e comparar
        valor_lido_norm = valor_lido.upper().strip().replace(" ", "")
        valor_esperado_norm = valor_esperado_str.upper().strip().replace(" ", "")

        # Comparação especial para quantidade (numérica)
        if "QUANT" in nome_campo.upper():
            try:
                val_lido_num = valor_lido_norm.replace(",", "").replace(".", "").replace("-", "").lstrip("0") or "0"
                val_esp_num = valor_esperado_norm.replace(",", "").replace(".", "").replace("-", "").lstrip("0") or "0"
                valores_iguais = val_lido_num == val_esp_num
            except:
                valores_iguais = valor_lido_norm == valor_esperado_norm
        else:
            valores_iguais = valor_lido_norm == valor_esperado_norm

        if valores_iguais:
            gui_log(f"[{nome_campo}] ✅ Valor correto! '{valor_lido}'")
            return True, valor_lido
        else:
            gui_log(f"[{nome_campo}] ⚠️ Valor diferente!")
            gui_log(f"   Esperado: '{valor_esperado_str}'")
            gui_log(f"   Lido:     '{valor_lido}'")

            if tentativa < max_tentativas:
                gui_log(f"[{nome_campo}] 🔄 Tentando novamente...")
                time.sleep(0.3)

    # Após todas as tentativas, falhou
    gui_log(f"[{nome_campo}] ❌ Falhou após {max_tentativas} tentativas!")
    return False, valor_lido

def digitar_campo(x, y, valor, nome):
    """
    Digita um valor no campo SEM verificação imediata.
    Fluxo igual ao commit anterior: click → delete → pyautogui.write()
    """
    valor_str = str(valor).strip()
    gui_log(f"[{nome}] Digitando: '{valor_str}'")

    pyautogui.click(x, y)
    time.sleep(0.3)
    pyautogui.press('delete')
    time.sleep(0.1)
    safe_write(valor_str, contexto=nome)
    time.sleep(0.1)

def _comparar_campo(lido, esperado, nome):
    """
    Compara valor lido com esperado: strip + lower.
    Para campos de quantidade usa comparação numérica como fallback.
    """
    lido_norm = lido.strip().lower()
    esp_norm = str(esperado).strip().lower()

    if "quant" in nome.lower():
        try:
            lido_num = lido_norm.replace(",", "").replace(".", "").lstrip("0") or "0"
            esp_num = esp_norm.replace(",", "").replace(".", "").replace("-", "").lstrip("0") or "0"
            if lido_num.isdigit() and esp_num.isdigit():
                return lido_num == esp_num
        except Exception:
            pass

    return lido_norm == esp_norm

def _ler_campo_ctrl_c(x, y):
    """
    Lê o valor do campo com click simples + Ctrl+C (sem Ctrl+A).
    Retorna o texto lido ou string vazia se falhar.
    """
    try:
        backup = pyperclip.paste()
    except:
        backup = ""
    try:
        pyperclip.copy("")
        time.sleep(0.05)
        pyautogui.click(x, y)
        time.sleep(0.15)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.15)
        valor = pyperclip.paste().strip()
        try:
            pyperclip.copy(backup)
        except:
            pass
        return valor
    except Exception as e:
        gui_log(f"⚠️ Erro ao ler campo via Ctrl+C: {e}")
        return ""

def validar_e_corrigir_campo(coord_val, expected, nome):
    """
    Valida um campo após preenchimento:

    1. click → Ctrl+C → lê valor
    2. Compara com strip().lower()
    3. Se correto: retorna (True, valor_lido)
    4. Se errado: click → delete → write() (método antigo, sem Ctrl+A)
    5. click → Ctrl+C → lê valor de novo
    6. Se correto: retorna (True, valor_lido)
    7. Se ainda errado: retorna (False, valor_lido) → item marcado como erro

    coord_val: (x, y, largura, altura) — bounding box do campo
    Returns: (ok: bool, valor_lido: str)
    """
    x, y, w, h = coord_val
    centro_x = x + w // 2
    centro_y = y + h // 2
    expected_str = str(expected).strip()

    # ── 1ª leitura: click → Ctrl+C ───────────────────────────────────────────
    valor_lido = _ler_campo_ctrl_c(centro_x, centro_y)
    if _comparar_campo(valor_lido, expected_str, nome):
        gui_log(f"[{nome}] ✅ OK: '{valor_lido}'")
        return True, valor_lido

    gui_log(f"[{nome}] ⚠️ Diferente! Esperado: '{expected_str}' | Lido: '{valor_lido}'")
    gui_log(f"[{nome}] 🔄 Corrigindo: click → delete → write...")

    # ── Correção: 1 clique → pausa → duplo clique → delete → write ───────────
    # 1 clique simples, espera, depois duplo clique — Oracle seleciona tudo
    pyautogui.click(centro_x, centro_y)
    time.sleep(0.3)
    pyautogui.doubleClick(centro_x, centro_y)
    time.sleep(0.2)
    pyautogui.press('delete')
    time.sleep(0.2)
    safe_write(expected_str, contexto=nome)
    time.sleep(0.3)

    # ── 2ª leitura: click → Ctrl+C ───────────────────────────────────────────
    valor_lido2 = _ler_campo_ctrl_c(centro_x, centro_y)
    if _comparar_campo(valor_lido2, expected_str, nome):
        gui_log(f"[{nome}] ✅ Corrigido! '{valor_lido2}'")
        return True, valor_lido2

    gui_log(f"[{nome}] ❌ Correção falhou! Esperado: '{expected_str}' | Lido: '{valor_lido2}'")
    return False, valor_lido2

def verificar_modal_erro_campo(tipo_campo, coord_field, valor):
    """
    Verifica se apareceu modal de erro após preencher campo.
    Se sim: fecha com Alt+C e tenta reescrever (delete → safe_write → TAB).

    Args:
        tipo_campo:  "item", "endereco" ou "subinv"
        coord_field: tuple (x, y) do campo
        valor:       valor que deveria estar no campo

    Returns:
        "ok"        - sem modal, campo OK
        "corrigido" - modal fechado e campo reescrito com sucesso
        "erro"      - não foi possível corrigir
    """
    if tipo_campo == "item":
        nome_img = "erro_item_inexistente.png"
    elif tipo_campo == "subinv":
        nome_img = "erro_subinv_inexistente.png"
    else:
        nome_img = "erro_endereco_inexistente.png"

    caminho = os.path.join(base_path, "informacoes", nome_img)
    if not os.path.isfile(caminho):
        gui_log(f"⚠️ [{tipo_campo.upper()}] Imagem {nome_img} não encontrada — sem verificação de modal")
        return "ok"

    modal = detectar_imagem_opencv(caminho, confidence=0.8, timeout=1)
    if not modal:
        return "ok"

    # Modal encontrado — fechar com Alt+C (cursor volta ao campo automaticamente)
    gui_log(f"❌ Modal de erro detectado ({nome_img}) — fechando com Alt+C")
    pyautogui.hotkey('alt', 'c')
    time.sleep(0.3)
    gui_log("✅ Modal fechado")

    # Retry: delete → safe_write → TAB (cursor já está no campo após Alt+C)
    valor_str = str(valor).strip()
    gui_log(f"🔄 Retry: delete → safe_write '{valor_str}'")
    pyautogui.press('delete')
    time.sleep(0.1)
    safe_write(valor_str, contexto=f"retry {tipo_campo}")
    pyautogui.press("tab")
    time.sleep(0.5)

    # Verificar modal de novo
    modal2 = detectar_imagem_opencv(caminho, confidence=0.8, timeout=1)
    if not modal2:
        gui_log(f"✅ Campo corrigido com sucesso!")
        return "corrigido"

    # Ainda com modal — fechar com Alt+C e sinalizar erro
    gui_log(f"❌ Não foi possível corrigir o campo após retry")
    pyautogui.hotkey('alt', 'c')
    time.sleep(0.2)
    return "erro"

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
    """Digita um texto usando clipboard e opcionalmente pressiona teclas adicionais"""
    gui_log(f"⌨️ Digitando: {texto}")

    if MODO_TESTE:
        gui_log(f"[MODO TESTE] Simulando digitação de '{texto}'")
        if pressionar_teclas:
            gui_log(f"[MODO TESTE] Simulando teclas: {', '.join(pressionar_teclas)}")
        time.sleep(0.2)
        return

    # Usar clipboard para digitar (mais confiável)
    safe_write(texto, contexto="digitar_texto")
    time.sleep(0.3)

    if pressionar_teclas:
        for tecla in pressionar_teclas:
            gui_log(f"⌨️ Pressionando: {tecla.upper()}")
            safe_press(tecla, contexto=f"após digitar '{texto}'")
            time.sleep(0.3)

# =================== SISTEMA ANTI-HIBERNAÇÃO (Windows API) ===================
def ativar_anti_hibernacao():
    """
    Ativa o modo anti-hibernação usando Windows API.
    Previne que o sistema entre em modo de suspensão ou que a tela desligue.

    Retorna True se ativado com sucesso, False caso contrário.
    """
    if sys.platform != 'win32':
        gui_log("⚠️ [Anti-Hibernação] Sistema não é Windows - API não disponível")
        return False

    try:
        import ctypes

        # Constantes do Windows
        ES_CONTINUOUS = 0x80000000
        ES_SYSTEM_REQUIRED = 0x00000001
        ES_DISPLAY_REQUIRED = 0x00000002

        # Ativar anti-hibernação permanente
        # ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
        # - ES_CONTINUOUS: Mantém configuração até ser desativada
        # - ES_SYSTEM_REQUIRED: Previne que o sistema entre em sleep
        # - ES_DISPLAY_REQUIRED: Previne que a tela desligue
        resultado = ctypes.windll.kernel32.SetThreadExecutionState(
            ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
        )

        if resultado:
            gui_log("✅ [Anti-Hibernação] ATIVADO via Windows API")
            gui_log("   • Sistema: NUNCA entrará em suspensão")
            gui_log("   • Tela: NUNCA desligará automaticamente")
            return True
        else:
            gui_log("⚠️ [Anti-Hibernação] Falha ao ativar Windows API")
            return False

    except Exception as e:
        gui_log(f"⚠️ [Anti-Hibernação] Erro ao ativar: {e}")
        return False

def desativar_anti_hibernacao():
    """
    Desativa o modo anti-hibernação e restaura configurações normais do sistema.
    """
    if sys.platform != 'win32':
        return

    try:
        import ctypes
        ES_CONTINUOUS = 0x80000000

        # Restaurar comportamento normal do sistema
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
        gui_log("✅ [Anti-Hibernação] DESATIVADO - sistema restaurado ao normal")
    except Exception as e:
        gui_log(f"⚠️ [Anti-Hibernação] Erro ao desativar: {e}")

def iniciar_movimento_mouse_continuo():
    """
    Inicia uma thread que pressiona Shift a cada 3 segundos
    para evitar hibernação durante operações longas (processamento, upload)

    Returns:
        threading.Event: Evento para parar a thread quando necessário
    """
    import threading
    import time as time_module

    stop_event = threading.Event()

    def pressionar_shift_loop():
        global _rpa_running
        contador = 0
        inicio_thread = time_module.time()

        gui_log("⌨️ [Thread Anti-Hibernação] Iniciada - Shift a cada 3s")

        while not stop_event.is_set() and _rpa_running:
            try:
                if not MODO_TESTE:
                    # Pressionar Shift a cada 3 segundos
                    pyautogui.press('shift')

                contador += 1

                # Log a cada 20 pressionamentos (60 segundos)
                if contador % 20 == 0:
                    tempo_decorrido = int(time_module.time() - inicio_thread)
                    gui_log(f"⌨️ [Thread Anti-Hibernação] {contador} pressionamentos em {tempo_decorrido}s")
            except Exception as e:
                pass  # Ignora erros silenciosamente na thread

            # Aguardar 3 segundos antes do próximo pressionamento
            stop_event.wait(3)

        # Log quando thread parar
        if not _rpa_running:
            gui_log("🛑 [Thread Anti-Hibernação] Parada por _rpa_running=False")

    # Iniciar thread em background
    thread = threading.Thread(target=pressionar_shift_loop, daemon=True)
    thread.start()

    return stop_event

def aguardar_com_pausa(segundos, mensagem="Aguardando", evitar_hibernar=False):
    """
    Aguarda um tempo com possibilidade de interrupção

    Args:
        segundos: Tempo em segundos para aguardar
        mensagem: Mensagem a exibir
        evitar_hibernar: Parâmetro mantido por compatibilidade (anti-hibernação é global agora)
    """
    gui_log(f"⏳ {mensagem} ({segundos}s)...")

    inicio = time.time()

    while time.time() - inicio < segundos:
        if not _rpa_running:
            return False

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

def detectar_imagem_opencv(caminho_imagem, confidence=0.8, timeout=5, salvar_debug=False):
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
            safe_hotkey("ctrl", "s", contexto="salvar após Qtd Negativa")
            gui_log("[QTD NEG] << CTRL+S pressionado")
            time.sleep(1)
            gui_log("✅ [QTD NEG] Modal fechado e registro salvo!")
        else:
            gui_log("✅ [QTD NEG] Modal fechado! Continuando preenchimento...")

        return True
    else:
        return False

def contar_pixels_cor(cor="amarelo"):
    """
    Conta quantos pixels de uma cor específica existem na tela

    Args:
        cor: "amarelo" ou "vermelho"

    Returns:
        int: Quantidade de pixels da cor
    """
    import numpy as np
    from PIL import ImageGrab

    # Capturar tela
    screenshot = ImageGrab.grab()
    screenshot_np = np.array(screenshot)

    # Converter para HSV
    screenshot_hsv = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2HSV)

    if cor == "amarelo":
        # Amarelo em HSV
        lower = np.array([20, 150, 150])
        upper = np.array([30, 255, 255])
        mask = cv2.inRange(screenshot_hsv, lower, upper)
        pixels = cv2.countNonZero(mask)
        return pixels

    elif cor == "vermelho":
        # Vermelho em HSV (dois ranges porque vermelho "envolve")
        lower1 = np.array([0, 150, 150])
        upper1 = np.array([10, 255, 255])
        lower2 = np.array([170, 150, 150])
        upper2 = np.array([180, 255, 255])

        mask1 = cv2.inRange(screenshot_hsv, lower1, upper1)
        mask2 = cv2.inRange(screenshot_hsv, lower2, upper2)
        mask = mask1 + mask2
        pixels = cv2.countNonZero(mask)
        return pixels

    return 0


def detectar_modal_diferencial(cor_esperada, pixels_antes, threshold_aumento=500):
    """
    Detecta modal comparando pixels ANTES vs DEPOIS

    Args:
        cor_esperada: "amarelo" ou "vermelho"
        pixels_antes: Quantidade de pixels ANTES da ação
        threshold_aumento: Quantos pixels a mais indica que modal apareceu

    Returns:
        bool: True se modal apareceu, False caso contrário
    """
    pixels_depois = contar_pixels_cor(cor_esperada)
    aumento = pixels_depois - pixels_antes

    gui_log(f"[MODAL DIFF] Pixels {cor_esperada} ANTES: {pixels_antes}")
    gui_log(f"[MODAL DIFF] Pixels {cor_esperada} DEPOIS: {pixels_depois}")
    gui_log(f"[MODAL DIFF] Aumento: {aumento} pixels")

    if aumento >= threshold_aumento:
        gui_log(f"⚠️ [MODAL DIFF] ✅ Modal detectado! (aumento de {aumento} pixels)")

        # Salvar screenshot debug
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot = ImageGrab.grab()
            screenshot.save(f"debug_modal_{cor_esperada}_{timestamp}.png")
            gui_log(f"[MODAL DIFF] 💾 Debug salvo: debug_modal_{cor_esperada}_{timestamp}.png")
        except:
            pass

        return True
    else:
        gui_log(f"[MODAL DIFF] ✅ Nenhum modal detectado (aumento insuficiente)")
        return False


def detectar_modal_por_icone(timeout=3):
    """
    Detecta modais do Oracle procurando APENAS O ÍCONE (não cores na tela inteira)

    Retorna:
        "ERRO_CENTRO_CUSTO" - se detectou ícone vermelho
        "QUANTIDADE_NEGATIVA" - se detectou ícone amarelo
        None - se não detectou nenhum modal

    MUITO MAIS CONFIÁVEL que detecção por cor!
    Procura apenas o ícone específico, não elementos vermelhos/amarelos da UI
    """
    import os

    gui_log("[MODAL ÍCONE] 🔍 Detectando modal pelo ÍCONE...")

    # Caminhos dos ícones de referência
    base_path = os.path.dirname(os.path.abspath(__file__))

    # Tentar diferentes localizações dos ícones
    icone_qtd_neg_paths = [
        os.path.join(base_path, "informacoes", "icone_qtd_negativa.png"),
        os.path.join(base_path, "icone_qtd_negativa.png"),
    ]

    icone_erro_cc_paths = [
        os.path.join(base_path, "informacoes", "icone_erro_centro_custo.png"),
        os.path.join(base_path, "icone_erro_centro_custo.png"),
    ]

    # Encontrar qual existe
    icone_qtd_neg = None
    icone_erro_cc = None

    for path in icone_qtd_neg_paths:
        if os.path.isfile(path):
            icone_qtd_neg = path
            break

    for path in icone_erro_cc_paths:
        if os.path.isfile(path):
            icone_erro_cc = path
            break

    if not icone_qtd_neg and not icone_erro_cc:
        gui_log("⚠️ [MODAL ÍCONE] Nenhum ícone de referência encontrado!")
        gui_log("   Execute: python capturar_icones_modais.py")
        gui_log("   Voltando para detecção por cor...")
        return detectar_modal_por_cor_fallback(timeout)

    inicio = time.time()

    while time.time() - inicio < timeout:
        try:
            # Tentar detectar ícone de quantidade negativa (🟡)
            if icone_qtd_neg:
                try:
                    location = pyautogui.locateOnScreen(icone_qtd_neg, confidence=0.7)
                    if location:
                        gui_log(f"⚠️ [MODAL ÍCONE] ✅ ÍCONE AMARELO DETECTADO em {location}!")
                        gui_log("⚠️ [MODAL ÍCONE] Modal: Quantidade Negativa")

                        # Salvar debug
                        try:
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            screenshot = ImageGrab.grab()
                            screenshot.save(f"debug_yellow_icon_{timestamp}.png")
                            gui_log(f"[MODAL ÍCONE] 💾 Debug salvo: debug_yellow_icon_{timestamp}.png")
                        except:
                            pass

                        return "QUANTIDADE_NEGATIVA"
                except:
                    pass  # Não encontrou

            # Tentar detectar ícone de erro centro custo (🔴)
            if icone_erro_cc:
                try:
                    location = pyautogui.locateOnScreen(icone_erro_cc, confidence=0.7)
                    if location:
                        gui_log(f"⚠️ [MODAL ÍCONE] ✅ ÍCONE VERMELHO DETECTADO em {location}!")
                        gui_log("⚠️ [MODAL ÍCONE] Modal: Erro Centro de Custo")

                        # Salvar debug
                        try:
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            screenshot = ImageGrab.grab()
                            screenshot.save(f"debug_red_icon_{timestamp}.png")
                            gui_log(f"[MODAL ÍCONE] 💾 Debug salvo: debug_red_icon_{timestamp}.png")
                        except:
                            pass

                        return "ERRO_CENTRO_CUSTO"
                except:
                    pass  # Não encontrou

            time.sleep(0.3)

        except Exception as e:
            gui_log(f"⚠️ [MODAL ÍCONE] Erro: {e}")
            time.sleep(0.3)

    gui_log(f"[MODAL ÍCONE] ✅ Nenhum modal detectado em {timeout}s")
    return None


def detectar_modal_por_cor_fallback(timeout=3):
    """
    Detecta modais do Oracle pela COR DO ÍCONE

    Retorna:
        "ERRO_CENTRO_CUSTO" - se detectou ícone vermelho (🔴)
        "QUANTIDADE_NEGATIVA" - se detectou ícone amarelo (⚠️)
        None - se não detectou nenhum modal

    MUITO MAIS CONFIÁVEL que detecção por imagem!
    """
    import numpy as np
    from PIL import ImageGrab

    gui_log("[MODAL COR] 🎨 Detectando modal pela cor do ícone...")

    inicio = time.time()

    while time.time() - inicio < timeout:
        # Capturar tela
        screenshot = ImageGrab.grab()
        screenshot_np = np.array(screenshot)

        # ═══════════════════════════════════════════════════════════════
        # IMPORTANTE: Analisar apenas CENTRO da tela (onde modais aparecem)
        # Evita detectar elementos vermelhos/amarelos da UI do Oracle
        # ═══════════════════════════════════════════════════════════════
        height, width = screenshot_np.shape[:2]

        # Região central: 40% do centro da tela (horizontal e vertical)
        # Exemplo: tela 1920x1080 → região 768x432 no centro
        margin_x = int(width * 0.3)   # 30% de margem cada lado
        margin_y = int(height * 0.3)  # 30% de margem cima/baixo

        # Crop para região central
        screenshot_central = screenshot_np[margin_y:height-margin_y, margin_x:width-margin_x]

        gui_log(f"[MODAL COR] Analisando região central: {screenshot_central.shape[1]}x{screenshot_central.shape[0]} pixels")

        # Converter RGB para HSV (melhor para detectar cores)
        screenshot_hsv = cv2.cvtColor(screenshot_central, cv2.COLOR_RGB2HSV)

        # ═══════════════════════════════════════════════════════════════
        # DETECTAR ÍCONE VERMELHO (Erro Centro Custo)
        # Vermelho em HSV: H=0-10 ou H=170-180, S=100-255, V=100-255
        # ═══════════════════════════════════════════════════════════════
        lower_red1 = np.array([0, 150, 150])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 150, 150])
        upper_red2 = np.array([180, 255, 255])

        mask_red1 = cv2.inRange(screenshot_hsv, lower_red1, upper_red1)
        mask_red2 = cv2.inRange(screenshot_hsv, lower_red2, upper_red2)
        mask_red = mask_red1 + mask_red2

        # Contar pixels vermelhos
        red_pixels = cv2.countNonZero(mask_red)

        # ═══════════════════════════════════════════════════════════════
        # DETECTAR ÍCONE AMARELO (Quantidade Negativa)
        # Amarelo em HSV: H=20-30, S=150-255, V=150-255
        # ═══════════════════════════════════════════════════════════════
        lower_yellow = np.array([20, 150, 150])
        upper_yellow = np.array([30, 255, 255])

        mask_yellow = cv2.inRange(screenshot_hsv, lower_yellow, upper_yellow)

        # Contar pixels amarelos
        yellow_pixels = cv2.countNonZero(mask_yellow)

        gui_log(f"[MODAL COR] 🔴 Pixels vermelhos: {red_pixels}")
        gui_log(f"[MODAL COR] 🟡 Pixels amarelos: {yellow_pixels}")

        # ═══════════════════════════════════════════════════════════════
        # LÓGICA CORRIGIDA v2: Detectar qual cor DOMINA
        # - Threshold mínimo: 500 pixels (ignora pequenos elementos da UI)
        # - Se ambos passarem, precisa ter pelo menos 2x mais pixels para vencer
        #   (evita modais com botões coloridos serem confundidos)
        # ═══════════════════════════════════════════════════════════════

        threshold_minimo = 500  # Aumentado para 500 pixels

        # Calcular diferença relativa
        if red_pixels > 0 and yellow_pixels > 0:
            ratio_red_yellow = red_pixels / yellow_pixels
            ratio_yellow_red = yellow_pixels / red_pixels
        else:
            ratio_red_yellow = 0
            ratio_yellow_red = 0

        # Se ambos passaram do threshold, precisa ter 2x mais para vencer
        if red_pixels > threshold_minimo and yellow_pixels > threshold_minimo:
            # Precisa ter pelo menos 2x mais pixels para considerar como dominante
            if red_pixels > yellow_pixels * 2:
                gui_log(f"⚠️ [MODAL COR] ✅ VERMELHO DOMINA ({red_pixels} vs {yellow_pixels} pixels, ratio {ratio_red_yellow:.1f}x)")
                gui_log("⚠️ [MODAL COR] ✅ ÍCONE VERMELHO DETECTADO - Erro Centro Custo!")
                try:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    # Salvar screenshot COMPLETO (não apenas região central)
                    screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
                    cv2.imwrite(f"debug_red_icon_{timestamp}.png", screenshot_bgr)
                    # Salvar também a região analisada
                    screenshot_central_bgr = cv2.cvtColor(screenshot_central, cv2.COLOR_RGB2BGR)
                    cv2.imwrite(f"debug_red_region_{timestamp}.png", screenshot_central_bgr)
                    gui_log(f"[MODAL COR] 💾 Debug salvo: debug_red_icon_{timestamp}.png (tela completa)")
                    gui_log(f"[MODAL COR] 💾 Debug salvo: debug_red_region_{timestamp}.png (região analisada)")
                except:
                    pass
                return "ERRO_CENTRO_CUSTO"
            elif yellow_pixels > red_pixels * 2:
                gui_log(f"⚠️ [MODAL COR] ✅ AMARELO DOMINA ({yellow_pixels} vs {red_pixels} pixels, ratio {ratio_yellow_red:.1f}x)")
                gui_log("⚠️ [MODAL COR] ✅ ÍCONE AMARELO DETECTADO - Quantidade Negativa!")
                try:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
                    cv2.imwrite(f"debug_yellow_icon_{timestamp}.png", screenshot_bgr)
                    screenshot_central_bgr = cv2.cvtColor(screenshot_central, cv2.COLOR_RGB2BGR)
                    cv2.imwrite(f"debug_yellow_region_{timestamp}.png", screenshot_central_bgr)
                    gui_log(f"[MODAL COR] 💾 Debug salvo: debug_yellow_icon_{timestamp}.png (tela completa)")
                    gui_log(f"[MODAL COR] 💾 Debug salvo: debug_yellow_region_{timestamp}.png (região analisada)")
                except:
                    pass
                return "QUANTIDADE_NEGATIVA"
            else:
                # Ambos passaram threshold mas nenhum domina (sem 2x)
                # Isso indica que pode ter elementos coloridos no modal mas não é o ícone principal
                gui_log(f"⚠️ [MODAL COR] Ambos detectados mas nenhum domina (vermelho={red_pixels}, amarelo={yellow_pixels})")
                gui_log(f"[MODAL COR] Não há dominância clara - ignorando")
                # Continue procurando

        # Se só vermelho passou do threshold (amarelo não passou)
        elif red_pixels > threshold_minimo and yellow_pixels < threshold_minimo:
            gui_log(f"⚠️ [MODAL COR] ✅ APENAS VERMELHO ({red_pixels} pixels)")
            gui_log("⚠️ [MODAL COR] ✅ ÍCONE VERMELHO DETECTADO - Erro Centro Custo!")
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
                cv2.imwrite(f"debug_red_icon_{timestamp}.png", screenshot_bgr)
                screenshot_central_bgr = cv2.cvtColor(screenshot_central, cv2.COLOR_RGB2BGR)
                cv2.imwrite(f"debug_red_region_{timestamp}.png", screenshot_central_bgr)
                gui_log(f"[MODAL COR] 💾 Debug salvo: debug_red_icon_{timestamp}.png (tela completa)")
                gui_log(f"[MODAL COR] 💾 Debug salvo: debug_red_region_{timestamp}.png (região analisada)")
            except:
                pass
            return "ERRO_CENTRO_CUSTO"

        # Se só amarelo passou do threshold (vermelho não passou)
        elif yellow_pixels > threshold_minimo and red_pixels < threshold_minimo:
            gui_log(f"⚠️ [MODAL COR] ✅ APENAS AMARELO ({yellow_pixels} pixels)")
            gui_log("⚠️ [MODAL COR] ✅ ÍCONE AMARELO DETECTADO - Quantidade Negativa!")
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
                cv2.imwrite(f"debug_yellow_icon_{timestamp}.png", screenshot_bgr)
                screenshot_central_bgr = cv2.cvtColor(screenshot_central, cv2.COLOR_RGB2BGR)
                cv2.imwrite(f"debug_yellow_region_{timestamp}.png", screenshot_central_bgr)
                gui_log(f"[MODAL COR] 💾 Debug salvo: debug_yellow_icon_{timestamp}.png (tela completa)")
                gui_log(f"[MODAL COR] 💾 Debug salvo: debug_yellow_region_{timestamp}.png (região analisada)")
            except:
                pass
            return "QUANTIDADE_NEGATIVA"

        time.sleep(0.3)

    gui_log(f"[MODAL COR] ✅ Nenhum modal detectado em {timeout}s")
    return None

def verificar_e_fechar_modal_erro_centro_custo(timeout=5):
    """
    Verifica se o modal de erro de centro de custo apareceu e fecha com ENTER

    Args:
        timeout: Tempo máximo para procurar o modal (padrão: 5 segundos)

    Returns:
        bool: True se modal foi detectado e fechado, False caso contrário

    IMPORTANTE: Erro de centro de custo impede o salvamento no Oracle.
    Modal contém: "A transação do item com grupo de custo XXXX resulta em grupo de custo futuro"
    Onde XXXX varia (0010, 6010, etc), por isso usamos confidence 0.4 (40%).
    Score esperado: ~43% (devido ao número variável).
    """
    global _rpa_running

    caminho = os.path.join(base_path, "informacoes", "erro_centro_custo.png")

    if not os.path.isfile(caminho):
        gui_log("[ERRO CC] ⚠️ Imagem erro_centro_custo.png não encontrada")
        gui_log(f"[ERRO CC]    Caminho esperado: {caminho}")
        return False

    # Tentar detectar com OpenCV
    # Confidence 0.35 (35%) para ser EXTRA flexível (número do grupo de custo muda: 0010, 6010, etc)
    # Teste mostrou score de 43.53% - usando 0.35 para dar margem
    gui_log("[ERRO CC] 🔍 Verificando se modal de erro centro de custo apareceu...")
    gui_log(f"[ERRO CC]    📁 Imagem: {os.path.basename(caminho)}")
    gui_log(f"[ERRO CC]    🎯 Confidence: 0.35 (35% - EXTRA FLEXÍVEL)")
    gui_log(f"[ERRO CC]    💡 Número do grupo (0010, 6010...) é variável - score esperado ~43%")
    gui_log(f"[ERRO CC]    ⏱️ Timeout: {timeout}s")
    gui_log(f"[ERRO CC]    📊 Salvar debug: SIM")

    encontrado = detectar_imagem_opencv(caminho, confidence=0.35, timeout=timeout, salvar_debug=False)

    gui_log(f"[ERRO CC] 📊 Resultado da detecção: {encontrado}")

    if encontrado:
        gui_log("⚠️ [ERRO CC] MODAL DE ERRO CENTRO DE CUSTO DETECTADO!")

        # Aguardar 0.5 segundos antes de pressionar Enter
        time.sleep(0.5)

        gui_log("[ERRO CC] >> Pressionando ENTER (fechar modal)...")
        if not MODO_TESTE:
            pyautogui.press("enter")
        else:
            gui_log("[ERRO CC] [MODO TESTE] Simulando ENTER")
        gui_log("[ERRO CC] << ENTER pressionado")

        # Aguardar 1 segundo para o modal fechar
        time.sleep(1)

        gui_log("✅ [ERRO CC] Modal fechado!")
        gui_log("❌ [ERRO CC] ERRO: Oracle não salvará o item (erro centro de custo)")

        return True
    else:
        gui_log(f"[ERRO CC] ✅ Nenhum modal detectado no timeout de {timeout}s")
        gui_log("[ERRO CC]    ℹ️ Se o modal apareceu mas não foi detectado:")
        gui_log("[ERRO CC]       - Verifique a imagem de referência erro_centro_custo.png")
        gui_log(f"[ERRO CC]       - Ou aumente o timeout (atual: {timeout}s)")
        gui_log("[ERRO CC]       - Ou diminua confidence (atual: 0.4 - JÁ MUITO BAIXO!)")
        gui_log("[ERRO CC]       - Verifique os screenshots de debug salvos")
        gui_log("[ERRO CC]       - Score esperado: ~43% (número do grupo varia)")
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

    # Detectar com OpenCV (timeout de 1 segundo — erro aparece imediatamente)
    encontrado = detectar_imagem_opencv(erro_produto_path, confidence=0.8, timeout=1)

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
        notificar_parada_telegram("ERRO_PRODUTO", f"Produto inválido detectado - Linha {linha_atual}")
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
            encontrado = pyautogui.locateOnScreen(caminho_tempo_oracle, confidence=0.8)
            if encontrado:
                gui_log("⏱️ [TIMEOUT ORACLE] Detectado! Sistema Oracle expirou.")
                try:
                    service.spreadsheets().values().update(
                        spreadsheetId=SPREADSHEET_ID,
                        range=range_str,
                        valueInputOption="RAW",
                        body={"values": [["Timeout Oracle - Reabrir sistema"]]}
                    ).execute()
                except Exception:
                    pass
                _rpa_running = False
                notificar_parada_telegram("TIMEOUT", f"Sistema Oracle expirou - Linha {linha_atual}")
                return True
            else:
                gui_log("[TEMPO_ORACLE] ✅ Sem timeout.")
        except Exception:
            pass
    else:
        gui_log("[TEMPO_ORACLE] ❌ Arquivo tempo_oracle.png NÃO ENCONTRADO em nenhum caminho!")

    return False

# =================== ETAPAS DO PROCESSO ===================
def etapa_01_transferencia_subinventario(config):
    """Etapa 1: Duplo clique em Transferência de Subinventário"""

    # ═══════════════════════════════════════════════════════════════
    # 🔧 DEBUG CRÍTICO: VERIFICAR STATUS DO VALIDADOR HÍBRIDO
    # ═══════════════════════════════════════════════════════════════
    gui_log("="*70)
    gui_log("🔧 🔧 🔧 DEBUG CRÍTICO - STATUS DO VALIDADOR 🔧 🔧 🔧")
    gui_log("="*70)
    gui_log(f"   VALIDADOR_HIBRIDO_DISPONIVEL = {VALIDADOR_HIBRIDO_DISPONIVEL}")
    if VALIDADOR_HIBRIDO_DISPONIVEL:
        gui_log("   ✅ ✅ ✅ VALIDADOR ESTÁ ATIVO ✅ ✅ ✅")
        gui_log("   ✅ DETECÇÃO DE MODAIS VAI FUNCIONAR!")
    else:
        gui_log("   ❌ ❌ ❌ VALIDADOR ESTÁ DESATIVADO ❌ ❌ ❌")
        gui_log("   ❌ DETECÇÃO DE MODAIS NÃO VAI FUNCIONAR!")
        gui_log("   ⚠️  validador_hibrido.py não foi importado!")
    gui_log("="*70)

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

    time.sleep(0.3)
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
        time.sleep(0.5)

        # Pressionar 9 vezes a seta para baixo
        for i in range(9):
            pyautogui.press('down')
            time.sleep(0.1)
            gui_log(f"   Seta {i+1}/9")

        time.sleep(0.3)

        # Pressionar Enter para selecionar
        gui_log("⌨️ Pressionando Enter para selecionar Wallatas")
        pyautogui.press('enter')
        time.sleep(0.5)

        # Pressionar Enter novamente para confirmar o modal "Sim"
        gui_log("⌨️ Pressionando Enter para confirmar (Sim)")
        pyautogui.press('enter')
        time.sleep(0.5)

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

        # Obter ID da planilha Oracle do config
        if "planilhas" in config and "oracle_itens" in config["planilhas"]:
            SPREADSHEET_ID = config["planilhas"]["oracle_itens"]
            gui_log(f"📊 Usando planilha Oracle (do config): ...{SPREADSHEET_ID[-8:]}")
        else:
            # Fallback para produção se não configurado
            SPREADSHEET_ID = "14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk"
            gui_log(f"⚠️ Planilha Oracle não configurada, usando padrão (PROD)")

        SHEET_NAME = "Separação"

        # Igual RPA Oracle antigo: token no diretório atual
        token_path = "token.json"
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

        # ═══════════════════════════════════════════════════════════════
        # 🔧 DEBUG: VERIFICAR SE VALIDADOR ESTÁ DISPONÍVEL
        # ═══════════════════════════════════════════════════════════════
        gui_log("="*70)
        gui_log("🔧 [DEBUG CRÍTICO] VERIFICANDO STATUS DO VALIDADOR")
        gui_log("="*70)
        gui_log(f"   VALIDADOR_HIBRIDO_DISPONIVEL = {VALIDADOR_HIBRIDO_DISPONIVEL}")
        if VALIDADOR_HIBRIDO_DISPONIVEL:
            gui_log("   ✅ VALIDADOR ESTÁ ATIVO - Detecção de modais FUNCIONARÁ")
        else:
            gui_log("   ❌ VALIDADOR ESTÁ DESATIVADO - Detecção de modais NÃO funcionará!")
            gui_log("   ⚠️  Se você vê esta mensagem, o arquivo validador_hibrido.py não foi carregado!")
        gui_log("="*70)

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
                    "Erro salvamento",

                    # Erros de modal (campo digitado errado, retry no próximo ciclo)
                    "Erro modal: Item",
                    "Erro modal: Referencia",
                    "Erro modal: Sub.Origem",
                    "Erro modal: Sub.Destino",
                    "Erro modal: End.Origem",
                    "Erro modal: End.Destino",
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
                    # NÃO fazer retry de tela incorreta - requer correção manual
                    processar = False
                    gui_log(f"⏭️ [SKIP] Linha {i+2} (ID: {id_linha_temp}) com erro de tela incorreta - CORREÇÃO MANUAL NECESSÁRIA")
                    gui_log(f"⚠️ Tela incorreta requer intervenção manual. Não será reprocessada automaticamente.")
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
                    gui_log("⚠️ [INTERRUPÇÃO] RPA foi interrompido. Encerrando processamento...")
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
                    # ⌨️ RESET DE TECLADO - Liberar modificadores acumulados
                    # Evita que Shift/Ctrl/Alt fiquem "presos" após muitos itens
                    # ═══════════════════════════════════════════════════════════════
                    for _tecla_reset in ['shift', 'ctrl', 'alt', 'win']:
                        pyautogui.keyUp(_tecla_reset)

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
                    gui_log(f"[ITEM] Preenchendo campo Item: '{item}' em {coords['item']}")

                    if MODO_TESTE:
                        gui_log(f"[MODO TESTE] Simulando preenchimento de Item: '{item}'")
                        time.sleep(0.3)
                    else:
                        digitar_campo(coords["item"][0], coords["item"][1], item, "Item")

                    # TAB para sair do campo
                    safe_press("tab", contexto="após Item")
                    time.sleep(0.5)
                    gui_log(f"[ITEM] ✅ Item preenchido")

                    # Verificar modal de item inexistente
                    if not MODO_TESTE:
                        resultado_modal_item = verificar_modal_erro_campo("item", coords["item"], item)
                        if resultado_modal_item == "erro":
                            gui_log(f"❌ [ITEM] Modal não fechou após retry — limpando e pulando")
                            service.spreadsheets().values().update(
                                spreadsheetId=SPREADSHEET_ID,
                                range=range_str,
                                valueInputOption="RAW",
                                body={"values": [["Erro modal: Item"]]}
                            ).execute()
                            safe_press('f6', contexto="limpar após item inexistente")
                            time.sleep(1.0)
                            continue

                    # Verificar se foi interrompido
                    if not _rpa_running:
                        gui_log("⚠️ [INTERRUPÇÃO] RPA interrompido após preencher Item")
                        try:
                            service.spreadsheets().values().update(
                                spreadsheetId=SPREADSHEET_ID,
                                range=range_str,
                                valueInputOption="RAW",
                                body={"values": [["Interrompido - Refazer"]]}
                            ).execute()
                            gui_log("✅ Status atualizado: 'Interrompido - Refazer'")
                        except:
                            pass
                        return False

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
                    # PREENCHER REFERÊNCIA
                    # ═══════════════════════════════════════════════════════════════
                    gui_log(f"[REFERENCIA] Preenchendo campo Referência: '{referencia}'")

                    if MODO_TESTE:
                        gui_log(f"[MODO TESTE] Simulando preenchimento de Referência: '{referencia}'")
                        time.sleep(0.3)
                    else:
                        digitar_campo(coords["Referencia"][0], coords["Referencia"][1], referencia, "Referência")

                    safe_press("tab", contexto="após Referência")
                    time.sleep(0.5)
                    gui_log(f"[REFERENCIA] ✅ Referência preenchida")

                    # Verificar se Referência foi digitada corretamente (leitura via Ctrl+C)
                    if not MODO_TESTE:
                        cx_ref = coords_validacao["campo_referencia"][0] + coords_validacao["campo_referencia"][2] // 2
                        cy_ref = coords_validacao["campo_referencia"][1] + coords_validacao["campo_referencia"][3] // 2
                        val_ref_lido = _ler_campo_ctrl_c(cx_ref, cy_ref)
                        if not _comparar_campo(val_ref_lido, str(referencia).strip(), "Referência"):
                            gui_log(f"[REFERENCIA] ⚠️ Esperado '{referencia}', lido '{val_ref_lido}' — retentando")
                            pyautogui.click(coords["Referencia"][0], coords["Referencia"][1])
                            time.sleep(0.15)
                            pyautogui.press('delete')
                            time.sleep(0.1)
                            safe_write(str(referencia).strip(), contexto="retry Referência")
                            safe_press("tab", contexto="após retry Referência")
                            time.sleep(0.5)
                            val_ref_lido2 = _ler_campo_ctrl_c(cx_ref, cy_ref)
                            if _comparar_campo(val_ref_lido2, str(referencia).strip(), "Referência"):
                                gui_log(f"[REFERENCIA] ✅ Corrigido: '{val_ref_lido2}'")
                            else:
                                gui_log(f"[REFERENCIA] ❌ Ainda errado após retry: '{val_ref_lido2}' — limpando e pulando")
                                safe_press('f6', contexto="limpar após erro Referência")
                                time.sleep(1.0)
                                service.spreadsheets().values().update(
                                    spreadsheetId=SPREADSHEET_ID,
                                    range=range_str,
                                    valueInputOption="RAW",
                                    body={"values": [["Erro modal: Referencia"]]}
                                ).execute()
                                continue
                        else:
                            gui_log(f"[REFERENCIA] ✅ OK: '{val_ref_lido}'")

                    # ═══════════════════════════════════════════════════════════════
                    # PREENCHER SUB_ORIGEM
                    # ═══════════════════════════════════════════════════════════════
                    gui_log(f"[SUB_ORIGEM] Preenchendo campo Sub.Origem: '{sub_o}'")

                    if MODO_TESTE:
                        gui_log(f"[MODO TESTE] Simulando preenchimento de Sub.Origem: '{sub_o}'")
                        time.sleep(0.3)
                    else:
                        digitar_campo(coords["sub_origem"][0], coords["sub_origem"][1], sub_o, "Sub.Origem")

                    safe_press("tab", contexto="após Sub.Origem")
                    time.sleep(0.5)
                    gui_log(f"[SUB_ORIGEM] ✅ Sub.Origem preenchido")

                    # Verificar modal de subinventário origem inexistente
                    if not MODO_TESTE:
                        resultado_modal_sub_o = verificar_modal_erro_campo("subinv", coords["sub_origem"], sub_o)
                        if resultado_modal_sub_o == "erro":
                            gui_log(f"❌ [SUB_ORIGEM] Modal não fechou após retry — limpando e pulando")
                            safe_press('f6', contexto="limpar após erro Sub.Origem")
                            time.sleep(1.0)
                            service.spreadsheets().values().update(
                                spreadsheetId=SPREADSHEET_ID,
                                range=range_str,
                                valueInputOption="RAW",
                                body={"values": [["Erro modal: Sub.Origem"]]}
                            ).execute()
                            continue

                    # ═══════════════════════════════════════════════════════════════
                    # PREENCHER END_ORIGEM
                    # ═══════════════════════════════════════════════════════════════
                    gui_log(f"[END_ORIGEM] Preenchendo campo End.Origem: '{end_o}'")

                    if MODO_TESTE:
                        gui_log(f"[MODO TESTE] Simulando preenchimento de End.Origem: '{end_o}'")
                        time.sleep(0.3)
                    else:
                        digitar_campo(coords["end_origem"][0], coords["end_origem"][1], end_o, "End.Origem")

                    safe_press("tab", contexto="após End.Origem")
                    time.sleep(0.5)
                    gui_log(f"[END_ORIGEM] ✅ End.Origem preenchido")

                    # Verificar modal de endereço origem inexistente
                    if not MODO_TESTE:
                        resultado_modal_end_o = verificar_modal_erro_campo("endereco", coords["end_origem"], end_o)
                        if resultado_modal_end_o == "erro":
                            gui_log(f"❌ [END_ORIGEM] Modal não fechou após retry — limpando e pulando")
                            service.spreadsheets().values().update(
                                spreadsheetId=SPREADSHEET_ID,
                                range=range_str,
                                valueInputOption="RAW",
                                body={"values": [["Erro modal: End.Origem"]]}
                            ).execute()
                            safe_press('f6', contexto="limpar após endereço origem inexistente")
                            time.sleep(1.0)
                            continue

                    # Verifica se referencia inicia com "COD"
                    if str(referencia).strip().upper().startswith("COD"):
                        gui_log(f"[COD] Referencia '{referencia}' detectada como tipo COD. Pulando campos destino.")
                        if not MODO_TESTE:
                            gui_log(f"[COD] Cursor deve estar em SUB_DESTINO. Dando TAB para pular...")
                            safe_press("tab", contexto="COD pular Sub.Destino")
                            time.sleep(0.5)
                            gui_log(f"[COD] Cursor deve estar em END_DESTINO. Dando TAB para pular...")
                            safe_press("tab", contexto="COD pular End.Destino")
                            time.sleep(0.5)
                            gui_log(f"[COD] Cursor deve estar em QUANTIDADE agora.")
                        else:
                            gui_log(f"[MODO TESTE] Simulando TAB TAB para COD...")
                    else:
                        gui_log(f"[MOV] Referência '{referencia}' tratada como MOV. Preenchendo destinos.")

                        # ═══════════════════════════════════════════════════════════════
                        # PREENCHER SUB_DESTINO (MOV)
                        # ═══════════════════════════════════════════════════════════════
                        # Oracle auto-foca este campo após TAB do End.Origem.
                        # Padrão correto: DELETE primeiro (limpa campo já focado) → click → write
                        gui_log(f"[SUB_DESTINO] Preenchendo campo Sub.Destino: '{sub_d}'")

                        if MODO_TESTE:
                            gui_log(f"[MODO TESTE] Simulando preenchimento de Sub.Destino: '{sub_d}'")
                            time.sleep(0.3)
                        else:
                            pyautogui.press("delete")
                            pyautogui.click(coords["sub_destino"])
                            time.sleep(0.15)
                            safe_write(sub_d, contexto="Sub.Destino")

                        safe_press("tab", contexto="após Sub.Destino")
                        time.sleep(0.5)
                        gui_log(f"[SUB_DESTINO] ✅ Sub.Destino preenchido")

                        # Verificar modal de subinventário destino inexistente
                        if not MODO_TESTE:
                            resultado_modal_sub_d = verificar_modal_erro_campo("subinv", coords["sub_destino"], sub_d)
                            if resultado_modal_sub_d == "erro":
                                gui_log(f"❌ [SUB_DESTINO] Modal não fechou após retry — limpando e pulando")
                                safe_press('f6', contexto="limpar após erro Sub.Destino")
                                time.sleep(1.0)
                                service.spreadsheets().values().update(
                                    spreadsheetId=SPREADSHEET_ID,
                                    range=range_str,
                                    valueInputOption="RAW",
                                    body={"values": [["Erro modal: Sub.Destino"]]}
                                ).execute()
                                continue

                        # ═══════════════════════════════════════════════════════════════
                        # PREENCHER END_DESTINO (MOV)
                        # ═══════════════════════════════════════════════════════════════
                        # Mesmo padrão: Oracle auto-foca após TAB do Sub.Destino.
                        # DELETE primeiro → click → write
                        gui_log(f"[END_DESTINO] Preenchendo campo End.Destino: '{end_d}'")

                        if MODO_TESTE:
                            gui_log(f"[MODO TESTE] Simulando preenchimento de End.Destino: '{end_d}'")
                            time.sleep(0.3)
                        else:
                            pyautogui.press("delete")
                            pyautogui.click(coords["end_destino"])
                            time.sleep(0.15)
                            safe_write(end_d, contexto="End.Destino")

                        safe_press("tab", contexto="após End.Destino")
                        time.sleep(0.5)
                        gui_log(f"[END_DESTINO] ✅ End.Destino preenchido")

                        # Verificar modal de endereço destino inexistente
                        if not MODO_TESTE:
                            resultado_modal_end_d = verificar_modal_erro_campo("endereco", coords["end_destino"], end_d)
                            if resultado_modal_end_d == "erro":
                                gui_log(f"❌ [END_DESTINO] Modal não fechou após retry — limpando e pulando")
                                service.spreadsheets().values().update(
                                    spreadsheetId=SPREADSHEET_ID,
                                    range=range_str,
                                    valueInputOption="RAW",
                                    body={"values": [["Erro modal: End.Destino"]]}
                                ).execute()
                                safe_press('f6', contexto="limpar após endereço destino inexistente")
                                time.sleep(1.0)
                                continue

                    # ═══════════════════════════════════════════════════════════════
                    # PREENCHER QUANTIDADE - COM CORREÇÃO AUTOMÁTICA E DETECÇÃO DIFERENCIAL
                    # ═══════════════════════════════════════════════════════════════
                    gui_log(f"[QUANTIDADE] Preenchendo quantidade: {quantidade}")

                    # 1️⃣ CAPTURAR PIXELS AMARELOS ANTES
                    gui_log("[QUANTIDADE] 📸 Capturando baseline de pixels amarelos ANTES...")
                    pixels_amarelos_antes = contar_pixels_cor("amarelo")
                    gui_log(f"[QUANTIDADE] Baseline amarelo: {pixels_amarelos_antes} pixels")

                    # 2️⃣ PREENCHER QUANTIDADE
                    if MODO_TESTE:
                        gui_log(f"[MODO TESTE] Simulando preenchimento de Quantidade: '{quantidade}'")
                        time.sleep(0.3)
                    else:
                        digitar_campo(coords["quantidade"][0], coords["quantidade"][1], quantidade, "Quantidade")

                    # 3️⃣ SAIR DO CAMPO (TAB) - AQUI O MODAL PODE APARECER
                    gui_log("[QUANTIDADE] >> Pressionando TAB para sair do campo...")
                    if not MODO_TESTE:
                        safe_press("tab", contexto="após Quantidade")
                    gui_log("[QUANTIDADE] << TAB pressionado")

                    gui_log("[QUANTIDADE] Aguardando 1.0s...")
                    time.sleep(1.0)
                    gui_log(f"[QUANTIDADE] ✅ Quantidade preenchida e verificada")

                    # 4️⃣ DETECÇÃO DIFERENCIAL - Comparar ANTES vs DEPOIS
                    gui_log("[QTD NEG] ═══════════════════════════════════════════════")
                    gui_log("[QTD NEG] 🔍 DETECÇÃO DIFERENCIAL - Quantidade Negativa")
                    gui_log("[QTD NEG] ═══════════════════════════════════════════════")

                    modal_qtd_neg = detectar_modal_diferencial(
                        cor_esperada="amarelo",
                        pixels_antes=pixels_amarelos_antes,
                        threshold_aumento=500  # 500 pixels a mais = modal apareceu
                    )

                    if modal_qtd_neg:
                        gui_log("⚠️ [QTD NEG] MODAL DETECTADO (ícone amarelo)!")
                        time.sleep(0.2)
                        gui_log("[QTD NEG] >> Pressionando ENTER (fechar modal)...")
                        if not MODO_TESTE:
                            safe_press("enter", contexto="fechar modal Qtd Negativa")
                        gui_log("[QTD NEG] << ENTER pressionado")
                        time.sleep(0.5)
                        gui_log("✅ [QTD NEG] Modal fechado!")

                        # Marcar como erro e pular
                        gui_log("❌ [QTD NEG] Quantidade negativa NÃO É PERMITIDA")
                        gui_log("[QTD NEG] 🧹 Pressionando F6 para limpar formulário...")
                        if not MODO_TESTE:
                            safe_press('f6', contexto="limpar após Qtd Negativa")
                        time.sleep(1.0)
                        gui_log("[QTD NEG] ✅ Formulário limpo")

                        # Atualizar planilha
                        try:
                            service.spreadsheets().values().update(
                                spreadsheetId=SPREADSHEET_ID,
                                range=range_str,
                                valueInputOption="RAW",
                                body={"values": [["Quantidade Negativa"]]}
                            ).execute()
                            gui_log("✅ Status atualizado: 'Quantidade Negativa'")
                        except Exception as e:
                            gui_log(f"⚠️ Erro ao atualizar status: {e}")

                        gui_log("[QTD NEG] ⏭️ Pulando para próximo item")
                        continue  # Pular para próximo item

                    else:
                        # Não detectou modal - quantidade está OK, continua normal
                        gui_log("[QTD NEG] ✅ Nenhum modal detectado - quantidade válida")

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
                    # 🔍 VERIFICAÇÃO SIMPLES - checar se campos estão preenchidos
                    # ═══════════════════════════════════════════════════════════════
                    gui_log("[VALIDAÇÃO] Verificando se campos estão preenchidos...")
                    eh_cod = str(referencia).strip().upper().startswith("COD")
                    campos_checar = [
                        ("Item",       coords_validacao["campo_item"]),
                        ("Sub.Origem", coords_validacao["campo_sub_o"]),
                        ("End.Origem", coords_validacao["campo_end_o"]),
                        ("Quantidade", coords_validacao["campo_quantidade"]),
                    ]
                    if not eh_cod:
                        campos_checar += [
                            ("Sub.Destino", coords_validacao["campo_sub_d"]),
                            ("End.Destino", coords_validacao["campo_end_d"]),
                        ]

                    campo_vazio = None
                    if not MODO_TESTE:
                        for nome_cv, coord_cv in campos_checar:
                            if not _rpa_running:
                                return False
                            x_cv = coord_cv[0] + coord_cv[2] // 2
                            y_cv = coord_cv[1] + coord_cv[3] // 2
                            val_lido = _ler_campo_ctrl_c(x_cv, y_cv)
                            if not val_lido.strip():
                                campo_vazio = nome_cv
                                break
                            gui_log(f"[VALIDAÇÃO] {nome_cv}: preenchido ✅")

                    if campo_vazio:
                        gui_log(f"[VALIDAÇÃO] ❌ Campo '{campo_vazio}' está vazio — limpando e pulando")
                        if not MODO_TESTE:
                            safe_press('f6', contexto="limpar após campo vazio")
                            time.sleep(1.0)
                        try:
                            service.spreadsheets().values().update(
                                spreadsheetId=SPREADSHEET_ID,
                                range=range_str,
                                valueInputOption="RAW",
                                body={"values": [["Campo vazio encontrado"]]}
                            ).execute()
                        except Exception as e_val:
                            gui_log(f"⚠️ Erro ao atualizar status: {e_val}")
                        continue
                    else:
                        gui_log("[VALIDAÇÃO] ✅ Todos os campos preenchidos — prosseguindo")

                    # 🌐 Verificar queda de rede antes de salvar
                    if verificar_queda_rede():
                        gui_log("❌ QUEDA DE REDE detectada antes de salvar!")
                        return False

                    # ═══════════════════════════════════════════════════════════════
                    # 💾 ADICIONAR AO CACHE **ANTES** DE Ctrl+S (CRÍTICO!)
                    # MUDANÇA CRÍTICA: Cache ANTES do Ctrl+S elimina gap de duplicação
                    # Se crash/queda entre Ctrl+S e adicionar cache, item seria duplicado
                    # Agora: item JÁ está no cache ANTES de qualquer ação no Oracle
                    # ═══════════════════════════════════════════════════════════════
                    gui_log("💾 [CRÍTICO] Adicionando ao cache ANTES de Ctrl+S...")

                    sucesso_cache = cache.adicionar(
                        id_item=id_linha,
                        linha_atual=i,
                        item=item,
                        quantidade=quantidade,
                        referencia=referencia,
                        status="pre_save"  # Status específico: PRÉ-salvamento
                    )
                    if sucesso_cache:
                        gui_log(f"✅ Registrado no cache (PRE_SAVE): {id_linha}")
                    else:
                        gui_log(f"⚠️ Falha ao registrar no cache (ID vazio?)")

                    # ═══════════════════════════════════════════════════════════════
                    # SALVAR COM Ctrl+S (APÓS ADICIONAR AO CACHE)
                    # ═══════════════════════════════════════════════════════════════
                    gui_log("[SAVE] ═══════════════════════════════════════════════")

                    # Verificar se foi interrompido antes de salvar
                    if not _rpa_running:
                        gui_log("⚠️ [INTERRUPÇÃO] RPA interrompido antes de Ctrl+S")
                        try:
                            service.spreadsheets().values().update(
                                spreadsheetId=SPREADSHEET_ID,
                                range=range_str,
                                valueInputOption="RAW",
                                body={"values": [["Interrompido - Refazer"]]}
                            ).execute()
                            gui_log("✅ Status atualizado: 'Interrompido - Refazer'")
                        except:
                            pass
                        return False

                    # ═══════════════════════════════════════════════════════════════
                    # CTRL+S - COM DETECÇÃO DIFERENCIAL PARA ERRO CENTRO CUSTO
                    # ═══════════════════════════════════════════════════════════════
                    gui_log("[SAVE] Iniciando salvamento com Ctrl+S...")

                    # 1️⃣ CAPTURAR PIXELS VERMELHOS ANTES
                    gui_log("[SAVE] 📸 Capturando baseline de pixels vermelhos ANTES...")
                    pixels_vermelhos_antes = contar_pixels_cor("vermelho")
                    gui_log(f"[SAVE] Baseline vermelho: {pixels_vermelhos_antes} pixels")

                    # 2️⃣ PRESSIONAR CTRL+S
                    gui_log("[SAVE] >> Pressionando CTRL+S...")
                    if not MODO_TESTE:
                        safe_hotkey("ctrl", "s", contexto="salvar registro Oracle")
                    gui_log("[SAVE] << CTRL+S pressionado")
                    gui_log("[SAVE] Aguardando 0.5s para modal aparecer...")
                    time.sleep(0.5)
                    gui_log("[SAVE] ✅ Ctrl+S executado")

                    # Atualizar status do cache
                    cache.atualizar_status(id_linha, "ctrl_s_enviado")

                    # ═══════════════════════════════════════════════════════════════
                    # 🔍 DETECÇÃO DIFERENCIAL - Erro Centro de Custo (IMEDIATO!)
                    # CRÍTICO: Modal aparece IMEDIATAMENTE após Ctrl+S!
                    # Precisa detectar ANTES de aguardar_salvamento_concluido()
                    # Se aparecer: ENTER → Status Oracle = "Erro Centro de Custo" → F6 → Continue
                    # ═══════════════════════════════════════════════════════════════
                    gui_log("[ERRO CC POS] ═══════════════════════════════════════════════")
                    gui_log("[ERRO CC POS] 🔍 DETECÇÃO DIFERENCIAL - Erro Centro de Custo")
                    gui_log("[ERRO CC POS] ═══════════════════════════════════════════════")

                    modal_erro_cc = detectar_modal_diferencial(
                        cor_esperada="vermelho",
                        pixels_antes=pixels_vermelhos_antes,
                        threshold_aumento=500  # 500 pixels a mais = modal apareceu
                    )

                    if modal_erro_cc:
                        gui_log("❌ [ERRO CC POS] Erro Centro de Custo detectado APÓS Ctrl+S!")

                        # Definir mensagem de erro
                        mensagem_status = "Erro Centro de Custo"

                        # ═══════════════════════════════════════════════════════════════
                        # 1️⃣ FECHAR MODAL COM ENTER
                        # ═══════════════════════════════════════════════════════════════
                        gui_log("[ERRO CC POS] ═══════════════════════════════════════════════")
                        gui_log("[ERRO CC POS] >> Pressionando ENTER para fechar modal...")

                        if not MODO_TESTE:
                            time.sleep(0.2)
                            pyautogui.press("enter")
                            gui_log("[ERRO CC POS] << ENTER pressionado")
                            time.sleep(0.5)
                            gui_log("[ERRO CC POS] ✅ Modal fechado!")
                        else:
                            gui_log("[ERRO CC POS] [MODO TESTE] Simulando ENTER")

                        # ═══════════════════════════════════════════════════════════════
                        # 2️⃣ LIMPAR FORMULÁRIO COM F6 (OBRIGATÓRIO ANTES DE CONTINUAR)
                        # ═══════════════════════════════════════════════════════════════
                        gui_log("[ERRO CC POS] ═══════════════════════════════════════════════")
                        gui_log("[ERRO CC POS] 🧹 Pressionando F6 para limpar formulário...")

                        limpar_sucesso = False
                        try:
                            if MODO_TESTE:
                                gui_log("[ERRO CC POS] [MODO TESTE] Simulando pressionar F6")
                                limpar_sucesso = True
                            else:
                                # 🔧 CORREÇÃO: Pausar hook do teclado temporariamente
                                gui_log("[ERRO CC POS] Pausando hook do teclado para evitar interceptação...")
                                try:
                                    keyboard.unhook_all()
                                    gui_log("[ERRO CC POS] ✅ Hook pausado")
                                except:
                                    pass

                                # Tentar F6 com múltiplas tentativas
                                for tentativa in range(3):
                                    try:
                                        gui_log(f"[ERRO CC POS] >> Tentativa {tentativa+1}/3: Pressionando F6...")
                                        time.sleep(0.1)
                                        pyautogui.press('f6')
                                        gui_log(f"[ERRO CC POS] << F6 pressionado")
                                        time.sleep(0.5)
                                        limpar_sucesso = True
                                        break
                                    except Exception as e_f6:
                                        gui_log(f"[ERRO CC POS] ⚠️ Erro na tentativa {tentativa+1}: {e_f6}")
                                        time.sleep(0.3)

                                # Reativar hook
                                try:
                                    keyboard.hook(parar_callback)
                                    gui_log("[ERRO CC POS] ✅ Hook reativado")
                                except:
                                    pass

                        except Exception as e_limpar:
                            gui_log(f"[ERRO CC POS] ❌ Erro ao limpar: {e_limpar}")

                        if limpar_sucesso:
                            gui_log("[ERRO CC POS] ✅ Formulário limpo com F6")
                        else:
                            gui_log("[ERRO CC POS] ⚠️ Não foi possível confirmar limpeza do formulário")

                        # Atualizar Google Sheets
                        try:
                            range_str = f"'Separação'!T{i}:T{i}"
                            service.spreadsheets().values().update(
                                spreadsheetId=SPREADSHEET_ID,
                                range=range_str,
                                valueInputOption="RAW",
                                body={"values": [[mensagem_status]]}
                            ).execute()
                            gui_log(f"✅ [ERRO CC POS] Status atualizado: '{mensagem_status}'")
                        except Exception as e_sheets:
                            gui_log(f"⚠️ [ERRO CC POS] Erro ao atualizar Sheets: {e_sheets}")

                        # IMPORTANTE: NÃO adicionar ao cache (permite reprocessar)
                        gui_log("[ERRO CC POS] ⚠️ Item NÃO adicionado ao cache (pode ser reprocessado)")

                        # Continuar para próximo item
                        gui_log("[ERRO CC POS] ➡️ Continuando para próximo item...")
                        continue

                    else:
                        # ═══════════════════════════════════════════════════════════════
                        # ✅ NENHUM MODAL DETECTADO - Continuar fluxo normal
                        # ═══════════════════════════════════════════════════════════════
                        gui_log("[ERRO CC POS] ✅ Nenhum modal detectado - salvamento normal")

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
                                        time.sleep(0.1)  # Pequeno delay antes de pressionar
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
                                            notificar_parada_telegram("ESC", "Tecla ESC pressionada durante salvamento")
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
            notificar_parada_telegram("FAILSAFE", "Mouse no canto superior esquerdo (0,0) - PASSO 4/6")
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
            notificar_parada_telegram("FAILSAFE", "Mouse no canto superior esquerdo (0,0) - PASSO 5/6")
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
            notificar_parada_telegram("FAILSAFE", "Mouse no canto superior esquerdo (0,0) - PASSO 6/6")
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

    # Manter apenas as 8 colunas desejadas (REV. será capturado aqui mas removido antes de enviar ao Sheets)
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

    # Criar pasta out/ na PASTA DO EXECUTÁVEL (não na pasta interna)
    # Se rodando como .exe, usar pasta do executável; senão, pasta do script
    if getattr(sys, 'frozen', False):
        # Executando como .exe - usar pasta do executável
        base_dir = Path(sys.executable).parent
    else:
        # Executando como script - usar pasta do script
        base_dir = Path(__file__).parent

    # Salvar em rpa_bancada/out (dentro de Genesys/)
    out_dir = base_dir / "rpa_bancada" / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    gui_log(f"📁 [DEBUG] Salvando Excel em: {out_dir}")

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
            safe_hotkey('shift', 'f10', contexto="menu contexto Bancada")

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

            # Notificar início do envio
            if _telegram_notifier and _telegram_notifier.enabled:
                try:
                    _telegram_notifier.enviar_mensagem(
                        f"📤 <b>ENVIANDO BANCADA PARA GOOGLE SHEETS</b>\n\n"
                        f"📊 <b>Registros:</b> {len(df)}\n"
                        f"⏰ {datetime.now().strftime('%H:%M:%S')}"
                    )
                except:
                    pass

            try:
                sucesso_sheets = enviar_para_google_sheets(df)

                if sucesso_sheets:
                    gui_log("✅ Dados enviados para Google Sheets com sucesso!")

                    # Notificar sucesso do envio
                    if _telegram_notifier and _telegram_notifier.enabled:
                        try:
                            _telegram_notifier.enviar_mensagem(
                                f"✅ <b>BANCADA ENVIADA COM SUCESSO</b>\n\n"
                                f"📊 <b>Registros:</b> {len(df)}\n"
                                f"⏰ {datetime.now().strftime('%H:%M:%S')}"
                            )
                        except:
                            pass
                else:
                    gui_log("❌ Falha ao enviar para Google Sheets")

                    # Notificar falha do envio
                    if _telegram_notifier and _telegram_notifier.enabled:
                        try:
                            _telegram_notifier.enviar_mensagem(
                                f"❌ <b>FALHA AO ENVIAR BANCADA</b>\n\n"
                                f"📊 <b>Registros:</b> {len(df)}\n"
                                f"⏰ {datetime.now().strftime('%H:%M:%S')}"
                            )
                        except:
                            pass
            except Exception as e:
                gui_log(f"❌ Erro ao enviar para Google Sheets: {e}")
                import traceback
                gui_log(traceback.format_exc())

                # Notificar erro do envio
                if _telegram_notifier and _telegram_notifier.enabled:
                    try:
                        _telegram_notifier.enviar_mensagem(
                            f"❌ <b>ERRO AO ENVIAR BANCADA</b>\n\n"
                            f"⚠️ <b>Erro:</b> {str(e)[:100]}\n"
                            f"⏰ {datetime.now().strftime('%H:%M:%S')}"
                        )
                    except:
                        pass
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

        # Aguardar intervalo de verificação COM anti-hibernação ATIVO
        gui_log(f"⏳ Próxima verificação em {intervalo_verificacao//60} minuto(s)...")
        gui_log(f"   🖱️ Anti-hibernação ATIVO (pressiona Shift a cada 3s)")

        tempo_aguardado = 0

        while tempo_aguardado < intervalo_verificacao and _rpa_running:
            time.sleep(1)
            tempo_aguardado += 1

            # CRÍTICO: Pressionar Shift a cada 3 segundos para evitar hibernação
            if not MODO_TESTE and tempo_aguardado % 3 == 0:
                try:
                    pyautogui.press('shift')
                except:
                    pass  # Ignora erros silenciosamente

            # Mostrar progresso a cada 10 segundos
            if tempo_aguardado % 10 == 0:
                segundos_restantes_verificacao = intervalo_verificacao - tempo_aguardado
                print(f"   {segundos_restantes_verificacao}s até próxima verificação... (anti-hibernação ativo)", end='\r')

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
    gui_log("🔍 [DEBUG] Função verificar_tem_itens_pendentes() CHAMADA")

    if not GOOGLE_SHEETS_DISPONIVEL:
        gui_log("⚠️ [DEBUG] Google Sheets NÃO disponível")
        return False

    try:
        gui_log("🔍 [DEBUG] Iniciando verificação de itens pendentes...")
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
        # CRÍTICO: Usar a MESMA planilha que o processamento (config.json)
        SPREADSHEET_ID = "14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk"
        SHEET_NAME = "Separação"

        # Autenticar (IGUAL RPA Oracle antigo)
        creds = None
        if os.path.exists("token.json"):
            gui_log("🔍 [DEBUG] token.json EXISTE, carregando...")
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        else:
            gui_log("⚠️ [DEBUG] token.json NÃO existe")

        if not creds or not creds.valid:
            gui_log("🔍 [DEBUG] Credenciais inválidas ou expiradas")
            if creds and creds.expired and creds.refresh_token:
                gui_log("🔄 [DEBUG] Renovando token...")
                creds.refresh(Request())
            else:
                # CORREÇÃO: Abrir browser para autenticar (igual RPA Oracle antigo)
                gui_log("🌐 [DEBUG] Abrindo browser para autenticação...")
                creds_path = os.path.join(base_path, "CredenciaisOracle.json")
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                creds = flow.run_local_server(port=0)
                # Salvar token
                with open("token.json", "w") as token:
                    token.write(creds.to_json())
                gui_log("✅ [DEBUG] Token salvo com sucesso")

        service = build("sheets", "v4", credentials=creds)
        gui_log("✅ [DEBUG] Google Sheets service criado")

        # Ler headers primeiro
        gui_log("📋 [DEBUG] Lendo headers da planilha...")
        headers_result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A1:T1"
        ).execute()

        headers = headers_result.get("values", [[]])[0]
        gui_log(f"✅ [DEBUG] Headers lidos: {len(headers)} colunas")

        # Ler TODAS as linhas da planilha (sem limite de 1000)
        gui_log("📊 [DEBUG] Lendo TODAS as linhas da planilha (sem limite)...")
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A2:T"  # SEM LIMITE! Lê todas as linhas disponíveis
        ).execute()

        values = result.get("values", [])
        gui_log(f"✅ [DEBUG] Total de linhas lidas: {len(values)}")

        if not values:
            gui_log("⚠️ [DEBUG] Nenhuma linha de dados encontrada")
            return False

        # CRITÉRIO: Coluna P (Status) = CONCLUÍDO E Coluna T (Status Oracle) = vazio
        if "Status" not in headers or "Status Oracle" not in headers:
            gui_log("⚠️ Colunas 'Status' ou 'Status Oracle' não encontradas na planilha!")
            return False

        idx_status_bancada = headers.index("Status")  # Coluna P
        idx_status_oracle = headers.index("Status Oracle")  # Coluna T

        # DEBUG: Mostrar quantas linhas foram lidas
        gui_log(f"📊 [DEBUG] Total de linhas lidas: {len(values)}")
        gui_log(f"📊 [DEBUG] Coluna 'Status' (bancada): índice {idx_status_bancada}")
        gui_log(f"📊 [DEBUG] Coluna 'Status Oracle': índice {idx_status_oracle}")

        # Verificar se há linhas pendentes
        total_pendentes = 0
        total_linhas_verificadas = 0

        for i, row in enumerate(values, start=2):  # Start=2 porque A2 é primeira linha de dados
            total_linhas_verificadas += 1

            # Verificar Status (coluna P - bancada)
            if len(row) <= idx_status_bancada:
                gui_log(f"   [DEBUG] Linha {i}: Sem Status bancada (linha curta) - PULAR")
                continue  # Sem Status bancada, pular

            status_bancada = str(row[idx_status_bancada]).strip().upper()

            # REQUISITO: Status bancada DEVE ser CONCLUÍDO
            if "CONCLUÍDO" not in status_bancada and "CONCLUIDO" not in status_bancada:
                # Log apenas primeiras 3 linhas não CONCLUÍDO para não poluir
                if total_linhas_verificadas <= 3:
                    gui_log(f"   [DEBUG] Linha {i}: Status='{status_bancada}' (não é CONCLUÍDO) - PULAR")
                continue  # Não é CONCLUÍDO, pular

            # Verificar Status Oracle (coluna T)
            if len(row) <= idx_status_oracle:
                # Status Oracle vazio E Status bancada = CONCLUÍDO → PENDENTE!
                gui_log(f"✅ [DEBUG] Linha {i}: Status=CONCLUÍDO, Status Oracle=VAZIO (linha curta) → PENDENTE!")
                total_pendentes += 1
                continue

            status_oracle = str(row[idx_status_oracle]).strip()

            # Considerar pendente se Status Oracle vazio e Status bancada = CONCLUÍDO
            if not status_oracle or status_oracle == "":
                gui_log(f"✅ [DEBUG] Linha {i}: Status=CONCLUÍDO, Status Oracle='' (vazio) → PENDENTE!")
                total_pendentes += 1
            else:
                # Log apenas primeiras 3 linhas com Status Oracle preenchido
                if total_linhas_verificadas <= 3:
                    gui_log(f"   [DEBUG] Linha {i}: Status=CONCLUÍDO, Status Oracle='{status_oracle[:30]}...' - JÁ PROCESSADO")

        gui_log("")
        gui_log(f"📊 [RESUMO] Linhas verificadas: {total_linhas_verificadas}")
        gui_log(f"📊 [RESUMO] Itens PENDENTES encontrados: {total_pendentes}")
        gui_log("")

        if total_pendentes > 0:
            gui_log(f"✅ ✅ ✅ RESULTADO: TEM {total_pendentes} ITENS PENDENTES! ✅ ✅ ✅")
        else:
            gui_log(f"❌ RESULTADO: NENHUM item pendente (todos já foram processados)")

        return total_pendentes > 0

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
            notificar_parada_telegram("ESC", "Tecla ESC pressionada pelo usuário")
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
    # Usar horário de Brasília (UTC-3)
    from datetime import timezone, timedelta
    brasilia_tz = timezone(timedelta(hours=-3))
    _data_inicio_ciclo = datetime.now(brasilia_tz)
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
                        # Usar horário de Brasília (UTC-3)
                        from datetime import timezone, timedelta
                        brasilia_tz = timezone(timedelta(hours=-3))
                        data_fim = datetime.now(brasilia_tz)
                        atualizar_ciclo(_ciclo_atual, "Status", "Falha")
                        atualizar_ciclo(_ciclo_atual, "Data/Hora Fim", data_fim.strftime("%Y-%m-%d %H:%M:%S"))
                        atualizar_ciclo(_ciclo_atual, "Etapa Falha", nome_etapa)
                        atualizar_ciclo(_ciclo_atual, "RPA Oracle", etapas_status["RPA Oracle"])
                        atualizar_ciclo(_ciclo_atual, "RPA Bancada", etapas_status["RPA Bancada"])
                    except Exception:
                        pass

                return False

        # Sucesso!
        # Usar horário de Brasília (UTC-3)
        from datetime import timezone, timedelta
        brasilia_tz = timezone(timedelta(hours=-3))
        data_fim = datetime.now(brasilia_tz)
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

    # ═══════════════════════════════════════════════════════════════
    # ATIVAR ANTI-HIBERNAÇÃO PERMANENTE
    # ═══════════════════════════════════════════════════════════════
    ativar_anti_hibernacao()

    # Iniciar thread que pressiona Shift a cada 3s (anti-hibernação)
    stop_shift_event = iniciar_movimento_mouse_continuo()

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

        # Parar thread de anti-hibernação
        try:
            stop_shift_event.set()
            gui_log("⌨️ [Thread Anti-Hibernação] Parando...")
        except:
            pass

        # Desativar anti-hibernação do Windows
        desativar_anti_hibernacao()

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
