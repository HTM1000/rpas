# -*- coding: utf-8 -*-
"""
Helper para capturar coordenadas do mouse
Use este script para encontrar as coordenadas corretas dos elementos na tela
"""

import pyautogui
import time
import keyboard

print("="*60)
print("  HELPER DE COORDENADAS DO MOUSE")
print("="*60)
print()
print("Como usar:")
print("1. Posicione o mouse sobre o elemento desejado")
print("2. Pressione SPACE para capturar a coordenada")
print("3. Pressione ESC para sair")
print()
print("As coordenadas capturadas serão exibidas no console")
print("="*60)
print()
print("Aguardando... (Pressione SPACE para capturar)")
print()

coordenadas_capturadas = []

try:
    while True:
        if keyboard.is_pressed('space'):
            x, y = pyautogui.position()
            coordenadas_capturadas.append((x, y))
            print(f"✅ Capturado #{len(coordenadas_capturadas)}: X={x}, Y={y}")
            time.sleep(0.5)  # Evitar múltiplas capturas

        if keyboard.is_pressed('esc'):
            print()
            print("="*60)
            print("Encerrando...")
            break

        time.sleep(0.1)

except KeyboardInterrupt:
    print()
    print("="*60)
    print("Interrompido pelo usuário")

print()
print("="*60)
print("RESUMO DAS COORDENADAS CAPTURADAS:")
print("="*60)

if coordenadas_capturadas:
    for i, (x, y) in enumerate(coordenadas_capturadas, 1):
        print(f"{i}. X={x}, Y={y}")

    print()
    print("="*60)
    print("JSON para config.json:")
    print("="*60)
    for i, (x, y) in enumerate(coordenadas_capturadas, 1):
        print(f'"tela_{i:02d}": {{"x": {x}, "y": {y}, "descricao": "Descrição aqui"}},')
else:
    print("Nenhuma coordenada foi capturada")

print()
print("="*60)
