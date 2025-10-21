# -*- coding: utf-8 -*-
"""
Script para verificar se todas as dependências do RPA_Bancada estão instaladas
"""

import sys

def verificar_dependencias():
    """Verifica se todas as dependências necessárias estão instaladas"""

    print("=" * 60)
    print("VERIFICAÇÃO DE DEPENDÊNCIAS DO RPA_BANCADA")
    print("=" * 60)
    print()

    dependencias = {
        'pandas': 'Processamento de dados (DataFrame)',
        'pyperclip': 'Manipulação de clipboard',
        'pyautogui': 'Automação de mouse/teclado',
        'pygetwindow': 'Foco de janelas (opcional)',
        'openpyxl': 'Salvar arquivos Excel',
        'google.auth': 'Autenticação Google Sheets',
        'googleapiclient': 'API do Google Sheets'
    }

    instaladas = []
    faltantes = []
    opcionais_faltantes = []

    for modulo, descricao in dependencias.items():
        try:
            if '.' in modulo:
                # Para módulos com subpacotes, usar __import__ diretamente
                __import__(modulo)
            else:
                __import__(modulo)

            print(f"[OK] {modulo:20s} - {descricao}")
            instaladas.append(modulo)

        except ImportError:
            if modulo == 'pygetwindow':
                print(f"[OPT] {modulo:20s} - {descricao} (OPCIONAL - nao critico)")
                opcionais_faltantes.append(modulo)
            else:
                print(f"[ERR] {modulo:20s} - {descricao}")
                faltantes.append(modulo)

    print()
    print("=" * 60)
    print("RESUMO")
    print("=" * 60)
    print(f"[OK] Instaladas: {len(instaladas)}")
    print(f"[OPT] Opcionais faltantes: {len(opcionais_faltantes)}")
    print(f"[ERR] Faltantes criticas: {len(faltantes)}")
    print()

    if faltantes:
        print("Para instalar as dependencias faltantes, execute:")
        print()
        print(f"   pip install {' '.join(faltantes)}")
        print()
        return False
    elif opcionais_faltantes:
        print("Todas as dependencias criticas estao instaladas!")
        print()
        print("Dependencias opcionais faltantes (nao impedem funcionamento):")
        print(f"   pip install {' '.join(opcionais_faltantes)}")
        print()
        return True
    else:
        print("Todas as dependencias estao instaladas!")
        print()
        return True

if __name__ == "__main__":
    sucesso = verificar_dependencias()

    if sucesso:
        print("=" * 60)
        print("Sistema pronto para executar RPA_Bancada!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("=" * 60)
        print("Instale as dependencias antes de executar RPA_Bancada")
        print("=" * 60)
        sys.exit(1)
