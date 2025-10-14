# -*- coding: utf-8 -*-
"""
RPA CICLO - Módulo Principal (Versão para GUI)
Orquestra a execução sequencial de processos no Oracle
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

# Controle de execução
_rpa_running = False
_gui_log_callback = None
_ciclo_atual = 0
_data_inicio_ciclo = None

# ─── CACHE LOCAL ANTI-DUPLICAÇÃO (COMPARTILHADO COM RPA_ORACLE) ─────────────
class CacheLocal:
    """Cache persistente para evitar duplicações no Oracle"""

    def __init__(self, arquivo="processados.json"):
        # Salvar na pasta do rpa_oracle para compartilhar cache
        rpa_oracle_dir = BASE_DIR.parent / "rpa_oracle"
        self.arquivo = rpa_oracle_dir / arquivo
        self.dados = self._carregar()
        self.lock = threading.Lock()

    def _carregar(self):
        """Carrega cache do disco (persiste entre execuções)"""
        if self.arquivo.exists():
            try:
                with open(self.arquivo, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Erro ao carregar cache: {e}")
                return {}
        return {}

    def _salvar(self):
        """Salva cache no disco com lock"""
        with self.lock:
            try:
                with open(self.arquivo, 'w', encoding='utf-8') as f:
                    json.dump(self.dados, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"Erro ao salvar cache: {e}")

    def ja_processado(self, data_hora_sep):
        """Verifica se Data Hora Sep. já foi processada"""
        with self.lock:
            return data_hora_sep in self.dados

    def adicionar(self, data_hora_sep, linha_atual, item, quantidade, referencia, status="pendente"):
        """Adiciona ao cache APÓS Ctrl+S (status pendente)"""
        with self.lock:
            self.dados[data_hora_sep] = {
                "linha_atual": linha_atual,
                "item": item,
                "quantidade": quantidade,
                "referencia": referencia,
                "timestamp_processamento": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status_sheets": status
            }
            self._salvar()

    def marcar_concluido(self, data_hora_sep):
        """Marca como concluído quando Sheets atualizar"""
        with self.lock:
            if data_hora_sep in self.dados:
                self.dados[data_hora_sep]["status_sheets"] = "concluido"
                self._salvar()

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

# =================== FUNÇÕES DE AUTOMAÇÃO ===================
def clicar_coordenada(x, y, duplo=False, descricao=""):
    """Clica em uma coordenada específica na tela"""
    if descricao:
        gui_log(f"🖱️ {descricao}")

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

def etapa_05_executar_rpa_oracle(config):
    """Etapa 5: Processar linhas do Google Sheets no Oracle"""
    gui_log("🤖 ETAPA 5: Processamento no Oracle")

    try:
        # Importar Google Sheets
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        # Autenticar Google Sheets
        SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
        SPREADSHEET_ID = "14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk"
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

        # Loop de espera até encontrar pelo menos 1 item para processar
        itens_processados = 0
        tentativas_verificacao = 0

        while itens_processados == 0 and _rpa_running:
            tentativas_verificacao += 1

            # Buscar linhas para processar (Status = "CONCLUÍDO" e Status Oracle vazio)
            res = service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{SHEET_NAME}!A1:T"
            ).execute()

            valores = res.get("values", [])
            if not valores:
                gui_log("⚠️ Nenhuma linha encontrada no Google Sheets")
                if not aguardar_com_pausa(30, "Aguardando novas linhas no Google Sheets"):
                    return False
                continue

            headers, dados = valores[0], valores[1:]

            # Filtrar linhas para processar
            linhas_processar = []
            for i, row in enumerate(dados):
                if len(row) < len(headers):
                    row += [''] * (len(headers) - len(row))
                idx_status_oracle = headers.index("Status Oracle")
                idx_status = headers.index("Status")
                status_oracle = row[idx_status_oracle].strip()
                status = row[idx_status].strip().upper()
                if status_oracle == "" and "CONCLUÍDO" in status:
                    linhas_processar.append((i + 2, dict(zip(headers, row))))

            if not linhas_processar:
                gui_log(f"⏳ Nenhuma linha nova para processar (verificação #{tentativas_verificacao})")
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
                data_hora_sep = linha.get("Data Hora Sep.", "").strip()

                # ✅ VERIFICAR CACHE ANTI-DUPLICAÇÃO
                if cache.ja_processado(data_hora_sep):
                    gui_log(f"⏭️ Linha {i} (Sep: {data_hora_sep}) já processada anteriormente. Pulando.")
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

                # Salvar (Ctrl+S)
                pyautogui.hotkey("ctrl", "s")
                gui_log("⏳ Aguardando Oracle salvar...")
                time.sleep(3)  # Aguardar Oracle salvar antes de marcar como concluído

                # ✅ GRAVAR NO CACHE (APÓS Ctrl+S, ANTES de tentar Sheets)
                cache.adicionar(
                    data_hora_sep=data_hora_sep,
                    linha_atual=i,
                    item=item,
                    quantidade=quantidade,
                    referencia=referencia,
                    status="pendente"
                )
                gui_log(f"💾 Registrado no cache: {data_hora_sep}")

                # Atualizar Google Sheets
                try:
                    service.spreadsheets().values().update(
                        spreadsheetId=SPREADSHEET_ID,
                        range=f"{SHEET_NAME}!T{i}",
                        valueInputOption="RAW",
                        body={"values": [["Processo Oracle Concluído"]]}
                    ).execute()

                    # ✅ Marcar como concluído no cache
                    cache.marcar_concluido(data_hora_sep)
                    gui_log(f"✅ Linha {i} processada e salva no Oracle")
                except Exception as err:
                    gui_log(f"⚠️ Falha ao atualizar Sheets: {err}. Retry em background...")

                itens_processados += 1
                time.sleep(0.5)

            # Saída do loop após processar pelo menos 1 item
            if itens_processados > 0:
                break

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
    """Etapa 6: Navegação após RPA_Oracle"""
    gui_log("📋 ETAPA 6: Navegação pós-Oracle")

    # Clicar no campo janela (340, 40)
    clicar_coordenada(340, 40, descricao="Clicando no campo janela")

    tempo_espera = config["tempos_espera"]["entre_cliques"]
    if not aguardar_com_pausa(tempo_espera, "Aguardando janela"):
        return False

    # Clicar no navegador (385, 135)
    clicar_coordenada(385, 135, descricao="Clicando no navegador")

    tempo_espera = config["tempos_espera"]["entre_cliques"]
    if not aguardar_com_pausa(tempo_espera, "Aguardando navegador"):
        return False

    # Duplo clique para abrir a tela da bancada (831, 333)
    clicar_coordenada(831, 333, duplo=True, descricao="Duplo clique para abrir Bancada")

    tempo_espera = config["tempos_espera"]["apos_modal"]
    return aguardar_com_pausa(tempo_espera, "Aguardando abertura da Bancada")

def etapa_07_executar_rpa_bancada(config):
    """Etapa 7: Executar RPA_Bancada_v2 completo"""
    gui_log("🤖 ETAPA 7: Execução do RPA_Bancada_v2")

    # Caminho para o executável do RPA_Bancada_v2 (versão atualizada)
    caminho_bancada = BASE_DIR.parent / "rpa_bancada" / "dist" / "RPA_Bancada_v2.exe"

    if not caminho_bancada.exists():
        # Tentar com script Python v2
        caminho_bancada = BASE_DIR.parent / "rpa_bancada" / "main_v2.py"
        if not caminho_bancada.exists():
            gui_log(f"❌ RPA_Bancada_v2 não encontrado em: {caminho_bancada}")
            # Tentar fallback para versão antiga
            caminho_bancada = BASE_DIR.parent / "rpa_bancada" / "dist" / "RPA_Bancada.exe"
            if not caminho_bancada.exists():
                gui_log(f"❌ Nenhuma versão do RPA_Bancada encontrada")
                return False
            gui_log(f"⚠️ Usando versão antiga: RPA_Bancada.exe")

        use_python = True
    else:
        use_python = False

    gui_log(f"📂 Executando: {caminho_bancada}")

    try:
        if use_python:
            resultado = subprocess.run(
                [sys.executable, str(caminho_bancada)],
                cwd=str(caminho_bancada.parent),
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=1800  # 30 minutos máximo
            )
        else:
            resultado = subprocess.run(
                [str(caminho_bancada)],
                cwd=str(caminho_bancada.parent),
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=1800
            )

        if resultado.returncode == 0:
            gui_log("✅ RPA_Bancada_v2 executado com sucesso")
        else:
            gui_log(f"⚠️ RPA_Bancada_v2 finalizou com código: {resultado.returncode}")
            return True  # Continuar mesmo com código de saída diferente de 0

        tempo_espera = config["tempos_espera"]["apos_rpa_bancada"]
        return aguardar_com_pausa(tempo_espera, "Aguardando estabilização")

    except subprocess.TimeoutExpired:
        gui_log("⚠️ RPA_Bancada_v2 atingiu timeout")
        return False
    except Exception as e:
        gui_log(f"❌ Erro ao executar RPA_Bancada_v2: {e}")
        return False

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

    etapas_status = {
        "RPA Oracle": "Pendente",
        "RPA Bancada": "Pendente"
    }

    try:
        # Executar todas as etapas em sequência
        etapas = [
            ("Transferência Subinventário", etapa_01_transferencia_subinventario),
            ("Preenchimento Tipo", etapa_02_preencher_tipo),
            ("Seleção e Confirmação Funcionário", etapa_03_selecionar_funcionario),
            ("RPA Oracle", etapa_05_executar_rpa_oracle),
            ("Navegação", etapa_06_navegacao_pos_oracle),
            ("RPA Bancada", etapa_07_executar_rpa_bancada),
            ("Fechamento Bancada", etapa_08_fechar_bancada)
        ]

        for nome_etapa, funcao_etapa in etapas:
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
    gui_log("=" * 60)

    try:
        config = carregar_config()

        if modo_continuo:
            gui_log("🔄 Modo contínuo ativado - execução ininterrupta")
            gui_log("⚠️ O RPA Oracle aguardará automaticamente se não houver nada para processar")
            gui_log("🛑 Para parar: use o botão PARAR ou mova o mouse para o canto superior esquerdo")
            gui_log("")

            tentativas_falhas_consecutivas = 0
            max_falhas_consecutivas = 3  # Parar após 3 falhas consecutivas

            while _rpa_running:
                # Executar ciclo
                sucesso = executar_ciclo_completo(config)

                if sucesso:
                    tentativas_falhas_consecutivas = 0  # Reset contador de falhas
                    gui_log("✅ Ciclo concluído! Iniciando próximo ciclo...")

                    # Pequena pausa de 5 segundos entre ciclos para estabilização
                    if not aguardar_com_pausa(5, "Pausa entre ciclos"):
                        break
                else:
                    tentativas_falhas_consecutivas += 1
                    gui_log(f"⚠️ Ciclo falhou ({tentativas_falhas_consecutivas}/{max_falhas_consecutivas})")

                    if tentativas_falhas_consecutivas >= max_falhas_consecutivas:
                        gui_log("❌ Muitas falhas consecutivas! Encerrando RPA...")
                        break

                    # Aguardar 30 segundos antes de tentar novamente após falha
                    gui_log("⏳ Aguardando 30 segundos antes de tentar novamente...")
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
