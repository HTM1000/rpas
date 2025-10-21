# -*- coding: utf-8 -*-
"""
Script para criar registros duplicados na planilha de teste
Para testar se o RPA consegue evitar duplicação
"""
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import random

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY"
SHEET_NAME = "Separação"

def criar_duplicados():
    """Cria registros duplicados na planilha"""
    print("="*60)
    print("CRIAR REGISTROS DUPLICADOS PARA TESTE")
    print("="*60)

    # Autenticar
    print("\n[1/4] Autenticando...")
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    service = build("sheets", "v4", credentials=creds)

    # Buscar dados existentes
    print("[2/4] Buscando dados existentes...")
    res = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A1:AC"
    ).execute()

    valores = res.get("values", [])
    headers = valores[0]
    dados = valores[1:]

    idx_id = headers.index("ID")
    idx_status = headers.index("Status")
    idx_status_oracle = headers.index("Status Oracle")

    print(f"[INFO] Total de linhas na planilha: {len(dados)}")

    # Encontrar linhas que foram processadas (Status Oracle preenchido)
    linhas_processadas = []
    for i, row in enumerate(dados):
        if len(row) < len(headers):
            row += [''] * (len(headers) - len(row))

        status_oracle = row[idx_status_oracle].strip() if len(row) > idx_status_oracle else ""

        if status_oracle != "":
            linhas_processadas.append((i, row))

    print(f"[INFO] Linhas já processadas: {len(linhas_processadas)}")

    if not linhas_processadas:
        print("[ERRO] Nenhuma linha processada encontrada! Execute o teste primeiro.")
        return

    # Selecionar 5 linhas aleatórias para duplicar
    num_duplicatas = min(5, len(linhas_processadas))
    linhas_para_duplicar = random.sample(linhas_processadas, num_duplicatas)

    print(f"\n[3/4] Criando {num_duplicatas} linhas duplicadas...")

    novas_linhas = []
    for idx, linha in linhas_para_duplicar:
        # Criar cópia da linha
        nova_linha = linha.copy()

        # IMPORTANTE: Manter o mesmo ID (para testar duplicação)
        # Limpar Status Oracle (para aparecer na busca)
        nova_linha[idx_status_oracle] = ""

        # Garantir que Status tem CONCLUÍDO
        nova_linha[idx_status] = "CONCLUÍDO"

        novas_linhas.append(nova_linha)
        print(f"  - Duplicando ID: {nova_linha[idx_id]}")

    # Adicionar linhas duplicadas ao final da planilha
    print(f"\n[4/4] Adicionando {len(novas_linhas)} duplicadas na planilha...")

    range_destino = f"{SHEET_NAME}!A{len(valores) + 1}"

    service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=range_destino,
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": novas_linhas}
    ).execute()

    print("\n" + "="*60)
    print("DUPLICADOS CRIADOS COM SUCESSO!")
    print("="*60)
    print(f"Total de duplicados criados: {len(novas_linhas)}")
    print("\nIDs duplicados:")
    for linha in novas_linhas:
        print(f"  - {linha[idx_id]}")
    print("\n[PRÓXIMO PASSO] Execute o teste_rpa.py para verificar")
    print("se o RPA consegue evitar processar duplicados!")
    print("="*60)

if __name__ == "__main__":
    try:
        criar_duplicados()
    except Exception as e:
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()
