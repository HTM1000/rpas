# -*- coding: utf-8 -*-
"""
Script para ativar/desativar MODO TESTE no RPA_Ciclo
"""
import os
import sys

def toggle_modo_teste():
    script_path = "main_ciclo.py"

    if not os.path.exists(script_path):
        print(f"[ERRO] Arquivo {script_path} nao encontrado!")
        return

    # Ler arquivo
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Verificar estado atual
    if "MODO_TESTE = False" in content:
        # Ativar modo teste
        new_content = content.replace(
            "MODO_TESTE = False  # True = simula movimentos sem pyautogui | False = PRODUÇÃO",
            "MODO_TESTE = True  # True = simula movimentos sem pyautogui | False = PRODUÇÃO"
        )
        new_content = new_content.replace(
            "PARAR_QUANDO_VAZIO = False  # True = para quando vazio (teste) | False = continua rodando (PRODUÇÃO)",
            "PARAR_QUANDO_VAZIO = True  # True = para quando vazio (teste) | False = continua rodando (PRODUÇÃO)"
        )
        print("[OK] MODO TESTE ATIVADO!")
        print("   - MODO_TESTE = True")
        print("   - PARAR_QUANDO_VAZIO = True")
    elif "MODO_TESTE = True" in content:
        # Desativar modo teste
        new_content = content.replace(
            "MODO_TESTE = True  # True = simula movimentos sem pyautogui | False = PRODUÇÃO",
            "MODO_TESTE = False  # True = simula movimentos sem pyautogui | False = PRODUÇÃO"
        )
        new_content = new_content.replace(
            "PARAR_QUANDO_VAZIO = True  # True = para quando vazio (teste) | False = continua rodando (PRODUÇÃO)",
            "PARAR_QUANDO_VAZIO = False  # True = para quando vazio (teste) | False = continua rodando (PRODUÇÃO)"
        )
        print("[OK] MODO PRODUCAO ATIVADO!")
        print("   - MODO_TESTE = False")
        print("   - PARAR_QUANDO_VAZIO = False")
    else:
        print("[ERRO] Nao foi possivel identificar o modo atual!")
        return

    # Salvar
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"\nArquivo {script_path} atualizado!")
    print("\nIMPORTANTE: Se estiver usando o .exe, precisa recompilar!")

if __name__ == "__main__":
    toggle_modo_teste()
    input("\nPressione ENTER para fechar...")
