# -*- coding: utf-8 -*-
"""
TESTE - Google Sheets RPA Inventário
Testa busca de dados e atualização de status
"""

import sys
import google_sheets_inventario as gsheets

print("=" * 80)
print("TESTE - GOOGLE SHEETS RPA INVENTÁRIO")
print("=" * 80)
print()

# ============================================================================
# CONFIGURAÇÃO DO TESTE
# ============================================================================
INVENTARIO = "2025_12_ALMOX_RECEB2_RAW_TEST"  # ← ALTERE AQUI para o nome do seu inventário
TIPO_CONTAGEM = "primeira"  # "primeira" ou "segunda"
TIPO_PLANILHA = "bc2"  # "bc1" ou "bc2"
ROBO_ID = "TESTE-PC"

print(f"📋 Inventário: {INVENTARIO}")
print(f"📊 Tipo Contagem: {TIPO_CONTAGEM}")
print(f"📁 Planilha: {TIPO_PLANILHA}")
print(f"🤖 Robô ID: {ROBO_ID}")
print()

# ============================================================================
# ETAPA 1: Buscar dados da planilha
# ============================================================================
print("=" * 80)
print("ETAPA 1: BUSCANDO DADOS DA PLANILHA")
print("=" * 80)
print()

dados = gsheets.buscar_dados_inventario(
    nome_inventario=INVENTARIO,
    tipo_contagem=TIPO_CONTAGEM,
    tipo_planilha=TIPO_PLANILHA
)

print()
print("=" * 80)
print(f"RESULTADO: {len(dados)} itens encontrados")
print("=" * 80)
print()

if not dados:
    print("⚠️ Nenhum item encontrado para processar")
    print()
    print("Possíveis causas:")
    print("  - Nome do inventário incorreto")
    print("  - Todos os itens já foram processados")
    print("  - Nenhum item tem quantidade (Físico) preenchida")
    print()
    sys.exit(0)

# Mostrar primeiros 3 itens
print("📦 ITENS ENCONTRADOS (primeiros 3):")
print()
for idx, item in enumerate(dados[:3], start=1):
    print(f"  Item {idx}:")
    print(f"    - ID: {item.get('ID', 'N/A')}")
    print(f"    - Etiqueta: {item.get('Etiqueta', 'N/A')}")
    print(f"    - Nova Etiqueta: {item.get('Nova Etiqueta', 'N/A')}")
    print(f"    - Item: {item.get('Item', 'N/A')}")
    print(f"    - Descrição: {item.get('Descrição', 'N/A')[:50]}...")
    print(f"    - Sub Inventário: {item.get('Sub Inventário', 'N/A')}")
    print(f"    - Endereço: {item.get('Endereço', 'N/A')}")
    print(f"    - Físico: {item.get('Físico', 'N/A')}")
    print(f"    - Status RPA: '{item.get('Status RPA', '')}'")
    print()

# ============================================================================
# ETAPA 2: Testar marcação como "PROCESSANDO..."
# ============================================================================
print("=" * 80)
print("ETAPA 2: TESTANDO MARCAÇÃO COMO 'PROCESSANDO...'")
print("=" * 80)
print()

# Pegar o primeiro item para testar
primeiro_item = dados[0]
item_id = primeiro_item.get('ID', '')

if not item_id:
    print("❌ Primeiro item não tem ID - não é possível testar atualização")
    sys.exit(1)

print(f"📌 Testando com o primeiro item:")
print(f"   - ID: {item_id}")
print(f"   - Etiqueta: {primeiro_item.get('Etiqueta', 'N/A')}")
print()

print("🔄 Marcando como 'PROCESSANDO...'...")
print()

sucesso = gsheets.atualizar_status_rpa(
    item_id=item_id,
    status="PROCESSANDO...",
    tipo_contagem=TIPO_CONTAGEM,
    tipo_planilha=TIPO_PLANILHA,
    robo_id=ROBO_ID
)

print()
print("=" * 80)
if sucesso:
    print("✅ TESTE BEM-SUCEDIDO!")
    print()
    print(f"O item ID {item_id} foi marcado como 'PROCESSANDO... [{ROBO_ID}]'")
    print()
    print("⚠️ IMPORTANTE: Verifique na planilha se o status foi atualizado!")
    print()
    print("Para limpar o teste, você pode:")
    print(f"  1. Abrir a planilha do Google Sheets")
    print(f"  2. Procurar o item ID {item_id}")
    print(f"  3. Apagar o conteúdo da coluna 'Status RPA' manualmente")
else:
    print("❌ TESTE FALHOU!")
    print()
    print("O item NÃO foi marcado como 'PROCESSANDO...'")
    print()
    print("Verifique os logs acima para identificar o problema.")
print("=" * 80)
print()

# ============================================================================
# ETAPA 3 (OPCIONAL): Testar marcação como "PROCESSO CONCLUIDO"
# ============================================================================
print()
print("=" * 80)
print("DESEJA TESTAR MARCAÇÃO COMO 'PROCESSO CONCLUIDO'? (s/n)")
print("=" * 80)

try:
    resposta = input("Digite 's' para SIM ou 'n' para NÃO: ").strip().lower()

    if resposta == 's':
        print()
        print("🔄 Marcando como 'PROCESSO CONCLUIDO'...")
        print()

        sucesso_concluido = gsheets.atualizar_status_rpa(
            item_id=item_id,
            status="PROCESSO CONCLUIDO",
            tipo_contagem=TIPO_CONTAGEM,
            tipo_planilha=TIPO_PLANILHA,
            robo_id=ROBO_ID
        )

        print()
        if sucesso_concluido:
            print(f"✅ Item ID {item_id} marcado como 'PROCESSO CONCLUIDO [{ROBO_ID}]'")
        else:
            print(f"❌ Falha ao marcar como 'PROCESSO CONCLUIDO'")
        print()
    else:
        print()
        print("⏭️ Teste de 'PROCESSO CONCLUIDO' pulado")
        print()

except KeyboardInterrupt:
    print()
    print("⚠️ Teste interrompido pelo usuário")
    print()

print()
print("=" * 80)
print("🏁 TESTE FINALIZADO")
print("=" * 80)
