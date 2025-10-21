# 🧪 Teste Completo do RPA Ciclo V2

## 📋 Visão Geral

O `teste_ciclo_completo.py` é um script de teste que simula todo o fluxo do RPA Ciclo V2, incluindo:

- ✅ Processamento de até 50 itens do Oracle
- ✅ Teste de anti-duplicação
- ✅ Simulação de todos os cliques (sem precisar do Oracle aberto)
- ✅ Execução da Bancada (simulada)
- ✅ Loop completo com múltiplos ciclos

## 🎯 Objetivo

Testar toda a lógica do RPA sem precisar ter o Oracle aberto, validando:

1. **Lógica de espera inteligente** do Oracle
2. **Sistema de anti-duplicação** (cache)
3. **Fluxo completo** de coordenadas
4. **Retry da Bancada** (até 3x)
5. **Integração com Google Sheets** de teste

## 🚀 Como Usar

### Opção 1: Executar via Python

```bash
cd C:\Users\ID135\OneDrive\Desktop\www\rpas\rpa_ciclo
python teste_ciclo_completo.py
```

### Opção 2: Compilar para .exe

1. Execute o arquivo `build_teste.bat`
2. Aguarde a compilação
3. Execute `dist\Teste_RPA_Ciclo.exe`

## 📊 Planilhas de Teste

O teste usa as seguintes planilhas:

- **Oracle**: https://docs.google.com/spreadsheets/d/147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY/edit
- **Bancada**: https://docs.google.com/spreadsheets/d/1KMS-1_FY6-cU26ZlaFu5jciSHEWlmluHo-QOFbB1LFE/edit

## ⚙️ Configurações do Teste

No arquivo `teste_ciclo_completo.py`, você pode ajustar:

```python
MODO_TESTE = True                # Sempre True para teste
SIMULAR_CLIQUES = True           # Simula pyautogui
LIMITE_ITENS_TESTE = 50          # Máximo de itens por ciclo
TESTAR_DUPLICACAO = True         # Testa anti-duplicação
NUM_CICLOS_TESTE = 3             # Número de ciclos para rodar
```

## 📈 O Que o Teste Faz

### Ciclo Completo:

1. **Etapa 1**: Transferência de Subinventário (simulado)
2. **Etapa 2**: Preenchimento Tipo = SUB (simulado)
3. **Etapa 3**: Seleção do Funcionário Wallatas (simulado)
4. **Etapa 4**: RPA Oracle
   - Busca até 50 linhas da planilha de teste
   - Valida todos os campos
   - Testa duplicação a cada 5 itens
   - Simula preenchimento dos campos
   - Registra no cache
5. **Etapa 5**: Navegação pós-Oracle (simulado)
6. **Etapa 6**: Abertura Bancada Material (simulado)
7. **Etapa 7**: RPA Bancada (simulado)
8. **Etapa 8**: Fechamento Bancada (simulado)
9. **Loop**: Volta para Etapa 1

### Teste de Anti-Duplicação:

- A cada 5 itens processados, tenta processar um item já processado
- O cache deve bloquear a duplicação
- Estatísticas são mostradas ao final

## 📊 Logs do Teste

Durante a execução, você verá logs como:

```
[21:30:00] 🔄 CICLO DE TESTE #1 - 2025-10-17 21:30:00
[21:30:01] 📋 ETAPA 1: Transferência de Subinventário
[21:30:01] 🖱️ Duplo clique na opção Transferência de Subinventário
[21:30:01]   [SIM] moveTo(771, 388, duration=0.1)
[21:30:01]   [SIM] doubleClick()
[21:30:02] ⏳ Aguardando abertura do modal (0.5s)...
[21:30:02] 📋 ETAPA 2: Preenchimento do Tipo
...
[21:30:10] 🤖 ETAPA 5: Processamento no Oracle (TESTE)
[21:30:11] 📊 Planilha carregada: 150 linhas encontradas
[21:30:11] 📋 50 linhas disponíveis para processar
[21:30:11] 📋 Processando 50 linha(s)...
[21:30:12] ▶ Linha 2 (1/50): ID=001 | Item=ITEM001 | Qtd=10
[21:30:12]   [SIMULANDO] Preenchendo campos no Oracle...
[21:30:12]     → Item: ITEM001
[21:30:12]     → Referência: MOV
...
[21:30:15] 🔄 [TESTE DUPLICAÇÃO] Tentando processar item novamente...
[21:30:15] 🛡️ [CACHE BLOQUEOU] Linha 2 (ID: 001) já processada. Pulando.
[21:30:15]    📊 Estatísticas: 1 duplicações bloqueadas de 1 tentativas
...
```

## 📄 Relatório Final

Ao final do teste, será gerado um arquivo `relatorio_teste_ciclo.json` com:

```json
{
  "data_teste": "2025-10-17 21:35:00",
  "ciclos_sucesso": 3,
  "ciclos_falha": 0,
  "itens_processados": 150,
  "tentativas_duplicacao": 30,
  "duplicacoes_bloqueadas": 30,
  "itens_cache_final": 0,
  "configuracoes": {
    "limite_itens": 50,
    "testar_duplicacao": true,
    "num_ciclos": 3
  }
}
```

## 🗑️ Limpeza do Cache

Ao iniciar o teste, você será perguntado:

```
🗑️ Deseja limpar o cache antes de começar? (s/n):
```

- **s**: Limpa o cache e começa do zero
- **n**: Mantém o cache existente (para testar persistência)

## 📝 Arquivos Gerados

Durante e após o teste, os seguintes arquivos são criados:

- `cache_teste_ciclo.json`: Cache de itens processados
- `relatorio_teste_ciclo.json`: Relatório final do teste

## 🔧 Compilação do .exe

### Requisitos:

```bash
pip install pyinstaller
```

### Comando:

```bash
build_teste.bat
```

### O que o build inclui:

- Executável standalone (não precisa Python instalado)
- config.json embutido
- Todas as dependências do Google Sheets
- Console para ver os logs em tempo real

## 🐛 Troubleshooting

### "Erro ao carregar config"

- Certifique-se de que `config.json` está na mesma pasta
- Verifique se o JSON está válido

### "Erro ao autenticar Google Sheets"

- Certifique-se de que `CredenciaisOracle.json` está na pasta do rpa_oracle
- Verifique se o `token.json` está na pasta do rpa_oracle
- Execute a autenticação manualmente primeiro

### "Planilha de teste vazia"

- Verifique se as planilhas de teste têm dados
- Confira os IDs das planilhas no código
- Verifique permissões de acesso

## 📊 Interpretação dos Resultados

### ✅ Teste Bem-Sucedido:

```
✅ Ciclos com sucesso: 3
❌ Ciclos com falha: 0
📦 Total de itens processados: 150
🔄 Tentativas de duplicação: 30
🛡️ Duplicações bloqueadas: 30
💾 Itens no cache final: 0
📈 Taxa de bloqueio: 100.0%
```

Isso significa que:
- Todos os ciclos completaram
- 150 itens foram processados
- Todas as tentativas de duplicação foram bloqueadas (100%)
- Cache foi limpo corretamente após processamento

### ⚠️ Teste com Problemas:

```
✅ Ciclos com sucesso: 1
❌ Ciclos com falha: 2
📦 Total de itens processados: 50
🔄 Tentativas de duplicação: 10
🛡️ Duplicações bloqueadas: 7
💾 Itens no cache final: 3
📈 Taxa de bloqueio: 70.0%
```

Isso indica:
- Alguns ciclos falharam (verificar logs)
- Cache não está bloqueando todas as duplicações (70%)
- Alguns itens ficaram presos no cache (3 pendentes)

## 🎯 Objetivo do Teste

O teste valida:

1. ✅ **Lógica de espera do Oracle funciona?**
   - Primeira vez sem itens: segue
   - Segunda vez sem itens: aguarda

2. ✅ **Anti-duplicação funciona?**
   - Taxa de bloqueio deve ser 100%
   - Cache deve registrar todos os IDs

3. ✅ **Validações funcionam?**
   - Quantidade zero
   - Campos vazios
   - Transações não autorizadas

4. ✅ **Loop completo funciona?**
   - Todas as etapas executam
   - Volta ao início corretamente

## 📞 Dúvidas

Se tiver problemas, verifique:

1. Os logs detalhados no console
2. O arquivo `relatorio_teste_ciclo.json`
3. O conteúdo do `cache_teste_ciclo.json`

## 🚀 Próximos Passos

Após validar o teste:

1. Ajuste as configurações em `main_ciclo_v2.py`
2. Compile a versão de produção
3. Execute com o Oracle aberto
4. Monitore os logs e o Google Sheets
