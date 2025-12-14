# -*- coding: utf-8 -*-
"""
Módulo de integração com Google Sheets para RPA Inventário
Busca dados das planilhas de inventário (primeira e segunda contagem)
"""

import os
import sys
import time
import random
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pathlib import Path

# Diretório base compatível com .exe
BASE_DIR = Path(__file__).parent.resolve() if not getattr(sys, 'frozen', False) else Path(sys.executable).parent
BASE_PATH = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

# Configurações do Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# IDs das planilhas - BC1
SPREADSHEET_ID_BC1_PRIMEIRA = "1c3r5-9mIT8Gg_EyESrcoZ4-F-lNDbxLBGNW1z_6G3QM"  # BC1 Primeira contagem
SPREADSHEET_ID_BC1_SEGUNDA = "1Ou55wm9ynuwEV_ZDIVz7XNSV5JMEC7ZsNscn8FHhae0"  # BC1 Segunda contagem

# IDs das planilhas - BC2
SPREADSHEET_ID_BC2_PRIMEIRA = "1iZYNC1eMmpn8Evb6mAxzF1qZwug7xeO6LyOs3sWBbL4"  # BC2 Primeira contagem
SPREADSHEET_ID_BC2_SEGUNDA = "1rg9ExuM0auBC_HROBLu1wCwxz5X6hcUqgG10YdgcXk4"  # BC2 Segunda contagem

# ─── PROTEÇÃO CONTRA RATE LIMIT ────────────────────────────────────────────
def delay_randomico(min_seg=0.5, max_seg=2.0):
    """Adiciona delay randômico entre requests para evitar rate-limit"""
    delay = random.uniform(min_seg, max_seg)
    time.sleep(delay)

def retry_com_backoff(funcao, max_tentativas=5):
    """
    Executa função com retry e exponential backoff em caso de rate-limit

    Args:
        funcao: Função a ser executada
        max_tentativas: Número máximo de tentativas

    Returns:
        Resultado da função
    """
    for tentativa in range(max_tentativas):
        try:
            # Delay randômico antes de cada request (exceto primeira)
            if tentativa > 0:
                delay_randomico(1.0, 3.0)

            return funcao()

        except HttpError as e:
            # Se for rate limit (429) ou quota exceeded (403)
            if e.resp.status in [429, 403, 500, 503]:
                if tentativa < max_tentativas - 1:
                    # Exponential backoff: 2^tentativa segundos + jitter
                    wait_time = (2 ** tentativa) + random.uniform(0, 1)
                    print(f"⚠️ Rate limit detectado. Aguardando {wait_time:.1f}s (tentativa {tentativa + 1}/{max_tentativas})...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Falhou após {max_tentativas} tentativas")
                    raise
            else:
                # Outro erro HTTP, re-lançar
                raise
        except Exception as e:
            # Outro erro, re-lançar
            raise

def authenticate_google():
    """
    Autentica com Google Sheets usando OAuth2.
    Retorna o serviço do Google Sheets API.

    SEGURANÇA: CredenciaisOracle.json está EMBEDDED no executável.
    Apenas token.json é criado externamente (gerado pelo usuário).
    """
    # token.json fica na pasta de execução (criado pelo usuário)
    token_path = BASE_DIR / "token.json"

    # CredenciaisOracle.json está DENTRO do executável (embedded)
    creds_path = os.path.join(BASE_PATH, "CredenciaisOracle.json")

    print(f"[Auth] BASE_DIR: {BASE_DIR}")
    print(f"[Auth] BASE_PATH: {BASE_PATH}")
    print(f"[Auth] Token path: {token_path}")
    print(f"[Auth] Credentials path: {creds_path}")
    print(f"[Auth] Token exists: {token_path.exists()}")
    print(f"[Auth] Credentials exists: {os.path.exists(creds_path)}")

    creds = None

    # Carregar credenciais do token se existir
    if token_path.exists():
        try:
            print("[Auth] Carregando token.json existente...")
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
            print(f"[Auth] Token carregado: expired={creds.expired}, valid={creds.valid}")
        except Exception as e:
            print(f"[ERRO] Erro ao carregar token: {e}")
            creds = None

    # Se não há credenciais válidas, fazer login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("[Auth] Renovando token expirado...")
                creds.refresh(Request())
                print("[Auth] Token renovado com sucesso!")
            except Exception as e:
                print(f"[ERRO] Erro ao renovar token: {e}")
                creds = None

        if not creds:
            if not os.path.exists(creds_path):
                raise FileNotFoundError(f"Arquivo de credenciais não encontrado: {creds_path}")

            print("[Auth] Iniciando fluxo OAuth via navegador...")
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
            print("[Auth] Autenticação concluída!")

        # Salvar credenciais para próxima execução
        try:
            with open(token_path, "w") as token:
                token.write(creds.to_json())
            print(f"[Auth] Token salvo em: {token_path}")
        except Exception as e:
            print(f"[ERRO] Erro ao salvar token: {e}")

    print("[Auth] ✅ Autenticação bem-sucedida!")
    return build("sheets", "v4", credentials=creds)

def buscar_dados_inventario(nome_inventario: str, tipo_contagem: str = "primeira", tipo_planilha: str = "bc1"):
    """
    Busca dados de um inventário específico na planilha do Google Sheets
    Retorna apenas colunas A:J (ID até Físico)

    Args:
        nome_inventario: Nome do inventário a buscar
        tipo_contagem: "primeira" ou "segunda" contagem
        tipo_planilha: "bc1" ou "bc2"

    Returns:
        Lista de dicionários com os dados do inventário
        Colunas: ID, Inventário, Etiqueta, Nova Etiqueta, Item, Descrição,
                 Sub Inventário, Endereço, UDM, Físico
    """
    try:
        service = authenticate_google()

        # Selecionar planilha baseado no tipo de contagem e tipo de planilha
        tipo_planilha = tipo_planilha.lower()
        tipo_contagem = tipo_contagem.lower()

        if tipo_planilha == "bc1":
            if tipo_contagem == "primeira":
                spreadsheet_id = SPREADSHEET_ID_BC1_PRIMEIRA
            else:
                spreadsheet_id = SPREADSHEET_ID_BC1_SEGUNDA
        else:  # bc2 (padrão)
            if tipo_contagem == "primeira":
                spreadsheet_id = SPREADSHEET_ID_BC2_PRIMEIRA
            else:
                spreadsheet_id = SPREADSHEET_ID_BC2_SEGUNDA

        # Buscar todas as abas da planilha
        spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = spreadsheet.get('sheets', [])

        if not sheets:
            print(f"⚠️ Nenhuma aba encontrada na planilha {tipo_contagem}")
            return []

        # Usar a primeira aba (ou pode buscar por nome específico)
        sheet_name = sheets[0]['properties']['title']

        # Buscar dados colunas A:N (incluindo STATUS ORACLE na coluna N)
        range_name = f"{sheet_name}!A:N"
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()

        values = result.get('values', [])

        if not values:
            print(f"⚠️ Nenhum dado encontrado na planilha {tipo_contagem}")
            return []

        # Primeira linha é o cabeçalho
        headers = values[0]
        print(f"📋 Colunas encontradas ({len(headers)} colunas):")
        for idx, header in enumerate(headers):
            print(f"   Coluna {chr(65+idx)} (índice {idx}): '{header}'")

        dados = []

        # Processar cada linha
        for row_index, row in enumerate(values[1:], start=2):  # start=2 pois linha 1 é header
            # Criar dicionário para cada linha
            item = {'_linha': row_index}  # Guardar número da linha para referência

            for i, header in enumerate(headers):
                if i < len(row):
                    item[header] = row[i].strip() if isinstance(row[i], str) else row[i]
                else:
                    item[header] = ""

            # ═══════════════════════════════════════════════════════════════
            # FILTRO 1: INVENTÁRIO - Comparação EXATA
            # ═══════════════════════════════════════════════════════════════
            inventario_coluna = item.get('Inventário', '') or item.get('Inventario', '')
            inventario_str = str(inventario_coluna).strip()

            # Comparação EXATA (case-insensitive)
            if inventario_str.lower() != nome_inventario.lower():
                # Inventário diferente - PULAR
                continue

            # ═══════════════════════════════════════════════════════════════
            # FILTRO 2: Status RPA - NÃO PROCESSAR se já está processado/concluído
            # ═══════════════════════════════════════════════════════════════
            status_rpa = (
                item.get('Status RPA', '') or
                item.get('STATUS RPA', '') or
                item.get('status rpa', '') or
                item.get('Status_RPA', '') or
                item.get('STATUS_RPA', '')
            )

            # Converter para string e limpar
            status_str = str(status_rpa).strip().upper() if status_rpa else ''

            # PULAR se já tem qualquer status (PROCESSANDO, CONCLUIDO, etc)
            # MAS PROCESSAR se for status de reprocessamento (Interrompido, Login Expirado, Erro)
            if status_str and status_str != 'NONE':
                # Tem status - verificar se é algo que devemos pular

                # REPROCESSAR: Status que indicam que o item deve ser refeito
                if 'INTERROMPIDO' in status_str or 'REPROCESSAR' in status_str:
                    print(f"   [✅ REPROCESSAR] Item ID {item.get('ID')} (linha {row_index}) - Status: '{status_rpa}'")
                    # NÃO pular - deixar processar
                elif 'LOGIN ORACLE EXPIRADO' in status_str or 'LOGIN EXPIRADO' in status_str:
                    print(f"   [✅ REPROCESSAR] Item ID {item.get('ID')} (linha {row_index}) - Status: '{status_rpa}'")
                    # NÃO pular - deixar processar
                elif 'ERRO' in status_str and 'REPROCESSAR' in status_str:
                    print(f"   [✅ REPROCESSAR] Item ID {item.get('ID')} (linha {row_index}) - Status: '{status_rpa}'")
                    # NÃO pular - deixar processar

                # PULAR: Status que indicam que NÃO deve processar
                elif 'PROCESSANDO' in status_str:
                    print(f"   [SKIP] Item ID {item.get('ID')} (linha {row_index}) - Em processamento: '{status_rpa}'")
                    continue
                elif 'CONCLUIDO' in status_str or 'CONCLUÍDO' in status_str:
                    print(f"   [SKIP] Item ID {item.get('ID')} (linha {row_index}) - Já processado: '{status_rpa}'")
                    continue
                else:
                    # Qualquer outro status não vazio - pular por segurança
                    print(f"   [SKIP] Item ID {item.get('ID')} (linha {row_index}) - Status não vazio: '{status_rpa}'")
                    continue

            # ═══════════════════════════════════════════════════════════════
            # FILTRO 3: Físico/Quantidade - Deve estar preenchido
            # ═══════════════════════════════════════════════════════════════
            fisico = item.get('Físico', '') or item.get('Fisico', '')
            fisico_preenchido = fisico and str(fisico).strip() != ''

            if not fisico_preenchido:
                print(f"   [SKIP] Item ID {item.get('ID')} (linha {row_index}) - Físico vazio")
                continue

            # ═══════════════════════════════════════════════════════════════
            # FILTRO 4: Etiqueta - Deve ter Etiqueta ou Nova Etiqueta
            # ═══════════════════════════════════════════════════════════════
            if not (item.get('Etiqueta') or item.get('Nova Etiqueta')):
                print(f"   [SKIP] Item ID {item.get('ID')} (linha {row_index}) - Sem etiqueta")
                continue

            # ═══════════════════════════════════════════════════════════════
            # ✅ PASSOU EM TODOS OS FILTROS - Adicionar à lista
            # ═══════════════════════════════════════════════════════════════
            print(f"   [✅ OK] Item ID {item.get('ID')} (linha {row_index}) - Inventário: '{inventario_str}' - Status: VAZIO - Físico: '{fisico}'")
            dados.append(item)

        print(f"✅ {len(dados)} itens encontrados para inventário '{nome_inventario}'")

        # Debug: Mostrar primeiro item como exemplo
        if dados:
            print(f"📄 Exemplo do primeiro item:")
            primeiro = dados[0]
            print(f"   - Etiqueta: {primeiro.get('Etiqueta', 'N/A')}")
            print(f"   - Nova Etiqueta: {primeiro.get('Nova Etiqueta', 'N/A')}")
            print(f"   - Físico: {primeiro.get('Físico', 'N/A')}")

        return dados

    except Exception as e:
        print(f"❌ Erro ao buscar dados do inventário: {e}")
        import traceback
        traceback.print_exc()
        return []

def listar_abas(tipo_contagem: str = "primeira"):
    """
    Lista todas as abas disponíveis em uma planilha

    Args:
        tipo_contagem: "primeira" ou "segunda" contagem

    Returns:
        Lista com nomes das abas
    """
    try:
        service = authenticate_google()

        # Selecionar planilha baseado no tipo de contagem
        if tipo_contagem.lower() == "primeira":
            spreadsheet_id = SPREADSHEET_ID_PRIMEIRA
        else:
            spreadsheet_id = SPREADSHEET_ID_SEGUNDA

        spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = spreadsheet.get('sheets', [])

        abas = [sheet['properties']['title'] for sheet in sheets]
        return abas

    except Exception as e:
        print(f"❌ Erro ao listar abas: {e}")
        return []

def buscar_todos_dados(tipo_contagem: str = "primeira", aba_nome: str = None):
    """
    Busca todos os dados de uma aba específica

    Args:
        tipo_contagem: "primeira" ou "segunda" contagem
        aba_nome: Nome da aba (se None, usa a primeira aba)

    Returns:
        Lista de dicionários com todos os dados
    """
    try:
        service = authenticate_google()

        # Selecionar planilha baseado no tipo de contagem
        if tipo_contagem.lower() == "primeira":
            spreadsheet_id = SPREADSHEET_ID_PRIMEIRA
        else:
            spreadsheet_id = SPREADSHEET_ID_SEGUNDA

        # Se não especificou aba, buscar a primeira
        if not aba_nome:
            spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            sheets = spreadsheet.get('sheets', [])
            if sheets:
                aba_nome = sheets[0]['properties']['title']
            else:
                print("⚠️ Nenhuma aba encontrada")
                return []

        # Buscar dados
        range_name = f"{aba_nome}!A:Z"
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()

        values = result.get('values', [])

        if not values:
            print(f"⚠️ Nenhum dado encontrado na aba '{aba_nome}'")
            return []

        # Primeira linha é o cabeçalho
        headers = values[0]
        dados = []

        # Processar cada linha
        for row in values[1:]:
            item = {}
            for i, header in enumerate(headers):
                if i < len(row):
                    item[header] = row[i]
                else:
                    item[header] = ""
            dados.append(item)

        print(f"✅ {len(dados)} itens encontrados na aba '{aba_nome}'")
        return dados

    except Exception as e:
        print(f"❌ Erro ao buscar dados: {e}")
        import traceback
        traceback.print_exc()
        return []

def atualizar_status_rpa(item_id: str, status: str, tipo_contagem: str = "primeira", tipo_planilha: str = "bc1", robo_id: str = ""):
    """
    Atualiza o status na coluna N (Status RPA) da planilha
    COM PROTEÇÃO CONTRA RATE-LIMIT (retry + exponential backoff)

    Args:
        item_id: ID do item (coluna A)
        status: Status a ser escrito (ex: "PROCESSANDO...", "PROCESSO CONCLUIDO")
        tipo_contagem: "primeira" ou "segunda" contagem
        tipo_planilha: "bc1" ou "bc2"
        robo_id: ID do robô que processou

    Returns:
        True se atualizado com sucesso, False caso contrário
    """
    def _atualizar():
        """Função interna para ser executada com retry"""
        # Delay randômico ANTES do request (proteção rate-limit)
        delay_randomico(0.3, 1.0)

        print(f"[DEBUG] Atualizando Status RPA:")
        print(f"   - Item ID: '{item_id}' (tipo: {type(item_id)})")
        print(f"   - Status: '{status}'")
        print(f"   - Tipo Contagem: '{tipo_contagem}'")
        print(f"   - Tipo Planilha: '{tipo_planilha}'")
        print(f"   - Robô ID: '{robo_id}'")

        service = authenticate_google()

        # Selecionar planilha baseado no tipo de contagem e tipo de planilha
        tipo_planilha_lower = tipo_planilha.lower()
        tipo_contagem_lower = tipo_contagem.lower()

        if tipo_planilha_lower == "bc1":
            if tipo_contagem_lower == "primeira":
                spreadsheet_id = SPREADSHEET_ID_BC1_PRIMEIRA
            else:
                spreadsheet_id = SPREADSHEET_ID_BC1_SEGUNDA
        else:  # bc2
            if tipo_contagem_lower == "primeira":
                spreadsheet_id = SPREADSHEET_ID_BC2_PRIMEIRA
            else:
                spreadsheet_id = SPREADSHEET_ID_BC2_SEGUNDA

        print(f"   - Spreadsheet ID: {spreadsheet_id}")

        # Buscar todas as abas da planilha
        spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = spreadsheet.get('sheets', [])

        if not sheets:
            print(f"❌ Nenhuma aba encontrada na planilha {tipo_contagem}")
            return False

        # Usar a primeira aba
        sheet_name = sheets[0]['properties']['title']
        print(f"   - Aba: '{sheet_name}'")

        # Buscar todas as linhas da coluna A para encontrar o ID
        range_name = f"{sheet_name}!A:A"
        print(f"   - Buscando IDs em: {range_name}")

        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()

        values = result.get('values', [])
        print(f"   - Total de linhas na coluna A: {len(values)}")

        # Mostrar primeiros 5 IDs para debug
        print(f"   - Primeiros IDs encontrados:")
        for idx, row in enumerate(values[:5], start=1):
            if row:
                print(f"      Linha {idx}: '{row[0]}' (tipo: {type(row[0])})")
            else:
                print(f"      Linha {idx}: [vazio]")

        # Encontrar a linha com o ID (começando da linha 2, pois linha 1 é header)
        linha_encontrada = None
        item_id_str = str(item_id).strip()

        print(f"   - Procurando por ID: '{item_id_str}'")

        for i, row in enumerate(values[1:], start=2):  # start=2 porque linha 1 é header
            if row:
                id_da_linha = str(row[0]).strip()
                if id_da_linha == item_id_str:
                    linha_encontrada = i
                    print(f"   ✅ ID encontrado na linha {i}")
                    break

        if not linha_encontrada:
            print(f"❌ ID '{item_id_str}' não encontrado na planilha")
            print(f"   - IDs disponíveis (primeiras 10 linhas após header):")
            for i, row in enumerate(values[1:11], start=2):
                if row:
                    print(f"      Linha {i}: '{row[0]}'")
            return False

        # Atualizar coluna N (Status RPA) na linha encontrada
        # Coluna N é a 14ª coluna (A=1, B=2, ..., N=14)
        range_update = f"{sheet_name}!N{linha_encontrada}"

        # Se robo_id foi fornecido, adicionar ao status
        if robo_id:
            status_completo = f"{status} [{robo_id}]"
        else:
            status_completo = status

        print(f"   - Range para atualizar: {range_update}")
        print(f"   - Status completo: '{status_completo}'")

        body = {
            'values': [[status_completo]]
        }

        print(f"   - Iniciando UPDATE na planilha...")

        try:
            result = service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_update,
                valueInputOption='RAW',
                body=body
            ).execute()

            print(f"   - Resposta do Google Sheets: {result}")
            print(f"✅ Status RPA atualizado: ID {item_id} → '{status_completo}' (linha {linha_encontrada})")
            return True

        except Exception as e:
            print(f"❌ ERRO ao executar UPDATE:")
            print(f"   - Tipo do erro: {type(e).__name__}")
            print(f"   - Mensagem: {str(e)}")
            import traceback
            print(f"   - Traceback completo:")
            traceback.print_exc()
            raise  # Re-lançar para o retry_com_backoff tentar novamente

    # Executar com retry e exponential backoff
    try:
        return retry_com_backoff(_atualizar)
    except Exception as e:
        print(f"❌ Erro ao atualizar status após múltiplas tentativas: {e}")
        import traceback
        traceback.print_exc()
        return False

# Alias para compatibilidade com código antigo
atualizar_status_oracle = atualizar_status_rpa

if __name__ == "__main__":
    # Teste
    print("Testando conexão com Google Sheets...")
    print("\n=== Primeira Contagem ===")
    abas_primeira = listar_abas("primeira")
    print(f"Abas disponíveis: {abas_primeira}")

    print("\n=== Segunda Contagem ===")
    abas_segunda = listar_abas("segunda")
    print(f"Abas disponíveis: {abas_segunda}")
