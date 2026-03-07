"""
Script de Teste - Detecção de Modais do Oracle

Uso:
1. Abra o Oracle com o modal que quer testar visível na tela
2. Execute este script
3. O script vai capturar a tela e tentar detectar os modais

Testa:
- Modal de Quantidade Negativa (qtd_negativa.png)
- Modal de Erro Centro de Custo (erro_centro_custo.png)
"""

import cv2
import numpy as np
from PIL import ImageGrab
import os
import sys
import time
from datetime import datetime

def detectar_imagem_com_debug(caminho_template, screenshot_bgr, nome_teste, confidence_levels=None):
    """
    Tenta detectar uma imagem template em um screenshot com múltiplos níveis de confidence

    Args:
        caminho_template: Caminho da imagem template (modal de referência)
        screenshot_bgr: Screenshot da tela em formato BGR (OpenCV)
        nome_teste: Nome do teste para os logs
        confidence_levels: Lista de níveis de confidence para testar (padrão: [0.9, 0.8, 0.7, 0.6, 0.5])

    Returns:
        dict: Resultados da detecção
    """
    if confidence_levels is None:
        confidence_levels = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4]

    # Verificar se template existe
    if not os.path.isfile(caminho_template):
        print(f"❌ Imagem não encontrada: {caminho_template}")
        return None

    # Carregar template
    template = cv2.imread(caminho_template)
    if template is None:
        print(f"❌ Erro ao carregar imagem: {caminho_template}")
        return None

    template_h, template_w = template.shape[:2]
    screen_h, screen_w = screenshot_bgr.shape[:2]

    print(f"\n{'='*70}")
    print(f"🔍 TESTE: {nome_teste}")
    print(f"{'='*70}")
    print(f"📁 Template: {os.path.basename(caminho_template)}")
    print(f"📏 Dimensões Template: {template_w}x{template_h}")
    print(f"📏 Dimensões Tela: {screen_w}x{screen_h}")
    print(f"\n🎯 Testando com diferentes níveis de confidence...")
    print(f"-" * 70)

    # Verificar se template precisa ser redimensionado
    template_scaled = template
    if template_w > screen_w or template_h > screen_h:
        scale = min(screen_w / template_w, screen_h / template_h) * 0.95
        new_w = int(template_w * scale)
        new_h = int(template_h * scale)
        template_scaled = cv2.resize(template, (new_w, new_h))
        print(f"⚠️ Template redimensionado: {template_w}x{template_h} -> {new_w}x{new_h}")
        print(f"-" * 70)

    resultados = []
    melhor_resultado = None

    # Testar cada nível de confidence
    for conf in confidence_levels:
        # Fazer template matching
        result = cv2.matchTemplate(screenshot_bgr, template_scaled, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        detectado = max_val >= conf
        status = "✅ DETECTADO" if detectado else "❌ Não detectado"

        print(f"Confidence {conf:.0%}: Score {max_val:.2%} - {status}")

        resultado = {
            'confidence_threshold': conf,
            'score': max_val,
            'detectado': detectado,
            'posicao': max_loc
        }
        resultados.append(resultado)

        # Guardar melhor resultado
        if melhor_resultado is None or max_val > melhor_resultado['score']:
            melhor_resultado = resultado

    print(f"-" * 70)
    print(f"🏆 Melhor Score: {melhor_resultado['score']:.2%}")
    print(f"📍 Posição: x={melhor_resultado['posicao'][0]}, y={melhor_resultado['posicao'][1]}")

    # Criar imagem visual mostrando onde detectou
    screenshot_visual = screenshot_bgr.copy()

    # Desenhar retângulo vermelho onde encontrou (mesmo que score seja baixo)
    top_left = melhor_resultado['posicao']
    bottom_right = (top_left[0] + template_scaled.shape[1], top_left[1] + template_scaled.shape[0])
    cv2.rectangle(screenshot_visual, top_left, bottom_right, (0, 0, 255), 3)

    # Adicionar texto com o score
    texto = f"Score: {melhor_resultado['score']:.2%}"
    cv2.putText(screenshot_visual, texto, (top_left[0], top_left[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    # Salvar imagem de debug
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"debug_{nome_teste}_{timestamp}.png"
    cv2.imwrite(nome_arquivo, screenshot_visual)
    print(f"💾 Debug salvo: {nome_arquivo}")

    return {
        'template': os.path.basename(caminho_template),
        'melhor_score': melhor_resultado['score'],
        'posicao': melhor_resultado['posicao'],
        'detectado_em': [r for r in resultados if r['detectado']],
        'todos_resultados': resultados,
        'imagem_debug': nome_arquivo
    }

def main():
    """Função principal"""
    print("\n" + "="*70)
    print("🧪 TESTE DE DETECÇÃO DE MODAIS DO ORACLE")
    print("="*70)
    print("\nINSTRUÇÕES:")
    print("1. Abra o Oracle com o modal visível na tela")
    print("2. Pressione ENTER para iniciar")
    print("3. Você terá 3 segundos para posicionar a tela do Oracle")
    print("4. O script vai capturar e testar automaticamente")
    print("\nPressione ENTER quando estiver pronto...")
    input()

    # Countdown de 3 segundos para dar tempo de posicionar a tela
    print("\n⏳ Aguardando 3 segundos para você posicionar a tela do Oracle...")
    for i in range(3, 0, -1):
        print(f"   {i}...", flush=True)
        time.sleep(1)
    print("   📸 Capturando AGORA!")

    # Capturar screenshot da tela
    screenshot = ImageGrab.grab()
    screenshot_np = np.array(screenshot)
    screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
    print("✅ Tela capturada!")

    # Salvar screenshot original
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_filename = f"screenshot_teste_{timestamp}.png"
    cv2.imwrite(screenshot_filename, screenshot_bgr)
    print(f"💾 Screenshot salvo: {screenshot_filename}")

    # Caminhos das imagens
    base_path = os.path.dirname(os.path.abspath(__file__))

    templates = [
        {
            'caminho': os.path.join(base_path, "informacoes", "qtd_negativa.png"),
            'nome': "QUANTIDADE_NEGATIVA",
            'description': "Modal de quantidade negativa"
        },
        {
            'caminho': os.path.join(base_path, "informacoes", "erro_centro_custo.png"),
            'nome': "ERRO_CENTRO_CUSTO",
            'description': "Modal de erro centro de custo"
        }
    ]

    # Testar cada template
    resultados_finais = []

    for template_info in templates:
        if os.path.isfile(template_info['caminho']):
            resultado = detectar_imagem_com_debug(
                caminho_template=template_info['caminho'],
                screenshot_bgr=screenshot_bgr,
                nome_teste=template_info['nome']
            )
            if resultado:
                resultado['description'] = template_info['description']
                resultados_finais.append(resultado)
        else:
            print(f"\n⚠️ Template não encontrado: {template_info['nome']}")
            print(f"   Caminho: {template_info['caminho']}")

    # Resumo final
    print("\n" + "="*70)
    print("📊 RESUMO FINAL")
    print("="*70)

    for resultado in resultados_finais:
        print(f"\n🔍 {resultado['description'].upper()}")
        print(f"   Template: {resultado['template']}")
        print(f"   Melhor Score: {resultado['melhor_score']:.2%}")

        if resultado['detectado_em']:
            print(f"   ✅ DETECTADO nos seguintes níveis:")
            for det in resultado['detectado_em']:
                print(f"      - Confidence {det['confidence_threshold']:.0%}: Score {det['score']:.2%}")
        else:
            print(f"   ❌ NÃO DETECTADO em nenhum nível testado")
            print(f"   💡 Sugestões:")
            print(f"      - Score foi {resultado['melhor_score']:.2%}")
            if resultado['melhor_score'] >= 0.3:
                print(f"      - Score razoável! Tente confidence de {resultado['melhor_score'] - 0.05:.0%}")
            else:
                print(f"      - Score muito baixo! A imagem de referência pode estar incorreta")
            print(f"      - Verifique a imagem de debug: {resultado['imagem_debug']}")

        print(f"   📍 Posição encontrada: x={resultado['posicao'][0]}, y={resultado['posicao'][1]}")
        print(f"   💾 Debug: {resultado['imagem_debug']}")

    print("\n" + "="*70)
    print("✅ TESTE CONCLUÍDO!")
    print("="*70)
    print("\n📁 Arquivos gerados:")
    print(f"   - {screenshot_filename} (screenshot original)")
    for resultado in resultados_finais:
        print(f"   - {resultado['imagem_debug']} (debug com marcação)")

    print("\n💡 PRÓXIMOS PASSOS:")
    print("   1. Abra as imagens de debug para ver onde o OpenCV tentou detectar")
    print("   2. Se o score foi bom (>70%) mas não detectou, diminua o confidence")
    print("   3. Se o score foi baixo (<50%), a imagem de referência pode estar errada")
    print("   4. Compare a imagem de referência com o screenshot capturado")

    print("\nPressione ENTER para fechar...")
    input()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        print(traceback.format_exc())
        print("\nPressione ENTER para fechar...")
        input()
