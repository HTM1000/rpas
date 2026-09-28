import os
import sys
import time
import re
import win32com.client
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# ======================= CONFIG =======================
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "15d9oZBw2H7aXbnq1MY6r4duq0FbV85ULPLobfs19WH0"

ABA_ORIGEM         = "Registro Transportes"     # F=Transporte, K=Status Busca SAP
ABA_INPUT_SAP      = "INPUT ZWM3"               # saída SKU | Remessa | Qtd
ABA_INFO_TRANSP    = "Informações Transportes"  # saída consolidada por SKU (uma linha por SKU)
COL_STATUS_LETRA   = "K"                        # coluna Status Busca SAP (A=1 ... K=11)

# Export do SAP
PASTA_EXPORT     = r"C:\RPA"
NOME_ARQ_EXPORT  = "ZWM3.xls"

# ======================= AUX ==========================
def resource_path(relative_path):
    if getattr(sys, "_MEIPASS", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ------------------- AUTENTICAÇÃO ---------------------
def authenticate_google():
    token_path = resource_path("token.json")
    credenciais_path = resource_path("CredenciaisCLR.json")
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credenciais_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as token:
            token.write(creds.to_json())
    return build("sheets", "v4", credentials=creds)

def authenticate_sap():
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

# ------------- LER TRANSPORTES PENDENTES --------------
def ler_transportes_pendentes(service, spreadsheet_id, aba_nome):
    """Retorna [(transporte, row_index_1based)] onde K != 'OK'."""
    range_ = f"{aba_nome}!A2:K"
    valores = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=range_
    ).execute().get("values", [])
    pendentes = []
    for i, linha in enumerate(valores, start=2):
        transporte = linha[5].strip() if len(linha) > 5 else ""
        status_busca = linha[10].strip().upper() if len(linha) > 10 else ""
        if transporte and status_busca != "OK":
            pendentes.append((transporte, i))
    return pendentes

def ler_linha_origem(service, spreadsheet_id, row_idx):
    """Lê A:J da linha de origem (Registro Transportes) para montar Informações Transportes."""
    faixa = f"{ABA_ORIGEM}!A{row_idx}:J{row_idx}"
    vals = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=faixa
    ).execute().get("values", [[]])
    row = vals[0] if vals else []
    while len(row) < 10:
        row.append("")
    # A ID, B Data, C Mês, D (—), E Horário, F Transporte, G Placa, H Doca, I Tipo Mov., J Status
    return {
        "id":            row[0],
        "data":          row[1],
        "mes":           row[2],
        "numero_transp": row[5],
        "placa":         row[6],
        "hora_agenda":   row[4],
        "doca":          row[7],
        "tipo_mov":      row[8],
        "status":        row[9],
    }

# ---------------- EXPORTAÇÃO (igual VBA) ---------------
def extrair_dados_sap_para_xls(session, transporte):
    """Exporta /NZWM3 usando a mesma opção do VBA: radSPOPLI-SELFLAG[1,0]."""
    print(f"🚛 Processando transporte {transporte} no SAP...")
    try:
        if not os.path.exists(PASTA_EXPORT):
            os.makedirs(PASTA_EXPORT)
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

# -------------------- PARSE/LEITURA --------------------
def parse_zwm3(filepath):
    """
    Lê o export do SAP (UTF-16 ou Latin-1) e retorna:
      lista_input: [ [SKU, Remessa, Qtd] ... ]        -> para INPUT ZWM3
      lista_info:  [ (SKU, Qtd, Remessa) ... ]        -> para Informações Transportes

    Regras:
      - Detecta linhas de REMESSA (têm ao menos um número longo >= 6 dígitos).
      - Mantém a remessa corrente até aparecer uma nova remessa.
      - Para cada linha de SKU:
          SKU  = token logo após o primeiro número da linha
          Qtd  = último número da linha (coluna Diferença) -> convertido para int
          Remessa = remessa corrente
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
    remessa_corrente = ""

    for ln in linhas[start:]:
        tokens = [t for t in re.split(r"\s+", ln.strip()) if t]

        # Linha de REMESSA?
        longs = [t for t in tokens if longnum.fullmatch(t)]
        if longs:
            remessa_corrente = longs[0]
            continue

        # Linha de SKU: número + código
        sku = ""
        for idx, t in enumerate(tokens):
            if t.isdigit() and idx + 1 < len(tokens):
                sku = tokens[idx + 1]
                break
        if not sku:
            continue

        # Qtd = último número da linha (Diferença) -> INT
        numeros = [t for t in tokens if is_num(t)]
        if numeros:
            try:
                qtd = int(numeros[-1].replace(".", "").replace(",", ""))
            except ValueError:
                qtd = numeros[-1]  # fallback em string
        else:
            qtd = ""

        lista_input.append([sku, remessa_corrente, qtd])
        lista_info.append((sku, qtd, remessa_corrente))

    return lista_input, lista_info

# -------------------- COLAR NO SHEETS ------------------
def clear_and_set(service, spreadsheet_id, aba_nome, values):
    """Limpa a aba e escreve valores (usa RAW para preservar tipos: int vira número)."""
    service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id, range=aba_nome
    ).execute()
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"{aba_nome}!A1",
        valueInputOption="RAW",
        body={"values": values}
    ).execute()

# ======= APPEND PRESERVANDO FORMATAÇÃO (herda da linha anterior) =======
def _get_sheet_id(service, spreadsheet_id, sheet_title):
    meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    for sh in meta["sheets"]:
        if sh["properties"]["title"] == sheet_title:
            return sh["properties"]["sheetId"]
    raise ValueError(f"Sheet '{sheet_title}' não encontrada.")

def _get_last_row(service, spreadsheet_id, sheet_title):
    # última linha preenchida (1-based). Se a aba estiver vazia, retorna 0.
    rng = f"{sheet_title}!A:A"
    vals = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=rng
    ).execute().get("values", [])
    return len(vals)

def append_rows(service, spreadsheet_id, sheet_title, values):
    """
    Insere N linhas herdando a formatação da linha anterior e depois escreve os valores.
    """
    if not values:
        return

    sheet_id = _get_sheet_id(service, spreadsheet_id, sheet_title)
    last = _get_last_row(service, spreadsheet_id, sheet_title)  # 1-based
    n = len(values)

    # 1) Inserir linhas (0-based nos índices do batchUpdate)
    requests = [{
        "insertDimension": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "ROWS",
                "startIndex": last,         # linha após a última preenchida
                "endIndex": last + n
            },
            "inheritFromBefore": True
        }
    }]
    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": requests}
    ).execute()

    # 2) Preencher os valores nas linhas recém-inseridas
    start_row = last + 1  # volta para 1-based
    range_write = f"{sheet_title}!A{start_row}"
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_write,
        valueInputOption="RAW",
        body={"values": values}
    ).execute()

# ------------------- MARCAR STATUS OK ------------------
def marcar_status_ok(service, spreadsheet_id, row_index_1based):
    alvo = f"{ABA_ORIGEM}!{COL_STATUS_LETRA}{row_index_1based}"
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=alvo,
        valueInputOption="RAW",
        body={"values": [["OK"]]}
    ).execute()
    print(f"✅ Marcado OK em {alvo}")

# -------------- MONTAR "INFORMAÇÕES TRANSPORTES" --------------
def montar_linhas_info(origem_row_dict, lista_info):
    """
    Colunas:
    A ID | B Data | C Mês | D Numero Transporte | E Placa Veículo | F Horário Agenda |
    G Doca | H Tipo Movimentação | I SKU | J QTD. Nota | K Remessa | L Status |
    M Usuário ADM | N Observação | O TR + sku | P Docas | Q Tr | R Modelos | S Qtd. Pedido
    """
    linhas = []
    for sku, qtd, remessa in lista_info:
        num  = origem_row_dict["numero_transp"]
        doca = origem_row_dict["doca"]
        linhas.append([
            origem_row_dict["id"],             # A
            origem_row_dict["data"],           # B
            origem_row_dict["mes"],            # C
            num,                               # D
            origem_row_dict["placa"],          # E
            origem_row_dict["hora_agenda"],    # F
            doca,                              # G
            origem_row_dict["tipo_mov"],       # H
            sku,                               # I
            qtd,                               # J (número)
            remessa,                           # K
            origem_row_dict["status"],         # L
            "",                                # M
            "",                                # N
            f"{num}: {sku}",                   # O
            f"Doca: {doca}",                   # P
            f"Transporte: {num} - Doca: {doca}", # Q
            f"SKU: {sku}",                     # R
            f"Qtd Pedido: {qtd}",              # S
        ])
    return linhas

# --------------------- MAIN / FLUXO --------------------
def main():
    print("🔄 Iniciando automação...")
    service = authenticate_google()
    session = authenticate_sap()
    if not service or not session:
        print("❌ Falha de autenticação.")
        return

    pendentes = ler_transportes_pendentes(service, SPREADSHEET_ID, ABA_ORIGEM)
    if not pendentes:
        print("ℹ️ Nenhum transporte pendente (coluna K = OK).")
        return

    print(f"🧾 {len(pendentes)} transportes pendentes encontrados.")

    for transporte, row_idx in pendentes:
        print(f"\n➡️ Processando transporte {transporte} (linha {row_idx})")

        filepath = extrair_dados_sap_para_xls(session, transporte)
        if not filepath:
            continue

        try:
            lista_input, lista_info = parse_zwm3(filepath)
            if not lista_input:
                print("ℹ️ Nenhum dado válido no arquivo exportado.")
                continue

            # INPUT ZWM3 (limpa e cola)
            clear_and_set(
                service, SPREADSHEET_ID, ABA_INPUT_SAP,
                [["SKU", "Remessa", "Qtd. Solicitada"]] + lista_input
            )
            print("✔️ Dados colados em INPUT ZWM3.")

            # Informações Transportes (append 1 linha por SKU do transporte) preservando formatação
            origem_row = ler_linha_origem(service, SPREADSHEET_ID, row_idx)
            linhas_info = montar_linhas_info(origem_row, lista_info)
            append_rows(service, SPREADSHEET_ID, ABA_INFO_TRANSP, linhas_info)
            print(f"✔️ {len(linhas_info)} linha(s) adicionada(s) em 'Informações Transportes' (com formatação).")

            # marcar OK na origem
            marcar_status_ok(service, SPREADSHEET_ID, row_idx)

        finally:
            time.sleep(0.3)
            if filepath and os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    print(f"🗑️  Temporário removido: {filepath}")
                except Exception as e:
                    print(f"⚠️ Não foi possível remover temporário: {e}")

    print("\n🏁 Todos os transportes foram processados.")

if __name__ == "__main__":
    main()



# ==== NOVO BLOCO PARA FATURADO (um transporte específico) ====
COL_FATURADO_LETRA = "L"   # coluna Consulta Faturado em Registro Transportes
ABA_FATURADO       = "FATURADO"

def atualizar_um_transporte_faturado(service, spreadsheet_id, session, transporte):
    """
    Consulta no SAP apenas o transporte informado.
    Exporta SKU/Remessa/Qtd do SAP e cola em FATURADO (limpando antes).
    Depois atualiza a coluna T da aba Informações Transportes
    e marca "OK" na coluna L da aba Registro Transportes.
    """
    print(f"\n➡️ [FATURADO] Processando transporte {transporte}...")

    filepath = extrair_dados_sap_para_xls(session, transporte)
    if not filepath:
        return

    try:
        lista_input, lista_info = parse_zwm3(filepath)
        if not lista_input:
            print("ℹ️ Nenhum dado válido no arquivo exportado.")
            return

        # 1) Atualiza aba FATURADO (limpa antes de colar)
        clear_and_set(
            service,
            spreadsheet_id,
            ABA_FATURADO,
            [["SKU", "Remessa", "Qtd. Faturada"]] + lista_input
        )
        print("✔️ Dados colados em FATURADO.")

        # 2) Atualiza coluna T em Informações Transportes
        rng = f"{ABA_INFO_TRANSP}!A2:T"
        dados_info = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=rng
        ).execute().get("values", [])

        updates = []
        for sku, qtd, remessa in lista_info:
            for j, linha in enumerate(dados_info, start=2):
                if len(linha) < 11:
                    continue
                tr_info = str(linha[3]).strip()
                sku_info = str(linha[8]).strip()
                remessa_info = str(linha[10]).strip()

                if tr_info == str(transporte) and sku_info == sku and remessa_info == remessa:
                    alvo = f"{ABA_INFO_TRANSP}!T{j}"
                    updates.append({"range": alvo, "values": [[qtd]]})

        if updates:
            body = {"valueInputOption": "RAW", "data": updates}
            service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheet_id, body=body
            ).execute()
            print(f"✔️ Atualizadas {len(updates)} célula(s) na coluna T (Faturado)")

        # 3) Marca coluna L (Consulta Faturado) como OK na aba Registro Transportes
        range_registro = f"{ABA_ORIGEM}!A2:L"
        valores = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=range_registro
        ).execute().get("values", [])

        for i, linha in enumerate(valores, start=2):
            if len(linha) > 5 and linha[5].strip() == str(transporte):
                alvo = f"{ABA_ORIGEM}!{COL_FATURADO_LETRA}{i}"
                service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=alvo,
                    valueInputOption="RAW",
                    body={"values": [["OK"]]}
                ).execute()
                print(f"✅ Marcado OK em {alvo}")
                break

    finally:
        time.sleep(0.3)
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
                print(f"🗑️  Temporário removido: {filepath}")
            except Exception as e:
                print(f"⚠️ Não foi possível remover temporário: {e}")


def main_faturado_unico():
    print("📦 Iniciando atualização FATURADO (um transporte)...")
    service = authenticate_google()
    session = authenticate_sap()
    if not service or not session:
        print("❌ Falha de autenticação.")
        return

    # Pergunta o transporte
    transporte = input("Digite o número do transporte que deseja consultar: ").strip()
    if not transporte:
        print("❌ Nenhum transporte informado, saindo...")
        return

    atualizar_um_transporte_faturado(service, SPREADSHEET_ID, session, transporte)
    print("📦 Atualização FATURADO concluída.")


# ========== EXECUÇÃO ==========
if __name__ == "__main__":
    print("=====================================")
    print("   Genesys WMS - Automação SAP ⇆ GSheets")
    print("=====================================")
    print("Escolha o fluxo para rodar:")
    print("1 - Normal   (Registro ➝ Informações Transportes)")
    print("2 - Faturado (um transporte específico)")
    print("=====================================")

    escolha = input("Digite 1 ou 2 e pressione ENTER: ").strip()

    if escolha == "1":
        main()
    elif escolha == "2":
        main_faturado_unico()   # <-- aqui chamamos a função correta
    else:
        print("❌ Opção inválida. Encerrando...")

