"""
Script para Capturar APENAS OS ÍCONES dos Modais

Instruções:
1. Abra o Oracle com o modal visível
2. Execute este script
3. Clique no ÍCONE (🟡 ou 🔴) do modal
4. O script vai salvar apenas a região do ícone

Use isso para criar imagens de referência APENAS DO ÍCONE
"""

import pyautogui
import cv2
import numpy as np
from PIL import ImageGrab, Image
import time

def capturar_icone():
    """Captura apenas o ícone do modal"""

    print("=" * 70)
    print("CAPTURAR ÍCONE DO MODAL")
    print("=" * 70)
    print("\nInstruções:")
    print("1. Abra o Oracle com o modal visível")
    print("2. Quando pressionar ENTER, você terá 5 segundos")
    print("3. Clique no ÍCONE (🟡 amarelo ou 🔴 vermelho) do modal")
    print("4. O script vai capturar a região do ícone\n")

    input("Pressione ENTER para começar...")

    print("\n⏳ Você tem 5 segundos para clicar no ÍCONE do modal...")
    for i in range(5, 0, -1):
        print(f"   {i}...", flush=True)
        time.sleep(1)

    # Pegar posição do mouse (onde usuário clicou)
    print("\n📍 Pegue a posição do mouse e clique no ÍCONE...")
    print("   (Mova o mouse sobre o ícone e pressione ENTER)")

    input("\nPressione ENTER quando o mouse estiver sobre o ÍCONE...")

    x, y = pyautogui.position()
    print(f"\n✅ Posição do mouse: x={x}, y={y}")

    # Capturar screenshot
    screenshot = ImageGrab.grab()
    screenshot_np = np.array(screenshot)

    # Crop região do ícone (50x50 pixels ao redor do mouse)
    tamanho_icone = 50
    margin = tamanho_icone // 2

    x_start = max(0, x - margin)
    y_start = max(0, y - margin)
    x_end = min(screenshot_np.shape[1], x + margin)
    y_end = min(screenshot_np.shape[0], y + margin)

    icone = screenshot_np[y_start:y_end, x_start:x_end]

    # Salvar
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"icone_modal_{timestamp}.png"

    icone_bgr = cv2.cvtColor(icone, cv2.COLOR_RGB2BGR)
    cv2.imwrite(filename, icone_bgr)

    print(f"\n✅ Ícone capturado e salvo: {filename}")
    print(f"   Tamanho: {icone.shape[1]}x{icone.shape[0]} pixels")
    print(f"   Posição: ({x_start}, {y_start}) até ({x_end}, {y_end})")

    # Perguntar qual modal é
    print("\n" + "=" * 70)
    print("Qual modal você capturou?")
    print("1 - Quantidade Negativa (🟡 amarelo)")
    print("2 - Erro Centro de Custo (🔴 vermelho)")
    escolha = input("Digite 1 ou 2: ")

    if escolha == "1":
        novo_nome = "icone_qtd_negativa.png"
        print(f"\n✅ Renomeando para: {novo_nome}")
        import os
        os.rename(filename, novo_nome)
        print(f"   Use este arquivo como referência para quantidade negativa")
    elif escolha == "2":
        novo_nome = "icone_erro_centro_custo.png"
        print(f"\n✅ Renomeando para: {novo_nome}")
        import os
        os.rename(filename, novo_nome)
        print(f"   Use este arquivo como referência para erro centro custo")
    else:
        print(f"\n⚠️ Opção inválida. Arquivo salvo como: {filename}")

    print("\n" + "=" * 70)
    print("✅ CONCLUÍDO!")
    print("=" * 70)

if __name__ == "__main__":
    try:
        capturar_icone()
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        print(traceback.format_exc())

    input("\nPressione ENTER para fechar...")
