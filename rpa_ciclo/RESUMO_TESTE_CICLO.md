# 📦 Teste RPA Ciclo - Arquivos Criados

## ✅ O que foi criado

### 1. `teste_ciclo.py` - Script Principal de Teste
**Funcionalidades:**
- ✅ Integra RPA Oracle atualizado (nova lógica do exe)
- ✅ Integra RPA Bancada (dados da planilha de teste)
- ✅ Processa 50 itens por vez
- ✅ Loop contínuo: aguarda automaticamente quando não há itens
- ✅ Pula movimentos físicos do Oracle (modo teste)
- ✅ Sistema anti-duplicação com cache
- ✅ Log detalhado de todas as operações

**Planilhas utilizadas:**
- **Separação** (Oracle): `147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY`
- **Bancada** (Teste): `1KMS-1_FY6-cU26ZlaFu5jciSHEWlmluHo-QOFbB1LFE`

### 2. `executar_teste_ciclo.bat` - Launcher
Script batch para facilitar a execução do teste com interface amigável.

### 3. `README_TESTE_CICLO.md` - Documentação Completa
Documentação detalhada com:
- Descrição do que o teste faz
- Como executar
- Configurações disponíveis
- Fluxo de execução
- Validações aplicadas
- Troubleshooting

## 🎯 Fluxo do Teste

```
CICLO #1
├── RPA ORACLE (até 50 itens)
│   ├── Buscar linhas (Status=CONCLUÍDO, Status Oracle vazio)
│   ├── Aplicar regras de validação
│   ├── Simular preenchimento (sem pyautogui)
│   ├── Gerar Excel dados_oracle_processados.xlsx
│   ├── Atualizar Status Oracle no Sheets
│   └── Salvar no cache
│
├── PAUSA 2s
│
├── RPA BANCADA
│   ├── Buscar dados da planilha de teste
│   ├── Simular preenchimento na bancada
│   └── Gerar Excel dados_bancada_processados.xlsx
│
└── AGUARDAR 5s

CICLO #2 (repetir)
...

SE NÃO HÁ ITENS:
└── Aguardar 30s e verificar novamente
```

## 📊 Arquivos Gerados pelo Teste

Quando você executar o teste, serão criados:

| Arquivo | Descrição |
|---------|-----------|
| `dados_oracle_processados.xlsx` | Todos os itens processados pelo Oracle |
| `dados_bancada_processados.xlsx` | Todos os itens processados pela Bancada |
| `cache_teste_ciclo.json` | Cache para evitar duplicações |
| `teste_ciclo_log.txt` | Log detalhado de todas as operações |

## 🚀 Como Executar

### Método 1: Usando o .bat (mais fácil)
```bash
executar_teste_ciclo.bat
```

### Método 2: Diretamente
```bash
python teste_ciclo.py
```

### Para parar o teste:
- Pressione `Ctrl+C` no terminal
- O teste encerrará e mostrará um resumo

## ⚙️ Configurações Importantes

No arquivo `teste_ciclo.py`, você pode ajustar:

```python
# Limites
LIMITE_ITENS_POR_CICLO = 50  # Quantos itens processar por ciclo
TEMPO_AGUARDO_SEM_ITENS = 30  # Segundos para aguardar quando não há itens
```

## 🔍 Validações Aplicadas

O teste aplica TODAS as regras do RPA Oracle:

### ✅ Regra 1: Quantidade Zero
- Se quantidade = 0 → marca como "Quantidade Zero"

### ✅ Regra 2: Transações Restritas (Origem → RAWCENTR)
- RAWINDIR → RAWCENTR = ❌ NÃO AUTORIZADO
- RAWMANUT → RAWCENTR = ❌ NÃO AUTORIZADO
- RAWWAFIFE → RAWCENTR = ❌ NÃO AUTORIZADO

### ✅ Regra 3: Campos Vazios
- Item, Sub.Origem, End.Origem = OBRIGATÓRIOS
- Para MOV: Sub.Destino, End.Destino = OBRIGATÓRIOS
- Para COD: apenas origem obrigatória

### ✅ Regra 4: Mesma Origem e Destino
- RAWINDIR → RAWINDIR = ❌ NÃO AUTORIZADO
- RAWMANUT → RAWMANUT = ❌ NÃO AUTORIZADO
- RAWWAFIFE → RAWWAFIFE = ❌ NÃO AUTORIZADO

## 📝 Diferenças do Modo Produção

| Aspecto | Modo Teste | Modo Produção |
|---------|-----------|---------------|
| Movimentos Oracle | ❌ Simulados | ✅ Reais (pyautogui) |
| Planilha Bancada | 📋 Planilha de teste | 📋 Planilha real |
| Limite de itens | 50 por ciclo | Sem limite |
| Loop | ✅ Infinito | ✅ Infinito |
| Cache | ✅ Ativo | ✅ Ativo |
| Validações | ✅ Todas | ✅ Todas |
| Atualização Sheets | ✅ Sim | ✅ Sim |

## 🎯 Próximos Passos

### Para testar agora:
1. Execute `executar_teste_ciclo.bat`
2. Aguarde o teste rodar
3. Pressione Ctrl+C para parar
4. Verifique os arquivos gerados

### Para integrar no exe:
1. O código já está pronto no `teste_ciclo.py`
2. A lógica pode ser copiada para o `main_ciclo.py`
3. Ajustar apenas as constantes de planilhas
4. Ativar/desativar movimentos físicos com flag MODO_TESTE

## ⚠️ Observações

1. **Não faz movimentos físicos**: O teste NÃO move o mouse nem clica em nada
2. **Apenas testa a lógica**: Valida regras, busca dados, gera Excel, atualiza Sheets
3. **Loop infinito**: Continue rodando até você parar manualmente
4. **Cache persistente**: Evita processar o mesmo ID duas vezes
5. **Limite de 50**: Processa no máximo 50 itens por ciclo para performance

## 📞 Dúvidas?

Ver o `README_TESTE_CICLO.md` para documentação completa e troubleshooting.
