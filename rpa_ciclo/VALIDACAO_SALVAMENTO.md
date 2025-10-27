# Validação de Salvamento após Ctrl+S

## 📋 Problema Identificado

Após pressionar `Ctrl+S`, o Oracle pode demorar muito para salvar a linha quando há:
- **Problemas de conexão com internet**
- **Lentidão no servidor Oracle**
- **Timeouts de rede**

Sem validação, o RPA continuava para a próxima linha mesmo que a anterior não tivesse sido salva, causando:
- ❌ Linhas perdidas (não processadas)
- ❌ Cache marcando linhas como processadas quando não foram
- ❌ Inconsistência entre Google Sheets e Oracle

---

## ✅ Solução Implementada

Nova função **`aguardar_salvamento_concluido()`** com **Detecção Inteligente de Travamento**:

1. **Aguarda INDEFINIDAMENTE** até os campos serem limpos (sem timeout fixo!)
2. **Monitora mudanças nos pixels** para detectar se Oracle está processando
3. **Detecta travamento** se pixels não mudarem por 120 segundos
4. **Clica no botão LIMPAR** automaticamente se detectar travamento
5. **Marca linha como erro** no Google Sheets para reprocessamento

### 🧠 Lógica Inteligente

- ✅ **Campo VAZIO** → Linha salva com sucesso!
- 🔄 **Campo PREENCHIDO + Pixels mudando** → Oracle processando, aguarda...
- ⚠️ **Campo PREENCHIDO + Pixels SEM MUDANÇA por 120s** → Sistema TRAVADO!

---

## 🔄 Fluxo Completo

```
┌──────────────────────────────────────────────────────────┐
│  1. Preencher campos Oracle                              │
│     (Item, Quantidade, Referência, etc.)                 │
└────────────────┬─────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────┐
│  2. Validação Híbrida (3 etapas)                         │
│     - Pixels (campo preenchido?)                         │
│     - Clipboard (valor correto?)                         │
│     - Erros Oracle (imagens)                             │
└────────────────┬─────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────┐
│  3. Pressionar Ctrl+S                                    │
└────────────────┬─────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────┐
│  4. Tratar erro de quantidade negativa                   │
│     (se detectar qtd_negativa.png)                       │
└────────────────┬─────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────┐
│  5. ⏳ AGUARDAR SALVAMENTO SER CONCLUÍDO (NOVO!)         │
│                                                           │
│  Loop de verificação a cada 2 segundos:                  │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Campo Item está VAZIO?                          │    │
│  │                                                  │    │
│  │ ✅ SIM → Linha foi salva! Continua              │    │
│  │ ❌ NÃO → Ainda preenchido, aguarda mais 2s      │    │
│  │                                                  │    │
│  │ Timeout após 60 segundos → Marca erro           │    │
│  └─────────────────────────────────────────────────┘    │
└────────────────┬─────────────────────────────────────────┘
                 │
                 ▼
         ┌───────┴────────┐
         │                │
    SUCESSO           TIMEOUT
         │                │
         ▼                ▼
┌─────────────────┐  ┌──────────────────────────────┐
│ 6a. Adicionar   │  │ 6b. Clicar LIMPAR            │
│     ao cache    │  │     Marcar erro no Sheets    │
│                 │  │     NÃO adicionar ao cache   │
│ 7a. Atualizar   │  │     (será reprocessado)      │
│     Sheets OK   │  └──────────────────────────────┘
└─────────────────┘
```

---

## 🔍 Função `aguardar_salvamento_concluido()`

### Parâmetros

```python
aguardar_salvamento_concluido(
    timeout_travamento=120,  # Tempo SEM MUDANÇA para considerar travado (segundos)
    intervalo_check=2        # Intervalo entre verificações (segundos)
)
```

### Retorno

```python
(sucesso: bool, tipo_resultado: str, tempo_espera: float)
```

| Tipo de Resultado | Descrição                                                     |
|-------------------|---------------------------------------------------------------|
| `SALVO_OK`        | Campos foram limpos (linha salva com sucesso)                 |
| `TRAVADO`         | Pixels não mudaram por {timeout_travamento}s (sistema travou) |

### Como Funciona

1. **Captura coordenadas do campo Item:** `[67, 155, 118, 22]`

2. **Loop de verificação CONTÍNUO (sem timeout fixo):**
   - Verifica percentual de pixels não-brancos no campo
   - Compara com percentual anterior para detectar mudanças
   - Se **VAZIO** → Linha foi salva! ✅ (retorna imediatamente)
   - Se **PREENCHIDO + Mudança > 0.5%** → Oracle processando, aguarda...
   - Se **PREENCHIDO + SEM mudança por 120s** → Sistema TRAVADO! ⚠️

3. **Detecção de Travamento:**
   - Rastreia tempo desde última mudança nos pixels
   - Se pixels não mudarem por 120s consecutivos:
     - Marca como erro no Google Sheets
     - Clica no botão LIMPAR para limpar formulário
     - NÃO adiciona ao cache (linha será reprocessada)

### Vantagens da Nova Lógica

| Aspecto                    | Versão Antiga (Timeout Fixo) | Nova Versão (Detecção de Travamento) |
|----------------------------|------------------------------|--------------------------------------|
| **Salvamento lento**       | ❌ Timeout em 60s            | ✅ Aguarda indefinidamente           |
| **Sistema travado**        | ⚠️ Demora 60s para detectar  | ✅ Detecta em 120s (sem mudança)     |
| **Oracle processando**     | ❌ Pode dar timeout          | ✅ Detecta mudança e aguarda         |
| **Falso positivo**         | ❌ Comum (internet lenta)    | ✅ Raro (só se realmente travou)     |

---

## 📊 Logs de Execução

### Salvamento Rápido (6 segundos - Normal)

```
[SAVE] >> Pressionando CTRL+S...
[SAVE] << CTRL+S pressionado
[SAVE] Aguardando confirmação de salvamento...
⏳ [SALVAMENTO] Aguardando confirmação de salvamento...
   Modo: AGUARDAR INDEFINIDAMENTE até campo limpar
   Timeout travamento: 120s (sem mudança nos pixels)
   Intervalo: 2s
   [1] 2s - Campo: PREENCHIDO (4.2%) | 🔄 PROCESSANDO
   [2] 4s - Campo: PREENCHIDO (4.1%) | 🔄 PROCESSANDO
   [3] 6s - Campo: VAZIO (0.8%) | ⏸️  SEM MUDANÇA (2s)
✅ [SALVAMENTO] Linha salva e limpa! Tempo total: 6.2s
✅ [SAVE] Salvamento confirmado em 6.2s!
⏳ Inicio inserção no cache...
```

### Salvamento Lento (180 segundos - Internet Lenta, MAS FUNCIONA!)

```
[SAVE] >> Pressionando CTRL+S...
[SAVE] << CTRL+S pressionado
[SAVE] Aguardando confirmação de salvamento...
⏳ [SALVAMENTO] Aguardando confirmação de salvamento...
   Modo: AGUARDAR INDEFINIDAMENTE até campo limpar
   [1] 2s - Campo: PREENCHIDO (4.2%) | 🔄 PROCESSANDO
   [2] 4s - Campo: PREENCHIDO (4.3%) | 🔄 PROCESSANDO
   [3] 6s - Campo: PREENCHIDO (4.1%) | 🔄 PROCESSANDO
   ... (continua verificando - pixels MUDANDO) ...
   [50] 100s - Campo: PREENCHIDO (4.4%) | 🔄 PROCESSANDO
   [60] 120s - Campo: PREENCHIDO (4.2%) | 🔄 PROCESSANDO
   ... (aguarda mais - pixels AINDA MUDANDO) ...
   [89] 178s - Campo: PREENCHIDO (4.1%) | 🔄 PROCESSANDO
   [90] 180s - Campo: VAZIO (0.9%) | ⏸️  SEM MUDANÇA (2s)
✅ [SALVAMENTO] Linha salva e limpa! Tempo total: 180.3s (3 minutos!)
✅ [SAVE] Salvamento confirmado em 180.3s!
⏳ Inicio inserção no cache...
```
**👆 Veja a diferença: Aguardou 3 MINUTOS porque pixels estavam mudando!**

### Sistema Travado (120s sem mudança)

```
[SAVE] >> Pressionando CTRL+S...
[SAVE] << CTRL+S pressionado
[SAVE] Aguardando confirmação de salvamento...
⏳ [SALVAMENTO] Aguardando confirmação de salvamento...
   Modo: AGUARDAR INDEFINIDAMENTE até campo limpar
   [1] 2s - Campo: PREENCHIDO (4.2%) | 🔄 PROCESSANDO
   [2] 4s - Campo: PREENCHIDO (4.2%) | ⏸️  SEM MUDANÇA (2s)
   [3] 6s - Campo: PREENCHIDO (4.2%) | ⏸️  SEM MUDANÇA (4s)
   ... (pixels NÃO MUDAM) ...
   [60] 120s - Campo: PREENCHIDO (4.2%) | ⏸️  SEM MUDANÇA (120s)
⚠️ [SALVAMENTO] TRAVADO - Sem mudança nos pixels por 120s
   Tempo total decorrido: 120.5s
   Campo Item ainda preenchido: True (4.2%)
❌ [SAVE] SISTEMA TRAVADO após 120.5s - linha não foi salva
[SAVE] Tipo: TRAVADO
[SAVE] 🧹 Clicando no botão LIMPAR para forçar limpeza do formulário...
[SAVE] ✅ Botão Limpar clicado
✅ Status atualizado no Sheets: 'Sistema travado no Ctrl+S (120s sem mudança) - Verificar Oracle/Conexão'
[SAVE] Pulando para próxima linha (esta será reprocessada)
```

---

## ⚙️ Configuração

### Ajustar Timeout

Se o Oracle sempre demora mais de 60 segundos, ajuste o timeout:

```python
# Em main_ciclo.py, linha ~1920

sucesso_save, tipo_save, tempo_save = aguardar_salvamento_concluido(
    timeout=120,       # ← Aumentar para 120s (2 minutos)
    intervalo_check=2  # Verificar a cada 2s
)
```

### Ajustar Intervalo de Verificação

Para verificar mais frequentemente:

```python
sucesso_save, tipo_save, tempo_save = aguardar_salvamento_concluido(
    timeout=60,
    intervalo_check=1  # ← Verificar a cada 1s (mais rápido)
)
```

---

## 🎯 Coordenadas Usadas

A validação verifica o **campo Item** para detectar se foi limpo:

```python
# Campo Item (primeiro campo do formulário)
x = 67
y = 155
largura = 118
altura = 22
```

**Por que o campo Item?**
- É o primeiro campo do formulário
- Sempre é preenchido (campo obrigatório)
- Quando o Oracle salva, ele limpa TODOS os campos de uma vez
- Se Item está vazio → formulário foi limpo → linha foi salva

---

## 🔧 Troubleshooting

### Validação sempre dá timeout mesmo quando salva rápido

**Causa:** Threshold de pixels muito baixo, detecta campo como preenchido mesmo vazio.

**Solução:**
1. Verifique o threshold em `validador_hibrido.py`:
   ```python
   THRESHOLD_PIXELS = 0.02  # 2% dos pixels
   ```
2. Ajuste se necessário (valores típicos: 0.01 a 0.05)

### Validação passa muito rápido (não aguarda o suficiente)

**Causa:** Campo sendo detectado como vazio antes de realmente estar.

**Solução:**
1. Aumente o delay inicial após Ctrl+S:
   ```python
   # Em main_ciclo.py, antes de aguardar_salvamento_concluido()
   time.sleep(3)  # Aguardar 3s antes de começar verificação
   ```

### Timeout sempre acontece mas linha é salva

**Causa:** Oracle salva mas não limpa os campos automaticamente.

**Solução:**
1. Verifique se Oracle está configurado para limpar campos após salvar
2. Ou altere lógica para verificar se modal de confirmação aparece
3. Ou aumente o timeout para 120s ou mais

---

## 📈 Benefícios

### Antes (Sem Validação)
- ❌ RPA continuava mesmo com salvamento pendente
- ❌ Linhas perdidas em caso de timeout
- ❌ Cache marcava como processado erroneamente
- ❌ Inconsistência entre Sheets e Oracle
- ❌ Reprocessamento manual necessário

### Depois (Com Validação)
- ✅ RPA aguarda salvamento ser confirmado
- ✅ Timeout detectado automaticamente
- ✅ Linha marcada para reprocessamento
- ✅ Cache só atualizado se salvou com sucesso
- ✅ Consistência garantida
- ✅ Botão LIMPAR clicado automaticamente em timeout

---

## 🧪 Teste Manual

Para testar a validação de timeout:

1. **Simular lentidão:**
   - Desconecte a internet temporariamente
   - Ou adicione delay artificial antes do Ctrl+S

2. **Execute o RPA:**
   ```bash
   cd rpa_ciclo
   python RPA_Ciclo_GUI_v2.py
   ```

3. **Observe os logs:**
   - Deve mostrar tentativas de verificação a cada 2s
   - Após 60s, deve clicar em LIMPAR e marcar erro

4. **Verifique Google Sheets:**
   - Linha deve ter status: `Timeout salvamento (60s) - Verificar conexão/Oracle`

---

## 🔄 Integração com Sistema Híbrido

A validação de salvamento funciona em conjunto com o sistema de validação híbrida:

```
Validação Híbrida → Ctrl+S → Tratar Erros → Aguardar Salvamento
    (3 etapas)                                  (NOVO!)
```

**Ambos usam análise de pixels**, mas para propósitos diferentes:
- **Validação Híbrida:** Verifica se campos foram **preenchidos corretamente**
- **Validação Salvamento:** Verifica se campos foram **limpos** (linha salva)

---

## 📝 Mensagens de Erro no Google Sheets

| Mensagem                                           | Causa                              |
|----------------------------------------------------|------------------------------------|
| `Timeout salvamento (60s) - Verificar conexão/Oracle` | Salvamento demorou > 60s       |

---

## 🚀 Próximas Melhorias Possíveis

1. **Detecção de modal de confirmação:** Verificar se aparece modal "Salvo com sucesso"
2. **Timeout adaptativo:** Ajustar timeout baseado em histórico de salvamentos
3. **Retry automático:** Tentar salvar novamente em caso de timeout
4. **Métrica de performance:** Registrar tempo médio de salvamento

---

**Autor:** Claude Code
**Data:** 2025-10-24
**Versão:** 1.0
**Status:** ✅ Implementado e documentado
