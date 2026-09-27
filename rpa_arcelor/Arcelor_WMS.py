# -*- coding: utf-8 -*-
"""
Hawk Tech WMS - Arcelor Mittal.

Fluxo: o usuário cola os transportes copiados do Excel -> clica em "Atualizar WMS" ->
o RPA abre o ZSD106 no SAP, cola os transportes na seleção múltipla, executa, exporta a
planilha para C:\\RPA -> lê a planilha e abastece o Supabase (upsert).
"""
import os
import sys
import re
import time
import subprocess
import threading
from datetime import date
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

# --- Dependências externas ---
import ctypes
from ctypes import wintypes
import win32com.client
try:
    import pythoncom
except ImportError:
    pythoncom = None

from supabase import create_client
import pandas as pd

# ======================= CONFIG =======================

# Supabase (projeto da Arcelor). Só a chave ANON vai no EXE: ela não lê nem grava nada
# sozinha, só permite o login. Depois do login o RPA age como o usuário autenticado e quem
# manda no que ele pode gravar são as políticas (RLS) do banco. NUNCA colocar aqui a service_role.
SUPABASE_URL = "https://mtdjksyhkvncogxpaczb.supabase.co"
SUPABASE_ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im10ZGprc3loa3ZuY29neHBhY3piIiwi"
    "cm9sZSI6ImFub24iLCJpYXQiOjE3ODgyNzU5MzcsImV4cCI6MjEwMzg1MTkzN30.oq8mqh2N6eZAP-Dnr0gC1Hhm8gt0497n6LAAiizL8ow"
)

# "simulacao": lê a planilha e mostra no log o que iria gravar, sem escrever no banco.
# "gravar":    faz o upsert de verdade (só depois de preencher MAPEAMENTO e validar).
MODO_GRAVACAO = "simulacao"

# Como cada tabela do banco é preenchida a partir das colunas da planilha do ZSD106.
# Preencher depois de ver as colunas reais no log (modo simulação). Formato:
#   "arc_transporte": {
#       "conflito": "numero_tr",                       # coluna(s) única(s) usada(s) no upsert
#       "colunas": {"Transporte": "numero_tr", ...},   # coluna da planilha -> coluna do banco
#   }
MAPEAMENTO: dict[str, dict] = {}

# Export do SAP — pasta em C:\ acessível a qualquer usuário da máquina (mesmo padrão do CLR)
PASTA_EXPORT = r"C:\RPA"
NOME_ARQ_ZSD106 = "zsd106.xlsx"

# Filtros do ZSD106 (do script gravado). Datas: o script gravado usava só o ano corrente,
# o que deixaria de fora transportes criados em dezembro do ano anterior — por isso começa em 01.01 do ano passado.
PLANTA = "9733"
CENTRO_TRANSPORTE = "9733"
STATUS_DE, STATUS_ATE = "0", "9"
LAYOUT = "/wm"
DATA_DE = f"01.01.{date.today().year - 1}"
DATA_ATE = f"31.12.{date.today().year}"

# Diálogo do export &XXL: chave da lista de formatos gravada no script (VALIDAR no SAP real).
FORMATO_LISTBOX = "33"

GRID_ID = "wnd[0]/usr/cntlMY_CONTROL_AREA/shellcont/shell"

# ==== LOGOS/ÍCONES ====
ICON_ICO = "image.ico"
HEADER_LOGO = "imagelogo.png"

# ===================== ESTADO ==========================
_supabase = None          # cliente Supabase JÁ autenticado (reutilizar; um cliente novo perde o login)
_usuario_logado: dict = {}


# ======================= AUX ==========================
def resource_path(relative_path: str) -> str:
    """Compatível com PyInstaller."""
    base_path = sys._MEIPASS if getattr(sys, "_MEIPASS", False) else os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def _com_init():
    if pythoncom:
        try:
            pythoncom.CoInitialize()
        except Exception:
            pass

def _com_uninit():
    if pythoncom:
        try:
            pythoncom.CoUninitialize()
        except Exception:
            pass

def _set_window_icon(root: tk.Tk):
    try:
        ico_path = resource_path(ICON_ICO)
        if os.path.exists(ico_path):
            root.iconbitmap(default=ico_path)
    except Exception:
        pass

def _load_png(filename: str, max_height: int = 80):
    try:
        from PIL import Image, ImageTk
        p = resource_path(filename)
        if os.path.exists(p):
            img = Image.open(p)
            ratio = max_height / img.height
            img = img.resize((int(img.width * ratio), max_height), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
    except Exception:
        pass
    return None


# ------------------- AUTENTICAÇÃO ---------------------
def autenticar_usuario(email: str, senha: str) -> dict | None:
    """Login pelo Supabase Auth (e-mail + senha). Guarda o cliente autenticado em _supabase."""
    global _supabase
    try:
        sb = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        resp = sb.auth.sign_in_with_password({"email": email, "password": senha})
        user = resp.user
    except Exception:
        return None
    if not user:
        return None

    perfil = {}
    try:
        r = sb.table("usuarios").select("login,is_active,nivel_acesso").eq("user_id", user.id).limit(1).execute()
        perfil = r.data[0] if r.data else {}
    except Exception:
        pass  # sem permissão de leitura do próprio perfil: quem manda nas gravações é o RLS
    if perfil and perfil.get("is_active") is False:
        try:
            sb.auth.sign_out()
        except Exception:
            pass
        return None

    _supabase = sb
    return {
        "id": user.id,
        "email": email,
        "login": perfil.get("login") or email,
        "nivel_acesso": perfil.get("nivel_acesso") or "",
    }


# ---------------------- TRANSPORTES -------------------
def parse_transportes(texto: str) -> tuple[list[str], list[str]]:
    """Separa o texto colado (uma coluna do Excel) em (válidos, inválidos).
    Aceita quebra de linha, espaço, tab, vírgula ou ponto-e-vírgula. Remove duplicados
    mantendo a ordem. Válido = só dígitos, até 10 (tamanho do nº de transporte no SAP)."""
    validos, invalidos, vistos = [], [], set()
    for tok in re.split(r"[\s,;]+", texto.strip()):
        if not tok:
            continue
        if re.fullmatch(r"\d{1,3}(\.\d{3})+", tok):   # Excel com separador de milhar: 5.100.132.776
            tok = tok.replace(".", "")
        numero = tok.lstrip("0")                      # 0005100132776 == 5100132776
        if not tok.isdigit() or not numero or len(numero) > 10:
            invalidos.append(tok)
            continue
        if numero in vistos:
            continue
        vistos.add(numero)
        validos.append(numero)
    return validos, invalidos


_CF_UNICODETEXT = 13
_GMEM_MOVEABLE = 0x0002
_k32 = ctypes.WinDLL("kernel32", use_last_error=True)
_u32 = ctypes.WinDLL("user32", use_last_error=True)
_k32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
_k32.GlobalAlloc.restype = wintypes.HGLOBAL
_k32.GlobalLock.argtypes = [wintypes.HGLOBAL]
_k32.GlobalLock.restype = wintypes.LPVOID
_k32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
_k32.GlobalFree.argtypes = [wintypes.HGLOBAL]
_u32.OpenClipboard.argtypes = [wintypes.HWND]
_u32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
_u32.SetClipboardData.restype = wintypes.HANDLE

def _copiar_para_clipboard(texto: str, tentativas: int = 10):
    """Coloca o texto na área de transferência do Windows (o SAP cola de lá no btn[24]).
    Via ctypes: o SetClipboardData do pywin32 falhava (erro 998/6) para texto de uma linha só."""
    dados = (texto + "\0").encode("utf-16-le")
    for i in range(tentativas):
        if not _u32.OpenClipboard(None):
            if i == tentativas - 1:
                raise OSError("Não foi possível abrir a área de transferência (em uso por outro programa).")
            time.sleep(0.3)  # clipboard travado por outro processo
            continue
        try:
            _u32.EmptyClipboard()
            h = _k32.GlobalAlloc(_GMEM_MOVEABLE, len(dados))
            ptr = _k32.GlobalLock(h)
            ctypes.memmove(ptr, dados, len(dados))
            _k32.GlobalUnlock(h)
            if not _u32.SetClipboardData(_CF_UNICODETEXT, h):
                _k32.GlobalFree(h)
                raise ctypes.WinError(ctypes.get_last_error())
            return  # a partir daqui o Windows é dono do bloco de memória
        finally:
            _u32.CloseClipboard()


def garantir_pasta_export():
    """Cria C:\\RPA e libera modificação para qualquer usuário da máquina (grupo Users)."""
    if os.path.isdir(PASTA_EXPORT):
        return
    os.makedirs(PASTA_EXPORT, exist_ok=True)
    try:
        subprocess.run(
            ["icacls", PASTA_EXPORT, "/grant", "*S-1-5-32-545:(OI)(CI)M"],
            capture_output=True, check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        print(f"📁 Pasta {PASTA_EXPORT} criada e liberada para todos os usuários.")
    except Exception as e:
        print(f"⚠️ Pasta {PASTA_EXPORT} criada, mas não consegui liberar acesso a todos: {e}")


# ---------------------------- SAP ---------------------
def authenticate_sap():
    """Conecta na sessão ativa do SAP."""
    try:
        sap_gui = win32com.client.GetObject("SAPGUI")
        sap_app = sap_gui.GetScriptingEngine
        if sap_app.Children.Count > 0:
            session = sap_app.Children(0).Children(0)
            print("✅ Conectado ao SAP com sucesso.")
            return session
        print("❌ Nenhuma sessão SAP ativa encontrada.")
        return None
    except Exception as e:
        print(f"❌ Erro ao acessar SAP GUI: {e}")
        return None

def _sap_id(session, id_):
    """findById que, ao falhar, informa QUAL controle faltou e em que tela o SAP estava."""
    try:
        return session.findById(id_)
    except Exception as e:
        try:
            transacao = session.Info.Transaction
            tela = session.Info.ScreenNumber
            barra = session.findById("wnd[0]/sbar").Text
        except Exception:
            transacao = tela = barra = "?"
        raise RuntimeError(
            f"controle '{id_}' não encontrado (transação={transacao}, tela={tela}, "
            f"barra de status='{barra}')"
        ) from e

def _sap_existe(session, id_) -> bool:
    try:
        session.findById(id_)
        return True
    except Exception:
        return False

def _sap_fechar_popups(session):
    """Fecha janelas modais (wnd[1..n]) deixadas por uma execução anterior que falhou."""
    try:
        for _ in range(5):
            n = session.Children.Count
            if n <= 1:
                break
            session.findById(f"wnd[{n - 1}]").close()
    except Exception:
        pass

def _sap_aguardar(session, timeout=60):
    """Espera o SAP terminar de processar."""
    for _ in range(timeout * 2):
        try:
            if not session.Busy:
                return
        except Exception:
            return
        time.sleep(0.5)

def _aguardar_arquivo_estavel(filepath, timeout=30):
    """True quando o arquivo existe e o tamanho parou de mudar (SAP terminou de gravar)."""
    ultimo = -1
    for _ in range(timeout):
        time.sleep(1)
        if os.path.exists(filepath):
            tam = os.path.getsize(filepath)
            if tam > 0 and tam == ultimo:
                return True
            ultimo = tam
    return False

def _exportar_grid(session, filepath):
    """Exporta o ALV do ZSD106 (&MB_EXPORT > &XXL) tratando os diálogos que o SAP abrir, em ordem.
    O script gravado tinha várias tentativas; aqui cada diálogo é reconhecido pelo controle que ele tem."""
    grid = _sap_id(session, GRID_ID)
    grid.pressToolbarContextButton("&MB_EXPORT")
    grid.selectContextMenuItem("&XXL")

    radio = "wnd[1]/usr/subSUBSCREEN_STEPLOOP:SAPLSPO5:0150/sub:SAPLSPO5:0150/radSPOPLI-SELFLAG[0,0]"
    anterior, repeticoes = None, 0
    for _ in range(8):
        _sap_aguardar(session)
        if session.Children.Count <= 1:
            break  # nenhum diálogo aberto: exportação seguiu
        if _sap_existe(session, "wnd[1]/usr/cmbG_LISTBOX"):
            tipo = "formato"
            session.findById("wnd[1]/usr/cmbG_LISTBOX").key = FORMATO_LISTBOX
        elif _sap_existe(session, "wnd[1]/usr/ctxtDY_FILENAME"):
            tipo = "arquivo"
            if _sap_existe(session, "wnd[1]/usr/ctxtDY_PATH"):
                session.findById("wnd[1]/usr/ctxtDY_PATH").text = PASTA_EXPORT + "\\"
            session.findById("wnd[1]/usr/ctxtDY_FILENAME").text = NOME_ARQ_ZSD106
        elif _sap_existe(session, radio):
            tipo = "opcao"
            session.findById(radio).select()
        else:
            tipo = "desconhecido"
        # o mesmo diálogo voltando várias vezes = algo não foi aceito; não fica apertando OK às cegas
        repeticoes = repeticoes + 1 if tipo == anterior else 1
        anterior = tipo
        if repeticoes >= 3:
            raise RuntimeError(f"diálogo '{tipo}' do export não fecha (transação={session.Info.Transaction})")
        session.findById("wnd[1]/tbar[0]/btn[0]").press()  # confirma o diálogo atual

    if not _aguardar_arquivo_estavel(filepath):
        return None
    return filepath

def executar_zsd106(session, transportes: list[str]) -> str | None:
    """Abre o ZSD106, cola os transportes, executa e exporta para C:\\RPA. Retorna o caminho ou None."""
    print(f"📤 ZSD106: consultando {len(transportes)} transporte(s)...")
    try:
        garantir_pasta_export()
        filepath = os.path.join(PASTA_EXPORT, NOME_ARQ_ZSD106)
        if os.path.exists(filepath):
            os.remove(filepath)

        _sap_fechar_popups(session)
        session.findById("wnd[0]").maximize()
        # "/n" força sair da transação atual (sem ele, só funciona na tela inicial do SAP)
        _sap_id(session, "wnd[0]/tbar[0]/okcd").Text = "/nzsd106"
        session.findById("wnd[0]").sendVKey(0)
        _sap_aguardar(session)

        _sap_id(session, "wnd[0]/usr/ctxtS_WERKS-LOW").text = PLANTA
        _sap_id(session, "wnd[0]/usr/ctxtS_TPLST-LOW").text = CENTRO_TRANSPORTE
        _sap_id(session, "wnd[0]/usr/ctxtS_ERDAT-LOW").text = DATA_DE
        _sap_id(session, "wnd[0]/usr/ctxtS_ERDAT-HIGH").text = DATA_ATE
        _sap_id(session, "wnd[0]/usr/ctxtS_STTRG-LOW").text = STATUS_DE
        _sap_id(session, "wnd[0]/usr/ctxtS_STTRG-HIGH").text = STATUS_ATE
        _sap_id(session, "wnd[0]/usr/ctxtP_LAYOUT").text = LAYOUT

        # Seleção múltipla de transportes: cola da área de transferência (btn[24]) e confirma (F8)
        _copiar_para_clipboard("\r\n".join(transportes))
        _sap_id(session, "wnd[0]/usr/btn%_S_TKNUM_%_APP_%-VALU_PUSH").press()
        _sap_id(session, "wnd[1]/tbar[0]/btn[24]").press()
        session.findById("wnd[1]").sendVKey(8)
        session.findById("wnd[0]").sendVKey(8)  # executa o relatório
        _sap_aguardar(session)

        if not _sap_existe(session, GRID_ID):
            barra = ""
            try:
                barra = session.findById("wnd[0]/sbar").Text
            except Exception:
                pass
            print(f"⚠️ ZSD106 não retornou dados para esses transportes. SAP: '{barra}'")
            return None

        print("⏳ Exportando a planilha...")
        if _exportar_grid(session, filepath):
            print(f"✔️ Planilha exportada: {filepath}")
            return filepath
        print("❌ Export do ZSD106 falhou: arquivo não foi gerado.")
        return None
    except Exception as e:
        print(f"⚠️ [ERRO SAP ZSD106]: {e}")
        _sap_fechar_popups(session)  # não deixa popup aberto travando a próxima tentativa
        return None


NOME_ARQ_VT12 = "vt12.txt"


def _salvar_lista_local(session, filepath: str) -> bool:
    """Trata o diálogo de 'salvar lista como arquivo local' (wnd[1]), pelo
    mesmo padrão defensivo de `_exportar_grid` — reconhece o diálogo pelo
    controle que ele tem, não aperta OK às cegas."""
    radio = "wnd[1]/usr/subSUBSCREEN_STEPLOOP:SAPLSPO5:0150/sub:SAPLSPO5:0150/radSPOPLI-SELFLAG[1,0]"
    anterior, repeticoes = None, 0
    for _ in range(8):
        _sap_aguardar(session)
        if session.Children.Count <= 1:
            break
        if _sap_existe(session, radio):
            tipo = "opcao"
            session.findById(radio).select()
            session.findById("wnd[1]/tbar[0]/btn[0]").press()
        elif _sap_existe(session, "wnd[1]/usr/ctxtDY_PATH"):
            tipo = "arquivo"
            session.findById("wnd[1]/usr/ctxtDY_PATH").text = PASTA_EXPORT + "\\"
            if _sap_existe(session, "wnd[1]/usr/ctxtDY_FILENAME"):
                session.findById("wnd[1]/usr/ctxtDY_FILENAME").text = NOME_ARQ_VT12
            session.findById("wnd[1]/tbar[0]/btn[7]").press()
        else:
            tipo = "desconhecido"
        # o mesmo diálogo voltando várias vezes = algo não foi aceito; não fica apertando às cegas
        repeticoes = repeticoes + 1 if tipo == anterior else 1
        anterior = tipo
        if repeticoes >= 3:
            raise RuntimeError(f"diálogo '{tipo}' do VT12 não fecha (transação={session.Info.Transaction})")
        if tipo == "desconhecido":
            break
    return _aguardar_arquivo_estavel(filepath)


VT12_STATUS_ATE = "7"  # filtro de status do transporte no VT12 (K_STTRG-HIGH), vindo do script gravado


def executar_vt12(session, transportes: list[str]) -> str | None:
    """Abre o VT12, cola os transportes, roda a sequência de carregamento e
    salva como texto local em C:\\RPA. Adaptado de 'Script1 - VT12.vbs'
    (gravação original em SAP), com o mesmo tratamento defensivo de diálogos
    que `_exportar_grid` já usa para o ZSD106 (ainda NÃO validado contra SAP
    real — ver CLAUDE.md do rpa_arcelor)."""
    print(f"📤 VT12: consultando {len(transportes)} transporte(s)...")
    try:
        garantir_pasta_export()
        filepath = os.path.join(PASTA_EXPORT, NOME_ARQ_VT12)
        if os.path.exists(filepath):
            os.remove(filepath)

        _sap_fechar_popups(session)
        session.findById("wnd[0]").maximize()
        _sap_id(session, "wnd[0]/tbar[0]/okcd").Text = "/nvt12"
        session.findById("wnd[0]").sendVKey(0)
        _sap_aguardar(session)

        _sap_id(session, "wnd[0]/usr/ctxtK_STTRG-HIGH").text = VT12_STATUS_ATE

        _copiar_para_clipboard("\r\n".join(transportes))
        _sap_id(session, "wnd[0]/usr/btn%_K_TKNUM_%_APP_%-VALU_PUSH").press()
        _sap_id(session, "wnd[1]/tbar[0]/btn[24]").press()
        session.findById("wnd[1]").sendVKey(8)
        session.findById("wnd[0]").sendVKey(8)
        _sap_aguardar(session)

        _sap_id(session, "wnd[0]/tbar[1]/btn[30]").press()
        _sap_id(session, "wnd[0]/tbar[1]/btn[18]").press()
        _sap_id(session, "wnd[0]/tbar[1]/btn[7]").press()
        _sap_aguardar(session)

        shell = _sap_id(
            session,
            "wnd[0]/usr/subPLANNING:SAPLV56I_PLAN_SCREEN:0110/cntlV56I_PLAN_SCREEN_CONTAINER/"
            "shellcont/shell/shellcont[1]/shell[0]",
        )
        shell.pressToolbarContextButton("&PRINT_BACK")
        shell.selectContextMenuItem("&PRINT_PREV")
        _sap_id(session, "wnd[0]/mbar/menu[3]/menu[5]/menu[2]/menu[2]").select()
        _sap_aguardar(session)

        if not _salvar_lista_local(session, filepath):
            print("❌ Export do VT12 falhou: arquivo não foi gerado.")
            return None
        print(f"✔️ Sequência de carregamento exportada: {filepath}")
        return filepath
    except Exception as e:
        print(f"⚠️ [ERRO SAP VT12]: {e}")
        _sap_fechar_popups(session)
        return None


# --------------------- LEITURA DA PLANILHA ---------------
def ler_planilha(filepath: str) -> pd.DataFrame:
    """Lê o export do SAP. Decide o formato pelo CONTEÚDO (não pela extensão): o SAP costuma
    gravar texto separado por tab com extensão .xlsx (o pandas falha com 'not a zip file')."""
    with open(filepath, "rb") as f:
        raw = f.read()

    if raw[:2] == b"PK":                              # xlsx de verdade
        return pd.read_excel(filepath, dtype=str).fillna("")
    if raw[:4] == b"\xd0\xcf\x11\xe0":                # xls binário antigo
        return pd.read_excel(filepath, dtype=str, engine="xlrd").fillna("")

    # Texto separado por tab (UTF-16 com BOM ou Latin-1). Leitura manual: o pandas.read_csv
    # quebra em linhas com mais campos que o cabeçalho ("Expected N fields in line X, saw M").
    texto = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("latin-1", errors="ignore")
    linhas = [[c.strip() for c in ln.split("\t")] for ln in texto.splitlines()]
    linhas = [ln for ln in linhas if sum(1 for c in ln if c) >= 2]
    if len(linhas) < 2:
        raise ValueError("A planilha exportada não tem cabeçalho e linhas de dados.")
    cab = linhas[0]
    dados = [(ln + [""] * len(cab))[:len(cab)] for ln in linhas[1:]]
    return pd.DataFrame(dados, columns=cab)


# --------------------------- BANCO ---------------------
def gravar_no_banco(df: pd.DataFrame) -> bool:
    """Upsert das linhas da planilha nas tabelas de MAPEAMENTO. Em modo simulação só mostra o que leu."""
    print(f"📊 Planilha: {len(df)} linha(s), {len(df.columns)} coluna(s).")
    print("   Colunas: " + " | ".join(str(c) for c in df.columns))
    with pd.option_context("display.width", 200, "display.max_columns", 30, "display.max_colwidth", 22):
        print(df.head(5).to_string(index=False))

    if MODO_GRAVACAO != "gravar" or not MAPEAMENTO:
        print("ℹ️ Modo simulação: nada foi gravado no Supabase (mapeamento das colunas ainda não configurado).")
        return True

    for tabela, cfg in MAPEAMENTO.items():
        colunas = cfg["colunas"]
        faltando = [c for c in colunas if c not in df.columns]
        if faltando:
            raise ValueError(f"Colunas da planilha não encontradas para '{tabela}': {faltando}")
        registros = (
            df[list(colunas)].rename(columns=colunas)
            .replace("", None).drop_duplicates().to_dict("records")
        )
        for i in range(0, len(registros), 500):
            _supabase.table(tabela).upsert(registros[i:i + 500], on_conflict=cfg["conflito"]).execute()
        print(f"✅ {len(registros)} registro(s) enviados para '{tabela}'.")
    return True


# --------------------------- FLUXO ---------------------
def fluxo_atualizar_wms(transportes: list[str]) -> bool:
    """SAP (ZSD106) -> planilha -> Supabase. True só se todo o caminho concluiu."""
    print("🔄 Iniciando atualização do WMS...")
    session = authenticate_sap()
    if not session:
        print("❌ Falha ao conectar no SAP.")
        return False

    filepath = executar_zsd106(session, transportes)
    if not filepath:
        print("❌ Export ZSD106 falhou. Abortando.")
        return False

    # A planilha fica em C:\RPA para conferência; a próxima execução a substitui.
    df = ler_planilha(filepath)
    return gravar_no_banco(df)


# ===================== TELA DE LOGIN =====================
def criar_tela_login() -> dict | None:
    """Tela de login. Retorna dados do usuário logado ou None se fechar sem logar."""
    resultado = {"usuario": None}

    root = tk.Tk()
    root.title("Hawk Tech WMS — Arcelor Mittal — Login")
    root.resizable(False, False)
    _set_window_icon(root)

    frame = ttk.Frame(root, padding=30)
    frame.grid(sticky="nsew")

    logo_img = _load_png(HEADER_LOGO, max_height=60)
    if logo_img:
        lbl_logo = ttk.Label(frame, image=logo_img)
        lbl_logo.image = logo_img
        lbl_logo.grid(row=0, column=0, columnspan=2, pady=(0, 16))

    ttk.Label(frame, text="E-mail:").grid(row=1, column=0, sticky="e", padx=6, pady=6)
    entry_email = ttk.Entry(frame, width=32)
    entry_email.grid(row=1, column=1, padx=6, pady=6)

    ttk.Label(frame, text="Senha:").grid(row=2, column=0, sticky="e", padx=6, pady=6)
    entry_senha = ttk.Entry(frame, width=32, show="*")
    entry_senha.grid(row=2, column=1, padx=6, pady=6)

    lbl_erro = ttk.Label(frame, text="", foreground="red")
    lbl_erro.grid(row=3, column=0, columnspan=2, pady=(4, 0))

    btn_entrar = ttk.Button(frame, text="Entrar", width=20)
    btn_entrar.grid(row=4, column=0, columnspan=2, pady=(12, 0))

    def tentar_login(event=None):
        email = entry_email.get().strip()
        senha = entry_senha.get().strip()
        if not email or not senha:
            lbl_erro.config(text="Preencha e-mail e senha.")
            return
        if "@" not in email:
            lbl_erro.config(text="Use o e-mail cadastrado (não o login).")
            return
        btn_entrar.state(["disabled"])
        lbl_erro.config(text="Autenticando...")
        root.update()
        usuario = autenticar_usuario(email, senha)
        if usuario:
            resultado["usuario"] = usuario
            root.destroy()
        else:
            lbl_erro.config(text="E-mail ou senha inválidos, ou usuário inativo.")
            btn_entrar.state(["!disabled"])

    btn_entrar.configure(command=tentar_login)
    entry_senha.bind("<Return>", tentar_login)
    entry_email.bind("<Return>", lambda e: entry_senha.focus())

    root.protocol("WM_DELETE_WINDOW", root.destroy)
    entry_email.focus()
    root.mainloop()

    return resultado["usuario"]


# ===================== GUI (Tkinter) =====================
class _TextRedirector:
    """Redireciona stdout/stderr para o ScrolledText."""
    def __init__(self, widget: ScrolledText):
        self.widget = widget
    def write(self, msg: str):
        if not msg:
            return
        self.widget.insert("end", msg)
        self.widget.see("end")
    def flush(self):
        pass

def criar_gui(usuario: dict):
    global _usuario_logado
    _usuario_logado = usuario

    root = tk.Tk()
    root.title("Hawk Tech WMS — Arcelor Mittal")
    root.geometry("1020x680")
    _set_window_icon(root)

    top = ttk.Frame(root, padding=12)
    top.grid(row=0, column=0, sticky="nsew")
    top.columnconfigure(1, weight=1)

    logo_img = _load_png(HEADER_LOGO)
    if logo_img:
        lbl_logo = ttk.Label(top, image=logo_img)
        lbl_logo.image = logo_img
        lbl_logo.grid(row=0, column=0, rowspan=3, padx=(0, 16), sticky="nw")

    ttk.Label(
        top, text=f"Usuário: {usuario.get('login', '')}  |  {usuario.get('nivel_acesso', '')}", foreground="gray"
    ).grid(row=0, column=1, sticky="w")

    ttk.Label(top, text="Cole aqui os transportes copiados do Excel (um por linha):").grid(
        row=1, column=1, sticky="w", pady=(8, 2)
    )
    entrada = ScrolledText(top, width=40, height=9)
    entrada.grid(row=2, column=1, sticky="w")

    lbl_contagem = ttk.Label(top, text="Nenhum transporte informado.", foreground="gray")
    lbl_contagem.grid(row=3, column=1, sticky="w", pady=(4, 0))

    botoes = ttk.Frame(top)
    botoes.grid(row=4, column=1, sticky="w", pady=(8, 0))
    btn_atualizar = ttk.Button(botoes, text="Atualizar WMS", width=22)
    btn_atualizar.grid(row=0, column=0, padx=(0, 8))
    btn_limpar = ttk.Button(botoes, text="Limpar", width=12)
    btn_limpar.grid(row=0, column=1)

    txt = ScrolledText(root, width=110, height=20)
    txt.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
    redir = _TextRedirector(txt)
    sys.stdout = redir
    sys.stderr = redir

    root.columnconfigure(0, weight=1)
    root.rowconfigure(1, weight=1)

    def atualizar_contagem(event=None):
        validos, invalidos = parse_transportes(entrada.get("1.0", "end"))
        if not validos and not invalidos:
            lbl_contagem.config(text="Nenhum transporte informado.", foreground="gray")
        else:
            aviso = f"  |  {len(invalidos)} inválido(s) serão ignorados" if invalidos else ""
            lbl_contagem.config(
                text=f"{len(validos)} transporte(s) válido(s){aviso}",
                foreground="red" if invalidos else "green",
            )

    def limpar():
        entrada.delete("1.0", "end")
        atualizar_contagem()

    def executar():
        validos, invalidos = parse_transportes(entrada.get("1.0", "end"))
        if not validos:
            messagebox.showwarning("Atenção", "Cole ao menos um transporte válido (somente dígitos).")
            return
        if invalidos:
            amostra = ", ".join(invalidos[:5]) + ("..." if len(invalidos) > 5 else "")
            if not messagebox.askyesno(
                "Valores inválidos", f"{len(invalidos)} valor(es) serão ignorados ({amostra}).\nContinuar com os {len(validos)} válidos?"
            ):
                return
        btn_atualizar.state(["disabled"])
        btn_limpar.state(["disabled"])

        def trabalho():
            _com_init()
            try:
                print("=====================================\n   Hawk Tech WMS - Atualizar WMS (Arcelor)\n=====================================")
                if invalidos:
                    print(f"⚠️ Ignorados (inválidos): {', '.join(invalidos)}")
                if fluxo_atualizar_wms(validos):
                    print("\n✓ Atualização concluída.\n")
                else:
                    print("\n✗ Atualização NÃO concluída — veja o erro acima.\n")
            except Exception as e:
                print(f"\n[ERRO] Atualizar WMS: {e}\n")
            finally:
                _com_uninit()
                root.after(0, lambda: (btn_atualizar.state(["!disabled"]), btn_limpar.state(["!disabled"])))

        threading.Thread(target=trabalho, daemon=True).start()

    entrada.bind("<KeyRelease>", atualizar_contagem)
    entrada.bind("<<Paste>>", lambda e: root.after(50, atualizar_contagem))
    btn_atualizar.configure(command=executar)
    btn_limpar.configure(command=limpar)

    root.mainloop()


if __name__ == "__main__":
    usuario = criar_tela_login()
    if usuario:
        criar_gui(usuario)
