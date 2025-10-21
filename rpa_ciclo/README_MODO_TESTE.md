# 🧪 Modo Teste - RPA Ciclo

## 📋 O que é o Modo Teste?

O Modo Teste permite executar o RPA Ciclo SEM realizar movimentos físicos do mouse ou teclado. Ideal para:
- Testar a lógica do código
- Validar integrações com Google Sheets
- Testar o fluxo completo sem interferir no Oracle
- Desenvolver e debugar sem riscos

## ⚙️ Configurações Disponíveis

No arquivo `main_ciclo.py`, há 4 flags de configuração (igual ao RPA_Oracle):

```python
# ─── CONFIGURAÇÕES DE MODO TESTE ─────────────────────────────────────────────
MODO_TESTE = False  # True = simula movimentos sem pyautogui | False = PRODUÇÃO
PARAR_QUANDO_VAZIO = False  # True = para quando vazio (teste) | False = continua rodando (PRODUÇÃO)
SIMULAR_FALHA_SHEETS = False  # True = força falhas para testar retry | False = PRODUÇÃO
LIMITE_ITENS_TESTE = 50  # Limite de itens por ciclo no modo teste
```

### Flag 1: `MODO_TESTE`
- **`False` (Produção)**: Executa movimentos reais do mouse e teclado
- **`True` (Teste)**: Simula os movimentos, apenas testa a lógica

### Flag 2: `PARAR_QUANDO_VAZIO`
- **`False` (Produção)**: Continua rodando em loop mesmo quando não há itens
- **`True` (Teste)**: Para automaticamente quando não houver mais itens para processar

### Flag 3: `SIMULAR_FALHA_SHEETS`
- **`False` (Produção)**: Atualiza Google Sheets normalmente
- **`True` (Teste)**: Força falhas aleatórias para testar o sistema de retry

### Flag 4: `LIMITE_ITENS_TESTE`
- Número máximo de itens a processar por ciclo no modo teste
- Padrão: 50 itens

## 🚀 Como Ativar/Desativar o Modo Teste

### Opção 1: Script Automático (Recomendado)

Execute o script que alterna automaticamente:

```bash
python ativar_modo_teste.py
```

Esse script:
- ✅ Detecta o modo atual
- ✅ Alterna entre Teste e Produção
- ✅ Atualiza `MODO_TESTE` e `PARAR_QUANDO_VAZIO` automaticamente

### Opção 2: Manual

Edite o arquivo `main_ciclo.py` e altere as flags:

```python
# Para ATIVAR o modo teste:
MODO_TESTE = True
PARAR_QUANDO_VAZIO = True

# Para DESATIVAR (voltar para produção):
MODO_TESTE = False
PARAR_QUANDO_VAZIO = False
```

## 🎯 O que é Simulado no Modo Teste?

Quando `MODO_TESTE = True`:

### ✅ Etapa 1: Transferência de Subinventário
- Simula duplo clique
- **Não** move o mouse
- Apenas aguarda os tempos configurados

### ✅ Etapa 2: Preenchimento do Tipo
- Simula clique e digitação de "SUB"
- **Não** digita no teclado
- Apenas loga a ação

### ✅ Etapa 3: Seleção de Funcionário
- Simula navegação com setas
- Simula seleção com Enter
- **Não** pressiona teclas reais

### ✅ Etapa 4: RPA Oracle
- Simula preenchimento de todos os campos
- **Não** clica ou digita no Oracle
- **SIM** valida regras de negócio
- **SIM** atualiza Google Sheets
- **SIM** gerencia cache

### ✅ Etapa 5: Navegação pós-Oracle
- Simula cliques de navegação
- **Não** move o mouse

### ✅ Etapa 6: RPA Bancada
- Executa normalmente (chama o exe/script da bancada)

### ✅ Etapa 7: Fechamento da Bancada
- Simula clique no X
- **Não** move o mouse

## 📊 Exemplo de Log no Modo Teste

```
============================================================
🤖 RPA CICLO - Iniciado
[MODO TESTE ATIVADO] Simulação sem movimentos físicos - apenas teste de lógica
============================================================
✅ Configurações carregadas
🔄 Modo contínuo ativado - execução ininterrupta
⚠️ O RPA Oracle aguardará automaticamente se não houver nada para processar
🛑 Para parar: use o botão PARAR ou mova o mouse para o canto superior esquerdo

============================================================
🔄 CICLO #1 - 2025-10-17 20:30:00
============================================================
📋 ETAPA 1: Transferência de Subinventário
🖱️ Duplo clique na opção Transferência de Subinventário
[MODO TESTE] Simulando clique em (771, 388)
⏳ Aguardando abertura do modal (5.0s)...
📋 ETAPA 2: Preenchimento do Tipo
🖱️ Clique no campo Tipo, digita 'SUB', TAB e ENTER
[MODO TESTE] Simulando clique em (155, 217)
⌨️ Digitando: SUB
[MODO TESTE] Simulando digitação de 'SUB'
[MODO TESTE] Simulando teclas: tab, enter
...
```

## ⚠️ Importante

1. **Modo Teste NÃO substitui teste real**: Sempre teste em produção controlada antes de usar em larga escala
2. **Google Sheets é atualizado mesmo no modo teste**: As flags de status são gravadas na planilha
3. **Cache funciona normalmente**: Itens processados são marcados no cache
4. **RPA Bancada executa normalmente**: Apenas as etapas de navegação são simuladas

## 🔄 Recompilação do .exe

Se você alterou as flags e está usando o .exe:

```bash
# Limpar build anterior
rd /s /q build dist

# Recompilar
pyinstaller RPA_Ciclo.spec --clean --noconfirm
```

Ou use o script:
```bash
build.bat
```

## 📝 Testando o Fluxo Completo

Para testar o ciclo completo no modo teste:

1. Ative o modo teste:
```bash
python ativar_modo_teste.py
```

2. Execute o RPA:
```bash
python main_ciclo.py
```

3. O RPA irá:
   - Simular todas as navegações
   - Processar itens reais do Google Sheets
   - Atualizar Status Oracle normalmente
   - Parar automaticamente quando acabarem os itens

## 🆘 Troubleshooting

### "Erro ao clicar em..."
- Verifique se `MODO_TESTE = True`
- No modo teste, esse erro NÃO deve aparecer

### "Nenhuma simulação aparece no log"
- Verifique se o modo teste foi ativado corretamente
- Reinicie o script/exe após alterar as flags

### "RPA está clicando mesmo no modo teste"
- Certifique-se de que `MODO_TESTE = True`
- Se estiver usando .exe, recompile após alterar

## 📞 Suporte

Ver também:
- `README.md` - Documentação geral do RPA Ciclo
- `MANUAL_USO.md` - Manual de uso completo
- `regras-rpa-oracle.txt` - Regras de validação
