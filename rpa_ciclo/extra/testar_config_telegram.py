"""
Teste de configuracao do Telegram
Verifica se o config.json esta sendo lido corretamente
"""

import json
import sys

# Configurar encoding UTF-8 para console Windows
if sys.platform.startswith('win'):
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass

from telegram_notifier import inicializar_telegram

print("=" * 60)
print("TESTE DE CONFIGURACAO DO TELEGRAM")
print("=" * 60)

# 1. Ler o config.json manualmente
print("\n[1] Lendo config.json manualmente...")
try:
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        telegram_config = config.get("telegram", {})

        print("[OK] config.json lido com sucesso")
        print(f"\nConteúdo da seção 'telegram':")
        for key, value in telegram_config.items():
            if key == "bot_token":
                print(f"  {key}: {value[:20]}... (len={len(value)})")
            else:
                print(f"  {key}: {value}")

        bot_token = telegram_config.get("bot_token")
        chat_id = telegram_config.get("chat_id")
        habilitado = telegram_config.get("habilitado")

        print(f"\nValidação manual:")
        print(f"  bot_token presente: {bool(bot_token)}")
        print(f"  bot_token tipo: {type(bot_token)}")
        print(f"  chat_id presente: {bool(chat_id)}")
        print(f"  chat_id tipo: {type(chat_id)}")
        print(f"  chat_id valor: {chat_id}")
        print(f"  habilitado: {habilitado}")
        print(f"  bool(bot_token and chat_id): {bool(bot_token and chat_id)}")

except Exception as e:
    print(f"[ERRO] Erro ao ler config.json: {e}")
    import traceback
    traceback.print_exc()

# 2. Testar inicialização via telegram_notifier
print("\n" + "=" * 60)
print("[2] Inicializando via telegram_notifier...")
print("=" * 60)

try:
    notifier = inicializar_telegram()

    print(f"\nNotificador criado:")
    print(f"  enabled: {notifier.enabled}")
    print(f"  bot_token: {notifier.bot_token[:20] if notifier.bot_token else 'None'}...")
    print(f"  chat_id: {notifier.chat_id}")

    # 3. Tentar enviar mensagem de teste
    if notifier.enabled:
        print("\n[3] Enviando mensagem de teste...")
        resultado = notifier.enviar_mensagem("Teste de configuracao do Telegram - RPA Ciclo")

        if resultado:
            print("[OK] Mensagem enviada com SUCESSO!")
        else:
            print("[ERRO] Falha ao enviar mensagem")
    else:
        print("\n[ERRO] Notificador DESABILITADO - nao e possivel enviar mensagem")
        print("\nMotivos possiveis:")
        print("  - bot_token ou chat_id ausentes")
        print("  - bot_token ou chat_id vazios")
        print("  - Formato incorreto no config.json")

except Exception as e:
    print(f"[ERRO] Erro ao inicializar notificador: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("FIM DO TESTE")
print("=" * 60)
