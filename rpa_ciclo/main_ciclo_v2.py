# -*- coding: utf-8 -*-
"""
RPA CICLO V2 - Orquestração Oracle + Bancada
Implementa lógica de espera inteligente e retry automático
"""

import json
import os
import sys
import time
import subprocess
import threading
from pathlib import Path
from datetime import datetime
import pyautogui
import logging

# Configurar encoding UTF-8 para o console Windows
if sys.platform.startswith('win'):
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass

# Importar módulo Google Sheets
try:
    from google_sheets_ciclo import registrar_ciclo, atualizar_ciclo
    GOOGLE_SHEETS_DISPONIVEL = True
except ImportError:
    GOOGLE_SHEETS_DISPONIVEL = False
    print("⚠️ Google Sheets não disponível")

# =================== CONFIGURAÇÕES GLOBAIS ===================
BASE_DIR = Path(__file__).parent.resolve() if not getattr(sys, 'frozen', False) else Path(sys.executable).parent
CONFIG_FILE = BASE_DIR / "config.json"

# Compatibilidade com .exe
base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

# ─── CONFIGURAÇÕES DE MODO TESTE ─────────────────────────────────────────────
MODO_TESTE = False  # True = simula movimentos sem pyautogui | False = PRODUÇÃO
PARAR_QUANDO_VAZIO = False  # True = para quando vazio (teste) | False = continua rodando (PRODUÇÃO)
MAX_TENTATIVAS_BANCADA = 3  # Número de tentativas para envio da Bancada

# Controle de execução
_rpa_running = False
_gui_log_callback = None
_ciclo_atual = 0
_data_inicio_ciclo = None
_primeira_verificacao_oracle = True  # Flag para primeira verificação
_ja_processou_algum_item = False  # Flag para saber se já processou algum item no Oracle

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

# =================== FUNÇÕES DE AUTOMAÇÃO ===================
def clicar_coordenada(x, y, duplo=False, descricao=""):
    """Clica em uma coordenada específica na tela"""
    if descricao:
        gui_log(f"🖱️ {descricao}")

    if MODO_TESTE:
        gui_log(f"[MODO TESTE] Simulando clique em ({x}, {y})")
        time.sleep(0.2)
        return

    pyautogui.moveTo(x, y, duration=0.8)
    time.sleep(0.5)

    if duplo:
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
    while time.time() - inicio < segundos:
        if not _rpa_running:
            return False
        time.sleep(0.5)
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

    # Navegar com setas para baixo (9x) + Enter
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

def etapa_05_executar_rpa_oracle(config):
    """
    Etapa 5: Processar linhas do Google Sheets no Oracle

    LÓGICA DE ESPERA:
    - Se nunca processou nenhum item: aguarda até fazer pelo menos 1 + 30s
    - Se não tem nada a fazer:
      - Primeira verificação: pode seguir
      - Segunda verificação (já processou tudo): aguarda até fazer 1 + 30s
    """
    global _primeira_verificacao_oracle, _ja_processou_algum_item

    gui_log("🤖 ETAPA 5: Processamento no Oracle")

    try:
        # Importar Google Sheets
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        # Autenticar Google Sheets
        SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
        SPREADSHEET_ID = "147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY"  # PLANILHA MODO TESTE ORACLE
        SHEET_NAME = "Separação"

        # Usar o mesmo diretório que o RPA_Oracle para compartilhar token
        rpa_oracle_dir = BASE_DIR.parent / "rpa_oracle"
        token_path = rpa_oracle_dir / "token.json"
        creds_path = os.path.join(base_path, "CredenciaisOracle.json")

        creds = None
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, "w") as token:
                token.write(creds.to_json())

        service = build("sheets", "v4", credentials=creds)

        # Inicializar cache anti-duplicação (usar o cache do RPA_Oracle)
        sys.path.insert(0, str(rpa_oracle_dir))
        try:
            # Importar o RPA_Oracle para usar a mesma classe CacheLocal
            import importlib.util
            spec = importlib.util.spec_from_file_location("rpa_oracle", rpa_oracle_dir / "RPA_Oracle.py")
            rpa_oracle_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(rpa_oracle_module)
            CacheLocal = rpa_oracle_module.CacheLocal
        except Exception as e:
            gui_log(f"⚠️ Erro ao importar CacheLocal do RPA_Oracle: {e}")
            gui_log("⚠️ Usando implementação local do cache")
            # Fallback para implementação local
            class CacheLocal:
                def __init__(self, arquivo="processados.json"):
                    self.arquivo = rpa_oracle_dir / arquivo
                    self.dados = self._carregar()
                    self.lock = threading.Lock()
                    if not self.arquivo.exists() and not self.dados:
                        self._salvar()

                def _carregar(self):
                    if self.arquivo.exists():
                        try:
                            with open(self.arquivo, 'r', encoding='utf-8') as f:
                                return json.load(f)
                        except Exception as e:
                            gui_log(f"Erro ao carregar cache: {e}")
                            return {}
                    return {}

                def _salvar(self):
                    try:
                        json_str = json.dumps(self.dados, indent=2, ensure_ascii=False)
                        temp_arquivo = str(self.arquivo) + ".tmp"
                        with open(temp_arquivo, 'w', encoding='utf-8') as f:
                            f.write(json_str)
                            f.flush()
                            os.fsync(f.fileno())
                        if self.arquivo.exists():
                            os.replace(temp_arquivo, str(self.arquivo))
                        else:
                            os.rename(temp_arquivo, str(self.arquivo))
                    except Exception as e:
                        gui_log(f"[ERRO] Falha ao salvar cache: {e}")

                def ja_processado(self, id_item):
                    with self.lock:
                        return id_item in self.dados

                def adicionar(self, id_item, linha_atual, item, quantidade, referencia, status="pendente"):
                    if not id_item or str(id_item).strip() == "":
                        gui_log(f"[ERRO CACHE] ID vazio! Linha: {linha_atual}")
                        return False

                    dados_item = {
                        "linha_atual": linha_atual,
                        "item": item,
                        "quantidade": quantidade,
                        "referencia": referencia,
                        "timestamp_processamento": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "status_sheets": status
                    }

                    with self.lock:
                        self.dados[id_item] = dados_item

                    self._salvar()
                    return True

                def marcar_concluido(self, id_item):
                    removido = False
                    with self.lock:
                        if id_item in self.dados:
                            del self.dados[id_item]
                            removido = True

                    if removido:
                        self._salvar()

                    return removido

        cache = CacheLocal("processados.json")
        gui_log(f"💾 Cache carregado: {len(cache.dados)} itens processados anteriormente")

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

        # ═══════════════════════════════════════════════════════════════
        # LÓGICA DE ESPERA INTELIGENTE
        # ═══════════════════════════════════════════════════════════════

        itens_processados_nesta_execucao = 0

        while _rpa_running:
            # Buscar linhas para processar
            res = service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{SHEET_NAME}!A1:AC"
            ).execute()

            valores = res.get("values", [])
            if not valores:
                gui_log("⚠️ Nenhuma linha encontrada no Google Sheets")
                if not aguardar_com_pausa(30, "Aguardando novas linhas"):
                    return False
                continue

            headers, dados = valores[0], valores[1:]

            # Filtrar linhas para processar (Status = "CONCLUÍDO" e Status Oracle vazio)
            linhas_processar = []
            for i, row in enumerate(dados):
                if len(row) < len(headers):
                    row += [''] * (len(headers) - len(row))

                try:
                    idx_status_oracle = headers.index("Status Oracle")
                    idx_status = headers.index("Status")
                    idx_id = headers.index("ID")
                except ValueError as e:
                    gui_log(f"❌ Coluna não encontrada: {e}")
                    return False

                status_oracle = row[idx_status_oracle].strip() if idx_status_oracle < len(row) else ""
                status = row[idx_status].strip().upper() if idx_status < len(row) else ""
                id_item = row[idx_id].strip() if idx_id < len(row) else ""

                # Verificar se já está no cache
                if id_item and cache.ja_processado(id_item):
                    continue

                # Dupla proteção: Status Oracle vazio E Status CONCLUÍDO
                if status_oracle == "" and "CONCLUÍDO" in status:
                    linhas_processar.append((i + 2, dict(zip(headers, row))))

            # ═══════════════════════════════════════════════════════════════
            # DECISÃO DE ESPERA BASEADA NA LÓGICA SOLICITADA
            # ═══════════════════════════════════════════════════════════════

            if not linhas_processar:
                gui_log(f"📊 Nenhuma linha nova encontrada")

                # CASO 1: Nunca processou nenhum item ainda
                if not _ja_processou_algum_item:
                    gui_log("⏳ Primeira execução sem itens - Aguardando até processar pelo menos 1 item...")
                    if not aguardar_com_pausa(30, "Aguardando novos itens"):
                        return False
                    continue

                # CASO 2: Primeira verificação sem itens (mas já processou antes)
                if _primeira_verificacao_oracle:
                    gui_log("✅ Primeira verificação sem itens - Pode seguir!")
                    _primeira_verificacao_oracle = False
                    break

                # CASO 3: Segunda verificação sem itens (já processou tudo)
                gui_log("⏳ Segunda verificação sem itens - Aguardando até processar pelo menos 1 item + 30s...")

                # Aguardar até processar pelo menos 1 item
                aguardando_novo_item = True
                while aguardando_novo_item and _rpa_running:
                    if not aguardar_com_pausa(30, "Verificando novos itens"):
                        return False

                    # Verificar novamente
                    res = service.spreadsheets().values().get(
                        spreadsheetId=SPREADSHEET_ID,
                        range=f"{SHEET_NAME}!A1:AC"
                    ).execute()

                    valores = res.get("values", [])
                    if valores:
                        headers, dados = valores[0], valores[1:]
                        linhas_temp = []

                        for i, row in enumerate(dados):
                            if len(row) < len(headers):
                                row += [''] * (len(headers) - len(row))

                            idx_status_oracle = headers.index("Status Oracle")
                            idx_status = headers.index("Status")
                            idx_id = headers.index("ID")

                            status_oracle = row[idx_status_oracle].strip() if idx_status_oracle < len(row) else ""
                            status = row[idx_status].strip().upper() if idx_status < len(row) else ""
                            id_item = row[idx_id].strip() if idx_id < len(row) else ""

                            if id_item and cache.ja_processado(id_item):
                                continue

                            if status_oracle == "" and "CONCLUÍDO" in status:
                                linhas_temp.append((i + 2, dict(zip(headers, row))))

                        if linhas_temp:
                            linhas_processar = linhas_temp
                            aguardando_novo_item = False
                            gui_log(f"✅ Encontrado {len(linhas_processar)} novo(s) item(ns)!")

                # Se saiu do loop por interrupção
                if not _rpa_running:
                    return False

            # ═══════════════════════════════════════════════════════════════
            # PROCESSAR LINHAS
            # ═══════════════════════════════════════════════════════════════

            if linhas_processar:
                gui_log(f"📋 Processando {len(linhas_processar)} linha(s)...")

                for idx, (i, linha) in enumerate(linhas_processar, 1):
                    if not _rpa_running:
                        return False

                    try:
                        # Extrair dados
                        id_item = linha.get("ID", "").strip()
                        item = linha.get("Item", "")
                        sub_o = linha.get("Sub.Origem", "")
                        end_o = linha.get("End. Origem", "")
                        sub_d = linha.get("Sub. Destino", "")
                        end_d = linha.get("End. Destino", "")
                        quantidade = linha.get("Quantidade", "")
                        referencia = linha.get("Cód Referencia", "")

                        # Validar ID
                        if not id_item:
                            gui_log(f"⚠️ Linha {i} - ID vazio. Pulando.")
                            continue

                        # Verificar cache novamente
                        if cache.ja_processado(id_item):
                            gui_log(f"⏭️ Linha {i} (ID: {id_item}) já processada. Pulando.")
                            continue

                        # ═══════════════════════════════════════════════════════════════
                        # VALIDAÇÕES (mesmas do RPA_Oracle)
                        # ═══════════════════════════════════════════════════════════════

                        # REGRA 1: Quantidade Zero
                        try:
                            qtd_float = float(str(quantidade).replace(",", ".").replace(" ", ""))
                            if qtd_float == 0:
                                idx_status_oracle = headers.index("Status Oracle")
                                coluna_letra = chr(65 + idx_status_oracle) if idx_status_oracle < 26 else chr(65 + idx_status_oracle // 26 - 1) + chr(65 + idx_status_oracle % 26)
                                service.spreadsheets().values().update(
                                    spreadsheetId=SPREADSHEET_ID,
                                    range=f"{SHEET_NAME}!{coluna_letra}{i}",
                                    valueInputOption="RAW",
                                    body={"values": [["Quantidade Zero"]]}
                                ).execute()
                                gui_log(f"⚠️ Linha {i} - Quantidade Zero. Marcada.")
                                continue
                            elif qtd_float < 0:
                                gui_log(f"⚠️ Linha {i} - Quantidade negativa. Pulando.")
                                continue
                        except ValueError:
                            gui_log(f"⚠️ Linha {i} - Quantidade inválida. Pulando.")
                            continue

                        # REGRA 3: Campos vazios
                        campos_obrigatorios = {
                            "ITEM": item,
                            "SUB. ORIGEM": sub_o,
                            "END. ORIGEM": end_o,
                            "SUB. DESTINO": sub_d,
                            "END. DESTINO": end_d
                        }

                        # Se for COD, não precisa verificar destino
                        if str(referencia).strip().upper().startswith("COD"):
                            campos_obrigatorios = {
                                "ITEM": item,
                                "SUB. ORIGEM": sub_o,
                                "END. ORIGEM": end_o
                            }

                        campos_vazios = [nome for nome, valor in campos_obrigatorios.items() if not valor or str(valor).strip() == ""]
                        if campos_vazios:
                            idx_status_oracle = headers.index("Status Oracle")
                            coluna_letra = chr(65 + idx_status_oracle) if idx_status_oracle < 26 else chr(65 + idx_status_oracle // 26 - 1) + chr(65 + idx_status_oracle % 26)
                            service.spreadsheets().values().update(
                                spreadsheetId=SPREADSHEET_ID,
                                range=f"{SHEET_NAME}!{coluna_letra}{i}",
                                valueInputOption="RAW",
                                body={"values": [["Campo vazio encontrado"]]}
                            ).execute()
                            gui_log(f"⚠️ Linha {i} - Campos vazios: {', '.join(campos_vazios)}. Marcada.")
                            continue

                        # REGRA 2 e 4: Transações não autorizadas
                        subinvs_restritos = ["RAWINDIR", "RAWMANUT", "RAWWAFIFE"]
                        sub_o_upper = str(sub_o).strip().upper()
                        sub_d_upper = str(sub_d).strip().upper()

                        # REGRA 2
                        if sub_o_upper in subinvs_restritos and sub_d_upper == "RAWCENTR":
                            idx_status_oracle = headers.index("Status Oracle")
                            coluna_letra = chr(65 + idx_status_oracle) if idx_status_oracle < 26 else chr(65 + idx_status_oracle // 26 - 1) + chr(65 + idx_status_oracle % 26)
                            service.spreadsheets().values().update(
                                spreadsheetId=SPREADSHEET_ID,
                                range=f"{SHEET_NAME}!{coluna_letra}{i}",
                                valueInputOption="RAW",
                                body={"values": [["Transação não autorizada"]]}
                            ).execute()
                            gui_log(f"⚠️ Linha {i} - Transação não autorizada: {sub_o} → {sub_d}. Marcada.")
                            continue

                        # REGRA 4
                        if sub_o_upper in subinvs_restritos and sub_o_upper == sub_d_upper:
                            idx_status_oracle = headers.index("Status Oracle")
                            coluna_letra = chr(65 + idx_status_oracle) if idx_status_oracle < 26 else chr(65 + idx_status_oracle // 26 - 1) + chr(65 + idx_status_oracle % 26)
                            service.spreadsheets().values().update(
                                spreadsheetId=SPREADSHEET_ID,
                                range=f"{SHEET_NAME}!{coluna_letra}{i}",
                                valueInputOption="RAW",
                                body={"values": [["Transação não autorizada"]]}
                            ).execute()
                            gui_log(f"⚠️ Linha {i} - Transação não autorizada (mesmo subinv): {sub_o} → {sub_d}. Marcada.")
                            continue

                        gui_log(f"▶ Linha {i} ({idx}/{len(linhas_processar)}): ID={id_item} | Item={item} | Qtd={quantidade}")

                        # ═══════════════════════════════════════════════════════════════
                        # PREENCHER ORACLE
                        # ═══════════════════════════════════════════════════════════════

                        if MODO_TESTE:
                            gui_log("[MODO TESTE] Simulando preenchimento no Oracle...")
                            time.sleep(0.5)
                        else:
                            # Preencher Item
                            pyautogui.click(coords["item"])
                            time.sleep(0.3)
                            pyautogui.press("delete")
                            time.sleep(0.2)
                            pyautogui.write(item)
                            time.sleep(0.2)
                            pyautogui.press("tab")
                            time.sleep(1)

                            # Preencher Referência
                            pyautogui.click(coords["Referencia"])
                            pyautogui.write(referencia)
                            pyautogui.press("tab")
                            time.sleep(1)

                            # Preencher Sub Origem
                            pyautogui.click(coords["sub_origem"])
                            time.sleep(0.2)
                            pyautogui.write(sub_o)
                            pyautogui.press("tab")
                            time.sleep(1)

                            # Preencher End Origem
                            pyautogui.press("delete")
                            pyautogui.click(coords["end_origem"])
                            time.sleep(0.2)
                            pyautogui.write(end_o)
                            pyautogui.press("tab")
                            time.sleep(1)

                            # Se referência começa com "COD", pula destino
                            if str(referencia).strip().upper().startswith("COD"):
                                gui_log(f"[COD] Referência '{referencia}' - Pulando campos destino")
                                pyautogui.press("tab")
                                time.sleep(1)
                                pyautogui.press("tab")
                                time.sleep(1)
                            else:
                                # Preencher Sub Destino
                                pyautogui.press("delete")
                                pyautogui.click(coords["sub_destino"])
                                time.sleep(0.2)
                                pyautogui.write(sub_d)
                                pyautogui.press("tab")
                                time.sleep(1)

                                # Preencher End Destino
                                pyautogui.press("delete")
                                pyautogui.click(coords["end_destino"])
                                time.sleep(0.2)
                                pyautogui.write(end_d)
                                pyautogui.press("tab")
                                time.sleep(1)

                            # Preencher Quantidade
                            pyautogui.press("delete")
                            pyautogui.click(coords["quantidade"])
                            time.sleep(0.2)
                            pyautogui.write(quantidade)
                            time.sleep(1)

                            # Salvar (Ctrl+S)
                            gui_log("💾 Salvando no Oracle (Ctrl+S)...")
                            pyautogui.hotkey("ctrl", "s")
                            time.sleep(1.5)

                        # ═══════════════════════════════════════════════════════════════
                        # GRAVAR NO CACHE
                        # ═══════════════════════════════════════════════════════════════

                        cache.adicionar(
                            id_item=id_item,
                            linha_atual=i,
                            item=item,
                            quantidade=quantidade,
                            referencia=referencia,
                            status="pendente"
                        )
                        gui_log(f"💾 ID {id_item} registrado no cache")

                        # ═══════════════════════════════════════════════════════════════
                        # ATUALIZAR GOOGLE SHEETS
                        # ═══════════════════════════════════════════════════════════════

                        try:
                            idx_status_oracle = headers.index("Status Oracle")
                            coluna_letra = chr(65 + idx_status_oracle) if idx_status_oracle < 26 else chr(65 + idx_status_oracle // 26 - 1) + chr(65 + idx_status_oracle % 26)

                            service.spreadsheets().values().update(
                                spreadsheetId=SPREADSHEET_ID,
                                range=f"{SHEET_NAME}!{coluna_letra}{i}",
                                valueInputOption="RAW",
                                body={"values": [["Processo Oracle Concluído"]]}
                            ).execute()

                            # Marcar como concluído no cache
                            cache.marcar_concluido(id_item)
                            gui_log(f"✅ Linha {i} (ID: {id_item}) processada e salva no Oracle")

                        except Exception as err:
                            gui_log(f"⚠️ Falha ao atualizar Sheets para ID {id_item}: {err}")
                            gui_log(f"💾 Item permanece no cache para retry automático")

                        itens_processados_nesta_execucao += 1
                        _ja_processou_algum_item = True

                        time.sleep(0.5)

                    except Exception as e_proc:
                        gui_log(f"❌ Erro ao processar linha {i}: {e_proc}")
                        import traceback
                        gui_log(traceback.format_exc())
                        time.sleep(2)

                # Após processar pelo menos 1 item, aguardar 30s
                if itens_processados_nesta_execucao > 0:
                    gui_log(f"✅ {itens_processados_nesta_execucao} item(ns) processado(s)")
                    if not aguardar_com_pausa(30, "Aguardando estabilização pós-processamento"):
                        return False
                    break

        # Aguardar tempo configurado após Oracle
        tempo_espera = config["tempos_espera"]["apos_rpa_oracle"]
        return aguardar_com_pausa(tempo_espera, "Aguardando estabilização pós-Oracle")

    except Exception as e:
        gui_log(f"❌ Erro ao processar Oracle: {e}")
        import traceback
        gui_log(traceback.format_exc())
        return False

def etapa_06_navegacao_pos_oracle(config):
    """Etapa 6: Navegação após RPA_Oracle"""
    gui_log("📋 ETAPA 6: Navegação pós-Oracle")

    coord = config["coordenadas"]["tela_06_janela_navegador"]
    clicar_coordenada(coord["x"], coord["y"], descricao=coord["descricao"])

    tempo_espera = config["tempos_espera"]["entre_cliques"]
    return aguardar_com_pausa(tempo_espera, "Aguardando navegador")

def etapa_07_bancada_material(config):
    """Etapa 7: Duplo clique em Bancada de Material"""
    gui_log("📋 ETAPA 7: Abertura Bancada de Material")

    coord = config["coordenadas"]["tela_07_bancada_material"]
    clicar_coordenada(coord["x"], coord["y"], duplo=True, descricao=coord["descricao"])

    tempo_espera = config["tempos_espera"]["apos_modal"]
    return aguardar_com_pausa(tempo_espera, "Aguardando abertura da Bancada")

def etapa_08_executar_rpa_bancada(config):
    """
    Etapa 8: Executar RPA_Bancada com retry de até 3x
    Só aplica retry na parte final de envio
    """
    gui_log("🤖 ETAPA 8: Execução do RPA_Bancada")

    # Caminho para o main.py da bancada
    caminho_bancada = BASE_DIR.parent / "rpa_bancada" / "main.py"

    if not caminho_bancada.exists():
        gui_log(f"❌ RPA_Bancada não encontrado em: {caminho_bancada}")
        return False

    gui_log(f"📂 Executando: {caminho_bancada}")

    # ═══════════════════════════════════════════════════════════════
    # RETRY DE ATÉ 3X PARA O ENVIO DA BANCADA
    # ═══════════════════════════════════════════════════════════════

    for tentativa in range(1, MAX_TENTATIVAS_BANCADA + 1):
        gui_log(f"🔄 Tentativa {tentativa}/{MAX_TENTATIVAS_BANCADA}")

        try:
            resultado = subprocess.run(
                [sys.executable, str(caminho_bancada)],
                cwd=str(caminho_bancada.parent),
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=1800  # 30 minutos máximo
            )

            if resultado.returncode == 0:
                gui_log(f"✅ RPA_Bancada executado com sucesso na tentativa {tentativa}")

                tempo_espera = config["tempos_espera"]["apos_rpa_bancada"]
                return aguardar_com_pausa(tempo_espera, "Aguardando estabilização")

            else:
                gui_log(f"⚠️ RPA_Bancada finalizou com código: {resultado.returncode}")

                if tentativa < MAX_TENTATIVAS_BANCADA:
                    gui_log(f"🔄 Tentando novamente ({tentativa + 1}/{MAX_TENTATIVAS_BANCADA})...")
                    time.sleep(5)  # Aguardar 5s antes de tentar novamente
                else:
                    gui_log(f"❌ RPA_Bancada falhou após {MAX_TENTATIVAS_BANCADA} tentativas")
                    return False

        except subprocess.TimeoutExpired:
            gui_log(f"⚠️ RPA_Bancada atingiu timeout na tentativa {tentativa}")

            if tentativa < MAX_TENTATIVAS_BANCADA:
                gui_log(f"🔄 Tentando novamente ({tentativa + 1}/{MAX_TENTATIVAS_BANCADA})...")
                time.sleep(5)
            else:
                gui_log(f"❌ RPA_Bancada atingiu timeout após {MAX_TENTATIVAS_BANCADA} tentativas")
                return False

        except Exception as e:
            gui_log(f"❌ Erro ao executar RPA_Bancada na tentativa {tentativa}: {e}")

            if tentativa < MAX_TENTATIVAS_BANCADA:
                gui_log(f"🔄 Tentando novamente ({tentativa + 1}/{MAX_TENTATIVAS_BANCADA})...")
                time.sleep(5)
            else:
                gui_log(f"❌ RPA_Bancada falhou após {MAX_TENTATIVAS_BANCADA} tentativas")
                return False

    return False

def etapa_09_fechar_bancada(config):
    """Etapa 9: Fechar a janela da Bancada"""
    gui_log("📋 ETAPA 9: Fechamento da Bancada")

    coord = config["coordenadas"]["tela_08_fechar_bancada"]
    clicar_coordenada(coord["x"], coord["y"], descricao=coord["descricao"])

    tempo_espera = config["tempos_espera"]["entre_cliques"]
    return aguardar_com_pausa(tempo_espera, "Aguardando fechamento")

# =================== EXECUÇÃO DO CICLO COMPLETO ===================
def executar_ciclo_completo(config):
    """Executa um ciclo completo de todas as etapas"""
    global _ciclo_atual, _data_inicio_ciclo, _primeira_verificacao_oracle

    _ciclo_atual += 1
    _data_inicio_ciclo = datetime.now()
    _primeira_verificacao_oracle = True  # Resetar flag a cada ciclo

    gui_log("=" * 60)
    gui_log(f"🔄 CICLO #{_ciclo_atual} - {_data_inicio_ciclo.strftime('%Y-%m-%d %H:%M:%S')}")
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

    try:
        # Executar todas as etapas em sequência
        etapas = [
            ("Transferência Subinventário", etapa_01_transferencia_subinventario),
            ("Preenchimento Tipo", etapa_02_preencher_tipo),
            ("Seleção Funcionário", etapa_03_selecionar_funcionario),
            ("RPA Oracle", etapa_05_executar_rpa_oracle),
            ("Navegação pós-Oracle", etapa_06_navegacao_pos_oracle),
            ("Bancada Material", etapa_07_bancada_material),
            ("RPA Bancada", etapa_08_executar_rpa_bancada),
            ("Fechamento Bancada", etapa_09_fechar_bancada)
        ]

        for nome_etapa, funcao_etapa in etapas:
            if not _rpa_running:
                gui_log("⏸️ Ciclo interrompido pelo usuário")
                return False

            sucesso = funcao_etapa(config)

            if not sucesso:
                gui_log(f"❌ Falha na etapa: {nome_etapa}")

                # Atualizar no Google Sheets
                if GOOGLE_SHEETS_DISPONIVEL:
                    try:
                        data_fim = datetime.now()
                        atualizar_ciclo(_ciclo_atual, "Status", "Falha")
                        atualizar_ciclo(_ciclo_atual, "Data/Hora Fim", data_fim.strftime("%Y-%m-%d %H:%M:%S"))
                        atualizar_ciclo(_ciclo_atual, "Etapa Falha", nome_etapa)
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
    Função principal - executa em loop contínuo

    Args:
        modo_continuo: Se True, executa em loop contínuo (padrão: True)
    """
    global _rpa_running, _ciclo_atual

    _rpa_running = True

    gui_log("=" * 60)
    gui_log("🤖 RPA CICLO V2 - Iniciado")
    if MODO_TESTE:
        gui_log("[MODO TESTE ATIVADO] Simulação sem movimentos físicos")
    gui_log("=" * 60)

    try:
        config = carregar_config()

        if modo_continuo:
            gui_log("🔄 Modo contínuo ativado - execução ininterrupta")
            gui_log("⚠️ O RPA aguardará automaticamente na parte do Oracle quando necessário")
            gui_log("🛑 Para parar: use o botão PARAR ou mova o mouse para o canto superior esquerdo")
            gui_log("")

            while _rpa_running:
                sucesso = executar_ciclo_completo(config)

                if sucesso:
                    gui_log("✅ Ciclo concluído! Reiniciando ciclo...")

                    # Pequena pausa entre ciclos
                    if not aguardar_com_pausa(2, "Pausa entre ciclos"):
                        break
                else:
                    gui_log("⚠️ Ciclo falhou. Aguardando 30s antes de tentar novamente...")
                    if not aguardar_com_pausa(30, "Aguardando após falha"):
                        break

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
        gui_log("🏁 RPA CICLO V2 - Finalizado")
        gui_log(f"📊 Total de ciclos executados: {_ciclo_atual}")
        gui_log("=" * 60)

# =================== PONTO DE ENTRADA ===================
if __name__ == "__main__":
    # Configurar PyAutoGUI
    pyautogui.PAUSE = 0.5
    pyautogui.FAILSAFE = True

    # Executar RPA em modo contínuo
    main(modo_continuo=True)
