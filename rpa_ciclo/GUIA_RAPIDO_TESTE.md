# 🚀 GUIA RÁPIDO - Teste do RPA Ciclo V2

## ⚡ Início Rápido (3 passos)

### 1️⃣ Executar Teste (Python)

```bash
# Opção mais rápida - executar direto
executar_teste.bat
```

OU

### 1️⃣ Compilar para .exe

```bash
# Criar executável para acompanhar logs
build_teste.bat
```

Depois:

```bash
# Executar o .exe gerado
cd dist
Teste_RPA_Ciclo.exe
```

---

## 📊 O Que Vai Acontecer

```
╔═══════════════════════════════════════════════════════════════╗
║  1. Autenticação Google Sheets                                ║
║  2. Pergunta se quer limpar cache (s/n)                       ║
║  3. Aguarda você pressionar ENTER                             ║
║                                                                ║
║  ┌──────────────────────────────────────────┐                 ║
║  │ CICLO 1/3                                │                 ║
║  ├──────────────────────────────────────────┤                 ║
║  │ ✓ Transferência Subinventário (simul)   │                 ║
║  │ ✓ Preenchimento Tipo (simul)            │                 ║
║  │ ✓ Seleção Funcionário (simul)           │                 ║
║  │ ✓ RPA Oracle (até 50 itens)             │  ◄── AQUI       ║
║  │   → Testa duplicação                     │      TESTA      ║
║  │   → Valida campos                        │      TUDO       ║
║  │   → Simula preenchimento                 │                 ║
║  │ ✓ Navegação (simul)                      │                 ║
║  │ ✓ Bancada Material (simul)               │                 ║
║  │ ✓ RPA Bancada (simul)                    │                 ║
║  │ ✓ Fechamento (simul)                     │                 ║
║  └──────────────────────────────────────────┘                 ║
║                                                                ║
║  4. Repete para CICLO 2/3 e 3/3                               ║
║  5. Mostra estatísticas finais                                ║
║  6. Salva relatório em relatorio_teste_ciclo.json             ║
╚═══════════════════════════════════════════════════════════════╝
```

---

## 📈 Logs em Tempo Real

Você verá algo assim:

```
[21:30:00] 🔄 CICLO DE TESTE #1 - 2025-10-17 21:30:00
[21:30:01] 📋 ETAPA 1: Transferência de Subinventário
[21:30:01]   [SIM] moveTo(771, 388, duration=0.1)
[21:30:01]   [SIM] doubleClick()
[21:30:02] 📋 ETAPA 5: Processamento no Oracle (TESTE)
[21:30:03] 📊 Planilha carregada: 150 linhas encontradas
[21:30:03] 📋 50 linhas disponíveis para processar
[21:30:04] ▶ Linha 2 (1/50): ID=001 | Item=ITEM001 | Qtd=10
[21:30:04]   [SIMULANDO] Preenchendo campos no Oracle...
[21:30:04]     → Item: ITEM001
[21:30:04]     → Referência: MOV
[21:30:04]     → Sub.Origem: RAWCENTR | End.Origem: A-01-01
[21:30:04]     → Sub.Destino: RAWWIP | End.Destino: B-02-03
[21:30:04]     → Quantidade: 10
[21:30:05] 💾 ID 001 registrado no cache
[21:30:05] ✅ Linha 2 (ID: 001) processada com sucesso

... (processa até 50 itens) ...

[21:30:20] 🔄 [TESTE DUPLICAÇÃO] Tentando processar item novamente...
[21:30:20] 🛡️ [CACHE BLOQUEOU] Linha 2 (ID: 001) já processada. Pulando.
[21:30:20]    📊 Estatísticas: 1 duplicações bloqueadas de 1 tentativas

... (continua processando) ...

[21:30:45] ✅ 50 item(ns) processado(s) neste ciclo
[21:30:45] 📊 Total processado até agora: 50 itens
[21:30:46] ✅ CICLO DE TESTE #1 CONCLUÍDO COM SUCESSO!
```

---

## 📊 Estatísticas Finais

No final, você verá:

```
========================================
📊 ESTATÍSTICAS FINAIS DO TESTE
========================================
✅ Ciclos com sucesso: 3
❌ Ciclos com falha: 0
📦 Total de itens processados: 150
🔄 Tentativas de duplicação: 30
🛡️ Duplicações bloqueadas: 30
💾 Itens no cache final: 0
📈 Taxa de bloqueio: 100.0%
========================================
```

---

## ✅ O Que Validar

### 1. Taxa de Bloqueio = 100%

```
🛡️ Duplicações bloqueadas: 30
📈 Taxa de bloqueio: 100.0%  ✅ BOM!
```

Se for < 100%, o cache não está funcionando direito.

### 2. Todos os Ciclos com Sucesso

```
✅ Ciclos com sucesso: 3  ✅ BOM!
❌ Ciclos com falha: 0
```

Se tiver falhas, verificar os logs.

### 3. Itens Processados = Esperado

```
📦 Total de itens processados: 150  ✅ BOM!
(50 itens × 3 ciclos = 150)
```

### 4. Cache Limpo ao Final

```
💾 Itens no cache final: 0  ✅ BOM!
```

Se tiver itens no cache, eles não foram marcados como concluídos.

---

## 🎯 Configurações Rápidas

Edite `teste_ciclo_completo.py` linha 26-30:

```python
LIMITE_ITENS_TESTE = 50      # ◄── Mudar para 10 para teste rápido
TESTAR_DUPLICACAO = True     # ◄── False para não testar duplicação
NUM_CICLOS_TESTE = 3         # ◄── Mudar para 1 para teste único
```

---

## 🗑️ Limpeza

Ao iniciar, você verá:

```
🗑️ Deseja limpar o cache antes de começar? (s/n):
```

- Digite **s** + ENTER: Limpa cache e começa do zero
- Digite **n** + ENTER: Mantém cache existente

---

## 📂 Arquivos Gerados

Após o teste, você terá:

```
rpa_ciclo/
├── cache_teste_ciclo.json         ◄── Cache dos itens processados
├── relatorio_teste_ciclo.json     ◄── Relatório completo do teste
└── dist/
    └── Teste_RPA_Ciclo.exe        ◄── Executável (se compilou)
```

---

## 🐛 Problemas Comuns

### "Erro ao autenticar Google Sheets"

Solução:

```bash
# Certifique-se de que esses arquivos existem:
rpa_oracle/token.json
rpa_oracle/CredenciaisOracle.json  (ou rpa_ciclo/CredenciaisOracle.json)
```

### "Planilha de teste vazia"

Solução:
- Verifique se você tem acesso às planilhas de teste
- Confira os IDs no código

### "Cache não está bloqueando duplicações"

Solução:
- Delete `cache_teste_ciclo.json`
- Rode o teste novamente

---

## 🎉 Pronto para Produção?

Se o teste passar com:

- ✅ Taxa de bloqueio = 100%
- ✅ Todos os ciclos com sucesso
- ✅ Cache limpo ao final

Então você pode usar o `main_ciclo_v2.py` em produção! 🚀

---

## 📞 Resumo dos Comandos

```bash
# Teste rápido via Python
executar_teste.bat

# Compilar para .exe
build_teste.bat

# Executar .exe
cd dist
Teste_RPA_Ciclo.exe
```

---

**Pronto! Agora é só executar e acompanhar os logs em tempo real! 🎯**
