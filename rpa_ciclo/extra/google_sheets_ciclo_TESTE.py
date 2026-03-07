# -*- coding: utf-8 -*-
"""
Módulo de integração com Google Sheets para RPA Ciclo - VERSÃO TESTE
Registra histórico de execução dos ciclos na PLANILHA DE TESTE
"""

import os
import sys
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Diretório base compatível com .exe
BASE_PATH = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

# Configurações do Google Sheets - PLANILHA DE TESTE
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY"  # <<<< PLANILHA DE TESTE
SHEET_NAME = "Ciclo Automacao"  # Nova aba para logs do ciclo

def authenticate_google():
    """
    Autentica com Google Sheets usando OAuth2.
    Retorna o serviço do Google Sheets API.

    SEGURANÇA: CredenciaisOracle.json está EMBEDDED no executável.
    Apenas token.json é criado externamente (gerado pelo usuário).
    """
    # token.json fica na pasta de execução (criado pelo usuário)
    token_path = os.path.join(os.getcwd(), "token.json")

    # CredenciaisOracle.json está DENTRO do executável (embedded)
    # Quando compilado, BASE_PATH aponta para pasta temporária interna
    creds_path = os.path.join(BASE_PATH, "CredenciaisOracle.json")

    creds = None

    # Carregar credenciais do token se existir
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception as e:
            print(f"Erro ao carregar token: {e}")
            creds = None

    # Se não há credenciais válidas, fazer login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Erro ao renovar token: {e}")
                creds = None

        if not creds:
            if not os.path.exists(creds_path):
                raise FileNotFoundError(f"Arquivo de credenciais não encontrado: {creds_path}")

            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)

        # Salvar credenciais para próxima execução
        with open(token_path, "w") as token:
            token.write(creds.to_json())

    return build("sheets", "v4", credentials=creds)

def criar_aba_se_necessario(service):
    """
    Verifica se a aba 'Ciclo Automacao' existe, se não, cria.
    """
    try:
        # Buscar informações da planilha
        spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        sheets = spreadsheet.get('sheets', [])

        # Verificar se a aba existe
        aba_existe = False
        for sheet in sheets:
            if sheet['properties']['title'] == SHEET_NAME:
                aba_existe = True
                break

        if not aba_existe:
            # Criar nova aba
            request_body = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': SHEET_NAME,
                            'gridProperties': {
                                'rowCount': 1000,
                                'columnCount': 10
                            }
                        }
                    }
                }]
            }

            service.spreadsheets().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body=request_body
            ).execute()

            # Adicionar cabeçalhos
            headers = [
                "Data/Hora Início",
                "Data/Hora Fim",
                "Ciclo #",
                "Status",
                "Etapa Falha",
                "Tempo Execução (min)",
                "Observações",
                "Operador",
                "RPA Oracle",
                "RPA Bancada"
            ]

            service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{SHEET_NAME}!A1:J1",
                valueInputOption="RAW",
                body={"values": [headers]}
            ).execute()

            print(f"✅ Aba '{SHEET_NAME}' criada com sucesso [TESTE]")

        return True

    except Exception as e:
        print(f"❌ Erro ao criar/verificar aba: {e}")
        return False

def registrar_ciclo(
    ciclo_numero,
    status,
    data_inicio,
    data_fim=None,
    etapa_falha="",
    observacoes="",
    operador="Sistema",
    rpa_oracle_status="Pendente",
    rpa_bancada_status="Pendente"
):
    """
    Registra um ciclo de execução no Google Sheets.

    Args:
        ciclo_numero: Número do ciclo
        status: "Sucesso", "Falha", "Em Execução", "Pausado"
        data_inicio: DateTime do início
        data_fim: DateTime do fim (opcional)
        etapa_falha: Nome da etapa que falhou (se houver)
        observacoes: Observações adicionais
        operador: Nome do operador (padrão "Sistema")
        rpa_oracle_status: Status do RPA Oracle ("Sucesso", "Falha", "Pendente")
        rpa_bancada_status: Status do RPA Bancada ("Sucesso", "Falha", "Pendente")

    Returns:
        bool: True se sucesso, False se falhou
    """
    try:
        service = authenticate_google()

        # Criar aba se necessário
        criar_aba_se_necessario(service)

        # Calcular tempo de execução
        tempo_execucao = ""
        if data_fim and data_inicio:
            delta = data_fim - data_inicio
            minutos = delta.total_seconds() / 60
            tempo_execucao = f"{minutos:.2f}"

        # Formatar datas
        inicio_str = data_inicio.strftime("%Y-%m-%d %H:%M:%S") if data_inicio else ""
        fim_str = data_fim.strftime("%Y-%m-%d %H:%M:%S") if data_fim else ""

        # Preparar linha
        linha = [
            inicio_str,
            fim_str,
            str(ciclo_numero),
            status,
            etapa_falha,
            tempo_execucao,
            observacoes,
            operador,
            rpa_oracle_status,
            rpa_bancada_status
        ]

        # Adicionar linha à planilha
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A:J",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [linha]}
        ).execute()

        print(f"✅ Ciclo #{ciclo_numero} registrado no Google Sheets [TESTE]")
        return True

    except Exception as e:
        print(f"❌ Erro ao registrar ciclo no Google Sheets: {e}")
        import traceback
        traceback.print_exc()
        return False

def atualizar_ciclo(ciclo_numero, campo, valor):
    """
    Atualiza um campo específico de um ciclo já registrado.

    Args:
        ciclo_numero: Número do ciclo a atualizar
        campo: Nome do campo ("Status", "Data/Hora Fim", etc.)
        valor: Novo valor

    Returns:
        bool: True se sucesso, False se falhou
    """
    try:
        service = authenticate_google()

        # Mapear campo para índice de coluna
        campos_map = {
            "Data/Hora Início": "A",
            "Data/Hora Fim": "B",
            "Ciclo #": "C",
            "Status": "D",
            "Etapa Falha": "E",
            "Tempo Execução (min)": "F",
            "Observações": "G",
            "Operador": "H",
            "RPA Oracle": "I",
            "RPA Bancada": "J"
        }

        if campo not in campos_map:
            print(f"⚠️ Campo '{campo}' não reconhecido")
            return False

        coluna = campos_map[campo]

        # Buscar linha do ciclo
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!C:C"
        ).execute()

        valores = result.get('values', [])
        linha_numero = None

        for i, linha in enumerate(valores):
            if linha and str(linha[0]) == str(ciclo_numero):
                linha_numero = i + 1
                break

        if not linha_numero:
            print(f"⚠️ Ciclo #{ciclo_numero} não encontrado")
            return False

        # Atualizar célula
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!{coluna}{linha_numero}",
            valueInputOption="RAW",
            body={"values": [[valor]]}
        ).execute()

        print(f"✅ Ciclo #{ciclo_numero} atualizado: {campo} = {valor} [TESTE]")
        return True

    except Exception as e:
        print(f"❌ Erro ao atualizar ciclo: {e}")
        return False

# Testes
if __name__ == "__main__":
    print("Testando módulo Google Sheets Ciclo TESTE...")

    # Testar autenticação
    try:
        service = authenticate_google()
        print("✅ Autenticação bem-sucedida")
    except Exception as e:
        print(f"❌ Falha na autenticação: {e}")
        sys.exit(1)

    # Testar criação de aba
    if criar_aba_se_necessario(service):
        print("✅ Aba verificada/criada")
    else:
        print("❌ Falha ao criar aba")
        sys.exit(1)

    # Testar registro de ciclo
    agora = datetime.now()
    if registrar_ciclo(
        ciclo_numero=9999,
        status="Teste",
        data_inicio=agora,
        data_fim=agora,
        observacoes="Teste de integração - VERSÃO TESTE"
    ):
        print("✅ Registro de ciclo bem-sucedido")
    else:
        print("❌ Falha no registro")

    print("\n✅ Todos os testes concluídos!")
