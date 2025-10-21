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
import re
from io import StringIO

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

# Importar pytesseract para OCR (verificação visual)
try:
    import pytesseract
    from PIL import Image, ImageGrab
    PYTESSERACT_DISPONIVEL = True

    # Configurar caminho do tesseract (para .exe standalone OU desenvolvimento)
    tesseract_configurado = False

    # 1. PRIORIDADE: Tesseract na pasta local (junto com o .exe ou script)
    if getattr(sys, 'frozen', False):
        # Executável PyInstaller: pode estar em tesseract/ ou _internal/tesseract/
        base_dir = os.path.dirname(sys.executable)

        # Tentar primeiro em _internal/tesseract/ (PyInstaller modo onedir)
        local_tesseract = os.path.join(base_dir, '_internal', 'tesseract', 'tesseract.exe')
        if not os.path.exists(local_tesseract):
            # Fallback: tentar em tesseract/ direto
            local_tesseract = os.path.join(base_dir, 'tesseract', 'tesseract.exe')
    else:
        # Desenvolvimento: procurar na pasta do script
        local_tesseract = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tesseract', 'tesseract.exe')

    if os.path.exists(local_tesseract):
        pytesseract.pytesseract.tesseract_cmd = local_tesseract
        print(f"[OK] Tesseract LOCAL encontrado: {local_tesseract}")
        tesseract_configurado = True

    # 2. Fallback: Tesseract instalado no sistema
    if not tesseract_configurado:
        # Tentar localização padrão do instalador
        default_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if os.path.exists(default_path):
            pytesseract.pytesseract.tesseract_cmd = default_path
            print(f"[OK] Tesseract SISTEMA encontrado: {default_path}")
            tesseract_configurado = True
        else:
            # Tentar localizar no PATH
            import shutil
            tesseract_cmd = shutil.which('tesseract')
            if tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
                print(f"[OK] Tesseract PATH encontrado: {tesseract_cmd}")
                tesseract_configurado = True

    if not tesseract_configurado:
        print("[WARN] Tesseract-OCR não encontrado!")
        print("[WARN] OCR não funcionará. Copie a pasta 'tesseract' para junto do executável.")
        PYTESSERACT_DISPONIVEL = False
    else:
        print("[OK] pytesseract configurado com sucesso")

except ImportError as e:
    PYTESSERACT_DISPONIVEL = False
    print(f"[WARN] pytesseract não disponível: {e}")
    print("[WARN] Verificação visual por OCR desabilitada")

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

# =================== CONFIGURAÇÕES GLOBAIS ===================
BASE_DIR = Path(__file__).parent.resolve() if not getattr(sys, 'frozen', False) else Path(sys.executable).parent
CONFIG_FILE = BASE_DIR / "config.json"

# Compatibilidade com .exe
base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

# ─── CONFIGURAÇÕES DE MODO ──────────────────────────────────────────────────
# IMPORTANTE: Altere para True para testes, False para PRODUÇÃO
MODO_TESTE = False  # True = simula movimentos sem pyautogui | False = PRODUÇÃO
PARAR_QUANDO_VAZIO = True  # Para quando vazio (TESTE)
SIMULAR_FALHA_SHEETS = False  # True = força falhas para testar retry | False = PRODUÇÃO
LIMITE_ITENS_TESTE = 50  # Limite de itens por ciclo no modo teste
SEM_CTRL_S = True  # NAO executa Ctrl+S (TESTE)

# Controle de execução
_rpa_running = False
_gui_log_callback = None
_ciclo_atual = 0
_data_inicio_ciclo = None
_dados_inseridos_oracle = False  # Rastreia se dados foram inseridos no Oracle neste ciclo

# ─── CACHE LOCAL ANTI-DUPLICAÇÃO (IGUAL AO RPA_ORACLE) ──────────────────────
class CacheLocal:
    """Cache persistente para evitar duplicações no Oracle"""

    def __init__(self, arquivo="cache_teste_ciclo.json"):
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
        gui_log(f"⚠️ [OCR] pytesseract não disponível, pulando verificação de {nome_campo}")
        return (True, "", 0.0)  # Retorna sucesso se OCR não estiver disponível

    screenshot_path = None
    try:
        # Capturar região da tela
        screenshot = ImageGrab.grab(bbox=(x, y, x + largura, y + altura))

        # SEMPRE salvar screenshot em modo TESTE para debug
        if True:  # Forçar salvamento para debug
            screenshot_path = f"debug_ocr_{nome_campo.replace('.', '_').replace(' ', '_')}.png"
            screenshot.save(screenshot_path)
            gui_log(f"[DEBUG] Screenshot salvo: {screenshot_path}")

        # Converter para escala de cinza e aumentar contraste
        from PIL import ImageEnhance
        screenshot = screenshot.convert('L')  # Escala de cinza
        enhancer = ImageEnhance.Contrast(screenshot)
        screenshot = enhancer.enhance(2.0)  # Aumentar contraste

        # Salvar imagem processada também
        if True:
            processed_path = f"debug_ocr_{nome_campo.replace('.', '_').replace(' ', '_')}_processado.png"
            screenshot.save(processed_path)

        # Aplicar OCR com configurações otimizadas
        # --psm 7: linha única de texto
        # --oem 3: usar LSTM + tradicional
        # -c tessedit_char_whitelist: apenas caracteres alfanuméricos
        texto_lido = pytesseract.image_to_string(screenshot, config='--psm 7 --oem 3').strip()

        # Normalizar textos para comparação (remover espaços, converter para maiúsculas)
        texto_lido_norm = texto_lido.replace(" ", "").upper()
        valor_esperado_norm = str(valor_esperado).replace(" ", "").upper()

        # Verificar similaridade
        if texto_lido_norm == valor_esperado_norm:
            gui_log(f"✅ [OCR] {nome_campo}: '{texto_lido}' == '{valor_esperado}' (CORRETO)")
            return (True, texto_lido, 1.0)
        else:
            # Calcular similaridade parcial (porcentagem de caracteres corretos)
            if len(valor_esperado_norm) > 0:
                caracteres_corretos = sum(1 for a, b in zip(texto_lido_norm, valor_esperado_norm) if a == b)
                confianca = caracteres_corretos / len(valor_esperado_norm)
            else:
                confianca = 0.0

            gui_log(f"⚠️ [OCR] {nome_campo}: Esperado '{valor_esperado}', Lido '{texto_lido}' (Similaridade: {confianca*100:.1f}%)")

            # Se similaridade for > 80%, considera aceitável (OCR pode ter pequenos erros)
            if confianca >= 0.8:
                gui_log(f"✅ [OCR] {nome_campo}: Similaridade aceitável ({confianca*100:.1f}% >= 80%)")
                return (True, texto_lido, confianca)
            else:
                return (False, texto_lido, confianca)

    except Exception as e:
        gui_log(f"⚠️ [OCR] Erro ao verificar {nome_campo}: {e}")
        return (True, "", 0.0)  # Em caso de erro, não bloqueia o processamento

def validar_campos_oracle_ocr(coords, item, quantidade, referencia, sub_o, end_o, sub_d, end_d, salvar_debug=False):
    """
    Valida todos os campos do Oracle usando OCR com detecção de headers.
    Captura imagem incluindo headers e valores, localiza headers e busca valores abaixo.

    Args:
        coords: Dicionário com coordenadas dos campos (não usado)
        item, quantidade, referencia, sub_o, end_o, sub_d, end_d: Valores esperados
        salvar_debug: Se True, salva screenshots

    Returns:
        bool: True se todos os campos estão corretos, False caso contrário
    """
    if not PYTESSERACT_DISPONIVEL:
        gui_log("⚠️ [OCR] pytesseract não disponível, pulando validação visual")
        return True

    gui_log("🔍 [OCR] Iniciando validação visual com detecção de headers...")

    try:
        # COORDENADAS DA IMAGEM (headers + valores)
        X_INICIO = 67
        Y_INICIO = 105      # Subiu 35px para pegar headers
        LARGURA_TOTAL = 1236
        ALTURA_TOTAL = 70   # Dobrou: 35px headers + 35px valores

        # Capturar imagem grande
        screenshot = ImageGrab.grab(bbox=(X_INICIO, Y_INICIO, X_INICIO + LARGURA_TOTAL, Y_INICIO + ALTURA_TOTAL))
        screenshot.save("debug_ocr_TODOS_CAMPOS.png")
        gui_log("[DEBUG] Screenshot completo salvo: debug_ocr_TODOS_CAMPOS.png")

        # Processar imagem (escala de cinza + contraste)
        from PIL import ImageEnhance
        screenshot_processado = screenshot.convert('L')
        enhancer = ImageEnhance.Contrast(screenshot_processado)
        screenshot_processado = enhancer.enhance(2.0)
        screenshot_processado.save("debug_ocr_TODOS_CAMPOS_processado.png")

        # OCR com detecção de posição (retorna X, Y, Width, Height de cada palavra)
        import pandas as pd
        ocr_data = pytesseract.image_to_data(screenshot_processado, config='--psm 6', output_type=pytesseract.Output.DICT)

        # Converter para DataFrame para facilitar análise
        df_ocr = pd.DataFrame(ocr_data)
        df_ocr = df_ocr[df_ocr['conf'] != -1]  # Remover linhas vazias
        df_ocr['text'] = df_ocr['text'].str.strip()
        df_ocr = df_ocr[df_ocr['text'] != '']  # Remover textos vazios

        gui_log(f"[OCR] {len(df_ocr)} palavras detectadas")

        # Mapeamento: campo → header no Oracle
        HEADERS_ORACLE = {
            "item": "Item",
            "quantidade": "Quantidade",
            "referencia": "Referência",
            "sub_origem": "Subinvent.",
            "end_origem": "Endereço",
            "sub_destino": "Para Subinv.",
            "end_destino": "Para Loc."
        }

        # Valores esperados (normalizar tudo)
        def normalizar_valor(val):
            """Remove espaços, pontos, vírgulas e converte para maiúsculas"""
            return str(val).upper().replace(" ", "").replace(",", ".").replace(".", "").strip()

        valores_esperados = {
            "item": str(item).upper().strip(),
            "quantidade": str(quantidade).strip(),  # Manter original para quantidade
            "referencia": str(referencia).upper().strip(),
            "sub_origem": str(sub_o).upper().strip(),
            "end_origem": str(end_o).upper().strip(),
        }

        # Se não é COD, adicionar destino
        if not str(referencia).strip().upper().startswith("COD"):
            valores_esperados["sub_destino"] = str(sub_d).upper().strip()
            valores_esperados["end_destino"] = str(end_d).upper().strip()

        # Função auxiliar para busca flexível
        def encontrar_texto(df, texto_busca, tolerancia=0.8):
            """Busca texto com similaridade"""
            from difflib import SequenceMatcher
            texto_busca_norm = texto_busca.upper().replace(" ", "")

            for _, row in df.iterrows():
                texto_lido = str(row['text']).upper().replace(" ", "")
                # Similaridade exata ou parcial
                if texto_busca_norm in texto_lido or texto_lido in texto_busca_norm:
                    return row
                # Similaridade por ratio
                ratio = SequenceMatcher(None, texto_busca_norm, texto_lido).ratio()
                if ratio >= tolerancia:
                    return row
            return None

        # Validar cada campo usando headers como referência
        erros = []
        for campo, valor_esperado in valores_esperados.items():
            header_oracle = HEADERS_ORACLE[campo]

            # Tentar encontrar o header
            header_row = encontrar_texto(df_ocr, header_oracle, tolerancia=0.7)

            if header_row is not None:
                # Header encontrado! Agora buscar valor na mesma coluna (X similar) mas Y abaixo
                header_x = header_row['left']
                header_y = header_row['top']
                header_width = header_row.get('width', 0)

                # Margem mais restrita para quantidade (±20px), outros campos (±30px)
                margem_x = 20 if campo == "quantidade" else 30

                # Procurar textos abaixo do header (Y maior, X próximo)
                valores_abaixo = df_ocr[
                    (df_ocr['top'] > header_y) &
                    (df_ocr['left'].between(header_x - margem_x, header_x + margem_x))
                ]

                # Debug: mostrar o que foi encontrado abaixo do header
                if len(valores_abaixo) > 0:
                    textos_debug = [f"'{t}' (X:{x})" for t, x in zip(valores_abaixo['text'].tolist(), valores_abaixo['left'].tolist())]
                    gui_log(f"[DEBUG] Abaixo de '{header_oracle}' (X:{header_x}): {', '.join(textos_debug[:3])}")

                # Verificar se o valor esperado está nesses textos
                valor_encontrado = False
                for _, val_row in valores_abaixo.iterrows():
                    texto_lido = str(val_row['text']).upper().replace(" ", "")
                    valor_busca = valor_esperado.upper().replace(" ", "")
                    val_x = val_row['left']

                    # Para quantidade: validação EXATA (sem similaridade)
                    if campo == "quantidade":
                        texto_lido_norm = texto_lido.replace(",", "").replace(".", "")
                        valor_busca_norm = valor_busca.replace(",", "").replace(".", "")

                        # Comparação EXATA de números
                        if valor_busca_norm == texto_lido_norm:
                            gui_log(f"✅ [OCR] {campo} ('{valor_esperado}'): encontrado como '{val_row['text']}' (X:{val_x})")
                            valor_encontrado = True
                            break
                    else:
                        # Comparação flexível para outros campos
                        if valor_busca in texto_lido or texto_lido in valor_busca:
                            gui_log(f"✅ [OCR] {campo} ('{valor_esperado}'): encontrado como '{val_row['text']}' (X:{val_x})")
                            valor_encontrado = True
                            break

                        # Similaridade apenas para campos de texto (não quantidade)
                        from difflib import SequenceMatcher
                        ratio = SequenceMatcher(None, valor_busca, texto_lido).ratio()
                        if ratio >= 0.75:
                            gui_log(f"✅ [OCR] {campo} ('{valor_esperado}'): similar a '{val_row['text']}' ({ratio*100:.0f}%) (X:{val_x})")
                            valor_encontrado = True
                            break

                if not valor_encontrado:
                    textos_encontrados = ", ".join([f"'{t}' (X:{x})" for t, x in zip(valores_abaixo['text'].tolist(), valores_abaixo['left'].tolist())])
                    gui_log(f"❌ [OCR] {campo}: esperado '{valor_esperado}', abaixo de '{header_oracle}' (X:{header_x}) encontrei: {textos_encontrados}")
                    erros.append(f"{campo} (esperado: {valor_esperado})")
            else:
                # Header não encontrado, fazer busca geral na imagem (sem log)
                # Busca geral
                encontrado = encontrar_texto(df_ocr, valor_esperado, tolerancia=0.75)
                if encontrado is not None:
                    gui_log(f"✅ [OCR] {campo}: '{valor_esperado}' encontrado")
                else:
                    gui_log(f"❌ [OCR] {campo}: '{valor_esperado}' NÃO encontrado")
                    erros.append(f"{campo} (esperado: {valor_esperado})")

        # Resultado final
        if erros:
            gui_log(f"❌ [OCR] Validação FALHOU. {len(erros)} campo(s) com problema:")
            for erro in erros:
                gui_log(f"   - {erro}")
            # Mostrar todo texto lido para debug
            todos_textos = " | ".join(df_ocr['text'].tolist())
            gui_log(f"[OCR] Todos textos lidos: {todos_textos}")
            return False
        else:
            gui_log("✅ [OCR] Validação visual OK - Todos os campos validados!")
            return True

    except Exception as e:
        gui_log(f"⚠️ [OCR] Erro na validação: {e}")
        import traceback
        gui_log(traceback.format_exc())
        return True  # Em caso de erro, não bloqueia

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

def aguardar_com_pausa(segundos, mensagem="Aguardando"):
    """Aguarda um tempo com possibilidade de interrupção"""
    gui_log(f"⏳ {mensagem} ({segundos}s)...")
    inicio = time.time()
    while time.sleep(0.5) or time.time() - inicio < segundos:
        if not _rpa_running:
            return False
    return True

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
        SPREADSHEET_ID = "147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY"  # PLANILHA TESTE
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

        # Coordenadas dos campos no Oracle
        coords = {
            "item": (101, 156),
            "sub_origem": (257, 159),
            "end_origem": (335, 159),
            "sub_destino": (485, 159),
            "end_destino": (553, 159),
            "quantidade": (672, 159),
            "Referencia": (768, 159),
        }

        # Loop de espera até encontrar pelo menos 1 item para processar
        itens_processados = 0
        tentativas_verificacao = 0
        MAX_TENTATIVAS_PRIMEIRO_CICLO = 2  # Apenas 2 tentativas no primeiro ciclo

        while itens_processados == 0 and _rpa_running:
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
            # 🔒 TRAVA 4: Ignorar linhas com "PROCESSANDO..." (Lock temporário)
            linhas_processar = []
            for i, row in enumerate(dados):
                if len(row) < len(headers):
                    row += [''] * (len(headers) - len(row))
                idx_status_oracle = headers.index("Status Oracle")
                idx_status = headers.index("Status")
                status_oracle = row[idx_status_oracle].strip()
                status = row[idx_status].strip().upper()

                # Só processa se Status Oracle estiver VAZIO (não "PROCESSANDO...", não "Concluído", etc)
                # E Status contém "CONCLUÍDO"
                if status_oracle == "" and "CONCLUÍDO" in status:
                    linhas_processar.append((i + 2, dict(zip(headers, row))))

            if not linhas_processar:
                gui_log(f"⏳ Nenhuma linha nova para processar (verificação #{tentativas_verificacao})")

                # LÓGICA DIFERENTE PARA PRIMEIRO CICLO
                if primeiro_ciclo and tentativas_verificacao >= MAX_TENTATIVAS_PRIMEIRO_CICLO:
                    gui_log(f"✅ Primeiro ciclo: Após {MAX_TENTATIVAS_PRIMEIRO_CICLO} tentativas sem itens, prosseguindo para Bancada")

                    # ⚡ CLICAR NO BOTÃO PARA PREPARAR FECHAMENTO
                    # Clicar no botão (330, 66) para preparar o Oracle para fechamento
                    gui_log("🖱️ Clicando no botão de preparação (330, 66)...")
                    if not MODO_TESTE:
                        pyautogui.click(330, 66)
                        time.sleep(1.0)
                    else:
                        gui_log("[MODO TESTE] Simulando clique no botão")

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

                # ✅ VERIFICAR CACHE ANTI-DUPLICAÇÃO
                if cache.ja_processado(id_linha):
                    gui_log(f"⏭️ Linha {i} (ID: {id_linha}) já processada anteriormente. Pulando.")
                    continue

                # 🔒 TRAVA 4: LOCK TEMPORÁRIO - Marcar como "PROCESSANDO..." antes de processar
                # Isso evita que outras instâncias peguem a mesma linha
                try:
                    idx_status_oracle = headers.index("Status Oracle")
                    coluna_letra = indice_para_coluna(idx_status_oracle)
                    range_str = f"{SHEET_NAME}!{coluna_letra}{i}"

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

                # REGRA 1: Validar quantidade = 0
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
                    if qtd_float < 0:
                        continue
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

                # 🔒 TRAVA 5: TIMEOUT DE SEGURANÇA - Registrar início do processamento
                inicio_processamento = time.time()
                TIMEOUT_PROCESSAMENTO = 60  # 60 segundos por linha

                if MODO_TESTE:
                    gui_log("[MODO TESTE] Simulando preenchimento no Oracle (sem pyautogui)...")
                    time.sleep(0.5)  # Simula tempo de preenchimento
                else:
                    # Preencher Oracle
                    pyautogui.click(coords["item"])
                    pyautogui.press("delete")
                    pyautogui.write(item)
                    pyautogui.press("tab")
                    time.sleep(1)

                    pyautogui.click(coords["Referencia"])
                    pyautogui.write(referencia)
                    time.sleep(1)

                    pyautogui.click(coords["sub_origem"])
                    pyautogui.write(sub_o)
                    pyautogui.press("tab")
                    time.sleep(1)

                    pyautogui.press("delete")
                    pyautogui.click(coords["end_origem"])
                    pyautogui.write(end_o)
                    pyautogui.press("tab")
                    time.sleep(1)

                    # Se referência começa com "COD", pula destino
                    if str(referencia).strip().upper().startswith("COD"):
                        pyautogui.press("tab")
                        time.sleep(1)
                        pyautogui.press("tab")
                        time.sleep(1)
                    else:
                        pyautogui.press("delete")
                        pyautogui.click(coords["sub_destino"])
                        pyautogui.write(sub_d)
                        pyautogui.press("tab")
                        time.sleep(1)

                        pyautogui.press("delete")
                        pyautogui.click(coords["end_destino"])
                        pyautogui.write(end_d)
                        pyautogui.press("tab")
                        time.sleep(1)

                    pyautogui.press("delete")
                    pyautogui.click(coords["quantidade"])
                    pyautogui.write(quantidade)
                    time.sleep(1)

                    # ═══════════════════════════════════════════════════════════════
                    # 🔒 TRAVAS DE VALIDAÇÃO ANTES DO Ctrl+S
                    # ═══════════════════════════════════════════════════════════════

                    # 🔒 TRAVA 5: Verificar TIMEOUT
                    tempo_decorrido = time.time() - inicio_processamento
                    if tempo_decorrido > TIMEOUT_PROCESSAMENTO:
                        gui_log(f"⏱️ [TIMEOUT] Linha {i} demorou {tempo_decorrido:.1f}s (limite: {TIMEOUT_PROCESSAMENTO}s)")
                        gui_log(f"⚠️ [TIMEOUT] Abortando processamento da linha {i} por segurança")
                        # Reverter lock
                        try:
                            service.spreadsheets().values().update(
                                spreadsheetId=SPREADSHEET_ID,
                                range=range_str,
                                valueInputOption="RAW",
                                body={"values": [["TIMEOUT - Verificar manualmente"]]}
                            ).execute()
                        except:
                            pass
                        continue  # Pula para próxima linha

                    # 🔒 TRAVA 3: Validação de consistência dos dados digitados
                    # Verificar se campos obrigatórios não estão vazios (dupla verificação)
                    gui_log("🔍 [VALIDAÇÃO] Verificando consistência dos dados antes do Ctrl+S...")

                    # Validar quantidade (não pode ser negativa ou zero após processamento)
                    try:
                        qtd_float = float(str(quantidade).replace(",", ".").replace(" ", ""))
                        if qtd_float <= 0:
                            gui_log(f"⚠️ [VALIDAÇÃO] Quantidade inválida detectada: {quantidade}")
                            gui_log(f"⚠️ [VALIDAÇÃO] Abortando Ctrl+S para linha {i}")
                            # Reverter lock
                            try:
                                service.spreadsheets().values().update(
                                    spreadsheetId=SPREADSHEET_ID,
                                    range=range_str,
                                    valueInputOption="RAW",
                                    body={"values": [["Quantidade inválida"]]}
                                ).execute()
                            except:
                                pass
                            continue
                    except ValueError:
                        gui_log(f"⚠️ [VALIDAÇÃO] Quantidade não numérica: {quantidade}")
                        continue

                    # Validar que campos críticos não estão vazios
                    if not item.strip() or not sub_o.strip() or not end_o.strip():
                        gui_log(f"⚠️ [VALIDAÇÃO] Campos críticos vazios detectados antes do Ctrl+S")
                        continue

                    # Se não é COD, validar destino também
                    if not str(referencia).strip().upper().startswith("COD"):
                        if not sub_d.strip() or not end_d.strip():
                            gui_log(f"⚠️ [VALIDAÇÃO] Campos de destino vazios (não é COD)")
                            continue

                    gui_log("✅ [VALIDAÇÃO] Todos os dados estão consistentes. Prosseguindo com Ctrl+S...")

                    # 🔒 TRAVA 2: Verificação visual na tela com OCR
                    gui_log("👁️ [VISUAL] Iniciando verificação visual com OCR...")
                    time.sleep(0.5)  # Pausa breve para estabilização da tela

                    # Validar campos usando OCR
                    ocr_ok = validar_campos_oracle_ocr(
                        coords, item, quantidade, referencia,
                        sub_o, end_o, sub_d, end_d
                    )

                    if not ocr_ok:
                        gui_log("❌ [OCR] Validação visual falhou! Abortando Ctrl+S")
                        # Reverter lock
                        try:
                            service.spreadsheets().values().update(
                                spreadsheetId=SPREADSHEET_ID,
                                range=range_str,
                                valueInputOption="RAW",
                                body={"values": [["OCR - Dados não conferem"]]}
                            ).execute()
                        except:
                            pass
                        continue  # Pula para próxima linha

                    # ═══════════════════════════════════════════════════════════════
                    # ✅ TODAS AS VALIDAÇÕES PASSARAM - EXECUTAR Ctrl+S
                    # ═══════════════════════════════════════════════════════════════

                    # Salvar (Ctrl+S) - com flag de teste
                    if globals().get('SEM_CTRL_S', False):
                        gui_log("[TESTE] Ctrl+S SIMULADO (nao executado)")
                        time.sleep(1)

                        # No modo TESTE, limpar o formulário após processar
                        gui_log("🧹 [TESTE] Limpando formulário...")
                        # Coordenadas do botão Limpar (tela_06_limpar do config.json)
                        if not MODO_TESTE:
                            pyautogui.click(332, 66)  # Botão Limpar
                            time.sleep(1.5)
                        else:
                            gui_log("[MODO TESTE] Simulando clique no botão Limpar")
                    else:
                        gui_log("💾 [CTRL+S] Executando salvamento no Oracle...")
                        pyautogui.hotkey("ctrl", "s")
                        gui_log("⏳ Aguardando Oracle salvar...")
                        time.sleep(3)

                    gui_log("⏳ Inicio inserção no cache...")

                # ✅ GRAVAR NO CACHE (APÓS Ctrl+S, ANTES de tentar Sheets)
                sucesso_cache = cache.adicionar(
                    id_item=id_linha,
                    linha_atual=i,
                    item=item,
                    quantidade=quantidade,
                    referencia=referencia,
                    status="pendente"
                )
                if sucesso_cache:
                    gui_log(f"💾 Registrado no cache: {id_linha}")
                else:
                    gui_log(f"⚠️ Falha ao registrar no cache (ID vazio?)")

                # Atualizar Google Sheets
                try:
                    service.spreadsheets().values().update(
                        spreadsheetId=SPREADSHEET_ID,
                        range=f"{SHEET_NAME}!T{i}",
                        valueInputOption="RAW",
                        body={"values": [["Processo Oracle Concluído"]]}
                    ).execute()

                    # ✅ Marcar como concluído no cache
                    cache.marcar_concluido(id_linha)
                    gui_log(f"✅ Linha {i} processada e salva no Oracle")
                except Exception as err:
                    gui_log(f"⚠️ Falha ao atualizar Sheets: {err}. Retry em background...")

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

    NOVO FLUXO SIMPLIFICADO:
    - Se inseriu dados: limpar + fechar 2 X
    - Se NÃO inseriu: apenas fechar 2 X
    - Depois abrir Bancada
    """
    global _dados_inseridos_oracle

    gui_log("📋 ETAPA 6: Fechamento de modais e abertura da Bancada")

    tempo_espera = config["tempos_espera"]["entre_cliques"]

    # Verificar se dados foram inseridos no Oracle
    if _dados_inseridos_oracle:
        gui_log("🧹 Dados foram inseridos - Limpando formulário primeiro...")

        # 1. Limpar formulário (botão Limpar)
        coord = config["coordenadas"]["tela_06_limpar"]
        clicar_coordenada(coord["x"], coord["y"], descricao=coord["descricao"])

        if not aguardar_com_pausa(tempo_espera, "Aguardando limpeza"):
            return False
    else:
        gui_log("ℹ️ Nenhum dado foi inserido - Fechando modais diretamente...")

    # 2. Fechar janela "Subinventory Transfer (BC2)" - Botão X
    gui_log("🔴 Fechando 'Subinventory Transfer (BC2)'...")
    coord = config["coordenadas"]["tela_06_fechar_subinventory_transfer"]
    clicar_coordenada(coord["x"], coord["y"], descricao=coord["descricao"])

    if not aguardar_com_pausa(tempo_espera, "Aguardando fechar primeira janela"):
        return False

    # 3. Fechar janela "Transferencia do Subinventario (BC2)" - Botão X
    gui_log("🔴 Fechando 'Transferencia do Subinventario (BC2)'...")
    coord = config["coordenadas"]["tela_06_fechar_transferencia_subinventario_bc2"]
    clicar_coordenada(coord["x"], coord["y"], descricao=coord["descricao"])

    if not aguardar_com_pausa(tempo_espera, "Aguardando fechar segunda janela"):
        return False

    # 4. Clicar em "Janela" para dar foco
    gui_log("🖱️ Clicando em 'Janela'...")
    coord = config["coordenadas"]["navegador_janela"]
    clicar_coordenada(coord["x"], coord["y"], descricao=coord["descricao"])

    if not aguardar_com_pausa(tempo_espera, "Aguardando foco na janela"):
        return False

    # 5. Clicar no menu de navegação
    gui_log("🖱️ Clicando no menu de navegação...")
    coord = config["coordenadas"]["navegador_menu"]
    clicar_coordenada(coord["x"], coord["y"], descricao=coord["descricao"])

    if not aguardar_com_pausa(tempo_espera, "Aguardando menu navegação"):
        return False

    # 6. Duplo clique para abrir a bancada
    gui_log("📂 Abrindo Bancada de Material...")
    coord = config["coordenadas"]["tela_07_bancada_material"]
    duplo_clique = coord.get("duplo_clique", False)
    clicar_coordenada(coord["x"], coord["y"], duplo=duplo_clique, descricao=coord["descricao"])

    tempo_espera = config["tempos_espera"]["apos_modal"]
    return aguardar_com_pausa(tempo_espera, "Aguardando abertura da Bancada")

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

    while (time.time() - inicio) < max_tempo:
        if not _rpa_running:
            gui_log("⏸️ Monitoramento cancelado pelo usuário")
            return ""

        verificacoes += 1
        tempo_decorrido = int(time.time() - inicio)

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
        if not aguardar_com_pausa(120, "Carregamento da grid (2 minutos)"):
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

        texto_copiado = monitorar_clipboard_inteligente(
            max_tempo=15 * 60,        # Máximo 15 minutos
            intervalo_check=3,        # Verificar a cada 3 segundos (mais rápido)
            estabilidade_segundos=30  # Considerar completo após 30s sem mudança
        )

        if not texto_copiado or len(texto_copiado) < 50:
            gui_log("❌ ERRO: Clipboard vazio após todas as tentativas")
            gui_log("💡 O Oracle pode não ter conseguido copiar os dados")
            gui_log("💡 Verifique se a grid tem dados e tente novamente")
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

        tempo_espera = config["tempos_espera"]["apos_rpa_bancada"]
        return aguardar_com_pausa(tempo_espera, "Aguardando estabilização")

    except Exception as e:
        gui_log("=" * 60)
        gui_log(f"❌ ERRO ao extrair dados da Bancada: {e}")
        gui_log("=" * 60)
        import traceback
        gui_log(traceback.format_exc())

        # Não falhar o ciclo por causa disso
        tempo_espera = config["tempos_espera"]["apos_rpa_bancada"]
        return aguardar_com_pausa(tempo_espera, "Aguardando estabilização")


def etapa_08_fechar_bancada(config):
    """Etapa 8: Fechar a janela da Bancada"""
    gui_log("📋 ETAPA 8: Fechamento da Bancada")

    coord = config["coordenadas"]["tela_08_fechar_bancada"]
    clicar_coordenada(coord["x"], coord["y"], descricao=coord["descricao"])

    tempo_espera = config["tempos_espera"]["entre_cliques"]
    return aguardar_com_pausa(tempo_espera, "Aguardando fechamento")

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
    global _rpa_running, _ciclo_atual
    _rpa_running = True

    gui_log("=" * 60)
    gui_log("🤖 RPA CICLO - Iniciado")
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

            while _rpa_running:
                # Executar ciclo
                sucesso = executar_ciclo_completo(config)

                if sucesso:
                    gui_log("✅ Ciclo concluído com sucesso! Iniciando próximo ciclo...")

                    # Pequena pausa de 5 segundos entre ciclos para estabilização
                    if not aguardar_com_pausa(5, "Pausa entre ciclos"):
                        break
                else:
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
