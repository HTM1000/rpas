import os
import time
import tkinter as tk
from tkinter import messagebox
import pandas as pd
import win32com.client

# ========== CONFIGURAÇÕES ==========
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "1Bg243_Ge2ATKLymbYVjarFYxCVa2phn9kUk-srpnzLc"
ABA = "Expedição Conferencia"
CRED_PATH = "CredenciaisCLR.json"
TOKEN_PATH = "token.json"
PASTA_SAIDA = r"C:\RPA"

# ========== AUTENTICAÇÃO GOOGLE ==========
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

def authenticate_google():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CRED_PATH):
                raise FileNotFoundError("Credenciais 'CredenciaisCLR.json' não encontradas.")
            flow = InstalledAppFlow.from_client_secrets_file(CRED_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w", encoding="utf-8") as token:
            token.write(creds.to_json())
    return build("sheets", "v4", credentials=creds)

# ========== BUSCAR TRANSPORTE ==========
def buscar_transporte_google(transporte: str):
    try:
        service = authenticate_google()
        sheet = service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=ABA,
        ).execute()

        values = result.get("values", [])
        if not values:
            print("⚠️ Planilha vazia.")
            return None

        header = values[0]
        dados = values[1:]
        dados_corrigidos = [linha + [""] * (len(header) - len(linha)) for linha in dados]

        df = pd.DataFrame(dados_corrigidos, columns=header)
        df["Nº Transporte"] = df["Nº Transporte"].astype(str).str.strip()
        transporte = str(transporte).strip()
        df = df[df["Nº Transporte"] == transporte]

        if df.empty:
            print(f"⚠️ Transporte '{transporte}' não encontrado.")
            return None

        return df
    except Exception as e:
        print(f"❌ Erro ao acessar planilha: {e}")
        return None

# ========== GERAR TXT ==========
def gerar_txt_transporte(df, transporte, pasta_saida=PASTA_SAIDA):
    transporte_formatado = transporte.zfill(10)
    nome_arquivo = f"{transporte_formatado}.txt"
    caminho_arquivo = os.path.join(pasta_saida, nome_arquivo)
    os.makedirs(pasta_saida, exist_ok=True)

    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        f.write(f"1     60     {transporte_formatado}\n")
        for _, row in df.iterrows():
            sku = str(row["SKU Transporte"]).strip()
            serie = str(row["Nº Série"]).strip()
            if len(serie) > 2:
                serie = serie[:-2]
            remessa = str(row["Remessa"]).strip()
            linha = f"200013{sku}{serie}{remessa}"
            f.write(linha + "\n")

    print(f"✅ TXT gerado: {caminho_arquivo}")
    return caminho_arquivo

# ========== FECHAR SESSÃO ==========
def sair_de_todas_as_operacoes(session):
    try:
        session.findById("wnd[0]/tbar[0]/okcd").text = "/n"
        session.findById("wnd[0]").sendVKey(0)
        time.sleep(2)
    except Exception as e:
        print(f"Erro ao tentar sair de todas as operações: {e}")

# ========== EXECUTAR SAP ==========
def executar_sap_upload(transporte, caminho_txt):
    try:
        session = win32com.client.GetObject("SAPGUI").GetScriptingEngine.Children(0).Children(0)
        sair_de_todas_as_operacoes(session)

        print(f"🚀 Iniciando envio do transporte {transporte} para o SAP...")

        session.findById("wnd[0]/tbar[0]/okcd").text = "/NZBD1"
        session.findById("wnd[0]").sendVKey(0)
        time.sleep(1)

        session.findById("wnd[0]/usr/ctxtS_FILE").text = caminho_txt
        session.findById("wnd[0]/usr/ctxtS_TR").text = transporte.zfill(10)
        session.findById("wnd[0]/tbar[1]/btn[8]").press()
        time.sleep(3)

        try:
            if session.findById("wnd[1]/usr").Text:
                session.findById("wnd[1]").sendVKey(0)
        except:
            pass

        print(f"✅ Upload SAP executado com sucesso para o transporte {transporte}")
        os.startfile(caminho_txt)
        return True

    except Exception as erro:
        print(f"❌ Erro durante upload SAP do transporte {transporte}: {erro}")
        return False

# ========== INTERFACE ==========
class TransporteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RPA - Geração e Upload SAP")
        self.root.geometry("420x200")
        self.root.resizable(False, False)

        tk.Label(root, text="Digite o número do transporte:", font=("Arial", 12)).pack(pady=20)
        self.entry = tk.Entry(root, font=("Arial", 14), width=28)
        self.entry.pack()

        tk.Button(root, text="Iniciar Processo", font=("Arial", 12), command=self.processar_transporte).pack(pady=20)

    def processar_transporte(self):
        transporte = self.entry.get().strip()
        if not transporte:
            messagebox.showwarning("Atenção", "Digite o número do transporte.")
            return

        df = buscar_transporte_google(transporte)
        if df is None:
            messagebox.showerror("Erro", f"Transporte '{transporte}' não encontrado.")
            return

        caminho = gerar_txt_transporte(df, transporte)
        sucesso = executar_sap_upload(transporte, caminho)

        if sucesso:
            messagebox.showinfo("Finalizado", f"Transporte {transporte} enviado ao SAP com sucesso.")
        else:
            messagebox.showerror("Erro", f"Falha ao enviar o transporte {transporte} para o SAP.\nVerifique o terminal.")

# ========== MAIN ==========
if __name__ == "__main__":
    root = tk.Tk()
    app = TransporteApp(root)
    root.mainloop()
