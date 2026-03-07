"""
Script de Diagnóstico - Detecção de Cores em Tempo Real

Mostra quantos pixels vermelhos e amarelos estão sendo detectados na tela
"""

import cv2
import numpy as np
from PIL import ImageGrab
import time

def detectar_cores_tempo_real():
    """Detecta cores em tempo real e mostra estatísticas"""

    print("=" * 70)
    print("DIAGNÓSTICO DE DETECÇÃO DE CORES")
    print("=" * 70)
    print("\nInstruções:")
    print("1. Abra o Oracle com a tela que você quer testar")
    print("2. Pressione ENTER para iniciar monitoramento")
    print("3. O script vai mostrar quantos pixels vermelhos/amarelos detecta")
    print("4. Pressione Ctrl+C para parar\n")

    input("Pressione ENTER para começar...")
    print("\n🔍 Monitorando cores... (Ctrl+C para parar)\n")

    try:
        while True:
            # Capturar tela
            screenshot = ImageGrab.grab()
            screenshot_np = np.array(screenshot)
            screenshot_hsv = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2HSV)

            # ═══════════════════════════════════════════════════════════════
            # DETECTAR VERMELHO
            # ═══════════════════════════════════════════════════════════════
            lower_red1 = np.array([0, 150, 150])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([170, 150, 150])
            upper_red2 = np.array([180, 255, 255])

            mask_red1 = cv2.inRange(screenshot_hsv, lower_red1, upper_red1)
            mask_red2 = cv2.inRange(screenshot_hsv, lower_red2, upper_red2)
            mask_red = mask_red1 + mask_red2
            red_pixels = cv2.countNonZero(mask_red)

            # ═══════════════════════════════════════════════════════════════
            # DETECTAR AMARELO
            # ═══════════════════════════════════════════════════════════════
            lower_yellow = np.array([20, 150, 150])
            upper_yellow = np.array([30, 255, 255])
            mask_yellow = cv2.inRange(screenshot_hsv, lower_yellow, upper_yellow)
            yellow_pixels = cv2.countNonZero(mask_yellow)

            # ═══════════════════════════════════════════════════════════════
            # MOSTRAR RESULTADO
            # ═══════════════════════════════════════════════════════════════
            status_red = "✅ DETECTADO" if red_pixels > 100 else "❌ Não detectado"
            status_yellow = "✅ DETECTADO" if yellow_pixels > 100 else "❌ Não detectado"

            print(f"\r🔴 Vermelho: {red_pixels:>5} pixels ({status_red})  |  "
                  f"🟡 Amarelo: {yellow_pixels:>5} pixels ({status_yellow})",
                  end="", flush=True)

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\n✅ Diagnóstico encerrado!")

        # Salvar screenshot final para análise
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"diagnostico_final_{timestamp}.png"
        screenshot.save(filename)
        print(f"\n💾 Screenshot salvo: {filename}")

        # Salvar máscaras para visualização
        filename_red = f"diagnostico_red_mask_{timestamp}.png"
        filename_yellow = f"diagnostico_yellow_mask_{timestamp}.png"

        cv2.imwrite(filename_red, mask_red)
        cv2.imwrite(filename_yellow, mask_yellow)

        print(f"💾 Máscara vermelha salva: {filename_red}")
        print(f"💾 Máscara amarela salva: {filename_yellow}")

        print("\n" + "=" * 70)
        print("ANÁLISE DAS MÁSCARAS:")
        print("=" * 70)
        print("- Branco = pixels detectados (cor encontrada)")
        print("- Preto = pixels não detectados")
        print("\nAbra as imagens para ver o que está sendo detectado como vermelho/amarelo")

if __name__ == "__main__":
    detectar_cores_tempo_real()
