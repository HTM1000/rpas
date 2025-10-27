# -*- coding: utf-8 -*-
"""
Testar detecção da tela de transferência
"""

import cv2
import numpy as np
from PIL import ImageGrab
import time

print("=" * 60)
print("TESTE DE DETECAO - TELA TRANSFERENCIA")
print("=" * 60)

caminho = "informacoes/tela_transferencia_subinventory.png"

print(f"\n1. Carregando imagem: {caminho}")
template = cv2.imread(caminho)

if template is None:
    print("   ERRO: Nao foi possivel carregar a imagem")
    exit(1)

template_h, template_w = template.shape[:2]
print(f"   Tamanho template: {template_w}x{template_h}")

print("\n2. Capturando tela atual...")
screenshot = ImageGrab.grab()
screenshot_np = np.array(screenshot)
screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

screen_h, screen_w = screenshot_bgr.shape[:2]
print(f"   Tamanho tela: {screen_w}x{screen_h}")

print("\n3. Testando deteccao...")
confidence = 0.7  # Baixar um pouco para teste

# Se template maior que tela, redimensionar
if template_w > screen_w or template_h > screen_h:
    scale = min(screen_w / template_w, screen_h / template_h) * 0.95
    new_w = int(template_w * scale)
    new_h = int(template_h * scale)
    template_scaled = cv2.resize(template, (new_w, new_h))
    print(f"   Template redimensionado: {new_w}x{new_h}")
else:
    template_scaled = template
    print("   Template OK (cabe na tela)")

# Template matching
print("\n4. Buscando correspondencia...")
result = cv2.matchTemplate(screenshot_bgr, template_scaled, cv2.TM_CCOEFF_NORMED)
min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

print(f"   Score: {max_val:.4f} (0.0 a 1.0)")

if max_val >= confidence:
    print(f"   SUCESSO! Imagem encontrada (>= {confidence})")
else:
    print(f"   FALHOU! Score abaixo do esperado (< {confidence})")

# Tentar multi-escala
print("\n5. Testando diferentes escalas...")
melhor_escala = None
melhor_score = max_val

for escala in [0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3]:
    new_w = int(template_w * escala)
    new_h = int(template_h * escala)

    if new_w > screen_w or new_h > screen_h:
        print(f"   Escala {escala:.1f}: Muito grande ({new_w}x{new_h})")
        continue

    template_test = cv2.resize(template, (new_w, new_h))
    result_test = cv2.matchTemplate(screenshot_bgr, template_test, cv2.TM_CCOEFF_NORMED)
    _, max_val_test, _, _ = cv2.minMaxLoc(result_test)

    print(f"   Escala {escala:.1f}: Score = {max_val_test:.4f}", end="")

    if max_val_test > melhor_score:
        melhor_score = max_val_test
        melhor_escala = escala
        print(" <- MELHOR")
    else:
        print()

    if max_val_test >= confidence:
        print(f"\n   ENCONTRADO na escala {escala:.1f}!")
        break

print("\n" + "=" * 60)
print("RESULTADO")
print("=" * 60)

if melhor_score >= confidence:
    print(f"\nSUCESSO! Imagem detectada")
    print(f"Melhor score: {melhor_score:.4f}")
    if melhor_escala:
        print(f"Melhor escala: {melhor_escala:.1f}")
    print("\nA validacao de tela deve funcionar!")
else:
    print(f"\nFALHOU! Imagem NAO detectada")
    print(f"Melhor score: {melhor_score:.4f} (esperado >= {confidence:.4f})")
    print("\nPossibilidades:")
    print("1. Oracle nao esta na tela de Transferencia de Subinventario")
    print("2. Imagem de referencia precisa ser recapturada")
    print("3. Usar uma regiao menor/mais especifica da tela")

print("\n" + "=" * 60)
