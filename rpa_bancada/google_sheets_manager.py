import json
import sys
import os
from typing import List, Optional
import pandas as pd
from googleapiclient.discovery import build

# Escopo necessário para ler e escrever no Google Sheets
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Configurações da planilha
SPREADSHEET_ID = '1UgJWxmnYzv-FVTT4rrrVEx3J_MNXZsctwrPSTyyylPQ'  # BANCADA (Produção) - COMENTADO PARA TESTE
# SPREADSHEET_ID = '1KMS-1_FY6-cU26ZlaFu5jciSHEWlmluHo-QOFbB1LFE'  # BANCADA (TESTE) - USAR ESTE PARA TESTES
SHEET_NAME = None  # Será detectado automaticamente
RANGE_NAME = 'A:I'  # Colunas A até I (Codigo, Data + 7 colunas principais - SEM REV)

# Diretório base compatível com .exe (arquivos embutidos)
base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

# Diretório para arquivos de dados (onde o .exe está) - IGUAL RPA ORACLE
data_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))

# Arquivos de credenciais e token - IGUAL RPA ORACLE
OAUTH_CREDENTIALS_FILE = os.path.join(base_path, 'CredenciaisOracle.json')
TOKEN_FILE = os.path.join(data_path, 'token.json')

# ==========================
# Autenticação
# ==========================
def get_sheets_service():
    """
    Autentica com Google Sheets usando OAuth2 com token salvo (JSON)
    """
    if os.path.exists(OAUTH_CREDENTIALS_FILE):
        print("[Auth] Autenticando com Google Sheets (OAuth2)...")
        return get_sheets_service_oauth2()

    # Se não houver credenciais
    raise FileNotFoundError(f"Arquivo de credenciais não encontrado: {OAUTH_CREDENTIALS_FILE}")

def get_sheets_service_oauth2():
    """Autenticação OAuth2 - IGUAL RPA ORACLE"""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("🔐 Abrindo navegador para autenticação Google Sheets...")
            flow = InstalledAppFlow.from_client_secrets_file(OAUTH_CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            print("✅ Autenticação concluída!")

        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    return build('sheets', 'v4', credentials=creds)

# ==========================
# Helpers Sheets
# ==========================
def get_first_sheet_name(service):
    """
    Obtém o nome da primeira aba da planilha
    """
    try:
        result = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        sheets = result.get('sheets', [])
        if sheets:
            return sheets[0]['properties']['title']
        return 'Sheet1'  # fallback
    except Exception:
        return 'Sheet1'  # fallback

def filtrar_colunas_principais(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filtra e normaliza as colunas principais do DataFrame.
    Adiciona Codigo (sequencial) e Data (timestamp) no início.
    Colunas finais: Codigo, Data, ORG., SUB., ENDEREÇO, ITEM, DESCRIÇÃO ITEM, UDM PRINCIPAL, EM ESTOQUE (SEM REV)
    """
    # Mapeamento de possíveis variações nos nomes das colunas
    column_mapping = {
        'org.': 'ORG.',
        'sub.': 'SUB.',
        'endereço': 'ENDEREÇO',
        'item': 'ITEM',
        'descrição item': 'DESCRIÇÃO ITEM',
        'udm principal': 'UDM PRINCIPAL',
        'em estoque': 'EM ESTOQUE',
        'org': 'ORG.',
        'organization': 'ORG.',
        'sub': 'SUB.',
        'subinventory': 'SUB.',
        'endereco': 'ENDEREÇO',
        'locator': 'ENDEREÇO',
        'item_code': 'ITEM',
        'codigo_item': 'ITEM',
        'descricao': 'DESCRIÇÃO ITEM',
        'descrição': 'DESCRIÇÃO ITEM',
        'descricao item': 'DESCRIÇÃO ITEM',
        'descricao do item': 'DESCRIÇÃO ITEM',
        'description': 'DESCRIÇÃO ITEM',
        'udm': 'UDM PRINCIPAL',
        'unit': 'UDM PRINCIPAL',
        'uom': 'UDM PRINCIPAL',
        'estoque': 'EM ESTOQUE',
        'quantity': 'EM ESTOQUE',
        'qty': 'EM ESTOQUE',
        'quantidade': 'EM ESTOQUE'
    }

    # Normalizar nomes das colunas (minúsculo, sem espaços extras)
    df_clean = df.copy()
    df_clean.columns = [str(col).strip().lower() for col in df_clean.columns]

    # Mapear colunas para os nomes padrão
    new_columns = {}
    for col in df_clean.columns:
        if col in column_mapping:
            new_columns[col] = column_mapping[col]

    if new_columns:
        df_clean = df_clean.rename(columns=new_columns)

    # Definir as 7 colunas principais na ordem correta (SEM REV)
    required_columns = ['ORG.', 'SUB.', 'ENDEREÇO', 'ITEM', 'DESCRIÇÃO ITEM', 'UDM PRINCIPAL', 'EM ESTOQUE']

    # Adicionar colunas faltantes com valores vazios
    for col in required_columns:
        if col not in df_clean.columns:
            df_clean[col] = ''
            print(f"Coluna '{col}' não encontrada, adicionando com valores vazios")

    # Selecionar apenas as colunas principais
    df_filtered = df_clean[required_columns]

    # Adicionar coluna Codigo (sequencial) no início
    df_filtered.insert(0, 'Codigo', range(1, len(df_filtered) + 1))

    # Adicionar coluna Data (timestamp atual) logo após Codigo
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    df_filtered.insert(1, 'Data', timestamp)

    return df_filtered

def enviar_para_google_sheets(df: pd.DataFrame) -> bool:
    """
    Envia DataFrame para Google Sheets.
    Assume que o DataFrame JÁ VEM com as colunas corretas mapeadas pelo main.py
    Adiciona apenas Codigo (sequencial) e Data (horário Brasília UTC-3) no início.
    Retorna True se bem-sucedido, False caso contrário.
    """
    try:
        print(f"[Sheets] Recebido: {df.shape[0]} linhas x {df.shape[1]} colunas")

        if df.empty:
            print("[Sheets] ❌ DataFrame vazio")
            return False

        # Criar cópia para não modificar o original
        df_envio = df.copy()

        # Adicionar coluna Codigo (sequencial) no início
        df_envio.insert(0, 'Codigo', range(1, len(df_envio) + 1))

        # Adicionar coluna Data (timestamp atual) logo após Codigo
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        df_envio.insert(1, 'Data', timestamp)

        print(f"[Sheets] Preparado: {df_envio.shape[0]} linhas x {df_envio.shape[1]} colunas")
        print(f"[Sheets] Timestamp: {timestamp}")

        # Obter serviço do Google Sheets
        service = get_sheets_service()
        print("[Sheets] ✅ Serviço obtido")

        # Detectar nome da primeira aba
        sheet_name = get_first_sheet_name(service)
        print(f"[Sheets] Usando aba: {sheet_name}")

        # Preparar dados para envio (incluir cabeçalho)
        values = [df_envio.columns.tolist()] + df_envio.values.tolist()

        # Calcular range dinâmico baseado no número de colunas
        # A até a última coluna (ex: se 10 colunas, A:J)
        ultima_coluna = chr(64 + len(df_envio.columns))  # A=65, então 64+1=A
        range_name = f'{sheet_name}!A:{ultima_coluna}'
        print(f"[Sheets] Range: {range_name} ({len(values):,} linhas x {len(df_envio.columns)} colunas)")

        # Limpar planilha e enviar dados
        body = {'values': values}

        service.spreadsheets().values().clear(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name
        ).execute()

        result = service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()

        rows_updated = result.get('updatedRows', 0)
        print(f"[Sheets] ✅ Enviado: {rows_updated:,} linhas")
        return True

    except FileNotFoundError as e:
        print(f"[Sheets] ❌ Arquivo não encontrado: {OAUTH_CREDENTIALS_FILE}")
        print(f"[Sheets] (Dados salvos no Excel local)")
        return False
    except Exception as e:
        print(f"[Sheets] ❌ Erro ao enviar: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def testar_conexao() -> bool:
    """
    Testa a conexão com Google Sheets
    """
    try:
        service = get_sheets_service()
        result = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        title = result.get('properties', {}).get('title', 'Sem título')
        print(f"Conexão OK com planilha: {title}")
        return True
    except Exception as e:
        print(f"Erro na conexão: {e}")
        return False

if __name__ == "__main__":
    print("Testando conexão com Google Sheets...")
    sucesso = testar_conexao()

    if sucesso:
        print("\nTestando envio de dados de exemplo...")
        df_teste = pd.DataFrame({
            'ORG.': ['ORG001', 'ORG002'],
            'SUB.': ['SUB001', 'SUB002'],
            'ENDEREÇO': ['END001', 'END002'],
            'ITEM': ['ITEM001', 'ITEM002'],
            'DESCRIÇÃO ITEM': ['Desc 1', 'Desc 2'],
            'UDM PRINCIPAL': ['PC', 'UN'],
            'EM ESTOQUE': [100, 250]
        })

        if enviar_para_google_sheets(df_teste):
            print("Teste de envio concluído com sucesso!")
        else:
            print("Teste de envio falhou")
