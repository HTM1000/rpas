# -*- coding: utf-8 -*-
"""
Teste completo do fluxo de envio para Google Sheets
Simula exatamente o que o exe faz - COM REMOÇÃO DE REV
"""

import pandas as pd

print("=" * 70)
print("🧪 TESTE COMPLETO - FLUXO DO EXE (SEM REV)")
print("=" * 70)
print()
print("Este script simula EXATAMENTE o que o exe faz:")
print("  1. Criar dados fictícios (simulando bancada Oracle COM REV)")
print("  2. Processar colunas e REMOVER REV")
print("  3. Adicionar Codigo e Data")
print("  4. Enviar para Google Sheets (7 colunas + Codigo + Data)")
print()

input("Pressione ENTER para continuar...")
print()

# 1. CRIAR DADOS FICTÍCIOS (simulando dados da bancada Oracle)
print("📊 [1/4] Criando dados fictícios da bancada...")
df_bancada = pd.DataFrame({
    'Org.': ['01', '01', '01', '01'],
    'Sub.': ['FG', 'FG', 'RM', 'RM'],
    'Endereço': ['A-01-01', 'A-01-02', 'B-01-01', 'B-01-02'],
    'Item': ['ITEM001', 'ITEM002', 'ITEM003', 'ITEM004'],
    'Descrição do Item': ['Produto Teste 1', 'Produto Teste 2', 'Matéria Prima 1', 'Matéria Prima 2'],
    'Rev.': ['01', '02', '01', '01'],  # ESTA COLUNA SERÁ REMOVIDA
    'UDM Principal': ['PC', 'PC', 'KG', 'UN'],
    'Em Estoque': [100, 250, 500, 75],
    'Coluna Extra': ['Ignorar', 'Ignorar', 'Ignorar', 'Ignorar']  # Será removida
})

print(f"✅ Dados criados: {df_bancada.shape[0]} linhas, {df_bancada.shape[1]} colunas")
print(f"   Colunas originais: {list(df_bancada.columns)}")
print()

# 2. IMPORTAR FUNÇÃO DE ENVIO
print("📦 [2/4] Importando módulo Google Sheets...")
try:
    from google_sheets_manager import enviar_para_google_sheets
    print("✅ Módulo importado com sucesso")
except ImportError as e:
    print(f"❌ Erro ao importar: {e}")
    print()
    print("💡 Certifique-se de que google_sheets_manager.py existe")
    input("Pressione ENTER para sair...")
    exit(1)

print()

# 3. SIMULAR PROCESSAMENTO (mapear e remover REV)
print("⚙️ [3/5] Processando colunas (mapeando para nomes padrão)...")

# Mapear colunas como no main.py
mapeamento = {
    'Org.': 'ORG.',
    'Sub.': 'SUB.',
    'Endereço': 'ENDEREÇO',
    'Item': 'ITEM',
    'Descrição do Item': 'DESCRIÇÃO ITEM',
    'Rev.': 'REV.',
    'UDM Principal': 'UDM PRINCIPAL',
    'Em Estoque': 'EM ESTOQUE'
}

df_processado = df_bancada.rename(columns=mapeamento)
colunas_esperadas = ['ORG.', 'SUB.', 'ENDEREÇO', 'ITEM', 'DESCRIÇÃO ITEM', 'REV.', 'UDM PRINCIPAL', 'EM ESTOQUE']
df_processado = df_processado[colunas_esperadas]

print(f"✅ Colunas mapeadas: {list(df_processado.columns)}")
print()

# REMOVER COLUNA REV (como no main.py)
print("🗑️ [4/5] Removendo coluna REV...")
if 'REV.' in df_processado.columns:
    df_processado = df_processado.drop(columns=['REV.'])
    print(f"✅ Coluna REV removida!")
    print(f"📋 Colunas finais: {list(df_processado.columns)}")
else:
    print("⚠️ Coluna REV não encontrada")

print()

# 4. ENVIAR PARA GOOGLE SHEETS
print("📤 [5/5] Enviando para Google Sheets...")
print("   (O módulo vai adicionar Codigo e Data)")
print()

try:
    # Enviar DataFrame PROCESSADO (sem REV)
    sucesso = enviar_para_google_sheets(df_processado)

    print()
    print("=" * 70)

    if sucesso:
        print("✅ ENVIO BEM-SUCEDIDO!")
        print("=" * 70)
        print()
        print("📋 O que foi enviado:")
        print(f"   • {df_processado.shape[0]} linhas de dados")
        print(f"   • {df_processado.shape[1]} colunas principais (SEM REV)")
        print(f"   • Coluna 'Codigo': 1, 2, 3, 4")
        print(f"   • Coluna 'Data': Timestamp atual")
        print(f"   • 7 colunas: {list(df_processado.columns)}")
        print()
        print("🔗 Verifique a planilha:")
        print("   https://docs.google.com/spreadsheets/d/1KMS-1_FY6-cU26ZlaFu5jciSHEWlmluHo-QOFbB1LFE")
        print()
        print("✅ IMPORTANTE: Coluna REV NÃO deve aparecer na planilha!")
    else:
        print("❌ FALHA NO ENVIO")
        print("=" * 70)
        print()
        print("Possíveis causas:")
        print("  • Token expirado (delete token.json e tente novamente)")
        print("  • Sem permissão na planilha")
        print("  • Credenciais incorretas")
        print()
        print("💡 Verifique os erros acima para mais detalhes")

    print("=" * 70)

except Exception as e:
    print()
    print("=" * 70)
    print("❌ ERRO DURANTE O TESTE")
    print("=" * 70)
    print(f"Erro: {e}")
    print()
    import traceback
    traceback.print_exc()
    print()
    print("💡 Verifique os erros acima")
    print("=" * 70)

print()
input("Pressione ENTER para sair...")
