# 🔍 DIAGNÓSTICO: RPA Fechando Automaticamente no Modo Contínuo

**Data:** 2026-01-13
**Versão:** RPA Ciclo v4.4
**Tipo:** Guia de Diagnóstico

---

## 🚨 PROBLEMA REPORTADO

**Sintoma:** Quando executado em modo contínuo, o RPA fecha automaticamente sem intervenção do usuário.

**Impacto:** RPA não consegue rodar 24/7 como esperado.

---

## 🔍 CAUSAS POSSÍVEIS (ORDEM DE PROBABILIDADE)

### ❌ CAUSA 1: Falha Crítica em `executar_ciclo_completo()` (MAIS PROVÁVEL)

**O que acontece:**
```python
# Linha 4814-4829 em main_ciclo.py
sucesso = executar_ciclo_completo(config)

if not sucesso:  # ← SE RETORNA FALSE
    gui_log("❌ FALHA CRÍTICA DETECTADA!")
    break  # ← PARA O RPA IMEDIATAMENTE
```

**Quando ocorre:**
- Erro ao processar itens no Oracle
- Falha na navegação entre telas
- Problema ao executar RPA Bancada
- Erro de conexão com Google Sheets
- Coordenadas incorretas causando cliques errados

**Como identificar nos logs:**
```
❌ FALHA CRÍTICA DETECTADA!
🛑 RPA foi interrompido automaticamente
📋 Verifique os logs acima para identificar o problema
⚠️ Pode ser:
   - Falha ao processar itens no Oracle
   - Falha ao executar RPA Bancada
   - Problema de conexão com Google Sheets
   - Erro de coordenadas/cliques
```

**Solução:**
1. Verificar os logs **ACIMA** da mensagem de falha crítica
2. Identificar qual etapa falhou
3. Corrigir o problema específico (coordenadas, rede, etc.)

---

### ❌ CAUSA 2: FAILSAFE do PyAutoGUI (MUITO COMUM)

**O que acontece:**
```python
# Linha 4892-4893 em main_ciclo.py
except pyautogui.FailSafeException:
    gui_log("🛑 FAILSAFE acionado (mouse no canto superior esquerdo)")
```

**Quando ocorre:**
- Usuário move o mouse para o canto superior esquerdo (0, 0)
- Mouse acidentalmente vai para o canto
- Outro programa move o cursor

**Como identificar nos logs:**
```
🛑 FAILSAFE acionado (mouse no canto superior esquerdo)
🏁 RPA CICLO - Finalizado
```

**Solução:**
```python
# Desabilitar FAILSAFE (NÃO RECOMENDADO para produção)
pyautogui.FAILSAFE = False

# OU manter ativado e evitar mover mouse para o canto
```

**IMPORTANTE:** O FAILSAFE é uma medida de segurança. Desabilitar pode impedir paradas de emergência!

---

### ❌ CAUSA 3: Tecla ESC Pressionada

**O que acontece:**
```python
# Hook de teclado detecta ESC
def parar_callback(event):
    global _rpa_running
    if event.name == 'esc' and event.event_type == 'down':
        _rpa_running = False  # ← PARA O LOOP
```

**Quando ocorre:**
- Usuário pressiona ESC acidentalmente
- Outro programa envia evento de ESC
- Teclado com problema enviando ESC fantasma

**Como identificar nos logs:**
```
⚠️ [ESC] TECLA ESC PRESSIONADA - PARANDO RPA...
🛑 RPA parado pelo usuário durante espera
```

**Solução:**
1. Verificar se alguém pressionou ESC
2. Verificar se há programas interferindo no teclado
3. Testar com teclado diferente

---

### ❌ CAUSA 4: Exceção Não Tratada

**O que acontece:**
```python
# Linha 4894-4897 em main_ciclo.py
except Exception as e:
    gui_log(f"❌ Erro fatal: {e}")
    import traceback
    gui_log(traceback.format_exc())
```

**Quando ocorre:**
- Erro inesperado em qualquer parte do código
- Erro de timeout em API
- Erro de memória
- Erro de permissão de arquivo

**Como identificar nos logs:**
```
❌ Erro fatal: [mensagem de erro]
Traceback (most recent call last):
  File "...", line X, in ...
    [código que causou o erro]
[tipo do erro]: [mensagem detalhada]
```

**Solução:**
1. Ler o traceback completo
2. Identificar qual linha causou o erro
3. Corrigir o bug específico

---

### ❌ CAUSA 5: Erro em `verificar_tem_itens_pendentes()`

**O que acontece:**
```python
# Linha 4305-4306 em main_ciclo.py
except Exception as e:
    gui_log(f"⚠️ Erro ao verificar itens: {e}")
    # Continua sem parar (não é crítico)
```

**Quando ocorre:**
- Erro de autenticação Google Sheets
- Token expirado
- Timeout na API
- Erro de rede

**Como identificar nos logs:**
```
⚠️ Erro ao verificar itens: [mensagem de erro]
```

**IMPORTANTE:** Este erro NÃO para o RPA automaticamente. Ele apenas loga e continua.

**Solução:**
1. Verificar token.json está válido
2. Verificar CredenciaisOracle.json existe
3. Verificar conexão com internet

---

### ❌ CAUSA 6: Falha em `executar_apenas_bancada()`

**O que acontece:**
```python
# Linha 4876-4880 em main_ciclo.py
sucesso = executar_apenas_bancada(config)

if not sucesso:
    gui_log("❌ FALHA ao atualizar bancada")
    break  # ← PARA O RPA
```

**Quando ocorre:**
- Erro ao navegar para bancada
- Erro ao clicar em "Detalhado"
- Erro ao copiar dados da grid
- Erro ao processar dados com pandas

**Como identificar nos logs:**
```
⏰ 15 minutos completos sem novos itens
🔄 Atualizando bancada (executando apenas etapas de navegação + bancada)...
❌ FALHA ao atualizar bancada
```

**Solução:**
1. Verificar navegação até bancada
2. Verificar coordenadas do botão "Detalhado"
3. Verificar tempo de espera (2 minutos)

---

### ❌ CAUSA 7: Ctrl+C (KeyboardInterrupt)

**O que acontece:**
```python
# Linha 4890-4891 em main_ciclo.py
except KeyboardInterrupt:
    gui_log("⏸️ Interrompido pelo usuário (Ctrl+C)")
```

**Quando ocorre:**
- Usuário pressiona Ctrl+C no terminal
- Aplicativo recebe sinal de interrupção

**Como identificar nos logs:**
```
⏸️ Interrompido pelo usuário (Ctrl+C)
🏁 RPA CICLO - Finalizado
```

**Solução:**
- Não pressionar Ctrl+C durante execução
- Se executando via GUI, não fechar o terminal

---

## 🔧 COMO DIAGNOSTICAR

### Passo 1: Encontrar a Última Linha do Log

A última linha antes de "🏁 RPA CICLO - Finalizado" indica a causa:

```
# FAILSAFE:
🛑 FAILSAFE acionado (mouse no canto superior esquerdo)

# ESC:
⚠️ [ESC] TECLA ESC PRESSIONADA - PARANDO RPA...

# Falha Crítica:
❌ FALHA CRÍTICA DETECTADA!

# Erro Fatal:
❌ Erro fatal: [mensagem]

# Ctrl+C:
⏸️ Interrompido pelo usuário (Ctrl+C)
```

### Passo 2: Buscar Mensagens de Erro Acima

Role para cima nos logs e procure:
- ❌ Símbolos de erro
- Mensagens com "ERRO", "FALHA", "EXCEPTION"
- Tracebacks do Python

### Passo 3: Identificar a Etapa Que Falhou

```
[PASSO 1/6] ✅ ou ❌
[PASSO 2/6] ✅ ou ❌
[PASSO 3/6] ✅ ou ❌
...
```

A última etapa **ANTES** do erro é onde ocorreu o problema.

---

## 🎯 SOLUÇÕES RÁPIDAS

### Solução 1: Desabilitar FAILSAFE (Temporário)

**Arquivo:** `main_ciclo.py` linha 4926

```python
# ANTES:
pyautogui.FAILSAFE = True

# DEPOIS (NÃO RECOMENDADO):
pyautogui.FAILSAFE = False
```

**⚠️ AVISO:** Desabilitar FAILSAFE remove a parada de emergência! Use apenas para testes.

---

### Solução 2: Melhorar Tratamento de Erros

**Modificar linha 4816-4829:**

```python
# ANTES:
if not sucesso:
    gui_log("❌ FALHA CRÍTICA DETECTADA!")
    break  # ← PARA IMEDIATAMENTE

# DEPOIS (Tenta novamente):
if not sucesso:
    gui_log("❌ FALHA DETECTADA - Aguardando 30s antes de tentar novamente...")
    tentativas_falha += 1

    if tentativas_falha >= 3:
        gui_log("❌ FALHA CRÍTICA: 3 tentativas falharam consecutivamente")
        break

    time.sleep(30)
    continue  # ← TENTA NOVAMENTE AO INVÉS DE PARAR
else:
    tentativas_falha = 0  # Reset contador de falhas
```

---

### Solução 3: Adicionar Try-Catch no Loop Principal

**Modificar linha 4796:**

```python
# ANTES:
while _rpa_running:
    tem_itens = verificar_tem_itens_pendentes()
    ...

# DEPOIS:
while _rpa_running:
    try:
        tem_itens = verificar_tem_itens_pendentes()
        ...
    except Exception as e:
        gui_log(f"⚠️ Erro no ciclo: {e}")
        gui_log("🔄 Aguardando 60s antes de tentar novamente...")
        time.sleep(60)
        continue  # ← NÃO PARA, APENAS AGUARDA E TENTA DE NOVO
```

---

### Solução 4: Ignorar Erros de Verificação de Pendentes

**Modificar linha 4805:**

```python
# ANTES:
tem_itens = verificar_tem_itens_pendentes()

# DEPOIS:
try:
    tem_itens = verificar_tem_itens_pendentes()
except Exception as e:
    gui_log(f"⚠️ Erro ao verificar pendentes: {e}")
    gui_log("🔄 Considerando que NÃO tem itens (aguardará antes de tentar novamente)")
    tem_itens = False  # Assume que não tem itens se der erro
```

---

## 📊 LOGS DE EXEMPLO

### Exemplo 1: FAILSAFE Acionado

```
14:50:01 - 🔄 Modo contínuo ativado - execução ininterrupta
14:50:02 - 🔍 VERIFICANDO ITENS PENDENTES NO GOOGLE SHEETS...
14:50:05 - ✅ Itens pendentes encontrados!
14:50:06 - 🚀 Iniciando ciclo completo (Oracle + Bancada)...
14:50:07 - [PASSO 1/6] Navegando para Transfer Subinventory...
14:50:10 - 🛑 FAILSAFE acionado (mouse no canto superior esquerdo)
14:50:11 - ⌨️ [Thread Anti-Hibernação] Parando...
14:50:12 - ⌨️ [ESC] Monitoramento de teclado desativado
14:50:13 - 🏁 RPA CICLO - Finalizado
14:50:13 - 📊 Total de ciclos executados: 0
```

**Causa:** Mouse foi para o canto (0, 0)

---

### Exemplo 2: Falha Crítica no Oracle

```
14:50:01 - 🔄 Modo contínuo ativado - execução ininterrupta
14:50:02 - 🔍 VERIFICANDO ITENS PENDENTES NO GOOGLE SHEETS...
14:50:05 - ✅ Itens pendentes encontrados!
14:50:06 - 🚀 Iniciando ciclo completo (Oracle + Bancada)...
14:50:07 - [PASSO 1/6] Navegando para Transfer Subinventory...
14:50:10 - ✅ [PASSO 1/6] Transfer Subinventory detectado
14:50:11 - [PASSO 2/6] Preenchendo Type (SUB)...
14:50:15 - ❌ [PASSO 2/6] ERRO: Tela não detectada após 30s
14:50:16 - ❌ FALHA CRÍTICA DETECTADA!
14:50:16 - 🛑 RPA foi interrompido automaticamente
14:50:17 - 📋 Verifique os logs acima para identificar o problema
14:50:18 - 🏁 RPA CICLO - Finalizado
```

**Causa:** Etapa 2 falhou (tela não detectada)

---

### Exemplo 3: ESC Pressionado

```
14:50:01 - 🔄 Modo contínuo ativado - execução ininterrupta
14:50:02 - 🔍 VERIFICANDO ITENS PENDENTES NO GOOGLE SHEETS...
14:50:05 - ⚠️ Nenhum item pendente encontrado
14:50:06 - 🔄 MODO INTELIGENTE DE ESPERA
14:50:07 - ⏳ Próxima verificação em 1 minuto(s)...
14:50:30 - ⚠️ [ESC] TECLA ESC PRESSIONADA - PARANDO RPA...
14:50:31 - 🛑 RPA parado pelo usuário durante espera
14:50:32 - 🏁 RPA CICLO - Finalizado
```

**Causa:** Usuário pressionou ESC

---

## 🎯 RECOMENDAÇÕES

### Para Produção (24/7):

1. ✅ **Manter FAILSAFE ativado** (segurança)
2. ✅ **Adicionar retry logic** nas etapas críticas
3. ✅ **Não para no primeiro erro** - tenta novamente
4. ✅ **Logs detalhados** para diagnóstico remoto
5. ✅ **Notificação Telegram** quando ocorrer erro
6. ✅ **Monitoramento externo** para reiniciar se necessário

### Para Debug:

1. ✅ **Logs ainda mais verbosos** em cada etapa
2. ✅ **Screenshots automáticos** antes de cada clique
3. ✅ **Validação de coordenadas** antes de usar
4. ✅ **Timeout maior** nas detecções de imagem

---

## 🚀 PRÓXIMOS PASSOS

### 1. Coletar Logs Completos

Pedir ao cliente para enviar o arquivo de log completo da última execução que fechou automaticamente.

### 2. Identificar Padrão

- Sempre na mesma etapa?
- Sempre no mesmo horário?
- Sempre após N minutos?

### 3. Implementar Melhorias

Com base no padrão identificado, implementar retry logic ou tratamento específico.

### 4. Testar em Ambiente Controlado

Reproduzir o problema em ambiente de teste antes de deployar correção.

---

**Diagnóstico criado por:** Claude Code
**Data:** 2026-01-13
**Versão:** RPA Ciclo v4.4
**Status:** ✅ Guia Completo de Diagnóstico
