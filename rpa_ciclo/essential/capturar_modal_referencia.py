"""
Script para Capturar Modal de Referência

Uso:
1. Abra o Oracle com o modal visível na tela
2. Execute este script
3. Clique e arraste para selecionar APENAS o modal
4. A imagem será salva automaticamente

Este script ajuda a capturar a imagem de referência perfeita para detecção.
"""

import cv2
import numpy as np
from PIL import ImageGrab
import tkinter as tk
from tkinter import messagebox
import os

# Variáveis globais para seleção
start_x = start_y = end_x = end_y = 0
selecting = False
screenshot = None
screenshot_display = None
window = None
canvas = None

def mouse_callback(event, x, y, flags, param):
    """Callback do mouse para seleção de área"""
    global start_x, start_y, end_x, end_y, selecting, screenshot_display

    if event == cv2.EVENT_LBUTTONDOWN:
        # Início da seleção
        selecting = True
        start_x, start_y = x, y
        end_x, end_y = x, y

    elif event == cv2.EVENT_MOUSEMOVE:
        if selecting:
            # Atualizar fim da seleção
            end_x, end_y = x, y

    elif event == cv2.EVENT_LBUTTONUP:
        # Fim da seleção
        selecting = False
        end_x, end_y = x, y

def capturar_e_recortar():
    """Captura tela e permite recortar o modal"""
    global screenshot, screenshot_display

    print("\n" + "="*70)
    print("📸 CAPTURA DE MODAL DE REFERÊNCIA")
    print("="*70)
    print("\nINSTRUÇÕES:")
    print("1. Abra o Oracle com o modal VISÍVEL na tela")
    print("2. Pressione ENTER para capturar a tela")
    print("3. Clique e ARRASTE para selecionar APENAS o modal")
    print("4. Pressione ENTER para confirmar")
    print("5. Ou pressione ESC para cancelar")
    print("\n⚠️ IMPORTANTE:")
    print("   - Selecione APENAS o modal (não a tela toda)")
    print("   - Inclua bordas e título do modal")
    print("   - Não inclua o fundo escuro ao redor")
    print("\nPressione ENTER quando estiver pronto...")
    input()

    # Capturar tela
    print("\n📸 Capturando tela...")
    screenshot = ImageGrab.grab()
    screenshot_np = np.array(screenshot)
    screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
    print("✅ Tela capturada!")

    # Criar cópia para exibição
    screenshot_display = screenshot_bgr.copy()

    # Criar janela
    print("\n🖱️ Use o mouse para selecionar o modal:")
    print("   - Clique e ARRASTE para criar retângulo")
    print("   - Pressione ENTER quando terminar")
    print("   - Pressione ESC para cancelar")

    cv2.namedWindow("Selecione o Modal - ENTER para confirmar, ESC para cancelar", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("Selecione o Modal - ENTER para confirmar, ESC para cancelar", mouse_callback)

    while True:
        # Copiar screenshot original
        display = screenshot_bgr.copy()

        # Desenhar retângulo de seleção
        if start_x != end_x and start_y != end_y:
            cv2.rectangle(display, (start_x, start_y), (end_x, end_y), (0, 255, 0), 2)

            # Adicionar dimensões
            width = abs(end_x - start_x)
            height = abs(end_y - start_y)
            texto = f"{width}x{height}"
            cv2.putText(display, texto, (min(start_x, end_x), min(start_y, end_y) - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow("Selecione o Modal - ENTER para confirmar, ESC para cancelar", display)

        key = cv2.waitKey(1) & 0xFF

        # ESC para cancelar
        if key == 27:
            print("\n❌ Cancelado pelo usuário")
            cv2.destroyAllWindows()
            return None

        # ENTER para confirmar
        elif key == 13:
            if start_x == end_x or start_y == end_y:
                print("\n⚠️ Selecione uma área válida!")
                continue
            break

    cv2.destroyAllWindows()

    # Recortar área selecionada
    x1 = min(start_x, end_x)
    y1 = min(start_y, end_y)
    x2 = max(start_x, end_x)
    y2 = max(start_y, end_y)

    modal_recortado = screenshot_bgr[y1:y2, x1:x2]

    print(f"\n✅ Área selecionada: {x2-x1}x{y2-y1} pixels")

    return modal_recortado

def main():
    """Função principal"""
    # Capturar e recortar
    modal = capturar_e_recortar()

    if modal is None:
        input("\nPressione ENTER para fechar...")
        return

    # Escolher qual modal salvar
    print("\n" + "="*70)
    print("💾 SALVAR IMAGEM DE REFERÊNCIA")
    print("="*70)
    print("\nQual modal você capturou?")
    print("1 - Quantidade Negativa")
    print("2 - Erro Centro de Custo")
    print("3 - Outro (especificar nome)")
    print("\nDigite o número: ", end="")

    escolha = input().strip()

    base_path = os.path.dirname(os.path.abspath(__file__))
    informacoes_path = os.path.join(base_path, "informacoes")

    # Criar pasta informacoes se não existir
    if not os.path.exists(informacoes_path):
        os.makedirs(informacoes_path)
        print(f"✅ Pasta criada: {informacoes_path}")

    if escolha == "1":
        filename = "qtd_negativa.png"
        descricao = "Quantidade Negativa"
    elif escolha == "2":
        filename = "erro_centro_custo.png"
        descricao = "Erro Centro de Custo"
    elif escolha == "3":
        print("Digite o nome do arquivo (sem .png): ", end="")
        custom_name = input().strip()
        filename = f"{custom_name}.png"
        descricao = custom_name
    else:
        print("\n❌ Opção inválida!")
        input("Pressione ENTER para fechar...")
        return

    caminho_completo = os.path.join(informacoes_path, filename)

    # Verificar se arquivo já existe
    if os.path.exists(caminho_completo):
        print(f"\n⚠️ Arquivo já existe: {filename}")
        print("Deseja sobrescrever? (S/N): ", end="")
        resposta = input().strip().upper()
        if resposta != "S":
            print("❌ Operação cancelada")
            input("Pressione ENTER para fechar...")
            return

        # Fazer backup do arquivo antigo
        backup_name = filename.replace(".png", "_backup.png")
        backup_path = os.path.join(informacoes_path, backup_name)
        os.rename(caminho_completo, backup_path)
        print(f"💾 Backup criado: {backup_name}")

    # Salvar imagem
    cv2.imwrite(caminho_completo, modal)
    print(f"\n✅ Imagem salva com sucesso!")
    print(f"📁 Local: {caminho_completo}")
    print(f"📏 Dimensões: {modal.shape[1]}x{modal.shape[0]} pixels")

    # Exibir prévia
    print("\n👁️ Exibindo prévia da imagem salva...")
    print("   (Feche a janela para continuar)")
    cv2.imshow(f"Imagem Salva - {descricao}", modal)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # Testar detecção imediatamente
    print("\n" + "="*70)
    print("🧪 TESTAR DETECÇÃO AGORA?")
    print("="*70)
    print("\nDeseja testar a detecção da imagem que acabou de capturar?")
    print("(S/N): ", end="")

    resposta = input().strip().upper()

    if resposta == "S":
        print("\n🔄 Executando teste de detecção...")
        print("   Aguarde...")

        # Importar e executar teste
        try:
            import subprocess
            subprocess.run(["python", "testar_deteccao_modais.py"], cwd=base_path)
        except Exception as e:
            print(f"⚠️ Não foi possível executar teste automaticamente: {e}")
            print("\nExecute manualmente:")
            print("   python testar_deteccao_modais.py")

    print("\n" + "="*70)
    print("✅ CONCLUÍDO!")
    print("="*70)
    print(f"\n📋 Resumo:")
    print(f"   - Modal capturado: {descricao}")
    print(f"   - Arquivo: {filename}")
    print(f"   - Localização: informacoes/")
    print(f"   - Dimensões: {modal.shape[1]}x{modal.shape[0]}")
    print("\n💡 Próximos passos:")
    print("   1. Execute: python testar_deteccao_modais.py")
    print("   2. Veja o score de detecção")
    print("   3. Se score > 50%: ajuste confidence no código")
    print("   4. Faça o BUILD: BUILD_GENESYS.bat")

    input("\nPressione ENTER para fechar...")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        print(traceback.format_exc())
        input("\nPressione ENTER para fechar...")
