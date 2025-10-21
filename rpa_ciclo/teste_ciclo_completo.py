# -*- coding: utf-8 -*-
"""
TESTE COMPLETO DO RPA CICLO V2
Simula todo o fluxo com as planilhas de teste
- Processa até 50 itens do Oracle
- Testa anti-duplicação
- Simula todos os cliques
- Executa Bancada
- Loop completo
"""

import json
import os
import sys
import time
import subprocess
import threading
from pathlib import Path
from datetime import datetime
import random

# Configurar encoding UTF-8
if sys.platform.startswith('win'):
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass

# =================== CONFIGURAÇÕES DE TESTE ===================
BASE_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = BASE_DIR / "config.json"

# ─── MODO TESTE ATIVADO ─────────────────────────────────────────────
MODO_TESTE = True  # ✅ SEMPRE TRUE PARA TESTE
SIMULAR_CLIQUES = True  # Simula todos os cliques do pyautogui
LIMITE_ITENS_TESTE = 50  # Processa até 50 itens por ciclo
TESTAR_DUPLICACAO = True  # Tenta processar itens duplicados para testar cache
NUM_CICLOS_TESTE = 3  # Número de ciclos para testar

# IDs das planilhas de TESTE
SPREADSHEET_ID_ORACLE_TESTE = "147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY"
SPREADSHEET_ID_BANCADA_TESTE = "1KMS-1_FY6-cU26ZlaFu5jciSHEWlmluHo-QOFbB1LFE"

# Controle de execução
_rpa_running = False
_ciclo_atual = 0
_primeira_verificacao_oracle = True
_ja_processou_algum_item = False

# ─── RATE LIMITING GOOGLE SHEETS API ───────────────────────────────
# Google Sheets API limita a 60 requisições de escrita por minuto
_ultima_requisicao_sheets = 0
_requisicoes_por_minuto = []

def rate_limit_sheets():
    """Garante que não excedemos 60 requisições por minuto"""
    global _ultima_requisicao_sheets, _requisicoes_por_minuto

    agora = time.time()

    # Remove requisições mais antigas que 1 minuto
    _requisicoes_por_minuto = [t for t in _requisicoes_por_minuto if agora - t < 60]

    # Se já temos 50+ requisições no último minuto, espera
    if len(_requisicoes_por_minuto) >= 50:  # Margem de segurança (50 em vez de 60)
        tempo_espera = 60 - (agora - _requisicoes_por_minuto[0])
        if tempo_espera > 0:
            gui_log(f"⏳ Rate limit: Aguardando {tempo_espera:.1f}s...")
            time.sleep(tempo_espera + 1)

    # Registra esta requisição
    _requisicoes_por_minuto.append(time.time())
_itens_processados_total = 0
_tentativas_duplicacao = 0
_duplicacoes_bloqueadas = 0

# =================== SIMULAÇÃO DE PYAUTOGUI ===================
class PyAutoGUISimulado:
    """Simula pyautogui para testes sem GUI real"""

    PAUSE = 0.1
    FAILSAFE = True

    @staticmethod
    def moveTo(x, y, duration=0.8):
        print(f"  [SIM] moveTo({x}, {y}, duration={duration})")
        time.sleep(0.05)

    @staticmethod
    def click(button='left'):
        print(f"  [SIM] click(button='{button}')")
        time.sleep(0.05)

    @staticmethod
    def doubleClick():
        print(f"  [SIM] doubleClick()")
        time.sleep(0.05)

    @staticmethod
    def write(text):
        print(f"  [SIM] write('{text}')")
        time.sleep(0.05)

    @staticmethod
    def press(key):
        print(f"  [SIM] press('{key}')")
        time.sleep(0.05)

    @staticmethod
    def hotkey(*keys):
        print(f"  [SIM] hotkey({', '.join(keys)})")
        time.sleep(0.05)

    class FailSafeException(Exception):
        pass

# Usar PyAutoGUI simulado
pyautogui = PyAutoGUISimulado()

# =================== GOOGLE SHEETS ===================
def autenticar_google_sheets():
    """Autentica com Google Sheets"""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    # Usar token da pasta rpa_oracle
    rpa_oracle_dir = BASE_DIR.parent / "rpa_oracle"
    token_path = rpa_oracle_dir / "token.json"
    creds_path = BASE_DIR / "CredenciaisOracle.json"

    # Se não encontrar na pasta atual, procura na rpa_oracle
    if not creds_path.exists():
        creds_path = rpa_oracle_dir / "CredenciaisOracle.json"

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as token:
            token.write(creds.to_json())

    return build("sheets", "v4", credentials=creds)

# =================== CACHE LOCAL ===================
class CacheLocal:
    """Cache persistente para evitar duplicações"""

    def __init__(self, arquivo="cache_teste_ciclo.json"):
        self.arquivo = BASE_DIR / arquivo
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
                print(f"Erro ao carregar cache: {e}")
                return {}
        return {}

    def _salvar(self):
        try:
            json_str = json.dumps(self.dados, indent=2, ensure_ascii=False)
            with open(self.arquivo, 'w', encoding='utf-8') as f:
                f.write(json_str)
        except Exception as e:
            print(f"[ERRO] Falha ao salvar cache: {e}")

    def ja_processado(self, id_item):
        with self.lock:
            return id_item in self.dados

    def adicionar(self, id_item, linha_atual, item, quantidade, referencia, status="pendente"):
        if not id_item or str(id_item).strip() == "":
            print(f"[ERRO CACHE] ID vazio! Linha: {linha_atual}")
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

    def get_pendentes(self):
        """Retorna lista de IDs pendentes (com status_sheets = 'pendente')"""
        with self.lock:
            return [id_item for id_item, dados in self.dados.items()
                    if dados.get("status_sheets") == "pendente"]

    def limpar(self):
        """Limpa todo o cache"""
        with self.lock:
            self.dados = {}
        self._salvar()
        print("[CACHE] Cache limpo!")

# =================== FUNÇÕES AUXILIARES ===================
def gui_log(msg):
    """Log formatado com timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")

def aguardar_com_pausa(segundos, mensagem="Aguardando"):
    """Aguarda um tempo (no teste, acelera)"""
    tempo_real = 0.5 if MODO_TESTE else segundos  # Acelera no teste
    gui_log(f"⏳ {mensagem} ({tempo_real}s)...")
    time.sleep(tempo_real)
    return True

def carregar_config():
    """Carrega configurações do config.json"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        gui_log("✅ Configurações carregadas")
        return config
    except Exception as e:
        gui_log(f"❌ Erro ao carregar config: {e}")
        raise

# =================== ETAPAS SIMULADAS ===================
def etapa_01_transferencia_subinventario(config):
    """Etapa 1: Transferência de Subinventário (SIMULADO)"""
    gui_log("📋 ETAPA 1: Transferência de Subinventário")

    coord = config["coordenadas"]["tela_01_transferencia_subinventario"]
    gui_log(f"🖱️ {coord['descricao']}")
    pyautogui.moveTo(coord["x"], coord["y"], duration=0.1)
    pyautogui.doubleClick()

    return aguardar_com_pausa(1, "Aguardando abertura do modal")

def etapa_02_preencher_tipo(config):
    """Etapa 2: Preencher Tipo (SIMULADO)"""
    gui_log("📋 ETAPA 2: Preenchimento do Tipo")

    coord = config["coordenadas"]["tela_02_campo_tipo"]
    gui_log(f"🖱️ {coord['descricao']}")
    pyautogui.moveTo(coord["x"], coord["y"])
    pyautogui.click()
    pyautogui.write(coord["digitar"])

    for acao in coord["acoes"]:
        pyautogui.press(acao)

    return aguardar_com_pausa(1, "Aguardando processamento")

def etapa_03_selecionar_funcionario(config):
    """Etapa 3: Selecionar Funcionário (SIMULADO)"""
    gui_log("📋 ETAPA 3: Seleção de Funcionário")

    coord = config["coordenadas"]["tela_03_pastinha_funcionario"]
    gui_log(f"🖱️ {coord['descricao']}")
    pyautogui.moveTo(coord["x"], coord["y"])
    pyautogui.click()

    aguardar_com_pausa(0.5, "Aguardando modal")

    gui_log("⌨️ Navegando até Wallatas Moreira (9 setas para baixo)...")
    for i in range(9):
        pyautogui.press('down')

    pyautogui.press('enter')  # Selecionar
    pyautogui.press('enter')  # Confirmar Sim

    return aguardar_com_pausa(1, "Aguardando confirmação")

def sync_sheets_background_teste(cache, service):
    """Thread que tenta atualizar Sheets para linhas pendentes (com rate limiting)"""
    SHEET_NAME = "Separação"
    ciclo_retry = 0
    MAX_ITENS_POR_BATCH = 10  # Processar no máximo 10 itens por vez

    while True:
        time.sleep(30)  # Retry a cada 30 segundos

        try:
            ciclo_retry += 1
            pendentes = cache.get_pendentes()

            if not pendentes:
                continue

            # Limitar a 10 itens por vez
            pendentes = pendentes[:MAX_ITENS_POR_BATCH]
            gui_log(f"[RETRY] Ciclo {ciclo_retry} - Processando {len(pendentes)} itens pendentes...")

            # Buscar headers do Sheets
            rate_limit_sheets()  # Aplicar rate limiting
            res = service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID_ORACLE_TESTE,
                range=f"{SHEET_NAME}!A1:AC"
            ).execute()

            valores = res.get("values", [])
            if not valores:
                continue

            headers = valores[0]
            idx_status_oracle = headers.index("Status Oracle")
            idx_id = headers.index("ID")
            coluna_letra = chr(65 + idx_status_oracle) if idx_status_oracle < 26 else chr(65 + idx_status_oracle // 26 - 1) + chr(65 + idx_status_oracle % 26)

            # Coletar atualizações para batch update
            batch_updates = []
            ids_para_remover = []

            for id_item in pendentes:
                dados_cache = cache.dados.get(id_item, {})
                linha_atual = dados_cache.get("linha_atual")

                if linha_atual:
                    batch_updates.append({
                        "range": f"{SHEET_NAME}!{coluna_letra}{linha_atual}",
                        "values": [["Processo Oracle Concluído"]]
                    })
                    ids_para_remover.append(id_item)

            # Executar batch update se tiver algo
            if batch_updates:
                try:
                    rate_limit_sheets()  # Aplicar rate limiting
                    service.spreadsheets().values().batchUpdate(
                        spreadsheetId=SPREADSHEET_ID_ORACLE_TESTE,
                        body={"valueInputOption": "RAW", "data": batch_updates}
                    ).execute()

                    # SUCESSO! Remover do cache
                    for id_item in ids_para_remover:
                        cache.marcar_concluido(id_item)

                    gui_log(f"[RETRY] ✓ {len(ids_para_remover)} itens sincronizados e removidos do cache")

                except Exception as e:
                    gui_log(f"[RETRY] ✗ Batch update falhou: {str(e)[:100]}")

        except Exception as e:
            gui_log(f"[RETRY] Erro no ciclo {ciclo_retry}: {str(e)[:100]}")

def etapa_05_executar_rpa_oracle_teste(config, service, cache):
    """
    Etapa 5: RPA Oracle TESTE
    - Processa até 50 itens
    - Testa duplicação
    - Simula preenchimento
    - Sistema de retry automático
    """
    global _primeira_verificacao_oracle, _ja_processou_algum_item
    global _itens_processados_total, _tentativas_duplicacao, _duplicacoes_bloqueadas

    gui_log("🤖 ETAPA 5: Processamento no Oracle (TESTE)")

    SHEET_NAME = "Separação"
    itens_processados_nesta_execucao = 0

    # Iniciar thread de retry em background (apenas uma vez)
    import threading
    if not hasattr(etapa_05_executar_rpa_oracle_teste, '_retry_thread_started'):
        retry_thread = threading.Thread(
            target=sync_sheets_background_teste,
            args=(cache, service),
            daemon=True
        )
        retry_thread.start()
        etapa_05_executar_rpa_oracle_teste._retry_thread_started = True
        gui_log("[RETRY] Thread de retry automático iniciada")

    # Buscar linhas da planilha de TESTE
    res = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID_ORACLE_TESTE,
        range=f"{SHEET_NAME}!A1:AC"
    ).execute()

    valores = res.get("values", [])
    if not valores:
        gui_log("⚠️ Planilha de teste vazia!")
        return True

    headers, dados = valores[0], valores[1:]
    gui_log(f"📊 Planilha carregada: {len(dados)} linhas encontradas")

    # Filtrar linhas para processar
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

        # Dupla proteção
        if status_oracle == "" and "CONCLUÍDO" in status:
            linhas_processar.append((i + 2, dict(zip(headers, row))))

    gui_log(f"📋 {len(linhas_processar)} linhas disponíveis para processar")

    # Limitar a 50 itens
    if len(linhas_processar) > LIMITE_ITENS_TESTE:
        gui_log(f"⚠️ Limitando a {LIMITE_ITENS_TESTE} itens para teste")
        linhas_processar = linhas_processar[:LIMITE_ITENS_TESTE]

    if not linhas_processar:
        gui_log("📊 Nenhuma linha nova encontrada")

        # Aplicar lógica de espera
        if not _ja_processou_algum_item:
            gui_log("⏳ Primeira execução sem itens - Seguindo (teste)...")
            return True

        if _primeira_verificacao_oracle:
            gui_log("✅ Primeira verificação sem itens - Pode seguir!")
            _primeira_verificacao_oracle = False
            return True

        gui_log("⏳ Segunda verificação sem itens - No teste, seguindo...")
        return True

    # ═══════════════════════════════════════════════════════════════
    # PROCESSAR LINHAS
    # ═══════════════════════════════════════════════════════════════

    gui_log(f"📋 Processando {len(linhas_processar)} linha(s)...")

    ids_processados = []  # Lista de IDs processados neste ciclo
    batch_updates = []  # Coletar atualizações para batch update
    ids_para_atualizar = []  # IDs correspondentes ao batch

    for idx, (i, linha) in enumerate(linhas_processar, 1):
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

            if not id_item:
                gui_log(f"⚠️ Linha {i} - ID vazio. Pulando.")
                continue

            # ═══════════════════════════════════════════════════════════════
            # TESTE DE DUPLICAÇÃO - Tentar processar item JÁ PROCESSADO
            # ═══════════════════════════════════════════════════════════════
            if TESTAR_DUPLICACAO and idx % 5 == 0 and len(ids_processados) > 0:
                _tentativas_duplicacao += 1
                # Pegar um ID já processado para tentar duplicar
                id_duplicado = ids_processados[0]  # Pega o primeiro processado
                gui_log(f"🔄 [TESTE DUPLICAÇÃO #{_tentativas_duplicacao}] Tentando duplicar ID {id_duplicado}...")

                # Tentar processar novamente (deve ser bloqueado pelo cache)
                if cache.ja_processado(id_duplicado):
                    _duplicacoes_bloqueadas += 1
                    gui_log(f"🛡️ [BLOQUEADO] ID {id_duplicado} já foi processado! ({_duplicacoes_bloqueadas}/{_tentativas_duplicacao})")
                else:
                    gui_log(f"⚠️ [FALHA CACHE] ID {id_duplicado} NÃO estava no cache!")

            # Verificar se o item ATUAL já foi processado (não deveria)
            if cache.ja_processado(id_item):
                gui_log(f"⏭️ [PULADO] ID {id_item} já processado anteriormente")
                continue

            # Validações (mesmas do RPA_Oracle)
            try:
                qtd_float = float(str(quantidade).replace(",", ".").replace(" ", ""))
                if qtd_float == 0:
                    gui_log(f"⚠️ Linha {i} - Quantidade Zero. Marcando...")
                    # Não marcar no Sheets em teste para poder reprocessar
                    continue
                elif qtd_float < 0:
                    gui_log(f"⚠️ Linha {i} - Quantidade negativa. Pulando.")
                    continue
            except ValueError:
                gui_log(f"⚠️ Linha {i} - Quantidade inválida. Pulando.")
                continue

            # Campos vazios
            campos_obrigatorios = {
                "ITEM": item,
                "SUB. ORIGEM": sub_o,
                "END. ORIGEM": end_o,
                "SUB. DESTINO": sub_d,
                "END. DESTINO": end_d
            }

            if str(referencia).strip().upper().startswith("COD"):
                campos_obrigatorios = {
                    "ITEM": item,
                    "SUB. ORIGEM": sub_o,
                    "END. ORIGEM": end_o
                }

            campos_vazios = [nome for nome, valor in campos_obrigatorios.items() if not valor or str(valor).strip() == ""]
            if campos_vazios:
                gui_log(f"⚠️ Linha {i} - Campos vazios: {', '.join(campos_vazios)}. Pulando.")
                continue

            # Transações não autorizadas
            subinvs_restritos = ["RAWINDIR", "RAWMANUT", "RAWWAFIFE"]
            sub_o_upper = str(sub_o).strip().upper()
            sub_d_upper = str(sub_d).strip().upper()

            if sub_o_upper in subinvs_restritos and sub_d_upper == "RAWCENTR":
                gui_log(f"⚠️ Linha {i} - Transação não autorizada: {sub_o} → {sub_d}. Pulando.")
                continue

            if sub_o_upper in subinvs_restritos and sub_o_upper == sub_d_upper:
                gui_log(f"⚠️ Linha {i} - Transação não autorizada (mesmo subinv). Pulando.")
                continue

            gui_log(f"▶ Linha {i} ({idx}/{len(linhas_processar)}): ID={id_item} | Item={item} | Qtd={quantidade}")

            # ═══════════════════════════════════════════════════════════════
            # SIMULAR PREENCHIMENTO NO ORACLE
            # ═══════════════════════════════════════════════════════════════

            gui_log(f"  [SIMULANDO] Preenchendo campos no Oracle...")
            gui_log(f"    → Item: {item}")
            gui_log(f"    → Referência: {referencia}")
            gui_log(f"    → Sub.Origem: {sub_o} | End.Origem: {end_o}")

            if str(referencia).strip().upper().startswith("COD"):
                gui_log(f"    → [COD] Pulando campos destino")
            else:
                gui_log(f"    → Sub.Destino: {sub_d} | End.Destino: {end_d}")

            gui_log(f"    → Quantidade: {quantidade}")
            gui_log(f"  [SIMULANDO] Ctrl+S - Salvando no Oracle...")

            time.sleep(0.1)  # Simula tempo de processamento

            # Gravar no cache
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
            # COLETAR PARA BATCH UPDATE (em vez de atualizar individualmente)
            # ═══════════════════════════════════════════════════════════════
            # Calcular letra da coluna Status Oracle
            coluna_letra = chr(65 + idx_status_oracle) if idx_status_oracle < 26 else chr(65 + idx_status_oracle // 26 - 1) + chr(65 + idx_status_oracle % 26)

            batch_updates.append({
                "range": f"{SHEET_NAME}!{coluna_letra}{i}",
                "values": [["Processo Oracle Concluído"]]
            })
            ids_para_atualizar.append((id_item, i))

            gui_log(f"  [PREPARADO] Atualização da linha {i} adicionada ao batch")

            # Adicionar à lista de IDs processados (para teste de duplicação)
            ids_processados.append(id_item)

            itens_processados_nesta_execucao += 1
            _itens_processados_total += 1
            _ja_processou_algum_item = True

            time.sleep(0.05)  # Pequena pausa entre itens

        except Exception as e_proc:
            gui_log(f"❌ Erro ao processar linha {i}: {e_proc}")
            import traceback
            gui_log(traceback.format_exc())

    # ═══════════════════════════════════════════════════════════════
    # EXECUTAR BATCH UPDATE (uma única requisição para todos os itens)
    # ═══════════════════════════════════════════════════════════════
    if batch_updates:
        gui_log(f"")
        gui_log(f"📤 Executando batch update: {len(batch_updates)} linha(s) para atualizar...")

        try:
            # Aplicar rate limiting
            rate_limit_sheets()

            # Executar batch update
            service.spreadsheets().values().batchUpdate(
                spreadsheetId=SPREADSHEET_ID_ORACLE_TESTE,
                body={"valueInputOption": "RAW", "data": batch_updates}
            ).execute()

            gui_log(f"✅ Batch update concluído! {len(batch_updates)} linhas atualizadas no Sheets!")

            # SUCESSO! Remover todos os IDs do cache
            for id_item, linha_num in ids_para_atualizar:
                if cache.marcar_concluido(id_item):
                    gui_log(f"💾 ID {id_item} (linha {linha_num}) removido do cache (sincronizado)")

        except Exception as err_batch:
            gui_log(f"❌ Erro no batch update: {err_batch}")
            gui_log(f"💾 {len(ids_para_atualizar)} IDs permanecem no cache. Thread de retry tentará novamente...")
            # Items ficam no cache como "pendente" para retry

    gui_log(f"✅ {itens_processados_nesta_execucao} item(ns) processado(s) neste ciclo")
    gui_log(f"📊 Total processado até agora: {_itens_processados_total} itens")

    return aguardar_com_pausa(1, "Aguardando estabilização pós-Oracle")

def etapa_06_navegacao_pos_oracle(config):
    """Etapa 6: Navegação (SIMULADO)"""
    gui_log("📋 ETAPA 6: Navegação pós-Oracle")

    coord = config["coordenadas"]["tela_06_janela_navegador"]
    gui_log(f"🖱️ {coord['descricao']}")
    pyautogui.moveTo(coord["x"], coord["y"])
    pyautogui.click()

    return aguardar_com_pausa(0.5, "Aguardando navegador")

def etapa_07_bancada_material(config):
    """Etapa 7: Bancada Material (SIMULADO)"""
    gui_log("📋 ETAPA 7: Abertura Bancada de Material")

    coord = config["coordenadas"]["tela_07_bancada_material"]
    gui_log(f"🖱️ {coord['descricao']}")
    pyautogui.moveTo(coord["x"], coord["y"])
    pyautogui.doubleClick()

    return aguardar_com_pausa(1, "Aguardando abertura da Bancada")

def etapa_08_executar_rpa_bancada_teste():
    """Etapa 8: RPA Bancada TESTE - Insere dados REAIS no Google Sheets"""
    gui_log("🤖 ETAPA 8: Execução do RPA_Bancada (INSERINDO DADOS REAIS!)")

    try:
        # Autenticar Google Sheets
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
        rpa_oracle_dir = BASE_DIR.parent / "rpa_oracle"
        token_path = rpa_oracle_dir / "token.json"
        creds_path = BASE_DIR / "CredenciaisOracle.json"

        if not creds_path.exists():
            creds_path = rpa_oracle_dir / "CredenciaisOracle.json"

        creds = None
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, "w") as token:
                token.write(creds.to_json())

        service = build("sheets", "v4", credentials=creds)

        # Gerar dados de teste simulando a Bancada
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Dados simulados da Bancada (exemplo)
        dados_teste = [
            ['Codigo', 'Data', 'ORG.', 'SUB.', 'ENDEREÇO', 'ITEM', 'DESCRIÇÃO ITEM', 'REV.', 'UDM PRINCIPAL', 'EM ESTOQUE'],
            ['1', timestamp, 'TPC', 'RAWCENTR', 'A-01-01', 'ITEM001', 'Teste Item 1', 'A', 'PC', '100'],
            ['2', timestamp, 'TPC', 'RAWWIP', 'B-02-03', 'ITEM002', 'Teste Item 2', 'B', 'UN', '50'],
            ['3', timestamp, 'TPC', 'RAWFG', 'C-03-05', 'ITEM003', 'Teste Item 3', 'C', 'KG', '75'],
        ]

        gui_log(f"  [REAL] Gerando dados de teste da Bancada ({len(dados_teste)-1} itens)...")
        time.sleep(0.3)

        # Detectar nome da primeira aba
        result = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID_BANCADA_TESTE).execute()
        sheets = result.get('sheets', [])
        sheet_name = sheets[0]['properties']['title'] if sheets else 'Sheet1'

        gui_log(f"  [REAL] Usando aba: {sheet_name}")

        # Inserir dados no Google Sheets
        range_name = f'{sheet_name}!A:J'

        gui_log("  [REAL] Limpando planilha anterior...")
        rate_limit_sheets()  # Aplicar rate limiting
        service.spreadsheets().values().clear(
            spreadsheetId=SPREADSHEET_ID_BANCADA_TESTE,
            range=range_name
        ).execute()

        gui_log("  [REAL] Inserindo novos dados...")
        rate_limit_sheets()  # Aplicar rate limiting
        body = {'values': dados_teste}
        result = service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID_BANCADA_TESTE,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()

        rows_updated = result.get('updatedRows', 0)
        gui_log(f"✅ RPA_Bancada: {rows_updated} linhas inseridas no Google Sheets!")
        gui_log(f"   📊 Planilha: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID_BANCADA_TESTE}")

        return aguardar_com_pausa(1, "Aguardando estabilização")

    except Exception as e:
        gui_log(f"❌ Erro ao executar RPA_Bancada: {e}")
        import traceback
        gui_log(traceback.format_exc())
        return False

def etapa_09_fechar_bancada(config):
    """Etapa 9: Fechar Bancada (SIMULADO)"""
    gui_log("📋 ETAPA 9: Fechamento da Bancada")

    coord = config["coordenadas"]["tela_08_fechar_bancada"]
    gui_log(f"🖱️ {coord['descricao']}")
    pyautogui.moveTo(coord["x"], coord["y"])
    pyautogui.click()

    return aguardar_com_pausa(0.5, "Aguardando fechamento")

# =================== EXECUÇÃO DO CICLO COMPLETO ===================
def executar_ciclo_teste(config, service, cache):
    """Executa um ciclo completo de TESTE"""
    global _ciclo_atual, _primeira_verificacao_oracle

    _ciclo_atual += 1
    _primeira_verificacao_oracle = True

    gui_log("=" * 70)
    gui_log(f"🔄 CICLO DE TESTE #{_ciclo_atual} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    gui_log("=" * 70)

    try:
        etapas = [
            ("Transferência Subinventário", lambda c: etapa_01_transferencia_subinventario(c)),
            ("Preenchimento Tipo", lambda c: etapa_02_preencher_tipo(c)),
            ("Seleção Funcionário", lambda c: etapa_03_selecionar_funcionario(c)),
            ("RPA Oracle", lambda c: etapa_05_executar_rpa_oracle_teste(c, service, cache)),
            ("Navegação pós-Oracle", lambda c: etapa_06_navegacao_pos_oracle(c)),
            ("Bancada Material", lambda c: etapa_07_bancada_material(c)),
            ("RPA Bancada", lambda c: etapa_08_executar_rpa_bancada_teste()),
            ("Fechamento Bancada", lambda c: etapa_09_fechar_bancada(c))
        ]

        for nome_etapa, funcao_etapa in etapas:
            sucesso = funcao_etapa(config)

            if not sucesso:
                gui_log(f"❌ Falha na etapa: {nome_etapa}")
                return False

        gui_log("=" * 70)
        gui_log(f"✅ CICLO DE TESTE #{_ciclo_atual} CONCLUÍDO COM SUCESSO!")
        gui_log("=" * 70)

        return True

    except Exception as e:
        gui_log(f"❌ Erro durante o ciclo: {e}")
        import traceback
        gui_log(traceback.format_exc())
        return False

# =================== MAIN ===================
def main():
    """Função principal de TESTE"""
    global _rpa_running

    _rpa_running = True

    print("\n" + "=" * 70)
    print("🧪 TESTE COMPLETO DO RPA CICLO V2")
    print("=" * 70)
    print(f"📊 Configurações:")
    print(f"   - Modo Teste: {MODO_TESTE}")
    print(f"   - Simular Cliques: {SIMULAR_CLIQUES}")
    print(f"   - Limite de Itens: {LIMITE_ITENS_TESTE}")
    print(f"   - Testar Duplicação: {TESTAR_DUPLICACAO}")
    print(f"   - Número de Ciclos: {NUM_CICLOS_TESTE}")
    print(f"   - Planilha Oracle: {SPREADSHEET_ID_ORACLE_TESTE}")
    print(f"   - Planilha Bancada: {SPREADSHEET_ID_BANCADA_TESTE}")
    print("=" * 70)
    print()

    try:
        # Carregar configurações
        config = carregar_config()

        # Autenticar Google Sheets
        gui_log("🔐 Autenticando Google Sheets...")
        service = autenticar_google_sheets()
        gui_log("✅ Autenticado com sucesso!")

        # Inicializar cache
        cache = CacheLocal("cache_teste_ciclo.json")

        # Perguntar se quer limpar cache
        print()
        print("=" * 70)
        num_itens = len(cache.dados)
        if num_itens > 0:
            gui_log(f"⚠️ ATENÇÃO: Cache existente com {num_itens} itens")
            gui_log("O cache protege contra duplicações.")
            gui_log("Items só devem ser removidos após sucesso no Google Sheets.")
            print()

        resposta = input("🗑️ Deseja limpar o cache? (s/n) [Recomendado: n]: ").strip().lower()
        if resposta == 's':
            cache.limpar()
            gui_log("🗑️ Cache limpo!")
            gui_log("⚠️ Proteção contra duplicação resetada")
        else:
            gui_log(f"💾 Cache mantido: {num_itens} itens protegidos")
        print("=" * 70)

        print()
        input("⏸️ Pressione ENTER para iniciar o teste...")
        print()

        # Loop de teste
        ciclos_sucesso = 0
        ciclos_falha = 0

        for ciclo_num in range(NUM_CICLOS_TESTE):
            if not _rpa_running:
                break

            sucesso = executar_ciclo_teste(config, service, cache)

            if sucesso:
                ciclos_sucesso += 1
                gui_log(f"✅ Ciclo {ciclo_num + 1}/{NUM_CICLOS_TESTE} concluído!")

                if ciclo_num < NUM_CICLOS_TESTE - 1:
                    gui_log("⏳ Aguardando 2s antes do próximo ciclo...")
                    time.sleep(2)
            else:
                ciclos_falha += 1
                gui_log(f"❌ Ciclo {ciclo_num + 1}/{NUM_CICLOS_TESTE} falhou!")
                break

        # Estatísticas finais
        print()
        print("=" * 70)
        print("📊 ESTATÍSTICAS FINAIS DO TESTE")
        print("=" * 70)
        print(f"✅ Ciclos com sucesso: {ciclos_sucesso}")
        print(f"❌ Ciclos com falha: {ciclos_falha}")
        print(f"📦 Total de itens processados: {_itens_processados_total}")
        print(f"🔄 Tentativas de duplicação: {_tentativas_duplicacao}")
        print(f"🛡️ Duplicações bloqueadas: {_duplicacoes_bloqueadas}")
        print(f"💾 Itens no cache final: {len(cache.dados)}")

        if _tentativas_duplicacao > 0:
            taxa_bloqueio = (_duplicacoes_bloqueadas / _tentativas_duplicacao) * 100
            print(f"📈 Taxa de bloqueio: {taxa_bloqueio:.1f}%")

        print("=" * 70)

        # Salvar relatório
        relatorio = {
            "data_teste": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ciclos_sucesso": ciclos_sucesso,
            "ciclos_falha": ciclos_falha,
            "itens_processados": _itens_processados_total,
            "tentativas_duplicacao": _tentativas_duplicacao,
            "duplicacoes_bloqueadas": _duplicacoes_bloqueadas,
            "itens_cache_final": len(cache.dados),
            "configuracoes": {
                "limite_itens": LIMITE_ITENS_TESTE,
                "testar_duplicacao": TESTAR_DUPLICACAO,
                "num_ciclos": NUM_CICLOS_TESTE
            }
        }

        relatorio_path = BASE_DIR / "relatorio_teste_ciclo.json"
        with open(relatorio_path, 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, indent=2, ensure_ascii=False)

        gui_log(f"📄 Relatório salvo em: {relatorio_path}")

    except KeyboardInterrupt:
        gui_log("⏸️ Teste interrompido pelo usuário (Ctrl+C)")
    except Exception as e:
        gui_log(f"❌ Erro fatal no teste: {e}")
        import traceback
        gui_log(traceback.format_exc())
    finally:
        _rpa_running = False
        print()
        gui_log("🏁 Teste finalizado!")

if __name__ == "__main__":
    main()
