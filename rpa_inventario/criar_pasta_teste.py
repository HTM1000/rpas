# -*- coding: utf-8 -*-
"""
Script helper para criar pasta de teste e listar imagens necessárias
"""

import os
import sys
from pathlib import Path

# Configurar encoding para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Diretório base
BASE_DIR = Path(__file__).parent.resolve()
ELEMENTOS_DIR = BASE_DIR / "elementos"
TESTE_DIR = ELEMENTOS_DIR / "teste"

print("=" * 70)
print("CONFIGURACAO DA PASTA DE TESTE - RPA INVENTARIO")
print("=" * 70)
print()

# 1. Verificar se pasta elementos existe
if not ELEMENTOS_DIR.exists():
    print(f"❌ Pasta 'elementos' não encontrada em: {ELEMENTOS_DIR}")
    print("ℹ️ Criando pasta 'elementos'...")
    ELEMENTOS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✅ Pasta criada: {ELEMENTOS_DIR}")
else:
    print(f"✅ Pasta 'elementos' encontrada: {ELEMENTOS_DIR}")

print()

# 2. Criar pasta elementos/teste
if not TESTE_DIR.exists():
    print(f"ℹ️ Criando pasta 'elementos/teste'...")
    TESTE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✅ Pasta criada: {TESTE_DIR}")
else:
    print(f"✅ Pasta 'elementos/teste' já existe: {TESTE_DIR}")

print()

# 3. Listar imagens necessárias
print("📋 IMAGENS NECESSÁRIAS:")
print("=" * 70)
print()

imagens_necessarias = [
    "input_nome.png",
    "botao_localizar.png",
    "botao_nao.png",
    "input_etiqueta.png",
    "botao_salvar.png",
]

print("📁 Pasta NORMAL (elementos/):")
print("-" * 70)
for img in imagens_necessarias:
    caminho = ELEMENTOS_DIR / img
    status = "✅" if caminho.exists() else "❌"
    print(f"{status} {img}")

print()
print("📁 Pasta TESTE (elementos/teste/):")
print("-" * 70)
for img in imagens_necessarias:
    caminho = TESTE_DIR / img
    status = "✅" if caminho.exists() else "❌"
    print(f"{status} {img}")

print()
print("=" * 70)
print("📝 PRÓXIMOS PASSOS:")
print("=" * 70)
print()
print("1. Capture as imagens do sistema de TESTE (com cores diferentes)")
print("2. Salve as imagens com os MESMOS NOMES na pasta elementos/teste/:")
print()
for img in imagens_necessarias:
    print(f"   • {img}")
print()
print("3. Execute o RPA Inventário e marque '🧪 Modo Teste'")
print()
print("ℹ️ O Modo Teste irá buscar as imagens em elementos/teste/")
print("ℹ️ O Modo Normal irá buscar as imagens em elementos/")
print()
print("=" * 70)
print("✅ Configuração concluída!")
print("=" * 70)
