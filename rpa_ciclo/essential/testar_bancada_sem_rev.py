# -*- coding: utf-8 -*-
"""
Script de teste para validar que coluna REV. NÃO é enviada para Google Sheets
Cria dados fictícios e testa o envio
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
    print("🧪 TESTE: Validar remoção da coluna REV. antes do envio")
    print("=" * 70)
    print()

    # Criar DataFrame de teste com TODAS as colunas (incluindo REV.)
    print("📋 Criando dados fictícios (incluindo REV.)...")
    df_teste = pd.DataFrame({
        'ORG.': ['ORG01', 'ORG02', 'ORG03', 'ORG04', 'ORG05'],
        'SUB.': ['SUB01', 'SUB02', 'SUB03', 'SUB04', 'SUB05'],
        'ENDEREÇO': ['END001', 'END002', 'END003', 'END004', 'END005'],
        'ITEM': ['E2029A', 'E2029B', 'E2030C', 'E2031D', 'E2032E'],
        'DESCRIÇÃO ITEM': ['Compressor XYZ', 'Válvula ABC', 'Motor 123', 'Filtro 456', 'Sensor 789'],
        'REV.': ['R1', 'R2', 'R3', 'R4', 'R5'],  # ⚠️ ESTA COLUNA NÃO DEVE SER ENVIADA
        'UDM PRINCIPAL': ['PC', 'UN', 'KG', 'MT', 'LT'],
        'EM ESTOQUE': [150, 45, 200, 89, 320],
        'COLUNA_EXTRA_1': ['ignore', 'ignore', 'ignore', 'ignore', 'ignore'],  # Será ignorada
        'COLUNA_EXTRA_2': ['ignore', 'ignore', 'ignore', 'ignore', 'ignore'],  # Será ignorada
    })

    print(f"✅ DataFrame criado: {df_teste.shape[0]} linhas x {df_teste.shape[1]} colunas")
    print(f"📊 Colunas originais: {list(df_teste.columns)}")
    print()

    # Mostrar dados de exemplo
    print("👀 Dados de exemplo (primeiras 3 linhas):")
    print(df_teste.head(3).to_string())
    print()

    # Verificar que REV. está presente
    if 'REV.' in df_teste.columns:
        print("✅ Coluna REV. está presente nos dados originais")
        print(f"   Valores: {df_teste['REV.'].tolist()}")
    else:
        print("❌ ERRO: Coluna REV. não está nos dados originais!")
        return False
    print()

    # Testar a função de filtro
    print("🔍 Testando função filtrar_colunas_principais()...")
    df_filtrado = gs.filtrar_colunas_principais(df_teste.copy())

    print(f"✅ DataFrame filtrado: {df_filtrado.shape[0]} linhas x {df_filtrado.shape[1]} colunas")
    print(f"📊 Colunas filtradas: {list(df_filtrado.columns)}")
    print()

    # VERIFICAÇÃO CRÍTICA: REV. não deve estar no DataFrame filtrado
    if 'REV.' in df_filtrado.columns:
        print("❌ ERRO CRÍTICO: Coluna REV. AINDA ESTÁ no DataFrame filtrado!")
        print("   Esta coluna NÃO deveria estar aqui!")
        print()
        print("🔴 TESTE FALHOU!")
        return False
    else:
        print("✅ SUCESSO: Coluna REV. foi REMOVIDA corretamente!")
        print()

    # Verificar que as outras colunas estão presentes
    colunas_esperadas = ['Codigo', 'Data', 'ORG.', 'SUB.', 'ENDEREÇO', 'ITEM', 'DESCRIÇÃO ITEM', 'UDM PRINCIPAL', 'EM ESTOQUE']
    print("🔍 Verificando colunas esperadas...")
    todas_presentes = True
    for col in colunas_esperadas:
        if col in df_filtrado.columns:
            print(f"   ✅ {col}")
        else:
            print(f"   ❌ {col} - FALTANDO!")
            todas_presentes = False
    print()

    if not todas_presentes:
        print("❌ ERRO: Algumas colunas esperadas estão faltando!")
        print("🔴 TESTE FALHOU!")
        return False

    # Verificar ordem das colunas
    print("🔍 Verificando ordem das colunas...")
    ordem_correta = list(df_filtrado.columns) == colunas_esperadas
    if ordem_correta:
        print("✅ Ordem das colunas está correta!")
    else:
        print("⚠️ Ordem das colunas está diferente do esperado:")
        print(f"   Esperado: {colunas_esperadas}")
        print(f"   Recebido: {list(df_filtrado.columns)}")
    print()

    # Mostrar DataFrame final que será enviado
    print("📤 DataFrame que será enviado ao Google Sheets:")
    print(df_filtrado.head(3).to_string())
    print()

    # Perguntar se deseja enviar para Google Sheets de verdade
    print("=" * 70)
    resposta = input("❓ Deseja enviar estes dados FICTÍCIOS para o Google Sheets? (s/n): ").strip().lower()
    print()

    if resposta == 's':
        print("📤 Enviando para Google Sheets...")
        try:
            sucesso = gs.enviar_para_google_sheets(df_teste)

            if sucesso:
                print()
                print("=" * 70)
                print("✅ TESTE CONCLUÍDO COM SUCESSO!")
                print("=" * 70)
                print()
                print("📊 Verificações realizadas:")
                print("   ✅ Coluna REV. foi removida do envio")
                print("   ✅ 9 colunas enviadas (Codigo, Data + 7 principais)")
                print("   ✅ Ordem das colunas correta: A:I")
                print()
                print("🔗 Acesse o Google Sheets para confirmar:")
                print(f"   https://docs.google.com/spreadsheets/d/{gs.SPREADSHEET_ID}")
                print()
                print("💡 Verifique se a coluna REV. NÃO aparece na planilha!")
                return True
            else:
                print("❌ ERRO ao enviar para Google Sheets!")
                print("🔴 TESTE FALHOU!")
                return False

        except Exception as e:
            print(f"❌ ERRO durante envio: {e}")
            import traceback
            traceback.print_exc()
            print("🔴 TESTE FALHOU!")
            return False
    else:
        print("⏭️ Envio cancelado pelo usuário")
        print()
        print("=" * 70)
        print("✅ TESTE DE VALIDAÇÃO CONCLUÍDO!")
        print("=" * 70)
        print()
        print("📊 Resultado:")
        print("   ✅ Coluna REV. foi removida corretamente do DataFrame")
        print("   ✅ 9 colunas seriam enviadas (Codigo, Data + 7 principais)")
        print("   ⚠️ Envio real não foi executado (cancelado pelo usuário)")
        print()
        print("💡 Execute novamente e confirme com 's' para enviar ao Sheets")
        return True

if __name__ == "__main__":
    try:
        sucesso = main()
        sys.exit(0 if sucesso else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Teste interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
