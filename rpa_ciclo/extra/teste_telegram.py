"""
Script de teste para verificar notificações Telegram
Busca dados da planilha de teste e envia notificação
"""

import json
import sys
import os

# Adicionar path do módulo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from telegram_notifier import inicializar_telegram

# Importar Google Sheets
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    import pickle
except ImportError as e:
    print(f"❌ Erro ao importar bibliotecas Google: {e}")
    print("Execute: pip install google-auth google-auth-oauthlib google-api-python-client")
    sys.exit(1)

# Configurações da planilha de teste
SPREADSHEET_ID_TESTE = "147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY"
SHEET_NAME_TESTE = "Página1"  # Ajuste se necessário
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def autenticar_google():
    """Autentica com Google Sheets"""
    creds = None

    # Token salvo
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # Se não tem credenciais válidas, faz login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('CredenciaisOracle.json'):
                print("❌ Arquivo CredenciaisOracle.json não encontrado!")
                print("Certifique-se de ter o arquivo de credenciais do Google.")
                sys.exit(1)

            flow = InstalledAppFlow.from_client_secrets_file(
                'CredenciaisOracle.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Salvar credenciais
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds

def buscar_dados_teste():
    """Busca dados da planilha de teste"""
    print("🔍 Conectando ao Google Sheets...")

    try:
        creds = autenticar_google()
        service = build('sheets', 'v4', credentials=creds)

        print(f"📊 Buscando dados da planilha: {SPREADSHEET_ID_TESTE}")

        # Buscar dados
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID_TESTE,
            range=f"{SHEET_NAME_TESTE}!A1:Z100"  # Buscar até coluna Z, 100 linhas
        ).execute()

        values = result.get('values', [])

        if not values:
            print("⚠️ Planilha vazia!")
            return None

        print(f"✅ Encontradas {len(values)} linhas")

        # Exibir cabeçalhos
        if len(values) > 0:
            print(f"\n📋 Cabeçalhos: {values[0]}")

        # Exibir primeira linha de dados
        if len(values) > 1:
            print(f"📝 Primeira linha de dados: {values[1]}")

        return values

    except Exception as e:
        print(f"❌ Erro ao buscar planilha: {e}")
        import traceback
        traceback.print_exc()
        return None

def testar_telegram():
    """Testa envio de mensagem Telegram"""
    print("=" * 60)
    print("TESTE DE NOTIFICACOES TELEGRAM")
    print("=" * 60)

    # Carregar configuração
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            telegram_config = config.get("telegram", {})

        print(f"\nConfiguracao Telegram:")
        print(f"   Bot Token: {'OK Configurado' if telegram_config.get('bot_token') else 'NAO configurado'}")
        print(f"   Chat ID: {'OK Configurado' if telegram_config.get('chat_id') else 'NAO configurado'}")
        print(f"   Habilitado: {telegram_config.get('habilitado', False)}")

        if not telegram_config.get('bot_token') or not telegram_config.get('chat_id'):
            print("\n⚠️ ATENÇÃO: Configure bot_token e chat_id no config.json!")
            print("Veja README_TELEGRAM.md para instruções.")
            return

    except Exception as e:
        print(f"❌ Erro ao carregar config.json: {e}")
        return

    # Inicializar Telegram
    print("\n🚀 Inicializando Telegram...")
    notifier = inicializar_telegram()

    if not notifier or not notifier.enabled:
        print("❌ Telegram não está habilitado!")
        return

    print("✅ Telegram inicializado com sucesso!")

    # Buscar dados da planilha
    print("\n" + "=" * 60)
    dados = buscar_dados_teste()

    if not dados or len(dados) < 2:
        print("⚠️ Não há dados suficientes na planilha para teste")

        # Enviar mensagem de teste básica
        print("\n📤 Enviando mensagem de teste básica...")
        sucesso = notifier.enviar_mensagem(
            "🧪 <b>TESTE TELEGRAM - RPA CICLO</b>\n\n"
            "✅ Sistema de notificações funcionando!\n\n"
            "⏰ Teste realizado com sucesso"
        )

        if sucesso:
            print("✅ Mensagem de teste enviada com sucesso!")
        else:
            print("❌ Falha ao enviar mensagem de teste")

        return

    # Processar dados da planilha
    headers = dados[0]
    primeira_linha = dados[1] if len(dados) > 1 else []

    # Tentar extrair informações (ajustar índices conforme sua planilha)
    try:
        # Criar dict da primeira linha
        linha_dict = {}
        for i, header in enumerate(headers):
            if i < len(primeira_linha):
                linha_dict[header] = primeira_linha[i]

        print(f"\n📋 Dados extraídos da planilha:")
        for key, value in linha_dict.items():
            print(f"   {key}: {value}")

        # Extrair campos comuns (ajuste conforme sua planilha)
        item = linha_dict.get("Item", linha_dict.get("Produto", "TESTE-123"))
        quantidade = linha_dict.get("Quantidade", linha_dict.get("Qtd", "10"))
        sub_o = linha_dict.get("Sub.Origem", linha_dict.get("Origem", "EST"))
        sub_d = linha_dict.get("Sub. Destino", linha_dict.get("Destino", "PRO"))

        print(f"\n📦 Dados para notificação:")
        print(f"   Item: {item}")
        print(f"   Quantidade: {quantidade}")
        print(f"   Sub Origem: {sub_o}")
        print(f"   Sub Destino: {sub_d}")

    except Exception as e:
        print(f"⚠️ Erro ao extrair dados: {e}")
        item = "TESTE-123"
        quantidade = "10"
        sub_o = "EST"
        sub_d = "PRO"

    # Enviar notificações de teste
    print("\n" + "=" * 60)
    print("📤 ENVIANDO NOTIFICAÇÕES DE TESTE")
    print("=" * 60)

    # 1. Início do Ciclo
    print("\n1️⃣ Enviando: Início do Ciclo...")
    sucesso1 = notifier.notificar_ciclo_inicio(999)
    print(f"   {'✅ Enviado' if sucesso1 else '❌ Falhou'}")

    import time
    time.sleep(1)

    # 2. Início de processamento de item
    print("\n2️⃣ Enviando: Processando Item...")
    sucesso2 = notifier.notificar_inicio_item(2, item, quantidade, sub_o, sub_d)
    print(f"   {'✅ Enviado' if sucesso2 else '❌ Falhou'}")

    time.sleep(1)

    # 3. Item concluído
    print("\n3️⃣ Enviando: Item Concluído...")
    sucesso3 = notifier.notificar_sucesso_item(2, item)
    print(f"   {'✅ Enviado' if sucesso3 else '❌ Falhou'}")

    time.sleep(1)

    # 4. Item com erro
    print("\n4️⃣ Enviando: Item com Erro...")
    sucesso4 = notifier.notificar_erro_item(3, "ITEM-ERRO", "Erro Oracle: produto inválido")
    print(f"   {'✅ Enviado' if sucesso4 else '❌ Falhou'}")

    time.sleep(1)

    # 5. Item pulado
    print("\n5️⃣ Enviando: Item Pulado...")
    sucesso5 = notifier.notificar_skip_item(4, "ITEM-CACHE", "Já processado anteriormente")
    print(f"   {'✅ Enviado' if sucesso5 else '❌ Falhou'}")

    time.sleep(1)

    # 6. Ciclo concluído
    print("\n6️⃣ Enviando: Ciclo Concluído...")
    sucesso6 = notifier.notificar_ciclo_concluido(999, 15, 2)
    print(f"   {'✅ Enviado' if sucesso6 else '❌ Falhou'}")

    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO DO TESTE")
    print("=" * 60)

    total = 6
    enviados = sum([sucesso1, sucesso2, sucesso3, sucesso4, sucesso5, sucesso6])

    print(f"\n✅ Mensagens enviadas: {enviados}/{total}")
    print(f"❌ Mensagens falhadas: {total - enviados}/{total}")

    if enviados == total:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Sistema de notificações Telegram está funcionando perfeitamente!")
    elif enviados > 0:
        print("\n⚠️ ALGUNS TESTES FALHARAM")
        print("Verifique sua conexão com a internet e as configurações do Telegram.")
    else:
        print("\n❌ TODOS OS TESTES FALHARAM")
        print("Verifique:")
        print("  - Bot token está correto")
        print("  - Chat ID está correto")
        print("  - Você enviou pelo menos uma mensagem para o bot")
        print("  - Conexão com a internet está funcionando")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    testar_telegram()
