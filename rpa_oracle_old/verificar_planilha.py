# -*- coding: utf-8 -*-
"""
Script para verificar o estado atual da planilha
"""
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import pandas as pd

# CONFIGURACOES
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY"
SHEET_NAME = "Separação"

def authenticate_google():
    """Autentica no Google Sheets"""
    token_path = "token.json"
    creds_path = "CredenciaisOracle.json"
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

def verificar_estado_planilha(service):
    """Verifica o estado atual da planilha"""
    print("\n" + "="*80)
    print("VERIFICANDO ESTADO DA PLANILHA")
    print("="*80)

    res = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A1:T"
    ).execute()

    valores = res.get("values", [])
    if not valores:
        print("ERRO - Planilha vazia!")
        return

    headers, dados = valores[0], valores[1:]
    print(f"\nTotal de linhas na planilha: {len(dados)}")

    # Analisa os status
    idx_status_oracle = headers.index("Status Oracle")
    idx_status = headers.index("Status")
    idx_item = headers.index("Item")

    resultados = []

    for i, row in enumerate(dados):
        if len(row) < len(headers):
            row += [''] * (len(headers) - len(row))

        status_oracle = row[idx_status_oracle].strip()
        status = row[idx_status].strip().upper()
        item = row[idx_item].strip()
        linha_num = i + 2  # +2 porque começa em 1 e tem header

        resultados.append({
            "linha": linha_num,
            "item": item,
            "status": status,
            "status_oracle": status_oracle
        })

    # Criar DataFrame
    df = pd.DataFrame(resultados)

    # Estatísticas
    print("\n" + "="*80)
    print("ESTATISTICAS")
    print("="*80)

    total = len(df)
    concluido_status = len(df[df['status'].str.contains('CONCLUÍDO', na=False)])
    oracle_concluido = len(df[df['status_oracle'] == 'Processo Oracle Concluído'])
    oracle_vazio = len(df[df['status_oracle'] == ''])
    oracle_pd = len(df[df['status_oracle'] == 'PD'])

    print(f"\nTotal de linhas: {total}")
    print(f"Status = 'CONCLUIDO': {concluido_status}")
    print(f"Status Oracle = 'Processo Oracle Concluido': {oracle_concluido}")
    print(f"Status Oracle = vazio: {oracle_vazio}")
    print(f"Status Oracle = 'PD': {oracle_pd}")

    # Linhas que DEVERIAM ser processadas (Status=CONCLUIDO e Status Oracle=vazio)
    candidatas = df[(df['status'].str.contains('CONCLUÍDO', na=False)) & (df['status_oracle'] == '')]

    print("\n" + "="*80)
    print("LINHAS CANDIDATAS A PROCESSAMENTO")
    print("(Status = 'CONCLUIDO' e Status Oracle = vazio)")
    print("="*80)
    print(f"\nTotal: {len(candidatas)}")

    if len(candidatas) > 0:
        print("\nPrimeiras 20 linhas candidatas:")
        for idx, row in candidatas.head(20).iterrows():
            print(f"   Linha {row['linha']}: Item={row['item']}")

    # Linhas que foram processadas pelo teste
    processadas = df[(df['status'].str.contains('CONCLUÍDO', na=False)) &
                     (df['status_oracle'] == 'Processo Oracle Concluído')]

    print("\n" + "="*80)
    print("LINHAS PROCESSADAS")
    print("(Status = 'CONCLUIDO' e Status Oracle = 'Processo Oracle Concluido')")
    print("="*80)
    print(f"\nTotal: {len(processadas)}")

    if len(processadas) > 0:
        print("\nPrimeiras 20 linhas processadas:")
        for idx, row in processadas.head(20).iterrows():
            print(f"   Linha {row['linha']}: Item={row['item']}")

    # Salvar em Excel
    output_file = "estado_atual_planilha.xlsx"
    df.to_excel(output_file, index=False, engine='openpyxl')
    print(f"\n\nArquivo salvo: {output_file}")

if __name__ == "__main__":
    service = authenticate_google()
    verificar_estado_planilha(service)
