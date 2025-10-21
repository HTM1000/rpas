# -*- coding: utf-8 -*-
"""
Script de diagnóstico para verificar as colunas do Google Sheets
"""
import os
import sys
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Configurações
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk"
SHEET_NAME = "Separação"

# Diretório para arquivos de dados
data_path = os.path.dirname(os.path.abspath(__file__))

def authenticate_google():
    token_path = os.path.join(data_path, "token.json")
    creds_path = os.path.join(data_path, "CredenciaisOracle.json")
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

def diagnosticar_planilha():
    print("=" * 80)
    print("DIAGNÓSTICO DA PLANILHA - GOOGLE SHEETS")
    print("=" * 80)

    try:
        service = authenticate_google()
        print("\n✅ Autenticação realizada com sucesso!\n")

        # Buscar TODAS as colunas (A até ZZ para garantir)
        print(f"📊 Buscando dados da planilha: {SHEET_NAME}")
        print(f"🔗 ID da planilha: {SPREADSHEET_ID}\n")

        res = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A1:ZZ"  # Busca até a coluna ZZ
        ).execute()

        valores = res.get("values", [])

        if not valores:
            print("❌ ERRO: Nenhum dado encontrado na planilha!")
            return

        headers = valores[0]
        dados = valores[1:]

        print("=" * 80)
        print("📋 COLUNAS ENCONTRADAS NA PLANILHA")
        print("=" * 80)

        # Mostrar todas as colunas com índice
        for idx, coluna in enumerate(headers):
            letra_coluna = chr(65 + idx) if idx < 26 else f"{chr(65 + idx//26 - 1)}{chr(65 + idx%26)}"
            print(f"{idx:3d} | Coluna {letra_coluna:3s} | '{coluna}'")

        print("\n" + "=" * 80)
        print(f"📊 TOTAL DE COLUNAS: {len(headers)}")
        print(f"📊 TOTAL DE LINHAS DE DADOS: {len(dados)}")
        print("=" * 80)

        # Verificar se a coluna "ID" existe
        print("\n🔍 VERIFICANDO COLUNA 'ID':")
        if "ID" in headers:
            idx_id = headers.index("ID")
            letra_coluna = chr(65 + idx_id) if idx_id < 26 else f"{chr(65 + idx_id//26 - 1)}{chr(65 + idx%26)}"
            print(f"   ✅ Coluna 'ID' encontrada no índice {idx_id} (Coluna {letra_coluna})")
        else:
            print("   ❌ Coluna 'ID' NÃO ENCONTRADA!")
            print("\n   💡 SUGESTÕES:")
            print("      - Verifique se o nome da coluna está exatamente como 'ID' (maiúsculas)")
            print("      - Verifique se não há espaços extras antes ou depois")
            print("      - Possíveis variações encontradas:")
            for coluna in headers:
                if 'id' in coluna.lower():
                    print(f"         • '{coluna}'")

        # Verificar outras colunas importantes
        print("\n🔍 VERIFICANDO OUTRAS COLUNAS IMPORTANTES:")
        colunas_importantes = [
            "Item", "Sub.Origem", "End. Origem", "Sub. Destino",
            "End. Destino", "Quantidade", "Cód Referencia", "Status", "Status Oracle"
        ]

        for coluna in colunas_importantes:
            if coluna in headers:
                idx = headers.index(coluna)
                print(f"   ✅ '{coluna}' encontrada no índice {idx}")
            else:
                print(f"   ❌ '{coluna}' NÃO encontrada")
                # Buscar variações
                for h in headers:
                    if coluna.lower().replace(" ", "").replace(".", "") in h.lower().replace(" ", "").replace(".", ""):
                        print(f"      💡 Possível variação: '{h}' (índice {headers.index(h)})")

        # Mostrar exemplo de 3 primeiras linhas
        print("\n" + "=" * 80)
        print("📄 EXEMPLO DAS 3 PRIMEIRAS LINHAS (valores):")
        print("=" * 80)

        for i, linha in enumerate(dados[:3], start=2):
            print(f"\nLinha {i}:")
            # Garantir que a linha tem o mesmo tamanho que headers
            if len(linha) < len(headers):
                linha += [''] * (len(headers) - len(linha))

            for idx, valor in enumerate(linha):
                if idx < len(headers):
                    print(f"   {headers[idx]:20s} = '{valor}'")

        print("\n" + "=" * 80)
        print("✅ DIAGNÓSTICO CONCLUÍDO!")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    diagnosticar_planilha()
    input("\n\nPressione ENTER para fechar...")
