# -*- coding: utf-8 -*-
"""
Script de DEBUG para validação de tela
Mostra exatamente o que o sistema está vendo e comparando
"""

import pyautogui
import cv2
import numpy as np
from PIL import Image, ImageGrab
import os
from datetime import datetime

print("=" * 60)
print("DEBUG - VALIDACAO DE TELA")
print("=" * 60)

# Capturar tela atual
print("\n1. Capturando tela atual...")
screenshot = ImageGrab.grab()
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Salvar screenshot
screenshot_path = f"debug_tela_atual_{timestamp}.png"
screenshot.save(screenshot_path)
print(f"   Salvo: {screenshot_path}")

# Converter para OpenCV
tela_atual = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
print(f"   Tamanho: {tela_atual.shape[1]}x{tela_atual.shape[0]} pixels")

# Carregar imagem de referência
print("\n2. Carregando imagem de referência...")
ref_path = "informacoes/tela_transferencia_subinventory.png"

if not os.path.exists(ref_path):
    print(f"   ERRO: Imagem não encontrada: {ref_path}")
    exit(1)

img_referencia = cv2.imread(ref_path)
print(f"   Arquivo: {ref_path}")
print(f"   Tamanho: {img_referencia.shape[1]}x{img_referencia.shape[0]} pixels")

# Tentar localizar com PyAutoGUI
print("\n3. Tentando localizar com PyAutoGUI...")
try:
    resultado = pyautogui.locateOnScreen(ref_path, confidence=0.8)
    if resultado:
        print(f"   ✅ ENCONTRADO com confidence 0.8")
        print(f"   Posição: X={resultado.left}, Y={resultado.top}")
        print(f"   Tamanho: {resultado.width}x{resultado.height}")
    else:
        print(f"   ❌ NÃO ENCONTRADO com confidence 0.8")
except Exception as e:
    print(f"   ❌ ERRO: {e}")

# Tentar com confidence mais baixo
print("\n4. Testando diferentes níveis de confidence...")
for conf in [0.9, 0.8, 0.7, 0.6, 0.5]:
    try:
        resultado = pyautogui.locateOnScreen(ref_path, confidence=conf)
        if resultado:
            print(f"   ✅ Confidence {conf}: ENCONTRADO em ({resultado.left}, {resultado.top})")
        else:
            print(f"   ❌ Confidence {conf}: NÃO ENCONTRADO")
    except:
        print(f"   ❌ Confidence {conf}: ERRO")

# Template matching com OpenCV
print("\n5. Template Matching com OpenCV...")
result = cv2.matchTemplate(tela_atual, img_referencia, cv2.TM_CCOEFF_NORMED)
min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

print(f"   Melhor match: {max_val:.4f} (0.0 a 1.0)")
print(f"   Posição: {max_loc}")

if max_val >= 0.8:
    print(f"   ✅ MATCH BOM (>= 0.8)")
elif max_val >= 0.6:
    print(f"   ⚠️ MATCH RAZOÁVEL (0.6 a 0.8)")
else:
    print(f"   ❌ MATCH RUIM (< 0.6)")

# Criar imagem visual do match
print("\n6. Criando imagem visual do resultado...")
h, w = img_referencia.shape[:2]
top_left = max_loc
bottom_right = (top_left[0] + w, top_left[1] + h)

# Desenhar retângulo na tela capturada
tela_marcada = tela_atual.copy()
cv2.rectangle(tela_marcada, top_left, bottom_right, (0, 255, 0), 3)

# Adicionar texto com score
texto = f"Match: {max_val:.2f}"
cv2.putText(tela_marcada, texto, (top_left[0], top_left[1]-10),
            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

# Salvar imagem com marcação
resultado_path = f"debug_resultado_match_{timestamp}.png"
cv2.imwrite(resultado_path, tela_marcada)
print(f"   Salvo: {resultado_path}")

# Extrair região encontrada
print("\n7. Extraindo região encontrada...")
regiao_encontrada = tela_atual[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]]
regiao_path = f"debug_regiao_encontrada_{timestamp}.png"
cv2.imwrite(regiao_path, regiao_encontrada)
print(f"   Salvo: {regiao_path}")

# Comparar pixel por pixel (amostra)
print("\n8. Análise de diferenças...")
if regiao_encontrada.shape == img_referencia.shape:
    # Calcular diferença
    diff = cv2.absdiff(img_referencia, regiao_encontrada)
    diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

    # Contar pixels diferentes
    pixels_diferentes = np.count_nonzero(diff_gray > 30)  # Threshold de 30
    total_pixels = diff_gray.shape[0] * diff_gray.shape[1]
    percentual_diferenca = (pixels_diferentes / total_pixels) * 100

    print(f"   Total pixels: {total_pixels}")
    print(f"   Pixels diferentes: {pixels_diferentes}")
    print(f"   Diferença: {percentual_diferenca:.2f}%")

    # Salvar imagem de diferença
    diff_path = f"debug_diferenca_{timestamp}.png"
    cv2.imwrite(diff_path, diff)
    print(f"   Salvo: {diff_path}")

    # Criar heatmap de diferenças
    diff_heat = cv2.applyColorMap(diff_gray, cv2.COLORMAP_JET)
    heatmap_path = f"debug_heatmap_{timestamp}.png"
    cv2.imwrite(heatmap_path, diff_heat)
    print(f"   Heatmap: {heatmap_path}")
else:
    print(f"   ⚠️ Tamanhos diferentes, não é possível comparar pixel a pixel")
    print(f"   Referência: {img_referencia.shape}")
    print(f"   Encontrado: {regiao_encontrada.shape}")

# Análise de regiões estáticas vs dinâmicas
print("\n9. Sugestão de recorte...")
print(f"   Imagem atual: {w}x{h} pixels")

# Sugerir remover rodapé (últimos 10-15% da imagem)
altura_sem_rodape = int(h * 0.85)
print(f"   Sugestão 1: Remover rodapé (últimos 15%)")
print(f"   Novo tamanho: {w}x{altura_sem_rodape}")

# Sugerir remover cabeçalho com data/hora
altura_sem_cabecalho_rodape = int(h * 0.85)
inicio_sem_cabecalho = int(h * 0.05)
print(f"   Sugestão 2: Remover cabeçalho (5%) + rodapé (15%)")
print(f"   Recorte: Y={inicio_sem_cabecalho} até Y={altura_sem_cabecalho_rodape}")

# Criar versão recortada da referência
print("\n10. Criando versão recortada (sem rodapé)...")
ref_sem_rodape = img_referencia[0:altura_sem_rodape, 0:w]
ref_recortada_path = f"debug_referencia_recortada_{timestamp}.png"
cv2.imwrite(ref_recortada_path, ref_sem_rodape)
print(f"   Salvo: {ref_recortada_path}")

# Testar match com versão recortada
print("\n11. Testando match com versão recortada...")
try:
    # Procurar na tela atual
    result_recortado = cv2.matchTemplate(tela_atual, ref_sem_rodape, cv2.TM_CCOEFF_NORMED)
    min_val_r, max_val_r, min_loc_r, max_loc_r = cv2.minMaxLoc(result_recortado)

    print(f"   Score ORIGINAL: {max_val:.4f}")
    print(f"   Score RECORTADO: {max_val_r:.4f}")

    if max_val_r > max_val:
        print(f"   ✅ MELHOROU! (+{(max_val_r - max_val):.4f})")
    else:
        print(f"   Não melhorou significativamente")
except Exception as e:
    print(f"   ❌ Erro: {e}")

# Resumo final
print("\n" + "=" * 60)
print("RESUMO")
print("=" * 60)
print(f"\nArquivos gerados:")
print(f"  1. {screenshot_path} - Tela atual completa")
print(f"  2. {resultado_path} - Tela com marcação do match")
print(f"  3. {regiao_path} - Região encontrada")
print(f"  4. {diff_path} - Diferença pixel a pixel")
print(f"  5. {heatmap_path} - Mapa de calor das diferenças")
print(f"  6. {ref_recortada_path} - Referência sem rodapé")

print(f"\nScore de match: {max_val:.4f}")
if max_val >= 0.8:
    print("✅ VALIDAÇÃO OK - Imagem encontrada")
elif max_val >= 0.6:
    print("⚠️ VALIDAÇÃO PARCIAL - Pode dar falso negativo")
else:
    print("❌ VALIDAÇÃO FALHOU - Imagem não corresponde")

print("\nRecomendação:")
if max_val < 0.8:
    print("  1. Abra o arquivo de heatmap para ver onde estão as diferenças")
    print("  2. Recorte a imagem de referência removendo partes dinâmicas:")
    print("     - Rodapé (data, hora, status)")
    print("     - Cabeçalho (se tiver informações que mudam)")
    print("  3. Use uma ferramenta de edição para recortar a imagem")
    print("  4. Substitua informacoes/tela_transferencia_subinventory.png")
else:
    print("  Imagem de referência está OK!")

print("\n" + "=" * 60)
