#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script Python para build do RPA_Ciclo
Alternativa ao build.bat - mais confiável
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_separator(char="=", length=60):
    """Imprime separador"""
    print(char * length)

def print_header(title):
    """Imprime cabeçalho"""
    print_separator()
    print(f"   {title}")
    print_separator()
    print()

def check_python():
    """Verifica versão do Python"""
    print("Verificando Python...")
    print(f"✓ Python {sys.version}")
    print()

def install_dependencies():
    """Instala dependências"""
    print_header("Instalando Dependências")

    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True)
        print("\n✓ Dependências instaladas com sucesso\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Erro ao instalar dependências: {e}\n")
        return False

def clean_build():
    """Limpa builds anteriores"""
    print_header("Limpando Builds Anteriores")

    folders = ["build", "dist", "__pycache__"]
    for folder in folders:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
                print(f"✓ Removido: {folder}")
            except Exception as e:
                print(f"⚠ Erro ao remover {folder}: {e}")

    print()

def run_pyinstaller():
    """Executa PyInstaller"""
    print_header("Gerando Executável")

    try:
        # Usar python -m PyInstaller para garantir que encontre
        subprocess.run([
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "RPA_Ciclo.spec"
        ], check=True)

        print("\n✓ PyInstaller executado com sucesso\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Erro ao executar PyInstaller: {e}\n")
        return False

def copy_files():
    """Prepara arquivos e documentação"""
    print_header("Preparando Documentação")

    # SEGURANÇA: NÃO copiar CredenciaisOracle.json
    # Ele fica DENTRO do executável (embedded)
    print("🔒 SEGURANÇA:")
    print("  ✓ CredenciaisOracle.json está EMBEDDED no executável")
    print("  ✓ Dados sensíveis NÃO ficam visíveis")
    print("  ✓ Cliente não terá acesso às credenciais")
    print("  ✓ Apenas token.json será criado (OK para cliente)")
    print()

    # Criar README
    readme_content = """RPA CICLO - EXECUTAVEL STANDALONE
================================

🔒 SEGURANÇA:
- CredenciaisOracle.json está EMBEDDED no executável
- Dados sensíveis NÃO ficam visíveis
- Cliente não tem acesso às credenciais OAuth
- Apenas token.json será criado (gerado pelo usuário)

PRIMEIRA EXECUCAO:
1. Execute RPA_Ciclo.exe
2. Faça login com Google quando solicitado
3. Autorize acesso ao Google Sheets
4. Um arquivo token.json será criado na mesma pasta

EXECUCAO:
- Clique em "🎯 Ciclo Único" para executar uma vez
- Clique em "🔄 Modo Contínuo" para repetir a cada 30 min
- Clique em "⏹️ Parar RPA" para interromper

ARQUIVO GERADO:
- token.json (gerado após primeiro login - pode ficar visível)

LOGS:
- rpa_ciclo.log (arquivo local)
- Google Sheets - Aba "Ciclo Automacao"

RECURSOS:
- Botão "📂 Abrir Logs" - Abre pasta de logs
- Botão "☁️ Google Sheets" - Abre planilha
- Botão "❓ Ajuda" - Ajuda detalhada

Versão: 2.0
Desenvolvido para automação Oracle
"""

    try:
        with open("dist/LEIA-ME.txt", "w", encoding="utf-8") as f:
            f.write(readme_content)
        print("✓ Criado: LEIA-ME.txt")
    except Exception as e:
        print(f"⚠ Erro ao criar LEIA-ME.txt: {e}")

    print()

def verify_build():
    """Verifica se build foi bem-sucedido"""
    exe_path = Path("dist/RPA_Ciclo.exe")

    if exe_path.exists():
        print_header("BUILD CONCLUÍDO COM SUCESSO!")

        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"✓ Executável criado: {exe_path}")
        print(f"✓ Tamanho: {size_mb:.2f} MB")
        print()

        print("Conteúdo da pasta dist:")
        print_separator("-")
        for item in Path("dist").iterdir():
            if item.is_file():
                size = item.stat().st_size / 1024
                print(f"  {item.name} ({size:.1f} KB)")
        print_separator("-")
        print()

        print("PRONTO PARA USAR!")
        print("Execute: dist\\RPA_Ciclo.exe")
        print()

        return True
    else:
        print_header("ERRO NO BUILD!")
        print("✗ Executável não foi criado")
        print()
        print("DICAS:")
        print("- Verifique se todos os arquivos estão na pasta")
        print("- Verifique se Logo.png, Tecumseh.png, Topo.png existem")
        print("- Verifique se config.json existe")
        print("- Tente executar: python RPA_Ciclo_GUI.py")
        print()

        return False

def main():
    """Função principal"""
    print()
    print_header("RPA CICLO - BUILD DO EXECUTÁVEL")

    # Verificar se está na pasta correta
    if not os.path.exists("RPA_Ciclo_GUI.py"):
        print("✗ ERRO: Execute este script na pasta rpa_ciclo")
        print("  (onde está o arquivo RPA_Ciclo_GUI.py)")
        print()
        input("Pressione ENTER para sair...")
        return 1

    # 1. Verificar Python
    check_python()

    # 2. Instalar dependências
    if not install_dependencies():
        input("Pressione ENTER para sair...")
        return 1

    # 3. Limpar builds anteriores
    clean_build()

    # 4. Executar PyInstaller
    if not run_pyinstaller():
        input("Pressione ENTER para sair...")
        return 1

    # 5. Copiar arquivos
    copy_files()

    # 6. Verificar resultado
    success = verify_build()

    # Abrir pasta dist se sucesso
    if success and sys.platform == "win32":
        try:
            os.startfile("dist")
        except Exception:
            pass

    input("\nPressione ENTER para sair...")
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
