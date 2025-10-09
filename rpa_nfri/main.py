# -*- coding: utf-8 -*-
import threading
import time
import traceback
import os
import sys
import tkinter as tk
from tkinter import messagebox, scrolledtext
import pyautogui
import keyboard
from PIL import Image, ImageTk
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from pyscreeze import ImageNotFoundException as PyscreezeImageNotFoundException
from pyautogui import ImageNotFoundException as PyautoguiImageNotFoundException
import openpyxl
from datetime import datetime, timedelta
import subprocess

# Diretório base compatível com .exe
base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

# ─── CONFIGURAÇÕES ───────────────────────────────────────────────────────────
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "1GnHcBKhXWKfU4Pcucyqj1_Vv9jiIkbY4iJ4prugD9ZE"
SHEET_NAME = "Página1"

# Coordenadas dos cliques baseadas nas imagens
coords = {
    "sandra_valentim": (152, 287),          # "SANDRA VALENTIM - Restrito"
    "solucao_fiscal": (158, 335),           # Menu "Solução Fiscal"
    "nfs_recebimento": (163, 383),          # "NFs do Recebimento Integrado"
    "botao_excel": (507, 263),              # Botão EXCEL
    "campo_data": (690, 190),               # Campo de data
    "excel_baixado": (950, 128),            # Excel baixado no popup
}

estado = {"executando": False, "thread_rpa": None}

# ─── HELPERS DE UI ───────────────────────────────────────────────────────────
def set_title_running(is_running: bool, extra: str = ""):
    base = "RPA NFRi"
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
    """Adiciona mensagem ao log da interface com timestamp"""
    try:
        log_text.config(state='normal')
        log_text.insert('end', f"{time.strftime('%H:%M:%S')} - {msg}\n")
        log_text.see('end')
        log_text.config(state='disabled')
        app.update_idletasks()
    except Exception:
        pass

def abrir_pasta_downloads():
    """Abre a pasta de Downloads"""
    try:
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        os.makedirs(downloads_path, exist_ok=True)

        if sys.platform.startswith("win"):
            os.startfile(downloads_path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", downloads_path])
        else:
            subprocess.Popen(["xdg-open", downloads_path])

        log_interface(f"📂 Pasta aberta: {downloads_path}")
    except Exception as e:
        log_interface(f"❌ Erro ao abrir pasta: {e}")
        messagebox.showerror("Erro", f"Não foi possível abrir a pasta:\n{e}")

def mostrar_ajuda():
    """Mostra janela de ajuda"""
    ajuda_window = tk.Toplevel(app)
    ajuda_window.title("Ajuda - RPA NFRi")
    ajuda_window.geometry("600x550")
    ajuda_window.resizable(False, False)

    # Texto de ajuda
    ajuda_text = tk.Text(ajuda_window, wrap=tk.WORD, padx=10, pady=10)
    ajuda_text.pack(fill=tk.BOTH, expand=True)

    help_content = """
🤖 RPA NFRI - AJUDA

📋 FUNCIONALIDADES:
• Automação de extração de NFs do Recebimento Integrado
• Download automático do relatório Excel
• Processamento e envio para Google Sheets
• Backup local dos dados extraídos

🚀 COMO USAR:
1. Abra o sistema Sistemas Integrados no navegador
2. Faça login no sistema
3. Deixe na tela inicial
4. Clique em "🚀 Iniciar RPA"
5. O programa automaticamente:
   - Navegará até "Solução Fiscal"
   - Clicará em "NFs do Recebimento Integrado"
   - Gerará relatório Excel
   - Baixará o arquivo
   - Processará os dados
   - Enviará para Google Sheets

🔒 SEGURANÇA:
• Botão "⏹️ Parar RPA" para interrupção manual
• Pressione ESC durante execução para pausar
• Dados sempre salvos localmente como backup

📊 DADOS EXTRAÍDOS:
Todas as colunas do relatório NFRi são enviadas para Google Sheets:
• PLANTA
• RI
• ORIGEM
• RI ORIGEM
• RECEIVEDATE
• CLIENTE
• FISCAL DOCUMENT MODEL
• INVOICENUM
• E outras...

🔧 TROUBLESHOOTING:
• Se elementos não forem encontrados: Verifique resolução da tela
• Se falhar download: Verifique permissões da pasta Downloads
• Para problemas Google Sheets: Verifique credenciais
• Coordenadas incorretas: Ajuste em coords{}

📂 ARQUIVOS:
• Excel baixado: pasta Downloads (NFRi-*.xlsx)
• Credenciais: CredenciaisOracle.json
• Token: token.json (gerado após primeiro login)

🔑 PRIMEIRO LOGIN GOOGLE:
Na primeira execução, uma janela do navegador abrirá para:
1. Fazer login na conta Google
2. Autorizar acesso ao Google Sheets
3. Token será salvo automaticamente

📞 CONFIGURAÇÃO:
• Planilha ID: 1GnHcBKhXWKfU4Pcucyqj1_Vv9jiIkbY4iJ4prugD9ZE
• Aba: Página1
• Para mudar: edite SPREADSHEET_ID e SHEET_NAME no código

📝 COORDENADAS DE CLIQUE:
• Solução Fiscal: (158, 335)
• NFs Recebimento: (163, 383)
• Botão Excel: (507, 263)
• Campo Data: (690, 190)
• Excel Baixado: (950, 128)

Ajuste conforme sua resolução de tela se necessário!
    """

    ajuda_text.insert(1.0, help_content)
    ajuda_text.config(state='disabled')

    # Botão fechar
    tk.Button(ajuda_window, text="Fechar", command=ajuda_window.destroy).pack(pady=10)

# ─── GOOGLE SHEETS ───────────────────────────────────────────────────────────
def authenticate_google():
    """
    Autentica com Google Sheets.
    - CredenciaisOracle.json vem embutido no executável
    - token.json é salvo junto ao executável (pasta do usuário)
    """
    # Token sempre salvo junto ao executável (não no _MEIPASS)
    if getattr(sys, 'frozen', False):
        # Se for executável, salva token junto ao .exe
        exe_dir = os.path.dirname(sys.executable)
        token_path = os.path.join(exe_dir, "token.json")
    else:
        # Se for desenvolvimento, salva na pasta do script
        token_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "token.json")

    # Credenciais: tenta local primeiro, depois embutido
    creds_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "CredenciaisOracle.json")
    if not os.path.exists(creds_path):
        # Se não encontrou local, busca embutido no executável
        creds_path = os.path.join(base_path, "CredenciaisOracle.json")

    if not os.path.exists(creds_path):
        raise FileNotFoundError(
            "❌ Arquivo CredenciaisOracle.json não encontrado!\n\n"
            "O arquivo deve estar embutido no executável ou na mesma pasta."
        )

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

def enviar_para_sheets(service, dados):
    """
    Envia os dados processados para o Google Sheets.
    dados: lista de listas [["coluna1", "coluna2", ...], ["valor1", "valor2", ...], ...]
    """
    try:
        # Primeiro, limpar a planilha (opcional)
        # service.spreadsheets().values().clear(
        #     spreadsheetId=SPREADSHEET_ID,
        #     range=f"{SHEET_NAME}!A1:Z"
        # ).execute()

        # Enviar dados
        body = {
            'values': dados
        }
        result = service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A1",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute()

        log_interface(f"✅ {result.get('updates').get('updatedRows')} linhas enviadas para Google Sheets")
        return True
    except Exception as e:
        log_interface(f"❌ Erro ao enviar para Google Sheets: {e}")
        return False

# ─── FUNÇÕES DE CONTROLE ─────────────────────────────────────────────────────
def sleep_check_pause(segundos):
    """Pausa checando se o robô foi parado."""
    for _ in range(int(segundos * 10)):
        if not estado["executando"]:
            break
        time.sleep(0.1)

def processar_excel(caminho_excel):
    """
    Processa o arquivo Excel baixado e retorna os dados.
    Filtra apenas as colunas A até BB (54 colunas).
    Retorna lista de listas com os dados.
    """
    try:
        wb = openpyxl.load_workbook(caminho_excel)
        ws = wb.active

        dados = []
        for row in ws.iter_rows(values_only=True):
            # Pega apenas as primeiras 54 colunas (A até BB)
            linha_filtrada = list(row[:54])
            dados.append(linha_filtrada)

        wb.close()
        log_interface(f"📊 Excel processado: {len(dados)} linhas, 54 colunas (A-BB)")
        return dados
    except Exception as e:
        log_interface(f"❌ Erro ao processar Excel: {e}")
        return None

def rpa_worker():
    """Thread worker que executa o RPA principal"""
    try:
        log_interface("🚀 RPA iniciado - automatizando NFRi...")
        log_interface("⚠️ FAILSAFE ativo: pressione ESC para parar")

        service = authenticate_google()

        # Passo 1: Clicar em "SANDRA VALENTIM - Restrito"
        log_interface("▶ Clicando em 'SANDRA VALENTIM - Restrito'...")
        pyautogui.click(coords["sandra_valentim"])
        sleep_check_pause(7)  # +5s
        if not estado["executando"]:
            return

        # Passo 2: Clicar em "Solução Fiscal"
        log_interface("▶ Clicando em 'Solução Fiscal'...")
        pyautogui.click(coords["solucao_fiscal"])
        sleep_check_pause(7)  # +5s
        if not estado["executando"]:
            return

        # Passo 3: Clicar em "NFs do Recebimento Integrado"
        log_interface("▶ Clicando em 'NFs do Recebimento Integrado'...")
        pyautogui.click(coords["nfs_recebimento"])
        sleep_check_pause(8)  # +5s
        if not estado["executando"]:
            return

        # Passo 4: Preencher datas e gerar relatório
        log_interface("▶ Preenchendo datas...")
        pyautogui.click(coords["campo_data"])
        sleep_check_pause(6.5)  # +5s

        # Obter data de ONTEM (dia anterior)
        hoje = datetime.now()
        ontem = hoje - timedelta(days=1)
        data_ontem = ontem.strftime("%d/%m/%Y")
        data_hoje = hoje.strftime("%d/%m/%Y")

        # Campo 1: Data do dia ANTERIOR
        log_interface(f"▶ Inserindo data inicial: {data_ontem}")
        pyautogui.write(data_ontem, interval=0.15)
        sleep_check_pause(6)  # +5s
        if not estado["executando"]:
            return

        # TAB para próximo campo
        log_interface("▶ Navegando para próximo campo...")
        pyautogui.press("tab")
        sleep_check_pause(6)  # +5s
        if not estado["executando"]:
            return

        # Campo 2: Data de HOJE
        log_interface(f"▶ Inserindo data final: {data_hoje}")
        pyautogui.write(data_hoje, interval=0.15)
        sleep_check_pause(6)  # +5s
        if not estado["executando"]:
            return

        # TAB novamente
        log_interface("▶ Finalizando preenchimento...")
        pyautogui.press("tab")
        sleep_check_pause(6)  # +5s
        if not estado["executando"]:
            return

        # ENTER para gerar
        log_interface("▶ Gerando relatório...")
        pyautogui.press("enter")
        sleep_check_pause(13)  # +5s - aguardar processamento e download
        if not estado["executando"]:
            return

        # Passo 5: Clicar no Excel baixado
        log_interface("▶ Aguardando download do Excel...")
        sleep_check_pause(8)  # +5s
        if not estado["executando"]:
            return

        log_interface("▶ Clicando no arquivo Excel baixado...")
        pyautogui.click(coords["excel_baixado"])
        sleep_check_pause(9)  # +5s - aguardar Excel abrir
        if not estado["executando"]:
            return

        # Passo 6: Localizar o arquivo baixado
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")

        # Procurar pelo arquivo mais recente NFRi-*.xlsx
        arquivos_nfri = []
        for arquivo in os.listdir(downloads_path):
            if arquivo.startswith("NFRi-") and arquivo.endswith(".xlsx"):
                caminho_completo = os.path.join(downloads_path, arquivo)
                arquivos_nfri.append((caminho_completo, os.path.getmtime(caminho_completo)))

        if not arquivos_nfri:
            log_interface("❌ Nenhum arquivo NFRi encontrado na pasta Downloads")
            app.after(0, lambda: messagebox.showerror("Erro", "Nenhum arquivo NFRi encontrado na pasta Downloads"))
            return

        # Pegar o mais recente
        arquivos_nfri.sort(key=lambda x: x[1], reverse=True)
        caminho_excel = arquivos_nfri[0][0]
        log_interface(f"📄 Arquivo encontrado: {os.path.basename(caminho_excel)}")

        # Passo 7: Processar Excel
        log_interface("▶ Processando dados do Excel...")
        dados = processar_excel(caminho_excel)

        if dados:
            # Passo 8: Enviar para Google Sheets
            log_interface("▶ Enviando dados para Google Sheets...")
            if enviar_para_sheets(service, dados):
                log_interface("=" * 70)
                log_interface("✅ RPA FINALIZADO COM SUCESSO")
                log_interface("=" * 70)
                app.after(0, lambda: messagebox.showinfo("Sucesso", "✅ Dados enviados para o Google Sheets com sucesso!"))
            else:
                app.after(0, lambda: messagebox.showerror("Erro", "❌ Falha ao enviar dados para o Google Sheets"))
        else:
            app.after(0, lambda: messagebox.showerror("Erro", "❌ Falha ao processar o arquivo Excel"))

    except KeyboardInterrupt:
        log_interface("🛑 RPA interrompido pelo usuário (Ctrl+C)")
    except Exception as e:
        log_interface(f"❌ Erro no RPA: {e}")
        log_interface(traceback.format_exc())
        app.after(0, lambda: messagebox.showerror("Erro RPA", f"Erro durante execução do RPA:\n{e}"))
    finally:
        # Atualizar estado quando terminar
        estado["executando"] = False
        estado["thread_rpa"] = None
        app.after(0, lambda: atualizar_interface_parado())

        # Restaurar janela para o usuário ver que terminou
        app.after(100, lambda: restaurar_app())

def atualizar_interface_parado():
    """Atualiza interface quando RPA para"""
    btn_iniciar.config(state='normal')
    btn_parar.config(state='disabled')
    status_label.config(text="Status: Parado", fg="red")
    set_title_running(False)
    log_interface("⸏ RPA parado")

def monitorar_tecla():
    """Monitora a tecla ESC para parar o robô."""
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

def iniciar_rpa():
    """Inicia o RPA em thread separada"""
    if estado["executando"]:
        messagebox.showwarning("Aviso", "RPA já está em execução!")
        return

    # Confirmação
    resposta = messagebox.askyesno(
        "Confirmar Início",
        "Certifique-se de que:\n\n"
        "✓ Sistema Integrado está aberto no navegador\n"
        "✓ Você está logado e na tela inicial\n"
        "✓ A conexão com a internet está estável\n\n"
        "Deseja iniciar o RPA?"
    )

    if not resposta:
        return

    # Minimizar janela
    app.iconify()

    # Atualizar estado
    estado["executando"] = True
    btn_iniciar.config(state='disabled')
    btn_parar.config(state='normal')
    status_label.config(text="Status: Rodando", fg="green")
    set_title_running(True)

    # Limpar log
    log_text.config(state='normal')
    log_text.delete(1.0, 'end')
    log_text.config(state='disabled')

    # Iniciar thread do RPA
    estado["thread_rpa"] = threading.Thread(target=rpa_worker, daemon=True)
    estado["thread_rpa"].start()

    # Iniciar monitoramento de tecla ESC
    threading.Thread(target=monitorar_tecla, daemon=True).start()

    log_interface("▶️ Iniciando RPA...")

def parar_rpa():
    """Para o RPA"""
    if not estado["executando"]:
        messagebox.showinfo("Info", "RPA não está em execução!")
        return

    # Sinalizar parada
    estado["executando"] = False

    log_interface("🛑 Solicitando parada do RPA...")

    # Restaurar interface
    restaurar_app()

    # Atualizar interface
    atualizar_interface_parado()

# ─── INTERFACE PRINCIPAL ────────────────────────────────────────────────────
app = tk.Tk()
app.title("RPA NFRi")
app.geometry("550x650")
app.resizable(False, False)

# Ícone da janela
try:
    app.iconphoto(True, ImageTk.PhotoImage(file=os.path.join(base_path, "Topo.png")))
except Exception as e:
    print(f"Erro ao definir ícone: {e}")

# ─── ÁREA DOS LOGOS ─────────────────────────────────────────────────────────
try:
    logo_frame = tk.Frame(app, bg="#f7f7f7")
    logo_frame.pack(pady=(20, 15), fill=tk.X)

    # Logo Genesys
    logo1_img = Image.open(os.path.join(base_path, "Logo.png")).resize((150, 90))
    logo1_tk = ImageTk.PhotoImage(logo1_img)

    # Logo Tecumseh
    logo2_img = Image.open(os.path.join(base_path, "Tecumseh.png")).resize((90, 70))
    logo2_tk = ImageTk.PhotoImage(logo2_img)

    # Container centralizado para os logos
    logos_container = tk.Frame(logo_frame, bg="#f7f7f7")
    logos_container.pack()

    tk.Label(logos_container, image=logo1_tk, bg="#f7f7f7").pack(side="left", padx=15)
    tk.Label(logos_container, image=logo2_tk, bg="#f7f7f7").pack(side="left", padx=15)

except Exception as e:
    print(f"❌ Erro ao carregar logos: {e}")
    # Frame vazio se logos falharem
    logo_frame = tk.Frame(app, height=100, bg="#f7f7f7")
    logo_frame.pack(pady=(20, 15), fill=tk.X)
    tk.Label(logo_frame, text="RPA NFRI", font=("Arial", 16, "bold"), bg="#f7f7f7").pack()

# ─── ÁREA DE CONTROLES ──────────────────────────────────────────────────────
controls_frame = tk.Frame(app)
controls_frame.pack(pady=10)

# Botões principais
btn_iniciar = tk.Button(
    controls_frame,
    text="🚀 Iniciar RPA",
    command=iniciar_rpa,
    font=("Arial", 12, "bold"),
    bg="#4CAF50",
    fg="white",
    padx=20,
    pady=10,
    width=15
)
btn_iniciar.pack(side="left", padx=10)

btn_parar = tk.Button(
    controls_frame,
    text="⏹️ Parar RPA",
    command=parar_rpa,
    font=("Arial", 12, "bold"),
    bg="#f44336",
    fg="white",
    padx=20,
    pady=10,
    width=15,
    state='disabled'
)
btn_parar.pack(side="left", padx=10)

# ─── ÁREA DE UTILITÁRIOS ────────────────────────────────────────────────────
utils_frame = tk.Frame(app)
utils_frame.pack(pady=10)

tk.Button(
    utils_frame,
    text="📂 Abrir Downloads",
    command=abrir_pasta_downloads,
    font=("Arial", 10),
    padx=15,
    pady=5
).pack(side="left", padx=5)

tk.Button(
    utils_frame,
    text="❓ Ajuda",
    command=mostrar_ajuda,
    font=("Arial", 10),
    padx=15,
    pady=5
).pack(side="left", padx=5)

# ─── STATUS ─────────────────────────────────────────────────────────────────
status_frame = tk.Frame(app)
status_frame.pack(pady=10)

status_label = tk.Label(
    status_frame,
    text="Status: Aguardando",
    font=("Arial", 12, "bold"),
    fg="orange"
)
status_label.pack()

# ─── ÁREA DE LOG ────────────────────────────────────────────────────────────
log_frame = tk.Frame(app)
log_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

tk.Label(log_frame, text="📋 Log de Execução:", font=("Arial", 10, "bold")).pack(anchor="w")

# Text widget com scrollbar
log_text = scrolledtext.ScrolledText(
    log_frame,
    height=20,
    width=70,
    wrap=tk.WORD,
    state='disabled',
    font=("Consolas", 9),
    bg="#f8f8f8"
)
log_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

# ─── INICIALIZAÇÃO ──────────────────────────────────────────────────────────
# Ajusta o título inicial
set_title_running(False)

# Log inicial
log_interface("🤖 RPA NFRi carregado")
log_interface("✅ Sistema pronto para iniciar")
log_interface("📖 Clique em 'Ajuda' para instruções detalhadas")

# Interceptar fechamento da janela
def on_closing():
    if estado["executando"]:
        resposta = messagebox.askyesno(
            "Confirmar Saída",
            "RPA está em execução. Deseja realmente sair?\n\n"
            "Isso interromperá a automação."
        )
        if not resposta:
            return

        # Parar RPA se estiver rodando
        parar_rpa()

    app.destroy()

app.protocol("WM_DELETE_WINDOW", on_closing)

# ─── EXECUÇÃO ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.mainloop()
