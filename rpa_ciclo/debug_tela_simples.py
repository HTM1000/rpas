# -*- coding: utf-8 -*-
"""
Debug simples - Validacao de tela
"""

import cv2
import numpy as np
from PIL import ImageGrab
import os
from datetime import datetime

print("=" * 60)
print("DEBUG - VALIDACAO DE TELA")
print("=" * 60)

# Capturar tela
print("\n1. Capturando tela atual...")
screenshot = ImageGrab.grab()
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
screenshot_path = f"debug_tela_atual_{timestamp}.png"
screenshot.save(screenshot_path)
print(f"   Salvo: {screenshot_path}")

tela_atual = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
altura_tela, largura_tela = tela_atual.shape[:2]
print(f"   TELA: {largura_tela}x{altura_tela} pixels")

# Carregar referência
print("\n2. Carregando imagem de referencia...")
ref_path = "informacoes/tela_transferencia_subinventory.png"

if not os.path.exists(ref_path):
    print(f"   ERRO: Arquivo nao encontrado: {ref_path}")
    exit(1)

img_referencia = cv2.imread(ref_path)
altura_ref, largura_ref = img_referencia.shape[:2]
print(f"   Arquivo: {ref_path}")
print(f"   REFERENCIA: {largura_ref}x{altura_ref} pixels")

# Verificar compatibilidade
print("\n3. Verificando compatibilidade...")
if largura_ref > largura_tela or altura_ref > altura_tela:
    print("   PROBLEMA DETECTADO!")
    print(f"   A imagem de referencia ({largura_ref}x{altura_ref}) eh MAIOR")
    print(f"   que a tela atual ({largura_tela}x{altura_tela})")
    print("")
    print("   SOLUCOES:")
    print("   1. Recapturar a imagem na resolucao atual (1366x768)")
    print("   2. Redimensionar a imagem de referencia")
    print("   3. Capturar apenas uma regiao menor (nao a tela toda)")

    # Calcular escala
    escala_x = largura_tela / largura_ref
    escala_y = altura_tela / altura_ref
    escala = min(escala_x, escala_y)

    print(f"\n   Sugestao: Redimensionar para {escala:.2%} do tamanho original")

    # Criar versão redimensionada
    nova_largura = int(largura_ref * escala * 0.95)  # 95% para garantir
    nova_altura = int(altura_ref * escala * 0.95)

    print(f"   Novo tamanho sugerido: {nova_largura}x{nova_altura}")

    ref_redim = cv2.resize(img_referencia, (nova_largura, nova_altura))
    ref_redim_path = f"tela_transferencia_subinventory_REDIMENSIONADA_{timestamp}.png"
    cv2.imwrite(ref_redim_path, ref_redim)
    print(f"\n   CRIADA versao redimensionada: {ref_redim_path}")
    print("   Substitua a imagem original por esta!")

    # Testar com redimensionada
    print("\n4. Testando com versao redimensionada...")
    result = cv2.matchTemplate(tela_atual, ref_redim, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    print(f"   Score: {max_val:.4f}")

    if max_val >= 0.8:
        print("   OK - Match encontrado!")
    else:
        print("   Ainda nao encontrado. Score baixo.")

    # Marcar na tela
    h, w = ref_redim.shape[:2]
    top_left = max_loc
    bottom_right = (top_left[0] + w, top_left[1] + h)

    tela_marcada = tela_atual.copy()
    cv2.rectangle(tela_marcada, top_left, bottom_right, (0, 255, 0), 3)

    resultado_path = f"debug_resultado_{timestamp}.png"
    cv2.imwrite(resultado_path, tela_marcada)
    print(f"   Tela marcada salva: {resultado_path}")

else:
    print("   OK - Tamanhos compativeis")

    # Template matching
    print("\n4. Buscando correspondencia...")
    result = cv2.matchTemplate(tela_atual, img_referencia, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    print(f"   Score: {max_val:.4f} (0.0 a 1.0)")

    if max_val >= 0.8:
        print("   OK - Tela correspondente!")
    elif max_val >= 0.6:
        print("   ATENCAO - Match parcial")
    else:
        print("   ERRO - Nao corresponde")

    # Marcar
    h, w = img_referencia.shape[:2]
    top_left = max_loc
    bottom_right = (top_left[0] + w, top_left[1] + h)

    tela_marcada = tela_atual.copy()
    cv2.rectangle(tela_marcada, top_left, bottom_right, (0, 255, 0), 3)

    resultado_path = f"debug_resultado_{timestamp}.png"
    cv2.imwrite(resultado_path, tela_marcada)
    print(f"   Resultado: {resultado_path}")

print("\n" + "=" * 60)
print("CONCLUIDO")
print("=" * 60)
