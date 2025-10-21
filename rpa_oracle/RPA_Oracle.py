# -*- coding: utf-8 -*-
import threading
import time
import traceback
import os
import sys
import csv
import subprocess
import json
import random
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
MODO_TESTE = False  # True = simula Oracle sem pyautogui | False = PRODUÇÃO
PARAR_QUANDO_VAZIO = False  # True = para quando vazio (teste) | False = continua rodando (PRODUÇÃO)
SIMULAR_FALHA_SHEETS = False  # True = força falhas para testar retry | False = PRODUÇÃO

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY"  # PLANILHA MODO TESTE ORACLE
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
        # VALIDAÇÃO: não permitir IDs vazios no cache
        if not id_item or str(id_item).strip() == "":
            log_interface(f"[ERRO CACHE] Tentativa de adicionar ID vazio ao cache! Linha: {linha_atual}, Item: {item}")
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

    PROTEÇÃO ANTI-DUPLICAÇÃO:
    - Só retorna linhas onde "Status Oracle" está VAZIO
    - Se Status Oracle tiver qualquer valor (mesmo "PD"), não retorna
    - Isso evita duplicação caso cache seja limpo manualmente
    """
    res = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A1:AC"  # até AC (inclui coluna ID que está em AC)
    ).execute()
    valores = res.get("values", [])
    if not valores:
        return [], None, None

    headers, dados = valores[0], valores[1:]

    with sessao_lock:
        if not sessao["headers"]:
            sessao["headers"] = headers
            # LOG DE DIAGNÓSTICO: Mostrar nomes das colunas na primeira vez
            log_interface(f"[HEADERS] Colunas encontradas no Sheets: {headers}")

            # Mostrar índice das colunas importantes
            try:
                idx_status_oracle = headers.index("Status Oracle")
                # Converter índice para letra de coluna (0=A, 1=B, etc)
                if idx_status_oracle < 26:
                    letra_coluna = chr(65 + idx_status_oracle)
                else:
                    letra_coluna = chr(65 + idx_status_oracle // 26 - 1) + chr(65 + idx_status_oracle % 26)
                log_interface(f"[HEADERS] 'Status Oracle' está no índice {idx_status_oracle} (Coluna {letra_coluna})")
            except ValueError:
                log_interface(f"[ERRO] Coluna 'Status Oracle' não encontrada!")

    linhas = []
    linhas_analisadas = 0
    linhas_com_status_oracle_vazio = 0
    linhas_com_concluido = 0
    linhas_aprovadas = 0

    # segurança contra linhas curtas
    for i, row in enumerate(dados):
        linhas_analisadas += 1
        if len(row) < len(headers):
            row += [''] * (len(headers) - len(row))
        idx_status_oracle = headers.index("Status Oracle")
        idx_status = headers.index("Status")
        status_oracle = row[idx_status_oracle].strip()
        status = row[idx_status].strip().upper()

        # LOG DE DIAGNÓSTICO
        if linhas_analisadas <= 5:  # Mostrar apenas as primeiras 5 linhas
            log_interface(f"[DEBUG BUSCA] Linha {i+2}: Status Oracle='{status_oracle}' | Status='{status}'")

        # Contar condições
        if status_oracle == "":
            linhas_com_status_oracle_vazio += 1
        if "CONCLUÍDO" in status:
            linhas_com_concluido += 1

        # DUPLA PROTEÇÃO:
        # 1. Status Oracle deve estar completamente vazio
        # 2. Status deve conter "CONCLUÍDO"
        if status_oracle == "" and "CONCLUÍDO" in status:
            linhas_aprovadas += 1
            linhas.append((i + 2, dict(zip(headers, row))))  # +2 cabeçalho + 1-based

    # LOG FINAL DA BUSCA
    log_interface(f"[BUSCA SHEETS] Total analisadas: {linhas_analisadas}")
    log_interface(f"[BUSCA SHEETS] Com Status Oracle vazio: {linhas_com_status_oracle_vazio}")
    log_interface(f"[BUSCA SHEETS] Com CONCLUÍDO no Status: {linhas_com_concluido}")
    log_interface(f"[BUSCA SHEETS] Aprovadas para processar: {linhas_aprovadas}")

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

def atualizar_status_oracle(service, headers, linha, status_valor):
    """Atualiza o Status Oracle dinamicamente baseado no índice da coluna"""
    try:
        idx_status_oracle = headers.index("Status Oracle")
        coluna_letra = indice_para_coluna(idx_status_oracle)
        range_str = f"{SHEET_NAME}!{coluna_letra}{linha}"

        log_interface(f"[SHEETS] Atualizando linha {linha}, coluna {coluna_letra} (índice {idx_status_oracle}) com '{status_valor}'")

        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=range_str,
            valueInputOption="RAW",
            body={"values": [[status_valor]]}
        ).execute()
        return True
    except Exception as e:
        log_interface(f"[ERRO] Falha ao atualizar Status Oracle: {e}")
        return False

def verificar_erro_endereco(service, headers, i, id_item):
    """Verifica se o modal de erro de endereço apareceu na tela"""
    erro_endereco_path = os.path.join(base_path, "erroendereco.png")
    if os.path.isfile(erro_endereco_path):
        try:
            encontrado = pyautogui.locateOnScreen(erro_endereco_path, confidence=0.8)
        except (PyautoguiImageNotFoundException, PyscreezeImageNotFoundException):
            encontrado = None
        if encontrado:
            atualizar_status_oracle(service, headers, i, "PD")
            log_interface(f"[ERRO] Linha {i} marcada como 'PD' (pendente) por erro de endereço detectado.")

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
    ciclo_retry = 0
    while True:
        time.sleep(30)  # Retry a cada 30 segundos

        if not estado["executando"]:
            continue

        try:
            ciclo_retry += 1
            pendentes = cache.get_pendentes()

            if not pendentes:
                continue

            log_interface(f"[RETRY THREAD] Ciclo {ciclo_retry} - Encontrados {len(pendentes)} itens pendentes para atualizar")

            # Buscar todas as linhas do Sheets (até AC para incluir coluna ID)
            res = service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{SHEET_NAME}!A1:AC"
            ).execute()

            valores = res.get("values", [])
            if not valores:
                log_interface(f"[RETRY THREAD] Nenhum valor retornado do Sheets")
                continue

            headers, dados = valores[0], valores[1:]
            idx_id = headers.index("ID")
            idx_status_oracle = headers.index("Status Oracle")
            log_interface(f"[RETRY THREAD] Sheets carregado - {len(dados)} linhas encontradas")

            # Tentar atualizar cada pendente
            sucesso_count = 0
            falha_count = 0

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
                        log_interface(f"[RETRY THREAD] Linha ID {id_item} deletada no Sheets, removida do cache")
                    continue

                # Tentar atualizar Sheets usando detecção dinâmica
                try:
                    coluna_letra = indice_para_coluna(idx_status_oracle)
                    range_str = f"{SHEET_NAME}!{coluna_letra}{linha_atual}"

                    service.spreadsheets().values().update(
                        spreadsheetId=SPREADSHEET_ID,
                        range=range_str,
                        valueInputOption="RAW",
                        body={"values": [["Processo Oracle Concluído"]]}
                    ).execute()

                    if cache.marcar_concluido(id_item):
                        log_interface(f"[RETRY THREAD] ✓ ID {id_item} - Sheets atualizado com sucesso na coluna {coluna_letra} (linha {linha_atual}), removido do cache")
                        sucesso_count += 1
                except Exception as e:
                    # Falhou, tentará novamente em 30s
                    log_interface(f"[RETRY THREAD] ✗ ID {id_item} - Falha ao atualizar: {str(e)[:100]}")
                    falha_count += 1

            if sucesso_count > 0 or falha_count > 0:
                log_interface(f"[RETRY THREAD] Ciclo {ciclo_retry} finalizado - Sucesso: {sucesso_count}, Falhas: {falha_count}")

        except Exception as e:
            log_interface(f"[RETRY THREAD] Erro crítico no ciclo {ciclo_retry}: {str(e)[:150]}")
            log_interface(f"[RETRY THREAD] Detalhes: {traceback.format_exc()[:300]}")

def robo_loop():
    estado["executando"] = True
    log_interface("="*60)
    if MODO_TESTE:
        log_interface("[MODO TESTE ATIVADO] Simulação sem Oracle - apenas teste de lógica e Sheets")
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
                # Modo teste: para automaticamente quando não houver linhas
                if PARAR_QUANDO_VAZIO and MODO_TESTE:
                    log_interface("[MODO TESTE] Nenhuma linha para processar. Encerrando automaticamente...")
                    log_interface("[CONCLUÍDO] Todas as linhas foram processadas!")
                    estado["executando"] = False
                    set_title_running(False, " [TESTE CONCLUÍDO]")
                    restaurar_app()
                    messagebox.showinfo("Teste Concluído", "Todas as linhas foram processadas com sucesso!\n\nO robô foi parado automaticamente.")
                    break

                if not MODO_TESTE:
                    try:
                        pyautogui.press("shift")
                        log_interface("[KEEPALIVE] Pressionando shift para manter Oracle ativo")
                    except Exception as e:
                        log_interface(f"[AVISO] Erro ao pressionar shift: {e}")
                else:
                    log_interface("[MODO TESTE] Pulando keepalive (shift)")
                log_interface(f"[AGUARDANDO] Nenhuma linha nova. Aguardando {IDLE_KEEPALIVE_SECONDS}s...")
                sleep_check_pause(IDLE_KEEPALIVE_SECONDS)
                continue

            # 4) Processar
            log_interface(f"[PROCESSAMENTO] Iniciando processamento de {len(linhas)} linhas...")
            linhas_puladas = 0
            linhas_processadas = 0
            total_linhas = len(linhas)

            for idx, (i, linha) in enumerate(linhas, 1):
                if not estado["executando"]:
                    log_interface(f"[STOP] Processamento interrompido na linha {idx}/{total_linhas}")
                    break

                # Atualizar título com progresso
                try:
                    progresso = f" - {idx}/{total_linhas} linhas"
                    set_title_running(True, (" [MODO TESTE]" if MODO_TESTE else "") + progresso)
                except Exception:
                    pass

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

                    # VALIDAR ID (não pode estar vazio)
                    if not id_item or id_item == "":
                        log_interface(f"[AVISO] Linha {i} ({idx}/{len(linhas)}) - ID vazio ou invalido. Pulando.")
                        log_interface(f"[DEBUG] Dados da linha: {linha}")
                        continue

                    # VERIFICAR CACHE ANTI-DUPLICACAO
                    if cache.ja_processado(id_item):
                        linhas_puladas += 1
                        log_interface(f"[CACHE] Linha {i} ({idx}/{len(linhas)}) - ID '{id_item}' ja processado. Pulando para proximo...")
                        continue

                    # ═══════════════════════════════════════════════════════════════
                    # REGRAS DE VALIDAÇÃO (regras-rpa-oracle.txt)
                    # ═══════════════════════════════════════════════════════════════

                    # REGRA 1: Quantidade Zero
                    try:
                        qtd_float = float(str(quantidade).replace(",", ".").replace(" ", ""))
                        if qtd_float == 0:
                            atualizar_status_oracle(service, headers, i, "Quantidade Zero")
                            log_interface(f"[REGRA 1] Linha {i} - Quantidade Zero detectada. Marcada como 'Quantidade Zero'. Pulando.")
                            continue
                        elif qtd_float < 0:
                            log_interface(f"[AVISO] Linha {i} ({idx}/{len(linhas)}) - Quantidade negativa: {quantidade}. Pulando.")
                            continue
                    except ValueError:
                        log_interface(f"[AVISO] Linha {i} ({idx}/{len(linhas)}) - Quantidade nao e numero valido: {quantidade}. Pulando.")
                        continue

                    # REGRA 3: Campos vazios
                    campos_obrigatorios = {
                        "ITEM": item,
                        "SUB. ORIGEM": sub_o,
                        "END. ORIGEM": end_o,
                        "SUB. DESTINO": sub_d,
                        "END. DESTINO": end_d
                    }
                    # Apenas verifica destino se não for COD
                    if str(referencia).strip().upper().startswith("COD"):
                        # Para COD, não precisa verificar destino
                        campos_obrigatorios = {
                            "ITEM": item,
                            "SUB. ORIGEM": sub_o,
                            "END. ORIGEM": end_o
                        }

                    campos_vazios = [nome for nome, valor in campos_obrigatorios.items() if not valor or str(valor).strip() == ""]
                    if campos_vazios:
                        atualizar_status_oracle(service, headers, i, "Campo vazio encontrado")
                        log_interface(f"[REGRA 3] Linha {i} - Campos vazios: {', '.join(campos_vazios)}. Marcada como 'Campo vazio encontrado'. Pulando.")
                        continue

                    # REGRA 2 e 4: Transações não autorizadas
                    subinvs_restritos = ["RAWINDIR", "RAWMANUT", "RAWWAFIFE"]
                    sub_o_upper = str(sub_o).strip().upper()
                    sub_d_upper = str(sub_d).strip().upper()

                    # REGRA 2: RAWINDIR/RAWMANUT/RAWWAFIFE -> RAWCENTR não autorizado
                    if sub_o_upper in subinvs_restritos and sub_d_upper == "RAWCENTR":
                        atualizar_status_oracle(service, headers, i, "Transação não autorizada")
                        log_interface(f"[REGRA 2] Linha {i} - Transação {sub_o} -> {sub_d} não autorizada. Marcada como 'Transação não autorizada'. Pulando.")
                        continue

                    # REGRA 4: RAWINDIR/RAWMANUT/RAWWAFIFE para eles mesmos não autorizado
                    if sub_o_upper in subinvs_restritos and sub_o_upper == sub_d_upper:
                        atualizar_status_oracle(service, headers, i, "Transação não autorizada")
                        log_interface(f"[REGRA 4] Linha {i} - Transação {sub_o} -> {sub_d} (mesmo subinv) não autorizada. Marcada como 'Transação não autorizada'. Pulando.")
                        continue

                    log_interface(
                        f"[PROCESSANDO] Linha {i} ({idx}/{len(linhas)}): ID={id_item} | Item={item} | Qtd={quantidade} | "
                        f"Origem={sub_o}/{end_o} | Destino={sub_d}/{end_d} | Ref={referencia}"
                    )

                    if MODO_TESTE:
                        log_interface(f"[MODO TESTE] Simulando preenchimento no Oracle (sem pyautogui)...")
                        time.sleep(1)  # Simula o tempo de preenchimento
                    else:
                        # Verificar posição do mouse antes de começar
                        pos_inicial = pyautogui.position()
                        log_interface(f"[DEBUG] Posicao inicial do mouse: {pos_inicial}")

                        # preenchimentos no Oracle
                        log_interface(f"[ORACLE] Clicando no campo Item em {coords['item']}")
                        pyautogui.click(coords["item"])
                        time.sleep(0.3)
                        log_interface(f"[ORACLE] Limpando campo Item")
                        pyautogui.press("delete")
                        time.sleep(0.2)
                        log_interface(f"[ORACLE] Digitando Item: '{item}'")
                        pyautogui.write(item)
                        time.sleep(0.2)
                        log_interface(f"[ORACLE] Pressionando Tab")
                        pyautogui.press("tab")
                        sleep_check_pause(1)
                        if not estado["executando"]:
                            break

                    if MODO_TESTE:
                        # No modo teste, pula verificações de tela
                        log_interface(f"[MODO TESTE] Pulando verificações de erro de produto...")
                    else:
                        # erro de produto?
                        erro_produto_path = os.path.join(base_path, "ErroProduto.png")
                        if os.path.isfile(erro_produto_path):
                            try:
                                encontrado = pyautogui.locateOnScreen(erro_produto_path, confidence=0.8)
                            except (PyautoguiImageNotFoundException, PyscreezeImageNotFoundException):
                                encontrado = None
                            if encontrado:
                                atualizar_status_oracle(service, headers, i, "PD")
                                log_interface(f"[ERRO] Linha {i} marcada como 'PD' (pendente) por erro detectado.")

                                estado["executando"] = False
                                set_title_running(False, " [Erro Produto]")
                                restaurar_app()
                                messagebox.showerror("Erro de Produto", "Erro de produto detectado. Robo parado!")
                                return  # Para completamente o robô

                    if MODO_TESTE:
                        log_interface(f"[MODO TESTE] Simulando preenchimento de Referencia, Sub/End Origem...")
                        time.sleep(0.5)
                    else:
                        # *** NOVA LÓGICA PARA REFERÊNCIA COMEÇANDO COM "COD" OU NÃO ***
                        pyautogui.click(coords["Referencia"])
                        pyautogui.write(referencia)
                        pyautogui.press("tab")
                        sleep_check_pause(1)

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
                        if verificar_erro_endereco(service, headers, i, id_item):
                            return  # Para completamente o robô

                    # Verifica se referencia inicia com "COD"
                    if str(referencia).strip().upper().startswith("COD"):
                        log_interface(f"[COD] Referencia '{referencia}' detectada como tipo COD. Pulando campos destino.")
                        if not MODO_TESTE:
                            pyautogui.press("tab"); sleep_check_pause(1)  # pular sub_destino
                            pyautogui.press("tab"); sleep_check_pause(1)  # pular end_destino
                    else:
                        log_interface(f"[MOV] Referencia '{referencia}' tratada como MOV. Preenchendo normalmente.")
                        if MODO_TESTE:
                            log_interface(f"[MODO TESTE] Simulando preenchimento de Sub/End Destino...")
                            time.sleep(0.5)
                        else:
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
                            if verificar_erro_endereco(service, headers, i, id_item):
                                return  # Para completamente o robô

                    if MODO_TESTE:
                        log_interface(f"[MODO TESTE] Simulando preenchimento de quantidade e Ctrl+S...")
                        time.sleep(0.5)
                    else:
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
                    linhas_processadas += 1
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

                except Exception as e_proc:
                    log_interface(f"[ERRO] Erro no processamento da linha {i} (ID {id_item}): {str(e_proc)[:150]}")
                    log_interface(f"[ERRO] Traceback: {traceback.format_exc()[:500]}")
                    # IMPORTANTE: Não para o loop, apenas registra o erro e continua
                    log_interface(f"[AVISO] Pulando linha {i} devido ao erro. Continuando com a próxima...")
                    sleep_check_pause(2)  # Pausa breve antes de continuar

                if sucesso:
                    # Atualiza Sheets - usando detecção dinâmica da coluna Status Oracle
                    try:
                        # SIMULAÇÃO DE FALHA (modo teste)
                        if SIMULAR_FALHA_SHEETS and random.random() < 0.5:
                            raise Exception("FALHA SIMULADA - Testando retry automático")

                        idx_status_oracle = headers.index("Status Oracle")
                        coluna_letra = indice_para_coluna(idx_status_oracle)
                        range_str = f"{SHEET_NAME}!{coluna_letra}{i}"

                        log_interface(f"[SHEETS] Tentando atualizar linha {i}, coluna {coluna_letra} (índice {idx_status_oracle}) - ID {id_item}")

                        service.spreadsheets().values().update(
                            spreadsheetId=SPREADSHEET_ID,
                            range=range_str,
                            valueInputOption="RAW",
                            body={"values": [["Processo Oracle Concluído"]]}
                        ).execute()

                        # Remove do cache ao concluir
                        if cache.marcar_concluido(id_item):
                            log_interface(f"[SHEETS] ✓ ID {id_item} - Sheets atualizado com sucesso na coluna {coluna_letra}, removido do cache")
                        else:
                            log_interface(f"[AVISO] ID {id_item} não estava no cache para remover")

                    except Exception as err_up:
                        log_interface(f"[ERRO SHEETS] ID {id_item} - Falha ao atualizar linha {i}: {str(err_up)[:150]}")
                        log_interface(f"[RETRY] ID {id_item} permanece no cache. Thread de retry tentará atualizar em 30s...")
                        # NÃO IMPRIME O TRACEBACK COMPLETO PARA NÃO POLUIR O LOG

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

                    # Log de progresso a cada 100 linhas
                    if idx % 100 == 0:
                        log_interface(f"[PROGRESSO] {idx}/{total_linhas} linhas processadas ({(idx/total_linhas*100):.1f}%)")
                    elif idx % 10 == 0:
                        # Log mais simples a cada 10 linhas (apenas no console interno)
                        pass  # Removido para não poluir

                    log_interface(f"[PROCESSAMENTO] Linha {i} (ID {id_item}) concluída. Continuando para próxima linha...")

            # 5) Log do resumo do processamento
            log_interface(f"[RESUMO] Ciclo finalizado: {linhas_processadas} linhas processadas, {linhas_puladas} linhas puladas (cache)")
            log_interface(f"[CONTINUAÇÃO] Loop continuará no próximo ciclo...")

            # 6) Pausa curta antes do próximo ciclo
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
    mensagem_confirmacao = "MODO TESTE ATIVADO!\n\nNão irá preencher no Oracle, apenas testará a lógica.\nDeseja iniciar?" if MODO_TESTE else "Oracle está pronto? Deseja iniciar?"
    if not messagebox.askyesno("Confirmação", mensagem_confirmacao):
        return

    if not MODO_TESTE:
        # TESTE DO PYAUTOGUI ANTES DE MINIMIZAR (só no modo real)
        try:
            pos = pyautogui.position()
            log_interface(f"[DEBUG] PyAutoGUI OK - Posição do mouse: {pos}")
            log_interface(f"[DEBUG] Tamanho da tela: {pyautogui.size()}")
            log_interface(f"[DEBUG] Failsafe: {pyautogui.FAILSAFE}")
            log_interface(f"[DEBUG] Coordenadas configuradas: {coords}")
        except Exception as e:
            log_interface(f"[ERRO] PyAutoGUI não está funcionando: {e}")
            messagebox.showerror("Erro", f"PyAutoGUI não está funcionando:\n{e}")
            return

        # Dar tempo para o usuário ver os logs antes de minimizar
        log_interface("[INFO] Minimizando janela em 2 segundos...")
        time.sleep(2)
        app.iconify()  # minimiza a janela para não atrapalhar
    else:
        log_interface("[MODO TESTE] Janela não será minimizada para facilitar acompanhamento")

    status_label.config(text="Status: Rodando" + (" [TESTE]" if MODO_TESTE else ""))
    set_title_running(True, " [MODO TESTE]" if MODO_TESTE else "")
    estado["executando"] = True
    log_interface("[DEBUG] Robô iniciado" + (" em modo teste" if MODO_TESTE else " e minimizado"))
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