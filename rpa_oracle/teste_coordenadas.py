# -*- coding: utf-8 -*-
"""
Script de teste para verificar coordenadas e preenchimento no Oracle
Execute este script com o Oracle aberto na tela correta
"""
import pyautogui
import time

coords = {
    "item": (101, 156),
    "sub_origem": (257, 159),
    "end_origem": (335, 159),
    "sub_destino": (485, 159),
    "end_destino": (553, 159),
    "quantidade": (672, 159),
    "Referencia": (768, 159),
}

print("=" * 60)
print("TESTE DE COORDENADAS - RPA ORACLE")
print("=" * 60)
print("\n⚠️  ATENÇÃO: Certifique-se de que o Oracle está aberto e visível!")
print("\n🕒 Você tem 5 segundos para posicionar a janela do Oracle...")
time.sleep(5)

print("\n📍 Testando coordenadas e preenchimento...")
print("-" * 60)

# Teste 1: Campo Item
print("\n1️⃣  TESTANDO CAMPO ITEM")
print(f"   Coordenada: {coords['item']}")
print("   Clicando...")
pyautogui.click(coords["item"])
time.sleep(0.5)
print("   Limpando campo...")
pyautogui.press("delete")
time.sleep(0.3)
print("   Digitando 'TESTE123'...")
pyautogui.write("TESTE123")
time.sleep(0.5)
print("   ✅ Campo Item testado")

# Teste 2: Campo Referência
print("\n2️⃣  TESTANDO CAMPO REFERÊNCIA")
print(f"   Coordenada: {coords['Referencia']}")
print("   Clicando...")
pyautogui.click(coords["Referencia"])
time.sleep(0.5)
print("   Digitando 'MOV001'...")
pyautogui.write("MOV001")
time.sleep(0.5)
print("   ✅ Campo Referência testado")

# Teste 3: Campo Sub.Origem
print("\n3️⃣  TESTANDO CAMPO SUB.ORIGEM")
print(f"   Coordenada: {coords['sub_origem']}")
print("   Clicando...")
pyautogui.click(coords["sub_origem"])
time.sleep(0.5)
print("   Digitando '01'...")
pyautogui.write("01")
time.sleep(0.3)
print("   Pressionando TAB...")
pyautogui.press("tab")
time.sleep(0.5)
print("   ✅ Campo Sub.Origem testado")

# Teste 4: Campo End.Origem
print("\n4️⃣  TESTANDO CAMPO END.ORIGEM")
print(f"   Coordenada: {coords['end_origem']}")
print("   Clicando...")
pyautogui.click(coords["end_origem"])
time.sleep(0.5)
print("   Limpando...")
pyautogui.press("delete")
time.sleep(0.3)
print("   Digitando 'A001'...")
pyautogui.write("A001")
time.sleep(0.3)
print("   Pressionando TAB...")
pyautogui.press("tab")
time.sleep(0.5)
print("   ✅ Campo End.Origem testado")

# Teste 5: Campo Quantidade
print("\n5️⃣  TESTANDO CAMPO QUANTIDADE")
print(f"   Coordenada: {coords['quantidade']}")
print("   Clicando...")
pyautogui.click(coords["quantidade"])
time.sleep(0.5)
print("   Limpando...")
pyautogui.press("delete")
time.sleep(0.3)
print("   Digitando '10'...")
pyautogui.write("10")
time.sleep(0.5)
print("   ✅ Campo Quantidade testado")

print("\n" + "=" * 60)
print("✅ TESTE CONCLUÍDO!")
print("=" * 60)
print("\n🔍 VERIFIQUE NO ORACLE:")
print("   • Os campos foram preenchidos corretamente?")
print("   • Os valores aparecem nos campos certos?")
print("   • O mouse clicou nas posições corretas?")
print("\n💡 Se algo não funcionou:")
print("   1. Use mouse.py para capturar as coordenadas corretas")
print("   2. Atualize as coordenadas em RPA_Oracle.py (linha 41-49)")
print("   3. Execute este teste novamente")
print("\n⚠️  IMPORTANTE: Não salve (Ctrl+S) - estes são apenas dados de teste!")
