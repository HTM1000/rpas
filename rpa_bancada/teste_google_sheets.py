# -*- coding: utf-8 -*-
"""
Script de teste para verificar envio de dados para Google Sheets
"""
import pandas as pd
import sys
import os

# Adicionar o diretório ao path para importar o módulo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar o módulo de Google Sheets
import google_sheets_manager as gsm

# ==========================================
# CONFIGURAÇÃO DA PLANILHA DE TESTE
# ==========================================
# ID da planilha extraído da URL:
# https://docs.google.com/spreadsheets/d/1KMS-1_FY6-cU26ZlaFu5jciSHEWlmluHo-QOFbB1LFE/edit
SPREADSHEET_ID_TESTE = '1KMS-1_FY6-cU26ZlaFu5jciSHEWlmluHo-QOFbB1LFE'

# Substituir temporariamente o ID da planilha
gsm.SPREADSHEET_ID = SPREADSHEET_ID_TESTE

print("=" * 60)
print("🧪 TESTE DE ENVIO PARA GOOGLE SHEETS")
print("=" * 60)
print(f"\n📋 Planilha ID: {SPREADSHEET_ID_TESTE}")
print(f"🔗 URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID_TESTE}/edit\n")

# ==========================================
# PASSO 1: TESTAR CONEXÃO
# ==========================================
print("📡 [1/3] Testando conexão com Google Sheets...")
try:
    if gsm.testar_conexao():
        print("✅ Conexão estabelecida com sucesso!\n")
    else:
        print("❌ Falha na conexão. Verifique as credenciais.\n")
        sys.exit(1)
except Exception as e:
    print(f"❌ Erro ao conectar: {e}\n")
    sys.exit(1)

# ==========================================
# PASSO 2: CRIAR DADOS DE TESTE
# ==========================================
print("📊 [2/3] Criando dados de teste...")
df_teste = pd.DataFrame({
    'ORG.': ['M02', 'M02', 'M02'],
    'SUB.': ['MP_ALMC', 'MP_ALMC', 'STOCK'],
    'ENDEREÇO': ['A-01-01-001', 'A-01-01-002', 'B-02-03-005'],
    'ITEM': ['ITEM-12345', 'ITEM-67890', 'ITEM-11111'],
    'DESCRIÇÃO ITEM': ['Parafuso M10x50', 'Porca M10', 'Arruela Lisa'],
    'REV.': ['A', 'B', 'A'],
    'UDM PRINCIPAL': ['PC', 'PC', 'UN'],
    'EM ESTOQUE': [150, 320, 500]
})

print(f"✅ Criado DataFrame com {len(df_teste)} linhas\n")
print("📋 Prévia dos dados:")
print(df_teste.to_string(index=False))
print()

# ==========================================
# PASSO 3: ENVIAR PARA GOOGLE SHEETS
# ==========================================
print("☁️ [3/3] Enviando dados para Google Sheets...")
print("⏳ Isso pode levar alguns segundos...\n")

try:
    sucesso = gsm.enviar_para_google_sheets(df_teste)

    if sucesso:
        print("\n" + "=" * 60)
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        print("=" * 60)
        print(f"\n📊 Dados enviados com as colunas:")
        print("   1. Codigo (sequencial)")
        print("   2. Data (timestamp)")
        print("   3. ORG.")
        print("   4. SUB.")
        print("   5. ENDEREÇO")
        print("   6. ITEM")
        print("   7. DESCRIÇÃO ITEM")
        print("   8. REV.")
        print("   9. UDM PRINCIPAL")
        print("   10. EM ESTOQUE")
        print(f"\n🔗 Verifique a planilha em:")
        print(f"   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID_TESTE}/edit")
        print("\n" + "=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ FALHA NO ENVIO")
        print("=" * 60)
        print("\nPossíveis causas:")
        print("  • Credenciais inválidas ou expiradas")
        print("  • Sem permissão de escrita na planilha")
        print("  • ID da planilha incorreto")
        print("  • Problema de conexão com a internet")

except Exception as e:
    print("\n" + "=" * 60)
    print("❌ ERRO DURANTE O TESTE")
    print("=" * 60)
    print(f"\nErro: {e}")
    import traceback
    print("\nDetalhes:")
    print(traceback.format_exc())

print("\n🏁 Teste finalizado")
