# -*- coding: utf-8 -*-
import threading
import time
import traceback
import os
import sys
import csv
import subprocess
import tkinter as tk
from tkinter import messagebox
import pyautogui
import keyboard
from PIL import Image, ImageTk
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from pyscreeze import ImageNotFoundException as PyscreezeImageNotFoundException
from pyautogui import ImageNotFoundException as PyautoguiImageNotFoundException

# Diretório base compatível com .exe
base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

# ─── CONFIGURAÇÕES ───────────────────────────────────────────────────────────
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY"
SHEET_NAME = "Separação"

# Intervalos
QUICK_RECHECK_SECONDS = 5
IDLE_KEEPALIVE_SECONDS = 30

# Pasta de exportações
EXPORT_DIR = os.path.join(base_path, "exportacoes")

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
            messagebox.showinfo("Exportar Movimentações", "Não há movimentações desta sessão para exportar.")
            log_interface("ℹ️ Exportação cancelada: sessão sem registros.")
            return

        os.makedirs(EXPORT_DIR, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        out_path = os.path.join(EXPORT_DIR, f"export_sessao_{ts}.csv")
        with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(headers)
            writer.writerows(rows)

        log_interface(f"✅ Exportado (sessão) para: {out_path}")
        messagebox.showinfo("Exportar Movimentações", f"Exportação concluída!\n\nArquivo:\n{out_path}")
    except Exception as e:
        log_interface(f"❌ Erro ao exportar (sessão): {e}")
        messagebox.showerror("Exportar Movimentações", f"Erro ao exportar:\n{e}")

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
        log_interface(f"📂 Pasta aberta: {EXPORT_DIR}")
    except Exception as e:
        log_interface(f"❌ Não foi possível abrir a pasta: {e}")
        messagebox.showerror("Abrir Pasta", f"Não foi possível abrir a pasta:\n{e}")

# ─── FUNÇÕES DE CONTROLE ─────────────────────────────────────────────────────
def sleep_check_pause(segundos):
    for _ in range(int(segundos * 10)):
        if not estado["executando"]:
            break
        time.sleep(0.1)

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

def robo_loop():
    estado["executando"] = True
    service = authenticate_google()

    while estado["executando"]:
        try:
            # 1) Ler linhas novas
            linhas, headers, _ = buscar_linhas_novas(service)

            # 2) Rechecar rápido
            if not linhas:
                log_interface("🔎 Procurando novas linhas…")
                sleep_check_pause(QUICK_RECHECK_SECONDS)
                if not estado["executando"]:
                    break
                linhas, headers, _ = buscar_linhas_novas(service)

            # 3) Se ainda não houver, manter Oracle acordado e aguardar
            if not linhas:
                try:
                    pyautogui.press("shift")
                except Exception:
                    pass
                log_interface("⏳ Nenhuma linha nova. Aguardando…")
                sleep_check_pause(IDLE_KEEPALIVE_SECONDS)
                continue

            # 4) Processar
            for i, linha in linhas:
                if not estado["executando"]:
                    break

                # ✅ ATUALIZA IMEDIATAMENTE COMO CONCLUÍDO PARA EVITAR DUPLICAÇÃO
                atualizado_sucesso = False
                try:
                    service.spreadsheets().values().update(
                        spreadsheetId=SPREADSHEET_ID,
                        range=f"{SHEET_NAME}!T{i}",
                        valueInputOption="RAW",
                        body={"values": [["Processo Oracle Concluído"]]}
                    ).execute()
                    log_interface(f"✅ Linha {i} marcada como 'Processo Oracle Concluído'")
                    atualizado_sucesso = True
                except Exception as err_up:
                    log_interface(f"❌ Erro ao marcar linha {i} como concluída: {err_up}")
                    log_interface(f"⚠️ Linha {i} IGNORADA - não será processada no Oracle")
                    continue  # Pula essa linha e vai para a próxima

                sucesso = False
                try:
                    # 🔹 Agora usamos os nomes fixos das colunas
                    item        = linha.get("Item", "")
                    sub_o       = linha.get("Sub.Origem", "")
                    end_o       = linha.get("End. Origem", "")
                    sub_d       = linha.get("Sub. Destino", "")
                    end_d       = linha.get("End. Destino", "")
                    quantidade  = linha.get("Quantidade", "")
                    referencia  = linha.get("Cód Referencia", "")

                    # validar quantidade
                    try:
                        qtd_float = float(str(quantidade).replace(",", ".").replace(" ", ""))
                        if qtd_float <= 0:
                            continue
                    except ValueError:
                        continue

                    log_interface(
                        f"▶ Linha {i}: Item={item} | Qtd={quantidade} | Origem={sub_o}/{end_o} | "
                        f"Destino={sub_d}/{end_d} | Ref={referencia}"
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
                                log_interface(f"❗ Linha {i} marcada como 'PD' (pendente) por erro detectado.")
                            except Exception as err_up:
                                log_interface(f"Erro ao marcar linha {i} como PD: {err_up}")

                            estado["executando"] = False
                            set_title_running(False, " [Erro Produto]")
                            restaurar_app()
                            messagebox.showerror("Erro de Produto", "❌ Erro de produto detectado. Robô parado!")
                            break

                    # *** NOVA LÓGICA PARA REFERÊNCIA COMEÇANDO COM "COD" OU NÃO ***
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

                    # Verifica se referência inicia com "COD"
                    if str(referencia).strip().upper().startswith("COD"):
                        log_interface(f"⚙️ Referência '{referencia}' detectada como tipo COD. Pulando campos destino.")
                        pyautogui.press("tab"); sleep_check_pause(1)  # pular sub_destino
                        pyautogui.press("tab"); sleep_check_pause(1)  # pular end_destino
                    else:
                        log_interface(f"🔁 Referência '{referencia}' tratada como MOV. Preenchendo normalmente.")
                        pyautogui.press("delete")
                        pyautogui.click(coords["sub_destino"])
                        time.sleep(0.2)
                        pyautogui.write(sub_d)
                        pyautogui.press("tab")
                        sleep_check_pause(1)

                        pyautogui.press("delete")
                        pyautogui.click(coords["end_destino"])
                        time.sleep(0.2)
                        pyautogui.write(end_d)
                        pyautogui.press("tab")
                        sleep_check_pause(1)

                    pyautogui.press("delete")
                    pyautogui.click(coords["quantidade"])
                    time.sleep(0.2)
                    pyautogui.write(quantidade)
                    sleep_check_pause(1)

                    pyautogui.hotkey("ctrl", "s")
                    sleep_check_pause(1)
                    time.sleep(0.5)

                    tratar_erro_oracle()
                    sucesso = True

                except Exception:
                    log_interface(traceback.format_exc())

                if sucesso:
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
                        log_interface(f"⚠️ Não foi possível registrar a linha na sessão: {e}")

                    sleep_check_pause(1)

            # 5) Pausa curta antes do próximo ciclo
            sleep_check_pause(QUICK_RECHECK_SECONDS)

        except Exception:
            log_interface(traceback.format_exc())
            estado["executando"] = False
            set_title_running(False, " [Erro]")
            restaurar_app()
            messagebox.showerror("Erro", "Erro inesperado. Veja o log.")

def monitorar_tecla():
    def parar_callback(event):
        if event.name == 'esc' and estado["executando"]:
            estado["executando"] = False
            status_label.config(text="⏸️ Pausado por hotkey")
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
    print(f"❌ Erro ao carregar logos: {e}")

tk.Button(app, text="Iniciar", command=iniciar_robo).pack(pady=5)
tk.Button(app, text="Parar", command=parar_robo).pack(pady=5)

# Botões de exportação
tk.Button(app, text="Exportar Movimentações", command=exportar_movimentacoes).pack(pady=(8, 2))
tk.Button(app, text="Abrir Pasta de Exportações", command=abrir_pasta_exportacoes).pack(pady=(0, 10))

status_label = tk.Label(app, text="Status: Aguardando")
status_label.pack(pady=5)

tk.Label(app, text="📋 Log de Execução:").pack()
log_text = tk.Text(app, height=16, width=70, wrap=tk.WORD, state='disabled')
log_text.pack(pady=5)

# Ajusta o título inicial
set_title_running(False)

app.mainloop()
