# -*- coding: utf-8 -*-
import threading
import time
import traceback
import os
import sys
import csv
import subprocess
import json
import tkinter as tk
from tkinter import messagebox
import pyautogui
import keyboard
from PIL import Image, ImageTk
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from pyscreeze import ImageNotFoundException as PyscreezeImageNotFoundException
from pyautogui import ImageNotFoundException as PyautoguiImageNotFoundException

# Diretório base compatível com .exe
base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

# Diretório para arquivos de dados (onde o .exe está)
data_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))

# ─── CONFIGURAÇÕES ───────────────────────────────────────────────────────────
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk"
SHEET_NAME = "Separação"

# Intervalos
QUICK_RECHECK_SECONDS = 5
IDLE_KEEPALIVE_SECONDS = 30

# Pasta de exportações
EXPORT_DIR = os.path.join(data_path, "exportacoes")

coords = {
    "item": (101, 156),
    "sub_origem": (257, 159),
    "end_origem": (335, 159),
    "sub_destino": (485, 159),
    "end_destino": (553, 159),
    "quantidade": (672, 159),
    "Referencia": (768, 159),
}

estado = {"executando": False}

# Armazena o que foi processado nesta sessão (some quando fechar o app)
sessao = {
    "headers": None,   # lista com nomes das colunas (A..T)
    "rows": []         # lista de listas com as linhas processadas
}
sessao_lock = threading.Lock()

# ─── CACHE LOCAL ANTI-DUPLICAÇÃO ────────────────────────────────────────────
class CacheLocal:
    """Cache persistente para evitar duplicações no Oracle"""

    def __init__(self, arquivo="processados.json"):
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
                print(f"Erro ao carregar cache: {e}")
                return {}
        return {}

    def _salvar(self):
        """Salva cache no disco com lock"""
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
            log_interface(f"[ERRO] Falha ao salvar cache: {e}")
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

    def marcar_concluido(self, id_item):
        """Remove do cache quando Sheets for atualizado com sucesso"""
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
        """Retorna lista de IDs pendentes para retry"""
        with self.lock:
            return [
                id_item for id_item, dados in self.dados.items()
                if dados.get("status_sheets") == "pendente"
            ]

# ─── HELPERS DE UI ───────────────────────────────────────────────────────────
def set_title_running(is_running: bool, extra: str = ""):
    base = "RPA Genesys"
    sufixo = " [Rodando]" if is_running else " [Parado]"
    try:
        app.title(f"{base}{sufixo}{extra}")
    except Exception:
        pass

def restaurar_app():
    try:
        app.deiconify()
        app.lift()
        try:
            app.focus_force()
        except Exception:
            pass
    except Exception:
        pass

def log_interface(msg: str):
    log_text.config(state='normal')
    log_text.insert('end', msg + '\n')
    log_text.see('end')
    log_text.config(state='disabled')

# ─── GOOGLE SHEETS ───────────────────────────────────────────────────────────
def authenticate_google():
    token_path = os.path.join(data_path, "token.json")
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
    return build("sheets", "v4", credentials=creds)

def buscar_linhas_novas(service):
    """
    Lê a planilha e retorna lista de tuplas (linha_index_na_planilha, dict_dos_campos)
    para linhas com Status Oracle vazio e Status contendo 'CONCLUÍDO'.
    """
    res = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A1:T"  # até T (Status Oracle)
    ).execute()
    valores = res.get("values", [])
    if not valores:
        return [], None, None

    headers, dados = valores[0], valores[1:]

    with sessao_lock:
        if not sessao["headers"]:
            sessao["headers"] = headers

    linhas = []
    # segurança contra linhas curtas
    for i, row in enumerate(dados):
        if len(row) < len(headers):
            row += [''] * (len(headers) - len(row))
        idx_status_oracle = headers.index("Status Oracle")
        idx_status = headers.index("Status")
        status_oracle = row[idx_status_oracle].strip()
        status = row[idx_status].strip().upper()
        if status_oracle == "" and "CONCLUÍDO" in status:
            linhas.append((i + 2, dict(zip(headers, row))))  # +2 cabeçalho + 1-based
    return linhas, headers, dados

# ─── EXPORTAÇÃO (apenas sessão) ──────────────────────────────────────────────
def exportar_movimentacoes():
    """Exporta somente o que foi processado nesta sessão."""
    try:
        with sessao_lock:
            headers = sessao["headers"]
            rows = list(sessao["rows"])  # cópia

        if not headers or not rows:
            messagebox.showinfo("Exportar Movimentacoes", "Nao ha movimentacoes desta sessao para exportar.")
            log_interface("[INFO] Exportacao cancelada: sessao sem registros.")
            return

        os.makedirs(EXPORT_DIR, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        out_path = os.path.join(EXPORT_DIR, f"export_sessao_{ts}.csv")
        with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(headers)
            writer.writerows(rows)

        log_interface(f"[SUCESSO] Exportado (sessao) para: {out_path}")
        messagebox.showinfo("Exportar Movimentacoes", f"Exportacao concluida!\n\nArquivo:\n{out_path}")
    except Exception as e:
        log_interface(f"[ERRO] Erro ao exportar (sessao): {e}")
        messagebox.showerror("Exportar Movimentacoes", f"Erro ao exportar:\n{e}")

def abrir_pasta_exportacoes():
    """Abre a pasta de exportações no Explorer/Finder."""
    try:
        os.makedirs(EXPORT_DIR, exist_ok=True)
        if sys.platform.startswith("win"):
            os.startfile(EXPORT_DIR)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", EXPORT_DIR])
        else:
            subprocess.Popen(["xdg-open", EXPORT_DIR])
        log_interface(f"[INFO] Pasta aberta: {EXPORT_DIR}")
    except Exception as e:
        log_interface(f"[ERRO] Nao foi possivel abrir a pasta: {e}")
        messagebox.showerror("Abrir Pasta", f"Nao foi possivel abrir a pasta:\n{e}")

def limpar_cache():
    """Limpa o cache de itens pendentes (processados.json)"""
    try:
        cache_path = os.path.join(data_path, "processados.json")
        if os.path.exists(cache_path):
            num_itens = len(json.load(open(cache_path, 'r', encoding='utf-8')))
            resposta = messagebox.askyesno(
                "Limpar Cache",
                f"Isso ira limpar o cache de {num_itens} itens pendentes.\n\n"
                "Itens pendentes sao aqueles que ja foram processados no Oracle\n"
                "mas ainda nao foram atualizados no Google Sheets.\n\n"
                "Deseja continuar?"
            )
            if resposta:
                os.remove(cache_path)
                log_interface("[CACHE] Cache limpo com sucesso!")
                messagebox.showinfo("Cache Limpo", f"{num_itens} itens pendentes foram removidos do cache!")
        else:
            messagebox.showinfo("Cache", "Nao ha cache para limpar (cache vazio).")
            log_interface("[CACHE] Nenhum cache encontrado.")
    except Exception as e:
        log_interface(f"[ERRO] Erro ao limpar cache: {e}")
        messagebox.showerror("Erro", f"Erro ao limpar cache:\n{e}")

def diagnostico_sistema():
    """Mostra informações de diagnóstico do sistema"""
    try:
        info = []

        # Verificar cache
        cache_path = os.path.join(data_path, "processados.json")
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                # Agora cache só contém pendentes (concluídos são removidos)
                info.append(f"Cache: {len(cache_data)} itens pendentes")
                if len(cache_data) > 0:
                    info.append("(aguardando atualizacao no Sheets)")
        else:
            info.append("Cache: Vazio (nenhum item pendente)")

        # Verificar token Google
        if os.path.exists("token.json"):
            info.append("Token Google: Autenticado")
        else:
            info.append("Token Google: Nao autenticado")

        # Verificar credenciais
        creds_path = os.path.join(base_path, "CredenciaisOracle.json")
        if os.path.exists(creds_path):
            info.append("Credenciais: OK")
        else:
            info.append("Credenciais: FALTANDO")

        # Verificar sessão atual
        with sessao_lock:
            info.append(f"Sessao Atual: {len(sessao['rows'])} linhas processadas")

        # Status
        info.append(f"Status: {'Rodando' if estado['executando'] else 'Parado'}")

        mensagem = "\n".join(info)
        log_interface(f"[DIAGNOSTICO]\n{mensagem}")
        messagebox.showinfo("Diagnostico do Sistema", mensagem)

    except Exception as e:
        log_interface(f"[ERRO] Erro no diagnostico: {e}")
        messagebox.showerror("Erro", f"Erro no diagnostico:\n{e}")

# ─── FUNÇÕES DE CONTROLE ─────────────────────────────────────────────────────
def sleep_check_pause(segundos):
    for _ in range(int(segundos * 10)):
        if not estado["executando"]:
            break
        time.sleep(0.1)

def verificar_erro_endereco(service, i, id_item):
    """Verifica se o modal de erro de endereço apareceu na tela"""
    erro_endereco_path = os.path.join(base_path, "erroendereco.png")
    if os.path.isfile(erro_endereco_path):
        try:
            encontrado = pyautogui.locateOnScreen(erro_endereco_path, confidence=0.8)
        except (PyautoguiImageNotFoundException, PyscreezeImageNotFoundException):
            encontrado = None
        if encontrado:
            try:
                service.spreadsheets().values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range=f"{SHEET_NAME}!T{i}",
                    valueInputOption="RAW",
                    body={"values": [["PD"]]}
                ).execute()
                log_interface(f"[ERRO] Linha {i} marcada como 'PD' (pendente) por erro de endereço detectado.")
            except Exception as err_up:
                log_interface(f"Erro ao marcar linha {i} como PD: {err_up}")

            estado["executando"] = False
            set_title_running(False, " [Erro Endereço]")
            restaurar_app()
            messagebox.showerror("Erro de Endereço", "Erro de endereço detectado. Robo parado!")
            return True
    return False

def tratar_erro_oracle():
    caminho = os.path.join(base_path, "qtd_negativa.png")
    try:
        if os.path.isfile(caminho) and pyautogui.locateOnScreen(caminho, confidence=0.8):
            pyautogui.press("enter")
            time.sleep(1)
            pyautogui.hotkey("ctrl", "s")
            time.sleep(1)
    except (PyautoguiImageNotFoundException, PyscreezeImageNotFoundException):
        pass

def sync_sheets_background(cache, service):
    """Thread que tenta atualizar Sheets para linhas pendentes (busca dinâmica)"""
    while True:
        time.sleep(30)  # Retry a cada 30 segundos

        if not estado["executando"]:
            continue

        try:
            pendentes = cache.get_pendentes()
            if not pendentes:
                continue

            # Buscar todas as linhas do Sheets
            res = service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{SHEET_NAME}!A1:T"
            ).execute()

            valores = res.get("values", [])
            if not valores:
                continue

            headers, dados = valores[0], valores[1:]
            idx_id = headers.index("ID")
            idx_status_oracle = headers.index("Status Oracle")

            # Tentar atualizar cada pendente
            for id_item in pendentes:
                # Buscar linha atual pelo ID
                linha_atual = None
                for i, row in enumerate(dados):
                    if len(row) > idx_id:
                        if row[idx_id].strip() == str(id_item):
                            linha_atual = i + 2  # +2 (header + 1-based)
                            break

                if linha_atual is None:
                    # Linha foi deletada, remove do cache
                    if cache.marcar_concluido(id_item):
                        log_interface(f"[CACHE] Linha ID {id_item} deletada no Sheets, removida do cache")
                    continue

                # Tentar atualizar Sheets
                try:
                    service.spreadsheets().values().update(
                        spreadsheetId=SPREADSHEET_ID,
                        range=f"{SHEET_NAME}!T{linha_atual}",
                        valueInputOption="RAW",
                        body={"values": [["Processo Oracle Concluído"]]}
                    ).execute()

                    if cache.marcar_concluido(id_item):
                        log_interface(f"[RETRY] ID {id_item} - Sheets atualizado com sucesso (retry), removido do cache")
                except Exception as e:
                    # Falhou, tentará novamente em 30s
                    pass

        except Exception:
            pass

def robo_loop():
    estado["executando"] = True
    log_interface("="*60)
    log_interface("[INICIO] Iniciando loop do robo...")

    try:
        service = authenticate_google()
        log_interface("[GOOGLE] Autenticacao realizada com sucesso")
    except Exception as e:
        log_interface(f"[ERRO] Falha na autenticacao Google: {e}")
        estado["executando"] = False
        set_title_running(False, " [Erro Auth]")
        restaurar_app()
        messagebox.showerror("Erro de Autenticacao", f"Falha ao autenticar:\n{e}")
        return

    # Inicializar cache anti-duplicação
    cache = CacheLocal("processados.json")
    log_interface(f"[CACHE] Cache carregado: {len(cache.dados)} itens processados anteriormente")

    # Iniciar thread de retry em background
    threading.Thread(
        target=sync_sheets_background,
        args=(cache, service),
        daemon=True
    ).start()
    log_interface("[RETRY] Thread de retry em background iniciada")

    ciclo = 0
    while estado["executando"]:
        try:
            ciclo += 1
            log_interface(f"[CICLO {ciclo}] Iniciando nova busca...")

            # 1) Ler linhas novas
            linhas, headers, _ = buscar_linhas_novas(service)
            log_interface(f"[CICLO {ciclo}] Encontradas {len(linhas)} linhas para processar")

            # 2) Rechecar rápido
            if not linhas:
                log_interface(f"[BUSCA] Nenhuma linha encontrada. Aguardando {QUICK_RECHECK_SECONDS}s...")
                sleep_check_pause(QUICK_RECHECK_SECONDS)
                if not estado["executando"]:
                    log_interface("[STOP] Robo foi parado pelo usuario")
                    break
                linhas, headers, _ = buscar_linhas_novas(service)
                log_interface(f"[BUSCA] Segunda tentativa: {len(linhas)} linhas encontradas")

            # 3) Se ainda não houver, manter Oracle acordado e aguardar
            if not linhas:
                try:
                    pyautogui.press("shift")
                    log_interface("[KEEPALIVE] Pressionando shift para manter Oracle ativo")
                except Exception as e:
                    log_interface(f"[AVISO] Erro ao pressionar shift: {e}")
                log_interface(f"[AGUARDANDO] Nenhuma linha nova. Aguardando {IDLE_KEEPALIVE_SECONDS}s...")
                sleep_check_pause(IDLE_KEEPALIVE_SECONDS)
                continue

            # 4) Processar
            log_interface(f"[PROCESSAMENTO] Iniciando processamento de {len(linhas)} linhas...")
            for idx, (i, linha) in enumerate(linhas, 1):
                if not estado["executando"]:
                    log_interface(f"[STOP] Processamento interrompido na linha {idx}/{len(linhas)}")
                    break

                sucesso = False
                try:
                    # 🔹 Agora usamos os nomes fixos das colunas
                    id_item     = linha.get("ID", "").strip()
                    item        = linha.get("Item", "")
                    sub_o       = linha.get("Sub.Origem", "")
                    end_o       = linha.get("End. Origem", "")
                    sub_d       = linha.get("Sub. Destino", "")
                    end_d       = linha.get("End. Destino", "")
                    quantidade  = linha.get("Quantidade", "")
                    referencia  = linha.get("Cód Referencia", "")

                    # VERIFICAR CACHE ANTI-DUPLICACAO
                    if cache.ja_processado(id_item):
                        log_interface(f"[CACHE] Linha {i} ({idx}/{len(linhas)}) - ID {id_item} ja processado. Pulando.")
                        continue

                    # validar quantidade
                    try:
                        qtd_float = float(str(quantidade).replace(",", ".").replace(" ", ""))
                        if qtd_float <= 0:
                            log_interface(f"[AVISO] Linha {i} ({idx}/{len(linhas)}) - Quantidade invalida ou negativa: {quantidade}. Pulando.")
                            continue
                    except ValueError:
                        log_interface(f"[AVISO] Linha {i} ({idx}/{len(linhas)}) - Quantidade nao e numero valido: {quantidade}. Pulando.")
                        continue

                    log_interface(
                        f"[PROCESSANDO] Linha {i} ({idx}/{len(linhas)}): ID={id_item} | Item={item} | Qtd={quantidade} | "
                        f"Origem={sub_o}/{end_o} | Destino={sub_d}/{end_d} | Ref={referencia}"
                    )

                    # preenchimentos no Oracle
                    pyautogui.click(coords["item"])
                    pyautogui.press("delete")
                    pyautogui.write(item)
                    pyautogui.press("tab")
                    sleep_check_pause(1)
                    if not estado["executando"]:
                        break

                    # erro de produto?
                    erro_produto_path = os.path.join(base_path, "ErroProduto.png")
                    if os.path.isfile(erro_produto_path):
                        try:
                            encontrado = pyautogui.locateOnScreen(erro_produto_path, confidence=0.8)
                        except (PyautoguiImageNotFoundException, PyscreezeImageNotFoundException):
                            encontrado = None
                        if encontrado:
                            try:
                                service.spreadsheets().values().update(
                                    spreadsheetId=SPREADSHEET_ID,
                                    range=f"{SHEET_NAME}!T{i}",
                                    valueInputOption="RAW",
                                    body={"values": [["PD"]]}
                                ).execute()
                                log_interface(f"[ERRO] Linha {i} marcada como 'PD' (pendente) por erro detectado.")
                            except Exception as err_up:
                                log_interface(f"Erro ao marcar linha {i} como PD: {err_up}")

                            estado["executando"] = False
                            set_title_running(False, " [Erro Produto]")
                            restaurar_app()
                            messagebox.showerror("Erro de Produto", "Erro de produto detectado. Robo parado!")
                            return  # Para completamente o robô

                    # *** NOVA LÓGICA PARA REFERÊNCIA COMEÇANDO COM “COD” OU NÃO ***
                    pyautogui.click(coords["Referencia"])
                    pyautogui.write(referencia)
                    sleep_check_pause(1)
                    time.sleep(0.2)

                    pyautogui.click(coords["sub_origem"])
                    time.sleep(0.2)
                    pyautogui.write(sub_o)
                    pyautogui.press("tab")
                    sleep_check_pause(1)

                    pyautogui.press("delete")
                    pyautogui.click(coords["end_origem"])
                    time.sleep(0.2)
                    pyautogui.write(end_o)
                    pyautogui.press("tab")
                    sleep_check_pause(1)

                    # Verificar erro de endereço após preencher endereço origem
                    if verificar_erro_endereco(service, i, id_item):
                        return  # Para completamente o robô

                    # Verifica se referencia inicia com "COD"
                    if str(referencia).strip().upper().startswith("COD"):
                        log_interface(f"[COD] Referencia '{referencia}' detectada como tipo COD. Pulando campos destino.")
                        pyautogui.press("tab"); sleep_check_pause(1)  # pular sub_destino
                        pyautogui.press("tab"); sleep_check_pause(1)  # pular end_destino
                    else:
                        log_interface(f"[MOV] Referencia '{referencia}' tratada como MOV. Preenchendo normalmente.")
                        log_interface(f"[MOV] Preenchendo Sub.Destino: {sub_d}")
                        pyautogui.press("delete")
                        pyautogui.click(coords["sub_destino"])
                        time.sleep(0.2)
                        pyautogui.write(sub_d)
                        pyautogui.press("tab")
                        sleep_check_pause(1)
                        log_interface(f"[MOV] Sub.Destino preenchido, verificando pausa...")
                        if not estado["executando"]:
                            log_interface(f"[MOV] Estado executando virou False, parando...")
                            break

                        log_interface(f"[MOV] Preenchendo End.Destino: {end_d}")
                        pyautogui.press("delete")
                        pyautogui.click(coords["end_destino"])
                        time.sleep(0.2)
                        pyautogui.write(end_d)
                        pyautogui.press("tab")
                        sleep_check_pause(1)
                        log_interface(f"[MOV] End.Destino preenchido")

                        # Verificar erro de endereço após preencher endereço destino
                        if verificar_erro_endereco(service, i, id_item):
                            return  # Para completamente o robô

                    log_interface(f"[QUANTIDADE] Preenchendo quantidade: {quantidade}")
                    pyautogui.press("delete")
                    pyautogui.click(coords["quantidade"])
                    time.sleep(0.2)
                    pyautogui.write(quantidade)
                    sleep_check_pause(1)
                    log_interface(f"[QUANTIDADE] Quantidade preenchida")

                    log_interface(f"[SAVE] Salvando com Ctrl+S...")
                    pyautogui.hotkey("ctrl", "s")
                    sleep_check_pause(1)
                    time.sleep(0.5)
                    log_interface(f"[SAVE] Ctrl+S executado, tratando possíveis erros...")

                    tratar_erro_oracle()
                    sucesso = True
                    log_interface(f"[SUCESSO] Processamento no Oracle concluído para ID {id_item}")

                    # GRAVAR NO CACHE (APOS Ctrl+S, ANTES de tentar Sheets)
                    try:
                        log_interface(f"[CACHE] Tentando adicionar ID {id_item} ao cache...")
                        cache.adicionar(
                            id_item=id_item,
                            linha_atual=i,
                            item=item,
                            quantidade=quantidade,
                            referencia=referencia,
                            status="pendente"
                        )
                        log_interface(f"[CACHE] ID {id_item} registrado no cache com sucesso")
                    except Exception as e_cache:
                        log_interface(f"[AVISO] Erro ao adicionar ao cache: {e_cache}")

                except Exception:
                    log_interface(traceback.format_exc())

                if sucesso:
                    # Atualiza Sheets - usando o indice correto (i ja e a linha correta)
                    try:
                        log_interface(f"[SHEETS] Tentando atualizar Sheets linha {i} coluna T (ID {id_item})...")
                        service.spreadsheets().values().update(
                            spreadsheetId=SPREADSHEET_ID,
                            range=f"{SHEET_NAME}!T{i}",
                            valueInputOption="RAW",
                            body={"values": [["Processo Oracle Concluído"]]}
                        ).execute()

                        # Remove do cache ao concluir
                        if cache.marcar_concluido(id_item):
                            log_interface(f"[SHEETS] ID {id_item} - Sheets atualizado com sucesso, removido do cache")

                    except Exception as err_up:
                        log_interface(f"[ERRO] ID {id_item} - Falha ao atualizar Sheets linha {i}: {err_up}. Retry em background...")
                        import traceback
                        log_interface(f"[ERRO] Detalhes do erro: {traceback.format_exc()}")

                    # Guarda linha desta sessão (com Status Oracle definido)
                    try:
                        with sessao_lock:
                            if not sessao["headers"]:
                                sessao["headers"] = headers
                            linha_sessao = [linha.get(h, "") for h in headers]
                            idx_so = headers.index("Status Oracle")
                            if idx_so < len(linha_sessao):
                                linha_sessao[idx_so] = "Processo Oracle Concluído"
                            sessao["rows"].append(linha_sessao)
                    except Exception as e:
                        log_interface(f"[AVISO] Nao foi possivel registrar a linha na sessao: {e}")

                    sleep_check_pause(1)

            # 5) Pausa curta antes do próximo ciclo
            log_interface(f"[CICLO {ciclo}] Ciclo concluido. Aguardando {QUICK_RECHECK_SECONDS}s ate proximo ciclo...")
            sleep_check_pause(QUICK_RECHECK_SECONDS)

        except Exception as e:
            log_interface(f"[ERRO CRITICO] Erro no loop principal: {e}")
            log_interface(traceback.format_exc())
            estado["executando"] = False
            set_title_running(False, " [Erro]")
            restaurar_app()
            messagebox.showerror("Erro", f"Erro inesperado no loop:\n{str(e)[:200]}\n\nVeja o log para mais detalhes.")

    log_interface("="*60)
    log_interface("[FIM] Loop do robo encerrado")
    estado["executando"] = False
    set_title_running(False)

def monitorar_tecla():
    def parar_callback(event):
        if event.name == 'esc' and estado["executando"]:
            estado["executando"] = False
            status_label.config(text="[PAUSADO] Pausado por hotkey")
            set_title_running(False, " [Pausado]")
            restaurar_app()
            keyboard.unhook_all()

    keyboard.hook(parar_callback)
    while estado["executando"]:
        time.sleep(0.1)

def iniciar_robo():
    if not messagebox.askyesno("Confirmação", "Oracle está pronto? Deseja iniciar?"):
        return
    app.iconify()  # minimiza a janela
    status_label.config(text="Status: Rodando")
    set_title_running(True)
    estado["executando"] = True
    threading.Thread(target=robo_loop, daemon=True).start()
    threading.Thread(target=monitorar_tecla, daemon=True).start()

def parar_robo():
    estado["executando"] = False
    status_label.config(text="Status: Parado")
    set_title_running(False)
    restaurar_app()

# ─── INTERFACE ───────────────────────────────────────────────────────────────
app = tk.Tk()
app.title("RPA Genesys")
app.geometry("500x560")

try:
    app.iconphoto(True, ImageTk.PhotoImage(file=os.path.join(base_path, "Topo.png")))
except Exception as e:
    print(f"Erro ao definir ícone: {e}")

try:
    logo_frame = tk.Frame(app, bg="#f7f7f7")
    logo1_img = Image.open(os.path.join(base_path, "Logo.png")).resize((150, 90))
    logo2_img = Image.open(os.path.join(base_path, "Tecumseh.png")).resize((90, 70))
    logo1_tk = ImageTk.PhotoImage(logo1_img)
    logo2_tk = ImageTk.PhotoImage(logo2_img)
    tk.Label(logo_frame, image=logo1_tk, bg="#f7f7f7").pack(side="left", padx=10)
    tk.Label(logo_frame, image=logo2_tk, bg="#f7f7f7").pack(side="left", padx=10)
    logo_frame.pack(pady=(20, 5))
except Exception as e:
    print(f"[ERRO] Erro ao carregar logos: {e}")

tk.Button(app, text="Iniciar", command=iniciar_robo, bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).pack(pady=5)
tk.Button(app, text="Parar", command=parar_robo, bg="#f44336", fg="white", font=("Arial", 10, "bold")).pack(pady=5)

# Botões de exportação
tk.Button(app, text="Exportar Movimentações", command=exportar_movimentacoes).pack(pady=(8, 2))
tk.Button(app, text="Abrir Pasta de Exportações", command=abrir_pasta_exportacoes).pack(pady=(0, 5))

# Frame para botões de manutenção
manutencao_frame = tk.Frame(app)
manutencao_frame.pack(pady=5)
tk.Button(manutencao_frame, text="Limpar Cache", command=limpar_cache, bg="#FF9800", fg="white").pack(side="left", padx=5)
tk.Button(manutencao_frame, text="Diagnóstico", command=diagnostico_sistema, bg="#2196F3", fg="white").pack(side="left", padx=5)

status_label = tk.Label(app, text="Status: Aguardando")
status_label.pack(pady=5)

tk.Label(app, text="Log de Execucao:").pack()
log_text = tk.Text(app, height=16, width=70, wrap=tk.WORD, state='disabled')
log_text.pack(pady=5)

# Ajusta o título inicial
set_title_running(False)

app.mainloop()