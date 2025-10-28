# -*- coding: utf-8 -*-
"""
Script de teste para verificar configuração do Telegram
"""

import json
import os

print("=" * 60)
print("TESTE DE CONFIGURAÇÃO TELEGRAM")
print("=" * 60)
print()

# 1. Verificar se config.json existe
print("1. Verificando config.json...")
if os.path.exists("config.json"):
    print("   ✅ config.json encontrado")
else:
    print("   ❌ config.json NÃO encontrado!")
    exit(1)

# 2. Ler config.json
print("\n2. Lendo config.json...")
try:
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    print("   ✅ JSON válido")
except Exception as e:
    print(f"   ❌ Erro ao ler JSON: {e}")
    exit(1)

# 3. Verificar seção telegram
print("\n3. Verificando seção 'telegram'...")
if "telegram" in config:
    print("   ✅ Seção 'telegram' existe")
    telegram_config = config["telegram"]
else:
    print("   ❌ Seção 'telegram' NÃO encontrada!")
    exit(1)

# 4. Verificar campos
print("\n4. Verificando campos do Telegram...")
print(f"   - bot_token: {telegram_config.get('bot_token')}")
print(f"   - chat_id: {telegram_config.get('chat_id')}")
print(f"   - habilitado: {telegram_config.get('habilitado')}")

bot_token = telegram_config.get("bot_token")
chat_id = telegram_config.get("chat_id")
habilitado = telegram_config.get("habilitado", True)

print("\n5. Validações...")
print(f"   - bot_token existe: {bot_token is not None}")
print(f"   - chat_id existe: {chat_id is not None}")
print(f"   - habilitado: {habilitado}")
print(f"   - bot_token tipo: {type(bot_token)}")
print(f"   - chat_id tipo: {type(chat_id)}")

if bot_token:
    print(f"   - bot_token.strip(): '{str(bot_token).strip()}'")
    print(f"   - len(bot_token): {len(str(bot_token))}")

if chat_id:
    print(f"   - chat_id.strip(): '{str(chat_id).strip()}'")
    print(f"   - len(chat_id): {len(str(chat_id))}")

# 6. Testar lógica do TelegramNotifier
print("\n6. Testando lógica enabled...")
enabled = bool(bot_token and chat_id and str(bot_token).strip() and str(chat_id).strip())
print(f"   - enabled (calculado): {enabled}")

# 7. Importar e testar TelegramNotifier
print("\n7. Testando importação do módulo...")
try:
    from telegram_notifier import TelegramNotifier, inicializar_telegram
    print("   ✅ telegram_notifier importado com sucesso")
except Exception as e:
    print(f"   ❌ Erro ao importar: {e}")
    exit(1)

# 8. Criar instância manual
print("\n8. Criando instância manual do TelegramNotifier...")
notifier = TelegramNotifier(bot_token, chat_id)
print(f"   - notifier.enabled: {notifier.enabled}")
print(f"   - notifier.bot_token: {notifier.bot_token}")
print(f"   - notifier.chat_id: {notifier.chat_id}")

# 9. Testar inicialização automática
print("\n9. Testando inicialização automática...")
notifier_auto = inicializar_telegram()
print(f"   - notifier_auto.enabled: {notifier_auto.enabled}")

# 10. Testar envio (se habilitado)
if notifier_auto.enabled:
    print("\n10. Testando envio de mensagem...")
    resultado = notifier_auto.enviar_mensagem("🧪 Teste de notificação do RPA Ciclo")
    if resultado:
        print("   ✅ Mensagem enviada com sucesso!")
    else:
        print("   ❌ Falha ao enviar mensagem")
else:
    print("\n10. ⚠️ Notificador desabilitado - pulando teste de envio")

print("\n" + "=" * 60)
print("TESTE CONCLUÍDO")
print("=" * 60)
