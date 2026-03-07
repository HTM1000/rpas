# -*- coding: utf-8 -*-
"""
Script de Teste - Enviar dados fictícios com horário de Brasília
"""

import os
import sys
from datetime import datetime, timezone, timedelta

# Importar bibliotecas Google
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
except ImportError:
    print("❌ Bibliotecas Google não instaladas!")
    print("Execute: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    sys.exit(1)

# Configurações
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "1fjkU2kSG6A91-lCD1FDcIiZobyBpcB_Vqquo8Meptvg"  # Planilha de teste
SHEET_NAME = "Página1"  # Nome da aba (ajuste se necessário)

# Diretório base
BASE_PATH = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

def authenticate_google():
    """Autentica com Google Sheets"""
    token_path = "token.json"
    creds_path = os.path.join(BASE_PATH, "CredenciaisOracle.json")

    print(f"[AUTH] Procurando token em: {token_path}")
    print(f"[AUTH] Credenciais em: {creds_path}")

    creds = None

    # Carregar token se existir
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            print("[AUTH] ✅ Token carregado")
        except Exception as e:
            print(f"[AUTH] ⚠️ Erro ao carregar token: {e}")
            creds = None

    # Se não há credenciais válidas, fazer login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("[AUTH] 🔄 Renovando token...")
                creds.refresh(Request())
                print("[AUTH] ✅ Token renovado")
            except Exception as e:
                print(f"[AUTH] ❌ Erro ao renovar: {e}")
                creds = None

        if not creds:
            if not os.path.exists(creds_path):
                raise FileNotFoundError(f"❌ Credenciais não encontradas: {creds_path}")

            print("[AUTH] 🌐 Abrindo navegador para autenticação...")
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)

        # Salvar token
        with open(token_path, "w") as token:
            token.write(creds.to_json())
        print("[AUTH] ✅ Token salvo")

    return build("sheets", "v4", credentials=creds)

def obter_nome_aba(service):
    """Obtém o nome da primeira aba da planilha"""
    try:
        result = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        sheets = result.get('sheets', [])
        if sheets:
            nome = sheets[0]['properties']['title']
            print(f"[INFO] Nome da aba detectado: '{nome}'")
            return nome
        return "Página1"
    except Exception as e:
        print(f"[WARN] Erro ao detectar aba: {e}")
        return "Página1"

def enviar_teste():
    """Envia dados de teste com horário de Brasília"""

    print("=" * 70)
    print("🧪 TESTE DE HORÁRIO - BRASÍLIA (UTC-3)")
    print("=" * 70)
    print()

    try:
        # Autenticar
        print("🔐 Autenticando com Google Sheets...")
        service = authenticate_google()
        print("✅ Autenticação bem-sucedida!")
        print()

        # Detectar nome da aba
        sheet_name = obter_nome_aba(service)
        print()

        # Obter horário atual de Brasília (UTC-3)
        print("🕐 Capturando horário de Brasília...")
        brasilia_tz = timezone(timedelta(hours=-3))
        agora_brasilia = datetime.now(brasilia_tz)

        # Formatar como string
        horario_str = agora_brasilia.strftime("%Y-%m-%d %H:%M:%S")
        horario_apenas = agora_brasilia.strftime("%H:%M:%S")
        data_apenas = agora_brasilia.strftime("%Y-%m-%d")

        print(f"   📅 Data: {data_apenas}")
        print(f"   ⏰ Hora: {horario_apenas}")
        print(f"   📊 Completo: {horario_str}")
        print()

        # Preparar dados de teste
        print("📋 Preparando dados de teste...")
        linha_teste = [
            "Teste Automático",              # Coluna A: Descrição
            horario_str,                      # Coluna B: Data/Hora Completa
            data_apenas,                      # Coluna C: Data
            horario_apenas,                   # Coluna D: Hora
            "Brasília (UTC-3)",              # Coluna E: Timezone
            agora_brasilia.strftime("%d/%m/%Y"),  # Coluna F: Data formatada BR
            "✅ Horário corrigido"           # Coluna G: Status
        ]

        # Verificar se há cabeçalhos
        print("🔍 Verificando planilha...")
        try:
            result = service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{sheet_name}!A1:Z1"
            ).execute()

            valores = result.get('values', [])

            if not valores or not valores[0]:
                print("📝 Adicionando cabeçalhos...")
                headers = [
                    "Descrição",
                    "Data/Hora Completa",
                    "Data",
                    "Hora",
                    "Timezone",
                    "Data (BR)",
                    "Status"
                ]

                service.spreadsheets().values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range=f"{sheet_name}!A1:G1",
                    valueInputOption="RAW",
                    body={"values": [headers]}
                ).execute()
                print("✅ Cabeçalhos adicionados")
            else:
                print("✅ Cabeçalhos já existem")
        except Exception as e:
            print(f"⚠️ Não foi possível verificar cabeçalhos: {e}")

        print()

        # Enviar dados
        print("📤 Enviando dados para planilha...")
        result = service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_name}!A:G",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [linha_teste]}
        ).execute()

        linhas_atualizadas = result.get('updates', {}).get('updatedRows', 0)

        print()
        print("=" * 70)
        print("✅ DADOS ENVIADOS COM SUCESSO!")
        print("=" * 70)
        print(f"📊 Linhas adicionadas: {linhas_atualizadas}")
        print(f"⏰ Horário enviado: {horario_str}")
        print()
        print(f"🔗 Acesse a planilha:")
        print(f"   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
        print()
        print("💡 Compare o horário na planilha com o horário do seu sistema")
        print("💡 Eles devem ser iguais (ou diferir por poucos segundos)")
        print("=" * 70)

        return True

    except FileNotFoundError as e:
        print()
        print("❌ ERRO:", e)
        print()
        print("💡 Certifique-se de que o arquivo CredenciaisOracle.json existe")
        return False

    except Exception as e:
        print()
        print("=" * 70)
        print("❌ ERRO AO ENVIAR DADOS")
        print("=" * 70)
        print(f"Erro: {e}")
        print()
        import traceback
        traceback.print_exc()
        print()
        return False

if __name__ == "__main__":
    print()
    print("🕐 TESTE DE HORÁRIO DE BRASÍLIA")
    print()
    print("Este script vai:")
    print("  1. Capturar o horário atual de Brasília (UTC-3)")
    print("  2. Enviar para a planilha de teste")
    print("  3. Você poderá verificar se o horário está correto")
    print()

    input("Pressione ENTER para continuar...")
    print()

    sucesso = enviar_teste()

    print()
    if sucesso:
        print("🎉 Teste concluído com sucesso!")
        print("📊 Verifique a planilha para confirmar o horário")
    else:
        print("❌ Teste falhou")
        print("📖 Verifique os erros acima")

    print()
    input("Pressione ENTER para sair...")
