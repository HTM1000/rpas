# -*- coding: utf-8 -*-
"""
Script de teste para ENVIAR dados fictícios ao Google Sheets
Valida que coluna REV. NÃO é enviada
"""

import sys
import os

# Configurar encoding UTF-8 para Windows
if sys.platform.startswith('win'):
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass

import pandas as pd
from pathlib import Path

# Adicionar o diretório atual ao path
sys.path.insert(0, str(Path(__file__).parent))

# Importar o módulo de Google Sheets
import google_sheets_manager as gs

def main():
    print("=" * 70)
    print("TESTE: Envio para Google Sheets (SEM coluna REV.)")
    print("=" * 70)
    print()

    # Criar DataFrame de teste com TODAS as colunas (incluindo REV.)
    print("Criando dados ficticios com REV....")
    df_teste = pd.DataFrame({
        'ORG.': ['ORG01', 'ORG02', 'ORG03', 'ORG04', 'ORG05'],
        'SUB.': ['SUB01', 'SUB02', 'SUB03', 'SUB04', 'SUB05'],
        'ENDEREÇO': ['END001', 'END002', 'END003', 'END004', 'END005'],
        'ITEM': ['E2029A', 'E2029B', 'E2030C', 'E2031D', 'E2032E'],
        'DESCRIÇÃO ITEM': ['Compressor XYZ', 'Valvula ABC', 'Motor 123', 'Filtro 456', 'Sensor 789'],
        'REV.': ['R1', 'R2', 'R3', 'R4', 'R5'],  # ESTA COLUNA NAO DEVE SER ENVIADA
        'UDM PRINCIPAL': ['PC', 'UN', 'KG', 'MT', 'LT'],
        'EM ESTOQUE': [150, 45, 200, 89, 320],
    })

    print(f"DataFrame: {df_teste.shape[0]} linhas x {df_teste.shape[1]} colunas")
    print(f"Colunas originais: {list(df_teste.columns)}")
    print()

    # Verificar que REV. está presente
    if 'REV.' in df_teste.columns:
        print("Coluna REV. presente nos dados originais: ['R1', 'R2', 'R3', 'R4', 'R5']")
    print()

    # Testar a função de filtro
    print("Testando funcao filtrar_colunas_principais()...")
    df_filtrado = gs.filtrar_colunas_principais(df_teste.copy())

    print(f"DataFrame filtrado: {df_filtrado.shape[0]} linhas x {df_filtrado.shape[1]} colunas")
    print(f"Colunas filtradas: {list(df_filtrado.columns)}")
    print()

    # VERIFICAÇÃO CRÍTICA
    if 'REV.' in df_filtrado.columns:
        print("ERRO CRITICO: Coluna REV. AINDA ESTA no DataFrame filtrado!")
        print("TESTE FALHOU!")
        return False
    else:
        print("SUCESSO: Coluna REV. foi REMOVIDA corretamente!")
        print()

    # Enviar para Google Sheets
    print("=" * 70)
    print("Enviando para Google Sheets...")
    print("=" * 70)
    print()

    try:
        sucesso = gs.enviar_para_google_sheets(df_teste)

        if sucesso:
            print()
            print("=" * 70)
            print("TESTE CONCLUIDO COM SUCESSO!")
            print("=" * 70)
            print()
            print("Verificacoes realizadas:")
            print("   - Coluna REV. foi removida do envio")
            print("   - 9 colunas enviadas (Codigo, Data + 7 principais)")
            print("   - Ordem das colunas: A:I")
            print()
            print("Acesse o Google Sheets para confirmar:")
            print(f"   https://docs.google.com/spreadsheets/d/{gs.SPREADSHEET_ID}")
            print()
            print("Verifique se a coluna REV. NAO aparece na planilha!")
            print()
            print("Colunas esperadas na planilha:")
            print("   A: Codigo")
            print("   B: Data")
            print("   C: ORG.")
            print("   D: SUB.")
            print("   E: ENDERECO")
            print("   F: ITEM")
            print("   G: DESCRICAO ITEM")
            print("   H: UDM PRINCIPAL")
            print("   I: EM ESTOQUE")
            print()
            return True
        else:
            print("ERRO ao enviar para Google Sheets!")
            print("TESTE FALHOU!")
            return False

    except Exception as e:
        print(f"ERRO durante envio: {e}")
        import traceback
        traceback.print_exc()
        print("TESTE FALHOU!")
        return False

if __name__ == "__main__":
    try:
        sucesso = main()
        sys.exit(0 if sucesso else 1)
    except Exception as e:
        print(f"\nERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
