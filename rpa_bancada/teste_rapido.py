# -*- coding: utf-8 -*-
"""
Teste rápido sem emojis
"""
import pandas as pd
from google_sheets_manager import enviar_para_google_sheets

print("=" * 70)
print("TESTE DE ENVIO SEM REV")
print("=" * 70)
print()

# Criar DataFrame de teste (7 colunas - SEM REV)
df = pd.DataFrame({
    'ORG.': ['01', '01', '01', '01'],
    'SUB.': ['FG', 'FG', 'RM', 'RM'],
    'ENDEREÇO': ['A-01-01', 'A-01-02', 'B-01-01', 'B-01-02'],
    'ITEM': ['ITEM001', 'ITEM002', 'ITEM003', 'ITEM004'],
    'DESCRIÇÃO ITEM': ['Produto Teste 1', 'Produto Teste 2', 'Materia Prima 1', 'Materia Prima 2'],
    'UDM PRINCIPAL': ['PC', 'PC', 'KG', 'UN'],
    'EM ESTOQUE': [100, 250, 500, 75]
})

print("[TESTE] DataFrame criado:")
print(f"  Linhas: {df.shape[0]}")
print(f"  Colunas: {df.shape[1]}")
print(f"  Nomes: {list(df.columns)}")
print()

print("[IMPORTANTE] Coluna REV NAO esta presente!")
print()

print("[TESTE] Enviando para Google Sheets...")
print()

try:
    sucesso = enviar_para_google_sheets(df)

    print()
    print("=" * 70)
    if sucesso:
        print("RESULTADO: SUCESSO!")
        print("=" * 70)
        print()
        print("Verifique a planilha:")
        print("https://docs.google.com/spreadsheets/d/1KMS-1_FY6-cU26ZlaFu5jciSHEWlmluHo-QOFbB1LFE")
        print()
        print("Deve conter 9 colunas:")
        print("  1. Codigo")
        print("  2. Data")
        print("  3. ORG.")
        print("  4. SUB.")
        print("  5. ENDERECO")
        print("  6. ITEM")
        print("  7. DESCRICAO ITEM")
        print("  8. UDM PRINCIPAL")
        print("  9. EM ESTOQUE")
        print()
        print("IMPORTANTE: Coluna REV NAO deve aparecer!")
    else:
        print("RESULTADO: FALHA")
        print("=" * 70)
        print("Verifique os logs acima para detalhes")

    print("=" * 70)

except Exception as e:
    print()
    print("=" * 70)
    print("ERRO DURANTE O TESTE")
    print("=" * 70)
    print(f"Tipo: {type(e).__name__}")
    print(f"Mensagem: {e}")
    import traceback
    traceback.print_exc()
    print("=" * 70)
