# -*- coding: utf-8 -*-
"""
Script helper para ativar/desativar MODO_TESTE no RPA_Oracle.py
Execute este script antes de gerar o executável para testar
"""

import os

def alternar_modo_teste():
    arquivo = "RPA_Oracle.py"

    if not os.path.exists(arquivo):
        print(f"❌ Arquivo {arquivo} não encontrado!")
        return

    with open(arquivo, 'r', encoding='utf-8') as f:
        conteudo = f.read()

    # Verificar estado atual
    if "MODO_TESTE = False" in conteudo:
        novo_conteudo = conteudo.replace("MODO_TESTE = False", "MODO_TESTE = True")
        novo_estado = "ATIVADO"
    elif "MODO_TESTE = True" in conteudo:
        novo_conteudo = conteudo.replace("MODO_TESTE = True", "MODO_TESTE = False")
        novo_estado = "DESATIVADO"
    else:
        print("❌ Não foi possível encontrar a variável MODO_TESTE no arquivo!")
        return

    # Salvar alteração
    with open(arquivo, 'w', encoding='utf-8') as f:
        f.write(novo_conteudo)

    print(f"✅ MODO_TESTE foi {novo_estado} com sucesso!")
    print(f"\n📝 Agora você pode:")
    if novo_estado == "ATIVADO":
        print("   1. Executar o RPA_Oracle.py diretamente (python RPA_Oracle.py)")
        print("   2. Ou gerar o executável (python -m PyInstaller RPA_Oracle.spec --noconfirm)")
        print("\n⚠️  No modo teste, o robô NÃO preencherá o Oracle, apenas testará a lógica!")
    else:
        print("   1. Gerar o executável para produção (python -m PyInstaller RPA_Oracle.spec --noconfirm)")
        print("\n✅ Modo produção: o robô preencherá normalmente no Oracle")

if __name__ == "__main__":
    alternar_modo_teste()
