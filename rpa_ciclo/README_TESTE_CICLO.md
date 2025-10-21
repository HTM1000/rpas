# 🧪 Teste do RPA Ciclo - Modo Completo

## 📋 Descrição

Este teste simula o fluxo completo do RPA Ciclo integrando:
- ✅ RPA Oracle (lógica atualizada do novo exe)
- ✅ RPA Bancada (dados da planilha de teste)
- ✅ Loop contínuo (50 itens por vez)
- ✅ Aguarda automaticamente quando não há itens

## 🎯 O que o teste faz

### 1️⃣ RPA Oracle (Simulado)
- Busca até **50 itens** da planilha Separação
- Aplica todas as regras de validação
- Simula o preenchimento (sem movimentos físicos do pyautogui)
- Atualiza Status Oracle na planilha
- Gera arquivo `dados_oracle_processados.xlsx`
- Evita duplicações usando cache

### 2️⃣ RPA Bancada (Simulado)
- Busca dados da planilha de teste da bancada
- Simula preenchimento na bancada
- Gera arquivo `dados_bancada_processados.xlsx`

### 3️⃣ Loop Contínuo
- Processa 50 itens por vez
- Quando não há itens, aguarda 30 segundos
- Verifica automaticamente se há novos itens
- Continua rodando em loop infinito

## 🚀 Como Executar

### Opção 1: Usando o .bat (Recomendado)
```bash
executar_teste_ciclo.bat
```

### Opção 2: Diretamente com Python
```bash
python teste_ciclo.py
```

## ⚙️ Configurações

As configurações podem ser alteradas no início do arquivo `teste_ciclo.py`:

```python
# Planilha de Separação (Oracle)
SPREADSHEET_SEPARACAO_ID = "147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY"
SHEET_SEPARACAO = "Separação"

# Planilha de Bancada (Teste)
SPREADSHEET_BANCADA_ID = "1KMS-1_FY6-cU26ZlaFu5jciSHEWlmluHo-QOFbB1LFE"
SHEET_BANCADA = "Bancada"

# Limites
LIMITE_ITENS_POR_CICLO = 50
TEMPO_AGUARDO_SEM_ITENS = 30  # segundos
```

## 📊 Arquivos Gerados

Após a execução, serão gerados:

| Arquivo | Descrição |
|---------|-----------|
| `dados_oracle_processados.xlsx` | Itens processados no Oracle |
| `dados_bancada_processados.xlsx` | Itens processados na Bancada |
| `cache_teste_ciclo.json` | Cache para evitar duplicações |
| `teste_ciclo_log.txt` | Log detalhado da execução |

## 🔄 Fluxo de Execução

```
┌─────────────────────────────────────┐
│  CICLO #1                           │
├─────────────────────────────────────┤
│  1. RPA Oracle (50 itens)           │
│     ├─ Buscar linhas na planilha    │
│     ├─ Validar regras               │
│     ├─ Simular preenchimento        │
│     └─ Atualizar Status Oracle      │
│                                     │
│  2. RPA Bancada                     │
│     ├─ Buscar dados de teste        │
│     ├─ Simular preenchimento        │
│     └─ Gerar Excel                  │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│  AGUARDAR 5s                        │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│  CICLO #2 (repetir)                 │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│  Se não há itens: aguardar 30s      │
└─────────────────────────────────────┘
         ↓
      (loop infinito)
```

## ✅ Validações Aplicadas

O teste aplica as mesmas regras do RPA Oracle:

### Regra 1: Quantidade Zero
- Se quantidade = 0, marca como "Quantidade Zero"
- Não processa a linha

### Regra 2: Transações Restritas
- RAWINDIR/RAWMANUT/RAWWAFIFE → RAWCENTR = NÃO PERMITIDO
- Marca como "Transação não autorizada"

### Regra 3: Campos Vazios
- Item, Sub.Origem, End.Origem obrigatórios
- Para MOV: Sub.Destino, End.Destino obrigatórios
- Para COD: apenas origem obrigatória

### Regra 4: Mesma Origem e Destino
- RAWINDIR/RAWMANUT/RAWWAFIFE para si mesmo = NÃO PERMITIDO
- Marca como "Transação não autorizada"

## 🛑 Como Parar o Teste

- Pressione `Ctrl+C` no terminal
- O teste encerrará graciosamente e mostrará o resumo

## 📝 Log de Exemplo

```
[2025-01-17 10:30:00] ============================================================
[2025-01-17 10:30:00] TESTE DO RPA CICLO - MODO TESTE COMPLETO
[2025-01-17 10:30:00] ============================================================
[2025-01-17 10:30:01] [1/2] Autenticando no Google Sheets...
[2025-01-17 10:30:02] [1/2] Autenticação concluída!
[2025-01-17 10:30:02] [2/2] Carregando cache...
[2025-01-17 10:30:02] [2/2] Cache: 0 itens processados anteriormente
[2025-01-17 10:30:02] ############################################################
[2025-01-17 10:30:02] # CICLO #1
[2025-01-17 10:30:02] ############################################################
[2025-01-17 10:30:02] ============================================================
[2025-01-17 10:30:02] [RPA ORACLE] Iniciando processamento (Ciclo #1)
[2025-01-17 10:30:02] ============================================================
[2025-01-17 10:30:03] [ORACLE] Encontradas 50 linhas para processar
[2025-01-17 10:30:03] [ORACLE] Processando 50 linhas (limite: 50)
...
```

## 🔍 Verificando Resultados

### 1. Ver Log em Tempo Real
```bash
type teste_ciclo_log.txt
```

### 2. Ver Itens Processados no Oracle
- Abrir `dados_oracle_processados.xlsx`
- Verificar IDs, quantidades, status

### 3. Ver Itens Processados na Bancada
- Abrir `dados_bancada_processados.xlsx`
- Verificar dados da bancada

### 4. Ver Cache
```bash
type cache_teste_ciclo.json
```

## ⚠️ Observações Importantes

1. **Não faz movimentos físicos**: O teste simula o preenchimento, mas não move o mouse nem preenche telas
2. **Usa planilha de teste**: Os dados da bancada vêm da planilha de teste configurada
3. **Loop infinito**: O teste continua rodando até você parar com Ctrl+C
4. **Limite de 50 itens**: Processa no máximo 50 itens por ciclo para evitar sobrecarga
5. **Anti-duplicação**: Usa cache para garantir que não processa o mesmo ID duas vezes

## 🆘 Troubleshooting

### Erro de Autenticação
- Verificar se `CredenciaisOracle.json` está na pasta
- Verificar se `token.json` foi gerado
- Tentar deletar `token.json` e autenticar novamente

### Planilha Vazia
- Verificar se a planilha tem dados
- Verificar se a aba existe
- Verificar os IDs das planilhas no código

### Nenhum Item Processado
- Verificar se há linhas com Status=CONCLUÍDO
- Verificar se Status Oracle está vazio
- Ver o log para identificar regras que estão bloqueando

## 📞 Suporte

Se tiver problemas, verificar:
1. Log completo em `teste_ciclo_log.txt`
2. Cache em `cache_teste_ciclo.json`
3. Planilhas do Google Sheets
