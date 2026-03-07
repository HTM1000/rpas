# -*- coding: utf-8 -*-
"""
Script simples de teste para Telegram
"""

import json
from telegram_notifier import inicializar_telegram

print("=" * 60)
print("TESTE DE TELEGRAM")
print("=" * 60)

# Carregar config
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)
    telegram_config = config.get("telegram", {})

print("\nConfiguracao:")
print(f"  Bot Token: {'OK' if telegram_config.get('bot_token') else 'VAZIO'}")
print(f"  Chat ID: {'OK' if telegram_config.get('chat_id') else 'VAZIO'}")

if not telegram_config.get('chat_id'):
    print("\nERRO: Chat ID nao configurado!")
    print("Configure o chat_id no config.json")
    exit(1)

# Inicializar
print("\nInicializando Telegram...")
notifier = inicializar_telegram()

if not notifier.enabled:
    print("ERRO: Telegram nao habilitado!")
    exit(1)

print("OK - Telegram inicializado!")

# Enviar teste
print("\n" + "=" * 60)
print("ENVIANDO MENSAGENS DE TESTE")
print("=" * 60)

import time

# 1. Ciclo
print("\n1. Enviando: Inicio do Ciclo...")
r1 = notifier.notificar_ciclo_inicio(999)
print(f"   Resultado: {'OK' if r1 else 'FALHOU'}")
time.sleep(1)

# 2. Item inicio
print("\n2. Enviando: Processando Item...")
r2 = notifier.notificar_inicio_item(2, "ITEM-123", "10", "EST", "PRO")
print(f"   Resultado: {'OK' if r2 else 'FALHOU'}")
time.sleep(1)

# 3. Item sucesso
print("\n3. Enviando: Item Concluido...")
r3 = notifier.notificar_sucesso_item(2, "ITEM-123")
print(f"   Resultado: {'OK' if r3 else 'FALHOU'}")
time.sleep(1)

# 4. Item erro
print("\n4. Enviando: Item com Erro...")
r4 = notifier.notificar_erro_item(3, "ITEM-ERRO", "Erro Oracle: produto invalido")
print(f"   Resultado: {'OK' if r4 else 'FALHOU'}")
time.sleep(1)

# 5. Item skip
print("\n5. Enviando: Item Pulado...")
r5 = notifier.notificar_skip_item(4, "ITEM-CACHE", "Ja processado")
print(f"   Resultado: {'OK' if r5 else 'FALHOU'}")
time.sleep(1)

# 6. Ciclo fim
print("\n6. Enviando: Ciclo Concluido...")
r6 = notifier.notificar_ciclo_concluido(999, 15, 2)
print(f"   Resultado: {'OK' if r6 else 'FALHOU'}")

# Resumo
print("\n" + "=" * 60)
print("RESUMO")
print("=" * 60)

total = 6
ok = sum([r1, r2, r3, r4, r5, r6])

print(f"\nEnviadas: {ok}/{total}")
print(f"Falhadas: {total - ok}/{total}")

if ok == total:
    print("\nSUCESSO! Todas as mensagens foram enviadas!")
elif ok > 0:
    print("\nPARCIAL: Algumas mensagens falharam")
else:
    print("\nERRO: Todas as mensagens falharam")
    print("\nVerifique:")
    print("  - Bot token correto")
    print("  - Chat ID correto")
    print("  - Voce enviou /start para o bot")

print("\n" + "=" * 60)
