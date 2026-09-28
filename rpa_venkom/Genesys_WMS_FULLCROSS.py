# -*- coding: utf-8 -*-
import os
import sys
import time
import re
import threading
from datetime import datetime, date, timedelta, timezone
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

# --- Dependências externas ---
import win32com.client
try:
    import pythoncom
except ImportError:
    pythoncom = None

from supabase import create_client
import pandas as pd

# ======================= CONFIG =======================

# Supabase — banco WMS Jundiaí (Full Cross)
SUPABASE_URL = "https://sdqzyctmtjvyvmppqtgj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNkcXp5Y3RtdGp2eXZtcHBxdGdqIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MTUyMTI5MCwiZXhwIjoyMDk3MDk3MjkwfQ.fQand6-L6TNdH34fWrpaNPfZ3cIvG5SaJuw08aGx9rU"

PASTA_SAIDA_C1 = r"C:\RPA"

# Export do SAP
PASTA_EXPORT    = r"C:\RPA"
NOME_ARQ_EXPORT = "ZWM3.xls"
NOME_ARQ_ZV52   = "zv52.xlsx"

# ZV52 — campo de filtro e valor da unidade Full Cross (planta 655, mesmo campo do
# rpa_clr, que usa 654). O valor antigo "ven1" no campo de depósito S_LGORT-LOW foi
# descartado: não retorna resultado no relatório.
ZV52_CAMPO = "S_WERKS-LOW"
ZV52_VALOR = "655"

# ==== LOGOS/ÍCONES ====
ICON_ICO    = "image.ico"
ICON_PNG    = "imagelogo.png"
HEADER_LOGO = "imagelogo.png"


# ===================== USUÁRIO LOGADO =================
_usuario_logado: dict = {}

# Evento de cancelamento da integração (setado pelo botão "Cancelar").
_cancelar_evento = threading.Event()

# ======================= AUX ==========================
def resource_path(relative_path: str) -> str:
    """Compatível com PyInstaller."""
    if getattr(sys, "_MEIPASS", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
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
            return
    except Exception:
        pass
    try:
        png_path = resource_path(ICON_PNG)
        if os.path.exists(png_path):
            img = tk.PhotoImage(file=png_path)
            root.iconphoto(True, img)
            root._icon_ref = img
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
def autenticar_usuario(login: str, senha: str) -> dict | None:
    """Autentica pelo login da tabela usuarios. Retorna dados do usuário ou None."""
    try:
        supabase = authenticate_supabase()
        resp = supabase.table("usuarios").select("*").eq("login", login).eq("is_active", True).execute()
        if not resp.data:
            return None
        usuario = resp.data[0]
        supabase.auth.sign_in_with_password({"email": usuario["email"], "password": senha})
        return usuario
    except Exception:
        return None

def authenticate_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


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

# ---------------- EXPORTAÇÃO SAP ---------------
def extrair_dados_sap_para_xls(session, transporte):
    """Exporta /NZWM3 usando a mesma opção do VBA."""
    print(f"🚛 Processando transporte {transporte} no SAP...")
    try:
        if not os.path.exists(PASTA_EXPORT):
            os.makedirs(PASTA_EXPORT, exist_ok=True)
        filepath = os.path.join(PASTA_EXPORT, NOME_ARQ_EXPORT)
        if os.path.exists(filepath):
            os.remove(filepath)

        session.findById("wnd[0]").maximize()
        session.findById("wnd[0]/tbar[0]/okcd").Text = "/NZWM3"
        session.findById("wnd[0]").sendVKey(0)

        session.findById("wnd[0]/usr/ctxtP_TKNUM").Text = str(transporte)
        session.findById("wnd[0]/tbar[1]/btn[8]").press()
        session.findById("wnd[0]/usr/lbl[1,1]").setFocus()
        session.findById("wnd[0]").sendVKey(2)

        session.findById("wnd[0]/tbar[1]/btn[45]").press()
        session.findById(
            "wnd[1]/usr/subSUBSCREEN_STEPLOOP:SAPLSPO5:0150/sub:SAPLSPO5:0150/radSPOPLI-SELFLAG[1,0]"
        ).select()
        session.findById("wnd[1]/tbar[0]/btn[0]").press()
        session.findById("wnd[1]/usr/ctxtDY_PATH").text = PASTA_EXPORT
        session.findById("wnd[1]/usr/ctxtDY_FILENAME").text = NOME_ARQ_EXPORT
        session.findById("wnd[1]/tbar[0]/btn[11]").press()

        time.sleep(6)
        if os.path.exists(filepath):
            print(f"✔️ Arquivo exportado: {filepath}")
            return filepath
        print("❌ Export falhou: arquivo não encontrado.")
        return None
    except Exception as e:
        print(f"⚠️ [ERRO SAP] Transporte {transporte}: {e}")
        return None

# --------------- EXPORTAÇÃO SAP — ZV52 ----------------
def extrair_zv52_para_xls(session):
    """Navega para ZV52 (planta 655), executa F8 e exporta para C:\\RPA\\zv52.xlsx."""
    print(f"📤 Exportando ZV52 do SAP ({ZV52_CAMPO} = {ZV52_VALOR})...")
    try:
        if not os.path.exists(PASTA_EXPORT):
            os.makedirs(PASTA_EXPORT, exist_ok=True)
        filepath = os.path.join(PASTA_EXPORT, NOME_ARQ_ZV52)
        if os.path.exists(filepath):
            os.remove(filepath)

        session.findById("wnd[0]").maximize()
        session.findById("wnd[0]/tbar[0]/okcd").Text = "zv52"
        session.findById("wnd[0]").sendVKey(0)

        campo_zv52 = session.findById(f"wnd[0]/usr/ctxt{ZV52_CAMPO}")
        campo_zv52.text = ZV52_VALOR
        campo_zv52.caretPosition = len(ZV52_VALOR)
        session.findById("wnd[0]").sendVKey(8)  # F8 — executa relatório

        # Abre menu de exportação
        session.findById("wnd[0]/mbar/menu[0]/menu[5]/menu[2]/menu[2]").select()
        # Seleciona formato planilha
        session.findById(
            "wnd[1]/usr/subSUBSCREEN_STEPLOOP:SAPLSPO5:0150/sub:SAPLSPO5:0150/radSPOPLI-SELFLAG[1,0]"
        ).select()
        session.findById(
            "wnd[1]/usr/subSUBSCREEN_STEPLOOP:SAPLSPO5:0150/sub:SAPLSPO5:0150/radSPOPLI-SELFLAG[1,0]"
        ).setFocus()
        session.findById("wnd[1]/tbar[0]/btn[0]").press()

        # Define pasta e nome do arquivo e clica Gerar (mesmo padrão do ZWM3)
        session.findById("wnd[1]/usr/ctxtDY_PATH").text = PASTA_EXPORT + "\\"
        session.findById("wnd[1]/usr/ctxtDY_FILENAME").text = NOME_ARQ_ZV52
        session.findById("wnd[1]/tbar[0]/btn[11]").press()  # Gerar

        print(f"⏳ Aguardando arquivo em: {filepath}")
        for _ in range(20):  # até 20s
            time.sleep(1)
            if os.path.exists(filepath):
                print(f"✔️ Arquivo ZV52 exportado: {filepath}")
                return filepath
        print("❌ Export ZV52 falhou: arquivo não encontrado.")
        return None
    except Exception as e:
        print(f"⚠️ [ERRO SAP ZV52]: {e}")
        return None

# -------------------- PARSE/LEITURA --------------------
def parse_zwm3(filepath):
    """
    Lê o export do SAP (UTF-16 ou Latin-1) e retorna:
      lista_input: [ [SKU, Remessa, Qtd] ... ]
      lista_info:  [ (SKU, Qtd, Remessa) ... ]
    """
    with open(filepath, "rb") as f:
        raw = f.read()
    try:
        texto = raw.decode("utf-16")
    except UnicodeDecodeError:
        texto = raw.decode("latin-1", errors="ignore")

    linhas = [ln for ln in texto.splitlines() if ln.strip()]
    start = 2 if linhas and "Box" in linhas[0] else 0

    longnum = re.compile(r"\b\d{6,}\b")
    is_num  = lambda s: s.replace(".", "").replace(",", "").isdigit()

    lista_input, lista_info = [], []
    remessa_corrente    = ""
    nome_cliente_corrente = ""

    for ln in linhas[start:]:
        tokens = [t for t in re.split(r"\s+", ln.strip()) if t]

        long_indices = [i for i, t in enumerate(tokens) if longnum.fullmatch(t)]
        if long_indices:
            remessa_corrente = tokens[long_indices[0]]
            # tokens entre posição 2 e o primeiro long = nome do cliente
            nome_tokens = tokens[2:long_indices[0]]
            if nome_tokens:
                nome_cliente_corrente = " ".join(nome_tokens)
            continue

        sku = ""
        for idx, t in enumerate(tokens):
            if t.isdigit() and idx + 1 < len(tokens):
                sku = tokens[idx + 1]
                break
        if not sku:
            continue

        numeros = [t for t in tokens if is_num(t)]
        if numeros:
            try:
                qtd = int(numeros[-1].replace(".", "").replace(",", ""))
            except ValueError:
                qtd = numeros[-1]
        else:
            qtd = ""

        lista_input.append([sku, remessa_corrente, qtd, nome_cliente_corrente])
        lista_info.append((sku, qtd, remessa_corrente))

    return lista_input, lista_info

# -------------------- PARSE — ZV52 --------------------
def _ler_zv52_tsv(filepath):
    """Tenta ler o export como TSV (UTF-16 ou Latin-1) — padrão do SAP."""
    import io as _io
    with open(filepath, "rb") as f:
        raw = f.read()
    # Detecta encoding pelo BOM. Sem BOM, decodifica como Latin-1.
    # Sem essa checagem, `decode("utf-16")` pode "ter sucesso" em arquivos Latin-1
    # de tamanho par e devolver texto corrompido (perde tabs e quebras de linha).
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        texto = raw.decode("utf-16")
    else:
        texto = raw.decode("latin-1", errors="ignore")

    linhas = texto.splitlines()
    header_idx = None
    for i, linha in enumerate(linhas):
        linha_lower = linha.lower()
        if "material" in linha_lower and "saldo" in linha_lower:
            header_idx = i
            break
    if header_idx is None:
        raise ValueError("Cabeçalho TSV não encontrado.")

    # O export do SAP é PAGINADO: a cada quebra de página repete o bloco de
    # cabeçalho ("Relatório:/Usuário:", com nº de campos diferente) e a própria
    # linha de colunas. Esses ruídos quebram o tokenizer do pandas
    # (ParserError: Expected N fields, saw M). Mantém só o cabeçalho + linhas
    # de dados com o mesmo nº de colunas, descartando cabeçalhos repetidos.
    header = linhas[header_idx]
    n_cols = len(header.split("\t"))
    selecionadas = [header]
    for linha in linhas[header_idx + 1:]:
        if len(linha.split("\t")) != n_cols:
            continue
        if linha == header:
            continue
        selecionadas.append(linha)

    df = pd.read_csv(_io.StringIO("\n".join(selecionadas)), sep="\t", dtype=str, header=0)
    df.columns = [c.strip() for c in df.columns]
    return df


def _ler_zv52_excel(filepath):
    """Tenta ler como Excel real (xlsx ou xls binário)."""
    try:
        df_raw = pd.read_excel(filepath, header=None, dtype=str)
    except Exception:
        df_raw = pd.read_excel(filepath, header=None, dtype=str, engine="openpyxl")

    header_idx = None
    for i, row in df_raw.iterrows():
        valores = " ".join(str(v).lower() for v in row.values if pd.notna(v))
        if "material" in valores and "saldo" in valores:
            header_idx = i
            break
    if header_idx is None:
        raise ValueError("Cabeçalho Excel não encontrado.")

    df = df_raw.iloc[header_idx + 1:].copy()
    df.columns = [str(c).strip() for c in df_raw.iloc[header_idx].values]
    return df.reset_index(drop=True)


def parse_zv52(filepath):
    """
    Lê o export ZV52. Tenta TSV (UTF-16/Latin-1) primeiro; se falhar, tenta Excel real.
    Detecta colunas 'material' e 'saldo' dinamicamente pelo cabeçalho.
    Retorna list[dict] com {'material': str, 'saldo_fisico': int}.
    """
    try:
        df = _ler_zv52_tsv(filepath)
    except Exception as e_tsv:
        try:
            df = _ler_zv52_excel(filepath)
        except Exception as e_xls:
            raise ValueError(
                f"Linha de cabeçalho com 'Material' e 'Saldo' não encontrada no ZV52. "
                f"TSV: {e_tsv} | Excel: {e_xls}"
            )

    mat_col = next((c for c in df.columns if "material" in c.lower()), None)
    # "sico" discrimina "Saldo Físico" de outras colunas "Saldo Dep.", "Sal. Res. V", etc.
    sal_col = next((c for c in df.columns if "sico" in c.lower()), None)

    if not mat_col or not sal_col:
        print(f"⚠️ Colunas encontradas no ZV52: {list(df.columns)}")
        raise ValueError(
            f"Colunas 'material' e/ou 'saldo' não encontradas. "
            f"Colunas disponíveis: {list(df.columns)}"
        )

    print(f"📊 ZV52 → '{mat_col}' = material | '{sal_col}' = saldo_fisico")

    registros = []
    for _, row in df.iterrows():
        mat = str(row[mat_col]).strip()
        if not mat or mat.lower() == "nan":
            continue
        sal_str = str(row[sal_col]).replace(".", "").replace(",", "").strip()
        try:
            sal = int(float(sal_str))
        except (ValueError, TypeError):
            sal = 0
        registros.append({"material": mat, "saldo_fisico": sal})

    return registros

# --------------------- FLUXO NORMAL --------------------------
def fluxo_normal(data_filtro=None):
    """
    Busca transportes pendentes (status_consulta_sap=false) no Supabase,
    exporta cada um do SAP, insere itens em transporte_itens e marca como processado.

    data_filtro: objeto datetime.date para filtrar transportes pelo DIA de created_at.
                 Se None, busca todos os pendentes (sem filtro de data).
    """
    print("🔄 Iniciando Integração...")
    supabase = authenticate_supabase()
    session = authenticate_sap()
    if not session:
        print("❌ Falha de autenticação no SAP.")
        return

    # Processa todos os transportes pendentes, sem filtrar por tipo — inclui
    # "devolução", igual ao rpa_clr.
    query = (
        supabase.table("transportes")
        .select("*")
        .eq("status_consulta_sap", False)
    )

    # Filtro por dia (created_at é timestamptz). Usa fuso de Brasília (-03:00) para
    # que "hoje" corresponda ao dia local, ignorando a hora.
    if data_filtro is not None:
        tz_br = timezone(timedelta(hours=-3))
        inicio = datetime(data_filtro.year, data_filtro.month, data_filtro.day, tzinfo=tz_br)
        fim = inicio + timedelta(days=1)
        query = query.gte("created_at", inicio.isoformat()).lt("created_at", fim.isoformat())

    resp = query.execute()
    pendentes = resp.data if resp.data else []

    descricao_filtro = f"data {data_filtro.strftime('%d/%m/%Y')}" if data_filtro else "todos os pendentes"

    if not pendentes:
        print(f"ℹ️ Nenhum transporte pendente ({descricao_filtro}).")
        return

    print(f"🧾 {len(pendentes)} transportes pendentes encontrados ({descricao_filtro}).")
    for transporte_row in pendentes:
        if _cancelar_evento.is_set():
            print("🛑 Cancelado pelo usuário. Interrompendo a integração.")
            break

        transporte   = transporte_row["numero_transporte"]
        transport_id = transporte_row["id"]
        print(f"\n➡️ Processando transporte {transporte} (id {transport_id})")

        filepath = extrair_dados_sap_para_xls(session, transporte)
        if not filepath:
            continue

        try:
            lista_input, _ = parse_zwm3(filepath)
            if not lista_input:
                print("ℹ️ Nenhum dado válido no arquivo exportado.")
                continue

            # Consolidar duplicatas por SKU + Remessa (SAP pode quebrar em múltiplas linhas)
            consolidado = {}
            for item in lista_input:
                sku, remessa, qtd, nome_cli = item[0], item[1], item[2], item[3]
                try:
                    qtd_int = int(str(qtd).replace(".", "").replace(",", ""))
                except (ValueError, TypeError):
                    qtd_int = 0
                chave = (sku, remessa)
                qtd_prev, _ = consolidado.get(chave, (0, ""))
                consolidado[chave] = (qtd_prev + qtd_int, nome_cli)

            # Remove itens anteriores e insere os consolidados
            supabase.table("transporte_itens").delete().eq("transporte_id", transport_id).execute()

            uid = _usuario_logado.get("id")
            novos_itens = [
                {
                    "transporte_id":     transport_id,
                    "sku":               sku,
                    "remessa":           remessa,
                    "quantidade_pedido": qtd_total,
                    "nome_cliente":      nome_cliente,
                    "usuario_id":        uid,
                }
                for (sku, remessa), (qtd_total, nome_cliente) in consolidado.items()
            ]
            supabase.table("transporte_itens").insert(novos_itens).execute()
            print(f"✔️ {len(novos_itens)} item(ns) inseridos em transporte_itens (após consolidação).")

            # Marca transporte como processado
            supabase.table("transportes").update({
                "status_consulta_sap": True,
                "usuario_id": uid,
            }).eq("id", transport_id).execute()
            print(f"✅ Transporte {transporte} marcado como processado.")

        finally:
            time.sleep(0.3)
            if filepath and os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    print(f"🗑️  Temporário removido: {filepath}")
                except Exception as e:
                    print(f"⚠️ Não foi possível remover temporário: {e}")

    if _cancelar_evento.is_set():
        print("\n🏁 Integração interrompida (cancelada pelo usuário).")
    else:
        print("\n🏁 Todos os transportes foram processados.")

# --------------------- FLUXO FATURADO ------------------------
# --------- RESOLUÇÃO DO TRANSPORTE (número → id) ---------
# O mesmo numero_transporte pode existir em mais de uma linha de `transportes`:
# um transporte descumprido pode voltar com o mesmo número, e números são
# reaproveitados semanas depois com outro tipo. Buscar pelo número e pegar a
# primeira linha (`data[0]`) pega a ocorrência errada nesses casos — daí todo o
# fluxo trabalhar com o `id` resolvido aqui.

# Grafias de status tratadas como descumprido. A coluna é texto livre; se
# aparecer outra grafia, basta acrescentar ao conjunto.
STATUS_DESCUMPRIDO = {
    "descumprido", "descumprida", "descumprimento",
    "nao_compareceu", "não compareceu",
}

CAMPOS_TRANSPORTE = (
    "id, numero_transporte, tipo, status, created_at, "
    "data_descumprimento, motivo_descumprimento"
)


def _is_descumprido(row: dict) -> bool:
    """Checa os campos próprios e o status: o Hawk Tech pode marcar de qualquer
    uma das duas formas, então não dá pra depender só de uma."""
    if row.get("data_descumprimento") or row.get("motivo_descumprimento"):
        return True
    return str(row.get("status") or "").strip().lower() in STATUS_DESCUMPRIDO


def _candidatos_validos(linhas):
    """Não-descumpridos, do mais recente para o mais antigo."""
    validas = [r for r in linhas if not _is_descumprido(r)]
    return sorted(validas, key=lambda r: str(r.get("created_at") or ""), reverse=True)


def escolher_transporte(linhas):
    """
    Função pura: recebe as linhas de `transportes` de um mesmo numero_transporte
    e devolve (escolhida, descartadas_no_desempate).

    Descarta as descumpridas; se ainda sobrar mais de uma, fica com a de
    `created_at` mais recente. Devolve (None, []) quando não sobra nenhuma.
    """
    validos = _candidatos_validos(linhas)
    if not validos:
        return None, []
    return validos[0], validos[1:]


def escolher_transporte_com_seriais(linhas, contar_seriais):
    """
    Função pura (a contagem entra por `contar_seriais(transporte_id) -> int`):
    desempate do fluxo de nº de série.

    Aqui a data não serve como critério. Um número reaproveitado semanas depois
    como `recebimento` não tem nenhuma linha em conferencia_expedicao, e o
    desempate por mais recente escolheria justamente esse — a expedição, que é
    quem tem os seriais, ficaria de fora. Então: entre os candidatos, prefere os
    que realmente têm seriais embarcados; entre esses, o mais recente.

    Se nenhum tiver seriais, devolve o mais recente para o fluxo seguir e exibir
    a mensagem padrão de "nenhum registro Embarcado".
    """
    validos = _candidatos_validos(linhas)
    if not validos:
        return None, []
    if len(validos) == 1:
        return validos[0], []

    com_seriais = [r for r in validos if contar_seriais(r["id"]) > 0]
    escolhido = com_seriais[0] if com_seriais else validos[0]
    return escolhido, [r for r in validos if r["id"] != escolhido["id"]]


def _descrever_transporte(row: dict) -> str:
    return (f"id {str(row.get('id'))[:8]} | {row.get('tipo')} | "
            f"criado {str(row.get('created_at') or '')[:10]} | status {row.get('status')}")


def _contar_seriais_embarcados(supabase, transporte_id) -> int:
    """Quantas linhas 'Embarcado' o transporte tem em conferencia_expedicao."""
    try:
        resp = supabase.table("conferencia_expedicao").select("id", count="exact").eq(
            "transporte_id", transporte_id
        ).eq("status_produto", "Embarcado").execute()
        return resp.count or 0
    except Exception as e:
        print(f"⚠️ Não foi possível contar seriais do transporte {str(transporte_id)[:8]}: {e}")
        return 0


def _resolver_com(supabase, transporte, escolher):
    """Busca as ocorrências do número, aplica `escolher` e loga o desempate."""
    resp = supabase.table("transportes").select(CAMPOS_TRANSPORTE).eq(
        "numero_transporte", str(transporte)
    ).execute()
    linhas = resp.data or []

    if not linhas:
        print(f"❌ Transporte {transporte} não encontrado no Supabase.")
        return None

    escolhido, descartados = escolher(linhas)
    if escolhido is None:
        print(f"❌ Transporte {transporte}: todas as {len(linhas)} ocorrência(s) "
              f"estão descumpridas.")
        return None

    if descartados:
        print(f"⚠️ {len(linhas)} transportes com o número {transporte}. Usando:")
        print(f"   ✔️ {_descrever_transporte(escolhido)}")
        for d in descartados:
            print(f"   ↳ descartado: {_descrever_transporte(d)}")

    return escolhido["id"]


def resolver_transporte_id(supabase, transporte) -> str | None:
    """
    numero_transporte → id, descartando descumpridos e ficando com o mais
    recente. Devolve None (com mensagem) se não houver transporte utilizável.
    """
    return _resolver_com(supabase, transporte, escolher_transporte)


def resolver_transporte_id_serial(supabase, transporte) -> str | None:
    """
    numero_transporte → id para o fluxo de nº de série, desempatando por quem
    tem seriais embarcados. Ver `escolher_transporte_com_seriais`.
    """
    return _resolver_com(
        supabase,
        transporte,
        lambda linhas: escolher_transporte_com_seriais(
            linhas, lambda tid: _contar_seriais_embarcados(supabase, tid)
        ),
    )


def atualizar_um_transporte_faturado(supabase, session, transporte, transporte_id):
    """
    Exporta /NZWM3, atualiza quantidade_faturado em transporte_itens
    e compara com quantidade_embarcada.
    """
    print(f"\n➡️ [FATURADO] Processando transporte {transporte}...")

    filepath = extrair_dados_sap_para_xls(session, transporte)
    if not filepath:
        return

    try:
        lista_input, _ = parse_zwm3(filepath)
        if not lista_input:
            print("ℹ️ Nenhum dado válido no arquivo exportado.")
            return

        # transporte_id já vem resolvido pelo chamador (ver resolver_transporte_id)
        transport_id = transporte_id

        # Consolidar duplicatas por SKU + Remessa antes de atualizar
        consolidado = {}
        for item in lista_input:
            sku, remessa, qtd = item[0], item[1], item[2]
            try:
                qtd_int = int(str(qtd).replace(".", "").replace(",", ""))
            except (ValueError, TypeError):
                qtd_int = 0
            chave = (sku, remessa)
            consolidado[chave] = consolidado.get(chave, 0) + qtd_int

        # Atualizar quantidade_faturado por SKU + Remessa
        uid = _usuario_logado.get("id")
        updates_ok = 0
        for (sku, remessa), qtd_total in consolidado.items():
            result = supabase.table("transporte_itens").update(
                {"quantidade_faturado": qtd_total, "usuario_id": uid}
            ).eq("transporte_id", transport_id).eq("sku", sku).eq("remessa", remessa).execute()
            if result.data:
                updates_ok += 1
        print(f"✔️ {updates_ok} item(ns) atualizados com quantidade_faturado (após consolidação).")

        # Comparação faturado vs embarcado
        print("🔎 Comparando quantidade_faturado × quantidade_embarcada...")
        itens_resp = supabase.table("transporte_itens").select(
            "sku, remessa, quantidade_faturado, quantidade_embarcada"
        ).eq("transporte_id", transport_id).execute()

        itens = itens_resp.data or []
        divergencia = False
        total_fat = 0
        total_emb = 0
        for item in itens:
            sku = item["sku"]
            rem = item["remessa"]
            qf  = int(item["quantidade_faturado"] or 0)
            qe  = int(item["quantidade_embarcada"] or 0)
            total_fat += qf
            total_emb += qe
            if qf == qe:
                print(f"   ✅ SKU={sku}, Remessa={rem}: Faturado={qf}, Embarcado={qe}")
            else:
                print(f"   ❌ SKU={sku}, Remessa={rem}: Faturado={qf}, Embarcado={qe}")
                divergencia = True

        print(f"📊 Totais → Faturado={total_fat} | Embarcado={total_emb}")
        if not divergencia and total_fat == total_emb:
            print("✅ FATURADO confere com EMBARCADO (por SKU/Remessa).")
        else:
            print("❌ Divergência encontrada na conferência de FATURADO x EMBARCADO.")

    finally:
        time.sleep(0.3)
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
                print(f"🗑️  Temporário removido: {filepath}")
            except Exception as e:
                print(f"⚠️ Não foi possível remover temporário: {e}")

# ------------------- UPLOAD Nº DE SÉRIE (Supabase) -------------------
def buscar_transporte_supabase_c1(supabase, transporte_id: str, transporte: str = ""):
    """
    Busca registros do transporte em conferencia_expedicao filtrando
    status_produto='Embarcado'.

    Filtra por transporte_id, não pelo número: com o número repetido em
    `transportes`, o filtro por número misturaria os seriais de dois
    transportes diferentes no TXT enviado ao SAP.
    """
    try:
        resp = supabase.table("conferencia_expedicao").select(
            "id, numero_transporte, sku, numero_serie, remessa, upload_sap, status_produto"
        ).eq("transporte_id", transporte_id).eq("status_produto", "Embarcado").execute()

        if not resp.data:
            print(f"⚠️ Nenhum registro encontrado para o transporte {transporte} com status 'Embarcado'.")
            return None

        return pd.DataFrame(resp.data)
    except Exception as e:
        print(f"❌ Erro ao buscar transporte no Supabase: {e}")
        return None

def marcar_upload_ok(supabase, transporte_id: str, transporte: str = ""):
    """
    Marca upload_sap='OK' para as linhas do transporte em conferencia_expedicao.

    Filtra por transporte_id pelo mesmo motivo de buscar_transporte_supabase_c1:
    pelo número, carimbaria as linhas de outro transporte homônimo.
    """
    try:
        supabase.table("conferencia_expedicao").update(
            {"upload_sap": "OK", "usuario_id": _usuario_logado.get("id")}
        ).eq("transporte_id", transporte_id).execute()
        print(f"✅ Transporte {transporte} marcado como 'OK' na coluna upload_sap.")
    except Exception as e:
        print(f"⚠️ Erro ao marcar upload_sap: {e}")

def executar_sap_upload_c1(transporte, caminho_txt):
    try:
        sap_gui = win32com.client.GetObject("SAPGUI")
        application = sap_gui.GetScriptingEngine
        if application.Children.Count == 0:
            print("❌ Nenhuma conexão SAP ativa.")
            return False
        session = application.Children(0).Children(0)
        print(f"🚀 Enviando transporte {transporte} via SAP (ZPCS)...")

        session.findById("wnd[0]").maximize()
        session.findById("wnd[0]/tbar[0]/okcd").Text = "/NZPCS"
        session.findById("wnd[0]").sendVKey(0)

        campo_arq = session.findById("wnd[0]/usr/txtP_ARQ")
        campo_arq.Text = ""
        campo_arq.Text = caminho_txt

        campo_impressora = session.findById("wnd[0]/usr/ctxtP_IMPR")
        campo_impressora.Text = ""
        campo_impressora.Text = "LP01"

        campo_impressora.setFocus()
        campo_impressora.caretPosition = 4

        session.findById("wnd[0]").sendVKey(8)

        try:
            session.findById("wnd[1]").sendVKey(0)
        except:
            pass

        session.findById("wnd[0]").sendVKey(12)

        print(f"✅ Upload concluído para transporte {transporte}")
        return True

    except Exception as e:
        print(f"❌ Erro SAP upload transporte {transporte}: {e}")
        return False

def gerar_txt_transporte_c1(df, transporte, pasta_saida=PASTA_SAIDA_C1):
    transporte_formatado = str(transporte).zfill(10)
    caminho_arquivo = os.path.join(pasta_saida, f"{transporte_formatado}.txt")
    os.makedirs(pasta_saida, exist_ok=True)
    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        f.write(f"1     60     {transporte_formatado}\n")
        for _, row in df.iterrows():
            sku = str(row.get("sku", "")).strip()
            serie = str(row.get("numero_serie", "")).strip()
            if len(serie) > 2:
                serie = serie[:-2]
            remessa = str(row.get("remessa", "")).strip()
            linha = f"200013{sku}{serie}{remessa}"
            f.write(linha + "\n")
    print(f"✅ TXT gerado: {caminho_arquivo}")
    return caminho_arquivo

# --------------------- FLUXO ZV52 --------------------------
def fluxo_zv52():
    """Exporta ZV52 do SAP e atualiza a tabela zv52 no Supabase (delete + insert)."""
    print("🔄 Iniciando atualização ZV52...")
    session = authenticate_sap()
    if not session:
        print("❌ Falha de autenticação no SAP.")
        return

    supabase = authenticate_supabase()
    filepath = extrair_zv52_para_xls(session)
    if not filepath:
        print("❌ Export ZV52 falhou. Abortando.")
        return

    try:
        registros = parse_zv52(filepath)
        print(f"📦 {len(registros)} registros lidos do ZV52.")

        print("🗑️ Limpando tabela zv52 no Supabase...")
        supabase.table("zv52").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()

        if registros:
            uid = _usuario_logado.get("id")
            for r in registros:
                r["usuario_id"] = uid
            supabase.table("zv52").insert(registros).execute()
            print(f"✅ {len(registros)} registros inseridos na tabela zv52.")
        else:
            print("⚠️ Nenhum registro para inserir.")
    finally:
        try:
            os.remove(filepath)
        except Exception:
            pass

# ===================== TELA DE LOGIN =====================
def criar_tela_login() -> dict | None:
    """Tela de login. Retorna dados do usuário logado ou None se fechar sem logar."""
    resultado = {"usuario": None}

    root = tk.Tk()
    root.title("RPA Full Cross — Login")
    root.resizable(False, False)
    _set_window_icon(root)

    frame = ttk.Frame(root, padding=30)
    frame.grid(sticky="nsew")

    logo_img = _load_png(HEADER_LOGO, max_height=60)
    if logo_img:
        lbl_logo = ttk.Label(frame, image=logo_img)
        lbl_logo.image = logo_img
        lbl_logo.grid(row=0, column=0, columnspan=2, pady=(0, 16))

    ttk.Label(frame, text="Login:").grid(row=1, column=0, sticky="e", padx=6, pady=6)
    entry_login = ttk.Entry(frame, width=28)
    entry_login.grid(row=1, column=1, padx=6, pady=6)

    ttk.Label(frame, text="Senha:").grid(row=2, column=0, sticky="e", padx=6, pady=6)
    entry_senha = ttk.Entry(frame, width=28, show="*")
    entry_senha.grid(row=2, column=1, padx=6, pady=6)

    lbl_erro = ttk.Label(frame, text="", foreground="red")
    lbl_erro.grid(row=3, column=0, columnspan=2, pady=(4, 0))

    btn_entrar = ttk.Button(frame, text="Entrar", width=20)
    btn_entrar.grid(row=4, column=0, columnspan=2, pady=(12, 0))

    def tentar_login(event=None):
        login = entry_login.get().strip()
        senha = entry_senha.get().strip()
        if not login or not senha:
            lbl_erro.config(text="Preencha login e senha.")
            return
        btn_entrar.state(["disabled"])
        lbl_erro.config(text="Autenticando...")
        root.update()
        usuario = autenticar_usuario(login, senha)
        if usuario:
            resultado["usuario"] = usuario
            root.destroy()
        else:
            lbl_erro.config(text="Login ou senha inválidos.")
            btn_entrar.state(["!disabled"])

    btn_entrar.configure(command=tentar_login)
    entry_senha.bind("<Return>", tentar_login)
    entry_login.bind("<Return>", lambda e: entry_senha.focus())

    root.protocol("WM_DELETE_WINDOW", root.destroy)
    entry_login.focus()
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

def _run_in_thread(fn):
    """Decorator: roda função em thread daemon + inicializa COM."""
    def wrapper(*args, **kwargs):
        def _target():
            _com_init()
            try:
                fn(*args, **kwargs)
            finally:
                _com_uninit()
        t = threading.Thread(target=_target, daemon=True)
        t.start()
    return wrapper

def parse_data_filtro(texto: str):
    """
    Interpreta o texto do campo de data (dd/mm/aaaa).
    Retorna:
      (date, True)  -> data válida
      (None, True)  -> campo vazio (sem filtro de data, busca todos pendentes)
      (None, False) -> formato inválido
    """
    texto = (texto or "").strip()
    if not texto:
        return None, True
    try:
        return datetime.strptime(texto, "%d/%m/%Y").date(), True
    except ValueError:
        return None, False


def validar_transporte(transp: str) -> bool:
    if not transp.isdigit():
        messagebox.showwarning("Atenção", "O número de transporte deve conter apenas dígitos.")
        return False
    # Sem trava de quantidade de dígitos: em Jundiaí o número de transporte
    # pode ter menos ou mais dígitos, então só exigimos que seja numérico.
    return True

def criar_gui(usuario: dict):
    global _usuario_logado
    _usuario_logado = usuario

    root = tk.Tk()
    root.title("RPA Full Cross")
    root.geometry("1020x560")

    _set_window_icon(root)

    top = ttk.Frame(root, padding=12)
    top.grid(row=0, column=0, sticky="nsew")

    logo_left_img = _load_png(HEADER_LOGO)
    if logo_left_img:
        logo_left = ttk.Label(top, image=logo_left_img)
        logo_left.image = logo_left_img
        logo_left.grid(row=0, column=0, rowspan=3, padx=(0, 16), sticky="nw")

    center = ttk.Frame(top)
    center.grid(row=0, column=1, sticky="nw")

    nome_usuario = usuario.get("login", "")
    nivel = usuario.get("nivel_acesso", "")
    ttk.Label(center, text=f"Usuário: {nome_usuario}  |  {nivel}", foreground="gray").grid(
        row=0, column=0, padx=6, pady=(0, 4), sticky="w"
    )

    btn_normal = ttk.Button(center, text="Integrar Informações Hawk Tech", width=30)
    btn_normal.grid(row=1, column=1, padx=6, pady=6, sticky="w")

    # Campo de data: filtra transportes pelo dia (created_at). Vazio = todos os pendentes.
    ttk.Label(center, text="Data (dd/mm/aaaa):").grid(row=1, column=2, padx=(12, 4), pady=6, sticky="e")
    entrada_data = ttk.Entry(center, width=14)
    entrada_data.grid(row=1, column=3, padx=6, pady=6, sticky="w")
    entrada_data.insert(0, date.today().strftime("%d/%m/%Y"))

    lbl1 = ttk.Label(center, text="Transporte:")
    entrada1 = ttk.Entry(center, width=22)
    btn_faturado = ttk.Button(center, text="Validação de Faturamento", width=24)
    lbl1.grid(row=2, column=0, padx=6, pady=6, sticky="w")
    entrada1.grid(row=2, column=1, padx=6, pady=6, sticky="w")
    btn_faturado.grid(row=2, column=2, padx=6, pady=6, sticky="w")

    lbl2 = ttk.Label(center, text="Transporte:")
    entrada2 = ttk.Entry(center, width=22)
    btn_serial = ttk.Button(center, text="Upload Número de Série", width=24)
    lbl2.grid(row=3, column=0, padx=6, pady=6, sticky="w")
    entrada2.grid(row=3, column=1, padx=6, pady=6, sticky="w")
    btn_serial.grid(row=3, column=2, padx=6, pady=6, sticky="w")

    btn_cancelar = ttk.Button(center, text="Cancelar", width=14)
    btn_cancelar.grid(row=1, column=4, padx=6, pady=6, sticky="w")
    btn_cancelar.state(["disabled"])

    btn_zv52 = ttk.Button(center, text="Atualizar ZV52", width=24)
    btn_zv52.grid(row=4, column=1, padx=6, pady=6, sticky="w")

    txt = ScrolledText(root, width=110, height=28)
    txt.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
    redir = _TextRedirector(txt)
    sys.stdout = redir
    sys.stderr = redir

    root.columnconfigure(0, weight=1)
    root.rowconfigure(1, weight=1)

    @_run_in_thread
    def acao_normal():
        data_filtro, ok = parse_data_filtro(entrada_data.get())
        if not ok:
            messagebox.showwarning("Atenção", "Data inválida. Use o formato dd/mm/aaaa (ex.: 30/06/2026) ou deixe vazio para buscar todos os pendentes.")
            return
        _cancelar_evento.clear()
        try:
            btn_normal.state(["disabled"]); btn_faturado.state(["disabled"]); btn_serial.state(["disabled"]); btn_zv52.state(["disabled"])
            btn_cancelar.state(["!disabled"])
            print("=====================================\n   Hawk Tech WMS Integrando Informações \n=====================================")
            fluxo_normal(data_filtro)
            print("\n✓ Integração concluída.\n")
        except Exception as e:
            print(f"\n[ERRO] Integração: {e}\n")
        finally:
            btn_cancelar.state(["disabled"])
            btn_normal.state(["!disabled"]); btn_faturado.state(["!disabled"]); btn_serial.state(["!disabled"]); btn_zv52.state(["!disabled"])

    def acao_cancelar():
        _cancelar_evento.set()
        btn_cancelar.state(["disabled"])
        print("\n🛑 Cancelamento solicitado. A integração será interrompida após o transporte atual...")

    @_run_in_thread
    def acao_faturado():
        transp = entrada1.get().strip()
        if not transp:
            messagebox.showwarning("Atenção", "Informe o número do transporte.")
            return
        if not validar_transporte(transp):
            return
        try:
            btn_normal.state(["disabled"]); btn_faturado.state(["disabled"]); btn_serial.state(["disabled"]); btn_zv52.state(["disabled"])
            print("=====================================\n   Hawk Tech WMS - Validação do FATURAMENTO  \n=====================================")

            supabase = authenticate_supabase()

            # Resolve o id uma única vez e repassa ao fluxo — evita consultar
            # (e logar o desempate) duas vezes.
            transporte_id = resolver_transporte_id(supabase, transp)
            if not transporte_id:
                messagebox.showwarning("Atenção", f"O transporte {transp} não consta em nosso banco de dados, por favor digite novamente!")
                return

            session = authenticate_sap()
            if not session:
                print("❌ Falha de autenticação no SAP.\n")
                return

            atualizar_um_transporte_faturado(supabase, session, transp, transporte_id)
            print("\n✓ Validação de Faturamento concluída.\n")
        except Exception as e:
            print(f"\n[ERRO] Validação de Faturamento: {e}\n")
        finally:
            btn_normal.state(["!disabled"]); btn_faturado.state(["!disabled"]); btn_serial.state(["!disabled"]); btn_zv52.state(["!disabled"])

    @_run_in_thread
    def acao_serial():
        transp = entrada2.get().strip()
        if not transp:
            messagebox.showwarning("Atenção", "Informe o número do transporte.")
            return
        if not validar_transporte(transp):
            return

        try:
            btn_normal.state(["disabled"]); btn_faturado.state(["disabled"]); btn_serial.state(["disabled"]); btn_zv52.state(["disabled"])
            print("=====================================\n   Hawk Tech WMS - Upload Nº Série\n=====================================")

            supabase = authenticate_supabase()

            transporte_id = resolver_transporte_id_serial(supabase, transp)
            if not transporte_id:
                messagebox.showwarning("Atenção", f"O transporte {transp} não consta em nosso banco de dados, por favor digite novamente!")
                return

            df = buscar_transporte_supabase_c1(supabase, transporte_id, transp)
            if df is None or df.empty:
                messagebox.showerror("Erro", "O transporte solicitado não consta em nosso banco de dados, por favor digite novamente!")
                print(f"❌ Transporte {transp} não encontrado ou não está 'Embarcado' no Supabase.")
                return

            if any(df["upload_sap"].astype(str).str.strip().str.upper() == "OK"):
                messagebox.showinfo("Aviso", "Esse transporte já foi processado anteriormente (Upload SAP=OK).")
                print(f"⛔ Transporte {transp} já processado (upload_sap = OK).")
                return

            caminho = gerar_txt_transporte_c1(df, transp)
            sucesso = executar_sap_upload_c1(transp, caminho)

            if sucesso:
                messagebox.showinfo("Sucesso", f"Transporte {transp} enviado ao SAP com sucesso.")
                marcar_upload_ok(supabase, transporte_id, transp)

            print("\n✓ Upload Nº Série concluído.\n")
        except Exception as e:
            print(f"\n[ERRO] Upload Nº Série: {e}\n")
        finally:
            btn_normal.state(["!disabled"]); btn_faturado.state(["!disabled"]); btn_serial.state(["!disabled"]); btn_zv52.state(["!disabled"])

    @_run_in_thread
    def acao_zv52():
        try:
            btn_normal.state(["disabled"]); btn_faturado.state(["disabled"]); btn_serial.state(["disabled"]); btn_zv52.state(["disabled"])
            print("=====================================\n   Hawk Tech WMS - Atualizar ZV52\n=====================================")
            fluxo_zv52()
            print("\n✓ Atualização ZV52 concluída.\n")
        except Exception as e:
            print(f"\n[ERRO] Atualizar ZV52: {e}\n")
        finally:
            btn_normal.state(["!disabled"]); btn_faturado.state(["!disabled"]); btn_serial.state(["!disabled"]); btn_zv52.state(["!disabled"])

    btn_normal.configure(command=acao_normal)
    btn_cancelar.configure(command=acao_cancelar)
    btn_faturado.configure(command=acao_faturado)
    btn_serial.configure(command=acao_serial)
    btn_zv52.configure(command=acao_zv52)

    root.mainloop()

if __name__ == "__main__":
    from multiprocessing import freeze_support
    freeze_support()
    try:
        if not os.path.exists(PASTA_EXPORT):
            os.makedirs(PASTA_EXPORT, exist_ok=True)
    except Exception:
        pass
    usuario = criar_tela_login()
    if not usuario:
        sys.exit(0)
    criar_gui(usuario)
