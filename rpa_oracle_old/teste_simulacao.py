# -*- coding: utf-8 -*-
"""
Script de TESTE para simular o comportamento do RPA Oracle
Salva resultados em Excel ao invés de inserir no Oracle
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

# Arquivo de saída
OUTPUT_FILE = "teste_resultado_simulacao.xlsx"

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

def buscar_linhas_novas(service):
    """
    Busca linhas com Status Oracle vazio e Status contendo 'CONCLUIDO'
    """
    print("\n" + "="*80)
    print("BUSCANDO LINHAS NA PLANILHA...")
    print("="*80)

    res = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A1:T"
    ).execute()

    valores = res.get("values", [])
    if not valores:
        print("ERRO - Planilha vazia!")
        return [], None, None

    headers, dados = valores[0], valores[1:]
    print(f"Headers encontrados: {headers}")
    print(f"Total de linhas na planilha: {len(dados)}")

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
            print(f"   OK - Linha {i+2}: Candidata ao processamento")

    print(f"\nTOTAL DE LINHAS ENCONTRADAS PARA PROCESSAR: {len(linhas)}")
    print("="*80)
    return linhas, headers, dados

def simular_insercao_oracle(linha_data, simular_erro=False):
    """
    Simula a insercao no Oracle
    retorna True se sucesso, False se erro
    """
    item = linha_data.get("Item", "")
    quantidade = linha_data.get("Quantidade", "")
    referencia = linha_data.get("Cód Referencia", "")

    print(f"\n   Simulando insercao no Oracle...")
    print(f"      - Item: {item}")
    print(f"      - Quantidade: {quantidade}")
    print(f"      - Referencia: {referencia}")

    # Simula tempo de processamento
    time.sleep(0.5)

    if simular_erro:
        print(f"      ERRO SIMULADO na insercao!")
        return False
    else:
        print(f"      OK - Insercao simulada com sucesso!")
        return True

def processar_linha(service, linha_num, linha_data, simular_erro=False):
    """
    Processa uma unica linha:
    1. Atualiza no Sheets como "Processo Oracle Concluido"
    2. Simula insercao no Oracle
    3. Retorna resultado
    """
    print(f"\n{'-'*80}")
    print(f"PROCESSANDO LINHA {linha_num}")
    print(f"{'-'*80}")

    # 1. ATUALIZA IMEDIATAMENTE NO SHEETS
    print(f"\n1) Atualizando Google Sheets (Linha {linha_num})...")
    try:
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!T{linha_num}",
            valueInputOption="RAW",
            body={"values": [["Processo Oracle Concluído"]]}
        ).execute()
        print(f"   OK - Google Sheets atualizado com sucesso!")
    except Exception as e:
        print(f"   ERRO ao atualizar Sheets: {e}")
        print(f"   ATENCAO - Linha {linha_num} sera IGNORADA")
        return {
            "linha": linha_num,
            "item": linha_data.get("Item", ""),
            "quantidade": linha_data.get("Quantidade", ""),
            "referencia": linha_data.get("Cód Referencia", ""),
            "status_sheets": "ERRO",
            "status_oracle": "NAO PROCESSADO",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "observacao": f"Erro ao atualizar Sheets: {e}"
        }

    # 2. SIMULA INSERCAO NO ORACLE
    print(f"\n2) Inserindo no Oracle (simulacao)...")
    sucesso_oracle = simular_insercao_oracle(linha_data, simular_erro)

    # 3. MONTA RESULTADO
    resultado = {
        "linha": linha_num,
        "item": linha_data.get("Item", ""),
        "quantidade": linha_data.get("Quantidade", ""),
        "referencia": linha_data.get("Cód Referencia", ""),
        "sub_origem": linha_data.get("Sub.Origem", ""),
        "end_origem": linha_data.get("End. Origem", ""),
        "sub_destino": linha_data.get("Sub. Destino", ""),
        "end_destino": linha_data.get("End. Destino", ""),
        "status_sheets": "ATUALIZADO",
        "status_oracle": "SUCESSO" if sucesso_oracle else "ERRO",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "observacao": "Processado com sucesso" if sucesso_oracle else "Erro na insercao Oracle"
    }

    print(f"\nResultado da linha {linha_num}:")
    print(f"   - Sheets: {resultado['status_sheets']}")
    print(f"   - Oracle: {resultado['status_oracle']}")

    return resultado

def main():
    """Funcao principal do teste"""
    print("\n" + "="*80)
    print("INICIANDO TESTE DE SIMULACAO DO RPA ORACLE")
    print("="*80)

    # Autentica
    print("\nAutenticando no Google Sheets...")
    service = authenticate_google()
    print("OK - Autenticacao realizada!")

    # Busca linhas
    linhas, headers, _ = buscar_linhas_novas(service)

    if not linhas:
        print("\nATENCAO - Nenhuma linha encontrada para processar!")
        print("   Verifique se ha linhas com:")
        print("   - Status = 'CONCLUIDO'")
        print("   - Status Oracle = vazio")
        return

    # Processa cada linha
    resultados = []

    print("\n" + "="*80)
    print("INICIANDO PROCESSAMENTO DAS LINHAS")
    print("="*80)

    for idx, (linha_num, linha_data) in enumerate(linhas):
        # Simula erro aleatorio em algumas linhas (20% de chance)
        simular_erro = random.random() < 0.2

        if simular_erro:
            print(f"\nATENCAO: Linha {linha_num} sera processada COM ERRO SIMULADO")

        resultado = processar_linha(service, linha_num, linha_data, simular_erro)
        resultados.append(resultado)

        # Pausa entre linhas
        time.sleep(1)

    # Salva resultados em Excel
    print("\n" + "="*80)
    print("SALVANDO RESULTADOS EM EXCEL")
    print("="*80)

    df = pd.DataFrame(resultados)
    df.to_excel(OUTPUT_FILE, index=False, engine='openpyxl')

    print(f"OK - Arquivo salvo: {OUTPUT_FILE}")
    print(f"\nRESUMO DO PROCESSAMENTO:")
    print(f"   - Total de linhas processadas: {len(resultados)}")
    print(f"   - Sucessos no Oracle: {len([r for r in resultados if r['status_oracle'] == 'SUCESSO'])}")
    print(f"   - Erros no Oracle: {len([r for r in resultados if r['status_oracle'] == 'ERRO'])}")
    print(f"   - Erros no Sheets: {len([r for r in resultados if r['status_sheets'] == 'ERRO'])}")

    print("\n" + "="*80)
    print("TESTE CONCLUIDO!")
    print("="*80)

    # Agora vamos buscar novamente para ver se duplica
    print("\n" + "="*80)
    print("VERIFICANDO SE HA DUPLICACAO (Buscando novamente)...")
    print("="*80)

    linhas_depois, _, _ = buscar_linhas_novas(service)

    if not linhas_depois:
        print("PERFEITO! Nenhuma linha foi encontrada novamente.")
        print("   Isso significa que NAO HOUVE DUPLICACAO!")
    else:
        print(f"ATENCAO! {len(linhas_depois)} linha(s) ainda aparecem como pendentes:")
        for linha_num, linha_data in linhas_depois:
            print(f"   - Linha {linha_num}: {linha_data.get('Item', 'N/A')}")
        print("\n   Isso pode indicar DUPLICACAO se essas linhas ja foram processadas!")

if __name__ == "__main__":
    main()
