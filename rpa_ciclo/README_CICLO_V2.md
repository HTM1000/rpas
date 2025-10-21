# RPA Ciclo V2 - Melhorias Implementadas

## 📋 Visão Geral

O `main_ciclo_v2.py` é uma versão melhorada do RPA Ciclo que implementa lógica inteligente de espera e retry automático.

## 🆕 Principais Melhorias

### 1. Lógica Inteligente de Espera no Oracle

A lógica de espera foi completamente redesenhada para atender aos requisitos específicos:

#### Caso 1: Nunca processou nenhum item
- **Comportamento**: Aguarda até processar pelo menos 1 item + 30s
- **Quando ocorre**: Primeira execução do ciclo, sem histórico de processamento
- **Razão**: Garante que o sistema não pule a etapa do Oracle sem processar nada

#### Caso 2: Primeira verificação sem itens (mas já processou antes)
- **Comportamento**: Pode seguir imediatamente
- **Quando ocorre**: Primeira vez que não encontra itens, mas já processou itens anteriormente
- **Razão**: Evita espera desnecessária quando o trabalho já foi feito

#### Caso 3: Segunda verificação sem itens (já processou tudo)
- **Comportamento**: Aguarda até processar pelo menos 1 item + 30s
- **Quando ocorre**: Segunda vez consecutiva sem itens encontrados
- **Razão**: Garante que o sistema aguarde por novos trabalhos antes de seguir

### 2. Retry Automático para Bancada (até 3x)

Implementado sistema de retry inteligente para o RPA_Bancada:

```python
MAX_TENTATIVAS_BANCADA = 3  # Configurável no topo do arquivo
```

**Comportamento:**
- Tenta executar o RPA_Bancada até 3 vezes
- Aguarda 5 segundos entre tentativas
- Se falhar nas 3 tentativas, marca o ciclo como falho
- Logs detalhados de cada tentativa

**Casos cobertos:**
- Timeout de execução
- Código de retorno diferente de 0
- Exceções durante a execução

### 3. Sistema de Cache Compartilhado

O cache de processamento é compartilhado com o RPA_Oracle:

- **Localização**: `rpa_oracle/processados.json`
- **Benefício**: Evita duplicação mesmo se o RPA_Oracle rodar independentemente
- **Thread-safe**: Usa locks para evitar race conditions

### 4. Flags de Controle de Estado

Duas flags globais controlam o comportamento:

```python
_primeira_verificacao_oracle = True   # Resetada a cada ciclo
_ja_processou_algum_item = False      # Persiste entre ciclos
```

## 🔄 Fluxo de Execução

```
┌─────────────────────────────────────────────────┐
│ 1. Transferência Subinventário                  │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│ 2. Preenchimento Tipo (SUB)                     │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│ 3. Seleção Funcionário (9x setas + Enter)       │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│ 4. RPA Oracle (Lógica Inteligente)              │
│    ┌──────────────────────────────────────┐     │
│    │ Nunca processou? → Aguarda 1 + 30s   │     │
│    ├──────────────────────────────────────┤     │
│    │ 1ª vez sem itens? → Segue            │     │
│    ├──────────────────────────────────────┤     │
│    │ 2ª vez sem itens? → Aguarda 1 + 30s  │     │
│    └──────────────────────────────────────┘     │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│ 5. Navegação pós-Oracle                         │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│ 6. Bancada Material (Duplo clique)              │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│ 7. RPA Bancada (com Retry até 3x)               │
│    Tentativa 1 → Falhou? → Aguarda 5s           │
│    Tentativa 2 → Falhou? → Aguarda 5s           │
│    Tentativa 3 → Falhou? → Marca como erro      │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│ 8. Fechamento Bancada                           │
└──────────────────┬──────────────────────────────┘
                   │
                   └──────────────► Reinicia Ciclo
```

## 🎯 Uso

### Modo Produção
```python
MODO_TESTE = False
PARAR_QUANDO_VAZIO = False
MAX_TENTATIVAS_BANCADA = 3
```

### Modo Teste
```python
MODO_TESTE = True
PARAR_QUANDO_VAZIO = True
MAX_TENTATIVAS_BANCADA = 3
```

## 📊 Monitoramento

O sistema gera logs detalhados de cada etapa:

```
🔄 CICLO #1 - 2025-10-17 21:30:00
📋 ETAPA 1: Transferência de Subinventário
🖱️ Duplo clique na opção Transferência de Subinventário
⏳ Aguardando abertura do modal (5.0s)...
📋 ETAPA 2: Preenchimento do Tipo
...
🤖 ETAPA 5: Processamento no Oracle
📊 Nenhuma linha nova encontrada
✅ Primeira verificação sem itens - Pode seguir!
...
🤖 ETAPA 8: Execução do RPA_Bancada
🔄 Tentativa 1/3
✅ RPA_Bancada executado com sucesso na tentativa 1
...
✅ CICLO #1 CONCLUÍDO COM SUCESSO!
```

## ⚙️ Configurações do config.json

Certifique-se de que o `config.json` tenha todas as coordenadas configuradas:

```json
{
  "coordenadas": {
    "tela_01_transferencia_subinventario": { "x": 771, "y": 388 },
    "tela_02_campo_tipo": { "x": 155, "y": 217, "digitar": "SUB", "acoes": ["tab", "enter"] },
    "tela_03_pastinha_funcionario": { "x": 32, "y": 120 },
    "tela_06_janela_navegador": { "x": 345, "y": 180 },
    "tela_07_bancada_material": { "x": 784, "y": 452, "duplo_clique": true },
    "tela_08_fechar_bancada": { "x": 754, "y": 97 }
  },
  "tempos_espera": {
    "entre_cliques": 4.5,
    "apos_modal": 5.0,
    "apos_rpa_oracle": 6.0,
    "apos_rpa_bancada": 6.0
  }
}
```

## 🔧 Validações Implementadas

Todas as validações do RPA_Oracle foram mantidas:

1. ✅ **Quantidade Zero**: Marca como "Quantidade Zero"
2. ✅ **Campos Vazios**: Marca como "Campo vazio encontrado"
3. ✅ **Transações Não Autorizadas**: Valida subinventários restritos
4. ✅ **Anti-duplicação**: Usa cache persistente compartilhado

## 🚀 Diferenças do main_ciclo.py

| Recurso | main_ciclo.py | main_ciclo_v2.py |
|---------|---------------|------------------|
| Lógica de espera Oracle | Simples (aguarda sempre) | Inteligente (3 casos) |
| Retry Bancada | Não | Sim (até 3x) |
| Cache compartilhado | Não | Sim |
| Flags de estado | Não | Sim |
| Logs detalhados | Básicos | Avançados |

## 📝 Notas Importantes

1. **Não mexe no código do RPA_Oracle e RPA_Bancada**: Todas as modificações estão apenas no `main_ciclo_v2.py`
2. **Compatível com .exe**: Usa `getattr(sys, '_MEIPASS', ...)` para encontrar arquivos
3. **Thread-safe**: Cache usa locks para evitar problemas de concorrência
4. **Failsafe**: Move o mouse para o canto superior esquerdo para parar

## 🐛 Troubleshooting

### O Oracle não está processando
- Verifique se o `token.json` está na pasta `rpa_oracle/`
- Verifique se as credenciais `CredenciaisOracle.json` estão corretas
- Verifique se a planilha tem linhas com Status = "CONCLUÍDO" e Status Oracle vazio

### O Bancada está falhando sempre
- Verifique se o arquivo `rpa_bancada/main.py` existe
- Verifique os logs do RPA_Bancada
- Aumente `MAX_TENTATIVAS_BANCADA` se necessário

### Cache não está funcionando
- Verifique se a pasta `rpa_oracle/` existe
- Verifique permissões de escrita
- Limpe o cache manualmente se necessário: delete `rpa_oracle/processados.json`

## 📞 Suporte

Para dúvidas ou problemas, verifique os logs detalhados gerados pelo sistema.
