"""
Script de Teste - Detecção de Modais em Arquivo de Imagem

Uso:
1. Arraste e solte uma imagem (screenshot) neste script
2. OU execute e digite o caminho da imagem
3. O script vai testar se detecta os modais nessa imagem

Testa:
- Modal de Quantidade Negativa (qtd_negativa.png)
- Modal de Erro Centro de Custo (erro_centro_custo.png)
"""

import cv2
import numpy as np
import os
import sys
from datetime import datetime

def detectar_com_multiplos_niveis(template_path, screenshot_bgr, nome_modal):
    """Testa detecção com vários níveis de confidence"""

    # Carregar template
    template = cv2.imread(template_path)
    if template is None:
        print(f"❌ Erro ao carregar template: {template_path}")
        return None

    template_h, template_w = template.shape[:2]
    screen_h, screen_w = screenshot_bgr.shape[:2]

    print(f"\n{'='*70}")
    print(f"🔍 {nome_modal}")
    print(f"{'='*70}")
    print(f"📏 Template: {template_w}x{template_h}")
    print(f"📏 Screenshot: {screen_w}x{screen_h}")

    # Redimensionar se necessário
    template_scaled = template
    if template_w > screen_w or template_h > screen_h:
        scale = min(screen_w / template_w, screen_h / template_h) * 0.95
        new_w = int(template_w * scale)
        new_h = int(template_h * scale)
        template_scaled = cv2.resize(template, (new_w, new_h))
        print(f"⚠️ Template redimensionado para: {new_w}x{new_h}")

    # Template matching
    result = cv2.matchTemplate(screenshot_bgr, template_scaled, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    print(f"\n📊 SCORES:")
    print(f"-" * 70)

    # Testar múltiplos níveis
    niveis = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3]
    melhor_detectado = None

    for nivel in niveis:
        detectado = max_val >= nivel
        status = "✅ DETECTADO" if detectado else "❌ Não"
        print(f"Confidence {nivel:.0%}: Score {max_val:.2%} {status}")

        if detectado and melhor_detectado is None:
            melhor_detectado = nivel

    print(f"-" * 70)

    if melhor_detectado:
        print(f"✅ DETECTÁVEL com confidence de {melhor_detectado:.0%} ou menor")
        print(f"📍 Posição: ({max_loc[0]}, {max_loc[1]})")
    else:
        print(f"❌ NÃO DETECTÁVEL em nenhum nível testado")
        print(f"💡 Score máximo foi apenas {max_val:.2%}")

    # Criar imagem visual
    screenshot_visual = screenshot_bgr.copy()
    top_left = max_loc
    bottom_right = (top_left[0] + template_scaled.shape[1], top_left[1] + template_scaled.shape[0])

    # Cor do retângulo baseado no score
    if max_val >= 0.7:
        cor = (0, 255, 0)  # Verde - alta confiança
    elif max_val >= 0.5:
        cor = (0, 165, 255)  # Laranja - média confiança
    else:
        cor = (0, 0, 255)  # Vermelho - baixa confiança

    cv2.rectangle(screenshot_visual, top_left, bottom_right, cor, 3)

    # Texto com score
    texto = f"{nome_modal}: {max_val:.1%}"
    cv2.putText(screenshot_visual, texto, (top_left[0], top_left[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, cor, 2)

    return {
        'max_score': max_val,
        'detectado_em': melhor_detectado,
        'posicao': max_loc,
        'imagem_visual': screenshot_visual
    }

def main():
    """Função principal"""
    print("\n" + "="*70)
    print("🧪 TESTE DE DETECÇÃO DE MODAIS - ARQUIVO")
    print("="*70)

    # Obter caminho da imagem
    if len(sys.argv) > 1:
        # Imagem passada como argumento (drag and drop)
        caminho_imagem = sys.argv[1]
        print(f"\n📁 Imagem recebida: {caminho_imagem}")
    else:
        # Solicitar caminho
        print("\n📁 Digite o caminho completo da imagem:")
        print("   (Ou arraste e solte a imagem neste script)")
        caminho_imagem = input("> ").strip().strip('"')

    # Verificar se arquivo existe
    if not os.path.isfile(caminho_imagem):
        print(f"\n❌ ERRO: Arquivo não encontrado!")
        print(f"   Caminho: {caminho_imagem}")
        input("\nPressione ENTER para fechar...")
        return

    # Carregar imagem
    print(f"\n📸 Carregando imagem...")
    screenshot_bgr = cv2.imread(caminho_imagem)

    if screenshot_bgr is None:
        print(f"❌ ERRO: Não foi possível carregar a imagem!")
        print(f"   Formatos suportados: PNG, JPG, BMP")
        input("\nPressione ENTER para fechar...")
        return

    print(f"✅ Imagem carregada: {screenshot_bgr.shape[1]}x{screenshot_bgr.shape[0]}")

    # Caminhos dos templates
    base_path = os.path.dirname(os.path.abspath(__file__))

    templates = {
        'QUANTIDADE NEGATIVA': os.path.join(base_path, "informacoes", "qtd_negativa.png"),
        'ERRO CENTRO DE CUSTO': os.path.join(base_path, "informacoes", "erro_centro_custo.png")
    }

    # Testar cada template
    resultados = {}
    screenshot_final = screenshot_bgr.copy()

    for nome, caminho in templates.items():
        if os.path.isfile(caminho):
            resultado = detectar_com_multiplos_niveis(caminho, screenshot_bgr, nome)
            if resultado:
                resultados[nome] = resultado
                # Copiar marcações para imagem final
                screenshot_final = resultado['imagem_visual'].copy()
        else:
            print(f"\n⚠️ Template não encontrado: {nome}")
            print(f"   Esperado em: {caminho}")

    # Salvar imagem com marcações
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"resultado_deteccao_{timestamp}.png"
    cv2.imwrite(output_filename, screenshot_final)

    # Resumo final
    print("\n" + "="*70)
    print("📊 RESUMO FINAL")
    print("="*70)

    for nome, resultado in resultados.items():
        print(f"\n🔍 {nome}:")
        print(f"   Score máximo: {resultado['max_score']:.2%}")

        if resultado['detectado_em']:
            print(f"   ✅ DETECTÁVEL com confidence {resultado['detectado_em']:.0%}")
            print(f"   📍 Posição: ({resultado['posicao'][0]}, {resultado['posicao'][1]})")

            # Recomendação
            if resultado['max_score'] >= 0.8:
                print(f"   💡 Recomendação: Use confidence 0.7 (70%)")
            elif resultado['max_score'] >= 0.6:
                print(f"   💡 Recomendação: Use confidence 0.5 ou 0.6 (50-60%)")
            else:
                print(f"   💡 Recomendação: Use confidence {resultado['detectado_em'] - 0.1:.0%}")
        else:
            print(f"   ❌ NÃO DETECTÁVEL (score muito baixo: {resultado['max_score']:.2%})")
            print(f"   ⚠️ A imagem de referência pode estar incorreta")
            print(f"   💡 Capture um novo screenshot do modal para usar como referência")

    print(f"\n💾 Imagem com marcações salva: {output_filename}")
    print("\n" + "="*70)
    print("✅ TESTE CONCLUÍDO!")
    print("="*70)

    print("\n💡 COMO USAR OS RESULTADOS:")
    print("   1. Abra o arquivo: " + output_filename)
    print("   2. Veja onde o OpenCV marcou (retângulos coloridos)")
    print("   3. Verde = alta confiança, Laranja = média, Vermelho = baixa")
    print("   4. Se detectou mas com score baixo: diminua o confidence no código")
    print("   5. Se não detectou: capture nova imagem de referência do modal")

    input("\nPressione ENTER para fechar...")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        print(traceback.format_exc())
        input("\nPressione ENTER para fechar...")
