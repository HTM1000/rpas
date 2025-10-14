# -*- coding: utf-8 -*-
"""
Script de TESTE RAPIDO - processa as linhas restantes
"""
import time
import random
import pandas as pd
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os

# CONFIGURACOES
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY"
SHEET_NAME = "Separação"
OUTPUT_FILE = "teste_resultado_final.xlsx"

def authenticate_google():
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

def buscar_linhas_novas(service):
    res = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A1:T"
    ).execute()

    valores = res.get("values", [])
    if not valores:
        return [], None, None

    headers, dados = valores[0], valores[1:]
    linhas = []

    for i, row in enumerate(dados):
        if len(row) < len(headers):
            row += [''] * (len(headers) - len(row))

        idx_status_oracle = headers.index("Status Oracle")
        idx_status = headers.index("Status")
        status_oracle = row[idx_status_oracle].strip()
        status = row[idx_status].strip().upper()

        if status_oracle == "" and "CONCLUÍDO" in status:
            linhas.append((i + 2, dict(zip(headers, row))))

    return linhas, headers, dados

def processar_linha(service, linha_num, linha_data, simular_erro=False):
    print(f"\nProcessando linha {linha_num}...", end=" ")

    # 1. ATUALIZA SHEETS
    try:
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!T{linha_num}",
            valueInputOption="RAW",
            body={"values": [["Processo Oracle Concluído"]]}
        ).execute()
        print("[Sheets: OK]", end=" ")
    except Exception as e:
        print(f"[Sheets: ERRO - {e}]")
        return {
            "linha": linha_num,
            "item": linha_data.get("Item", ""),
            "status_sheets": "ERRO",
            "status_oracle": "NAO PROCESSADO",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "observacao": f"Erro Sheets: {e}"
        }

    # 2. SIMULA ORACLE (rapido - sem delay)
    sucesso_oracle = not simular_erro
    print(f"[Oracle: {'SUCESSO' if sucesso_oracle else 'ERRO'}]")

    return {
        "linha": linha_num,
        "item": linha_data.get("Item", ""),
        "quantidade": linha_data.get("Quantidade", ""),
        "referencia": linha_data.get("Cód Referencia", ""),
        "status_sheets": "ATUALIZADO",
        "status_oracle": "SUCESSO" if sucesso_oracle else "ERRO",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "observacao": "OK" if sucesso_oracle else "Erro Oracle simulado"
    }

def main():
    print("\n" + "="*80)
    print("TESTE RAPIDO - PROCESSAMENTO DAS LINHAS RESTANTES")
    print("="*80)

    service = authenticate_google()

    # BUSCA ANTES
    print("\n1) Buscando linhas ANTES do processamento...")
    linhas_antes, _, _ = buscar_linhas_novas(service)
    print(f"   Encontradas: {len(linhas_antes)} linhas")

    if not linhas_antes:
        print("\nNenhuma linha para processar!")
        return

    # PROCESSA
    print(f"\n2) Processando {len(linhas_antes)} linhas...")
    resultados = []

    for idx, (linha_num, linha_data) in enumerate(linhas_antes):
        # 20% de chance de erro
        simular_erro = random.random() < 0.2
        resultado = processar_linha(service, linha_num, linha_data, simular_erro)
        resultados.append(resultado)
        time.sleep(0.3)  # Pausa curta

    # SALVA EXCEL
    print(f"\n3) Salvando resultados em Excel...")
    df = pd.DataFrame(resultados)
    df.to_excel(OUTPUT_FILE, index=False, engine='openpyxl')
    print(f"   Arquivo: {OUTPUT_FILE}")

    # ESTATISTICAS
    print("\n" + "="*80)
    print("RESUMO")
    print("="*80)
    print(f"Total processado: {len(resultados)}")
    print(f"Sucesso Oracle: {len([r for r in resultados if r['status_oracle'] == 'SUCESSO'])}")
    print(f"Erro Oracle: {len([r for r in resultados if r['status_oracle'] == 'ERRO'])}")
    print(f"Erro Sheets: {len([r for r in resultados if r['status_sheets'] == 'ERRO'])}")

    # BUSCA DEPOIS (para verificar duplicacao)
    print("\n4) Buscando linhas DEPOIS do processamento (verificar duplicacao)...")
    time.sleep(2)  # Aguarda atualizacao do Sheets
    linhas_depois, _, _ = buscar_linhas_novas(service)
    print(f"   Encontradas: {len(linhas_depois)} linhas")

    print("\n" + "="*80)
    print("VERIFICACAO DE DUPLICACAO")
    print("="*80)

    if len(linhas_depois) == 0:
        print("PERFEITO! Nenhuma linha duplicada.")
        print("Todas as linhas foram marcadas corretamente como 'Processo Oracle Concluido'")
    else:
        print(f"ATENCAO! Ainda existem {len(linhas_depois)} linhas pendentes:")
        for linha_num, linha_data in linhas_depois[:10]:
            print(f"   - Linha {linha_num}: {linha_data.get('Item', 'N/A')}")

        if len(linhas_depois) > 10:
            print(f"   ... e mais {len(linhas_depois) - 10} linhas")

    print("\n" + "="*80)
    print("TESTE CONCLUIDO!")
    print("="*80)

if __name__ == "__main__":
    main()
