# 🔢 FLUXO COMPLETO: Popup de Quantidade Negativa no Oracle

**Data:** 2026-01-12
**Sistema:** RPA Ciclo v4.3
**Tipo:** Documentação de Fluxo

---

## 🎯 VISÃO GERAL

Quando você insere uma **quantidade negativa** no Oracle, o sistema exibe um **popup de confirmação**.

**IMPORTANTE:** ✅ **Quantidade negativa NÃO é um erro!** É uma operação **válida e permitida** no Oracle. O popup é apenas uma **confirmação** que precisa ser fechada.

---

## 📋 FLUXO COMPLETO DO PROCESSAMENTO

### 🔹 ETAPA 1: Preenchimento dos Campos

```
1. RPA preenche campos:
   - Item: E2029A
   - Sub Origem: 06
   - End Origem: 01
   - Sub Destino: 01
   - End Destino: 01
   - Quantidade: -10  ← NEGATIVA!
   - Referência: 202501001
```

**Log:**
```
ℹ️ Linha 10 - Quantidade NEGATIVA (-10) - será processada normalmente
```

---

### 🔹 ETAPA 2: Validação com OCR

Durante a validação (leitura da tela com OCR), o Oracle pode exibir o popup de quantidade negativa.

**O que acontece:**

```python
# 1. RPA copia valores dos campos para validar
gui_log("[QTD NEG] 🔍 Verificando se modal apareceu durante validação...")

# 2. Detecta o popup usando OpenCV
modal_encontrado = detectar_imagem_opencv("qtd_negativa.png", confidence=0.8, timeout=3)

# 3. Se detectou, fecha o modal
if modal_encontrado:
    gui_log("✅ [QTD NEG] Modal de confirmação detectado durante validação!")
    time.sleep(0.5)

    gui_log("[QTD NEG] >> Pressionando ENTER (fechar modal)...")
    pyautogui.press("enter")  # ← FECHA O MODAL
    gui_log("[QTD NEG] << ENTER pressionado")

    time.sleep(1)
    gui_log("✅ [QTD NEG] Modal fechado! Continuando validação...")
```

**Log:**
```
[QTD NEG] 🔍 Verificando se modal apareceu durante validação...
✅ [QTD NEG] Modal de confirmação detectado durante validação!
[QTD NEG] >> Pressionando ENTER (fechar modal)...
[QTD NEG] << ENTER pressionado
✅ [QTD NEG] Modal fechado! Continuando validação...
```

**Resultado da Validação:**

```python
# Quantidade negativa NÃO é considerada erro!
if tipo_erro == "QTD_NEGATIVA":
    gui_log(f"✅ [VALIDADOR] Quantidade negativa detectada - É PERMITIDA, validação OK")
    validacao_ok = True  # ← VALIDAÇÃO PASSA!
    mensagem_status = "Processo Oracle Concluído"
```

---

### 🔹 ETAPA 3: Salvamento com Ctrl+S

Após validação bem-sucedida, o RPA salva com Ctrl+S:

```python
# 1. Adicionar ao cache ANTES de Ctrl+S
gui_log("💾 [CRÍTICO] Adicionando ao cache ANTES de Ctrl+S...")
cache.adicionar(id_linha, linha_atual, item, quantidade, referencia, status="ctrl_s_enviado")

# 2. Verificar internet
gui_log("🌐 [INTERNET] Verificando conectividade ANTES de Ctrl+S...")
if not internet_ok:
    # Parar se não tem internet
    return False

# 3. Executar Ctrl+S
gui_log("[SAVE] >> Pressionando CTRL+S...")
pyautogui.hotkey("ctrl", "s")
gui_log("[SAVE] << CTRL+S pressionado")
time.sleep(0.5)
```

**Log:**
```
[SAVE] Iniciando salvamento com Ctrl+S...
[SAVE] >> Pressionando CTRL+S...
[SAVE] << CTRL+S pressionado
[SAVE] Aguardando 0.5 segundos...
[SAVE] ✅ Ctrl+S executado
```

---

### 🔹 ETAPA 4: Aguardar Confirmação de Salvamento

Após Ctrl+S, o RPA aguarda a tela voltar ao estado normal:

```python
gui_log("[SAVE] Aguardando confirmação de salvamento...")
sucesso_save, tipo_save, tempo_save = aguardar_salvamento_concluido()
```

**Lógica de Confirmação:**

```
1. Aguarda 5 segundos
2. Verifica se tela voltou ao normal (detecta tela_transferencia_subinventory.png)
3. Se SIM: ✅ Salvo com sucesso!
4. Se NÃO: Aguarda mais 30 segundos
5. Verifica novamente
6. Se SIM: ✅ Salvo com sucesso!
7. Se NÃO: ❌ ERRO - Tela não voltou ao normal
```

**Log de Sucesso:**
```
⏳ [SALVAMENTO] Aguardando confirmação de salvamento...
   Método: DETECÇÃO DE IMAGEM (tela_transferencia_subinventory.png)
   Estratégia: 5s + (se falhar) 30s + (se falhar) ERRO
⏳ [SALVAMENTO] Aguardando 5 segundos...
🔍 [SALVAMENTO] Verificando tela (tentativa 1/2)...
✅ [SALVAMENTO] Tela correta detectada! Salvamento confirmado em 5.2s
```

---

### 🔹 ETAPA 5: Captura de Evidências

Após confirmação de salvamento, captura screenshot pós-save:

```python
gui_log("📸 [EVIDÊNCIAS] Capturando screenshot PÓS-save...")
screenshot_pos_path = _evidencias_manager.capturar_screenshot(
    item=item,
    quantidade=quantidade,
    referencia=referencia,
    sufixo="POS"
)
gui_log(f"✅ [EVIDÊNCIAS] Screenshot PÓS capturado: {screenshot_pos_path}")
```

---

### 🔹 ETAPA 6: Atualizar Google Sheets

Por fim, atualiza o status no Google Sheets:

```python
mensagem_status = "Processo Oracle Concluído"
gui_log(f"✅ Linha {i} - {mensagem_status}")
gui_log("☁️ Atualizando Google Sheets...")
# Atualiza coluna "Status Oracle" = "Processo Oracle Concluído"
```

**Log:**
```
☁️ Atualizando Google Sheets...
✅ Google Sheets atualizado com sucesso!
✅ Item processado e confirmado!
```

---

## 🔄 FLUXOGRAMA VISUAL

```
┌─────────────────────────────────────────────┐
│  1. Preencher campos no Oracle             │
│     Quantidade: -10 (NEGATIVA)             │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  2. Validação com OCR                      │
│     Copia valores dos campos               │
└─────────────────────────────────────────────┘
                    ↓
        ┌───────────────────────┐
        │ Popup apareceu?       │
        └───────────────────────┘
           SIM ↓       ↓ NÃO
    ┌──────────┘       └──────────┐
    ↓                              ↓
┌─────────────────────┐  ┌─────────────────────┐
│ Detecta popup       │  │ Continua validação  │
│ Pressiona ENTER     │  └─────────────────────┘
│ Fecha modal         │              ↓
└─────────────────────┘              │
            ↓                        │
            └────────────┬───────────┘
                         ↓
┌─────────────────────────────────────────────┐
│  3. Validação OK (qtd negativa é PERMITIDA) │
│     validacao_ok = True                     │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  4. Adicionar ao cache (anti-duplicação)    │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  5. Verificar internet                      │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  6. Executar Ctrl+S                         │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  7. Aguardar tela voltar ao normal          │
│     • 5s → Verifica                         │
│     • 30s → Verifica novamente              │
└─────────────────────────────────────────────┘
                    ↓
        ┌───────────────────────┐
        │ Tela voltou OK?       │
        └───────────────────────┘
           SIM ↓       ↓ NÃO
    ┌──────────┘       └──────────┐
    ↓                              ↓
┌─────────────────────┐  ┌─────────────────────┐
│ ✅ Salvamento OK    │  │ ❌ ERRO             │
└─────────────────────┘  │ Pressiona F6        │
            ↓             │ Limpa formulário    │
            │             └─────────────────────┘
            ↓
┌─────────────────────────────────────────────┐
│  8. Capturar evidências (screenshot PÓS)    │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  9. Atualizar Google Sheets                 │
│     Status Oracle = "Processo Oracle        │
│                      Concluído"             │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  10. Remover do cache (concluído)           │
└─────────────────────────────────────────────┘
                    ↓
            ✅ ITEM PROCESSADO!
```

---

## 🔍 DETALHES TÉCNICOS

### Detecção do Popup

**Arquivo de Imagem:** `informacoes/qtd_negativa.png`

**Método de Detecção:** OpenCV com template matching
- **Confiança mínima:** 80% (0.8)
- **Timeout:** 3 segundos
- **Multi-escala:** Detecta mesmo se popup estiver em tamanho diferente

**Código:**
```python
modal_encontrado = detectar_imagem_opencv(
    "informacoes/qtd_negativa.png",
    confidence=0.8,
    timeout=3
)
```

### Ação ao Detectar

1. **Aguarda 0.5s** para estabilização
2. **Pressiona ENTER** para fechar o modal
3. **Aguarda 1s** para o modal desaparecer completamente

**Código:**
```python
time.sleep(0.5)
pyautogui.press("enter")
time.sleep(1)
```

### Validação da Quantidade Negativa

```python
if tipo_erro == "QTD_NEGATIVA":
    # ✅ Quantidade negativa é PERMITIDA!
    gui_log(f"✅ [VALIDADOR] Quantidade negativa detectada - É PERMITIDA, validação OK")
    validacao_ok = True
    mensagem_status = "Processo Oracle Concluído"
```

---

## ⚠️ CENÁRIOS DE ERRO

### Cenário 1: Popup não Fecha

**Problema:** Popup detectado, mas ENTER não fecha

**Causa Possível:**
- Oracle travou
- Foco não estava no modal
- Keyboard hook interceptou o ENTER

**Solução no Código:**
```python
# Pausa hook temporariamente
keyboard.unhook_all()

# Pressiona ENTER
pyautogui.press('enter')

# Reativa hook
keyboard.hook(parar_callback)
```

### Cenário 2: Tela não Volta ao Normal

**Problema:** Após Ctrl+S, tela não volta ao estado esperado

**Causa Possível:**
- Oracle travou durante salvamento
- Processo muito lento
- Erro de rede

**O que o RPA faz:**
```
1. Aguarda 5s + 30s = 35s total
2. Se não voltar: MARCA COMO ERRO
3. Pressiona F6 (limpar formulário)
4. Continua para próximo item
```

**Status no Sheets:** `"Tela não voltou ao normal após Ctrl+S (35.2s) - Verificar Oracle"`

---

## 📊 LOGS DE EXEMPLO

### Caso de Sucesso (Quantidade Negativa)

```
14:50:01 - 📝 Processando: E2029A | Qtd: -10 | Ref: 202501001
14:50:01 - ℹ️ Linha 10 - Quantidade NEGATIVA (-10) - será processada normalmente
14:50:02 - 🖱️ Clicando campo Item (101, 156)
14:50:02 - ⌨️ Digitando: E2029A
...
14:50:10 - 🔍 Validando com OCR...
14:50:11 - [QTD NEG] 🔍 Verificando se modal apareceu durante validação...
14:50:11 - ✅ [QTD NEG] Modal de confirmação detectado durante validação!
14:50:12 - [QTD NEG] >> Pressionando ENTER (fechar modal)...
14:50:12 - [QTD NEG] << ENTER pressionado
14:50:13 - ✅ [QTD NEG] Modal fechado! Continuando validação...
14:50:14 - ✅ [VALIDADOR] Quantidade negativa detectada - É PERMITIDA, validação OK
14:50:15 - ✅ Item validado: E2029A ✓
14:50:15 - ✅ Quantidade validada: -10 ✓
14:50:16 - ✅ Referência validada: 202501001 ✓
14:50:17 - 💾 [CRÍTICO] Adicionando ao cache ANTES de Ctrl+S...
14:50:18 - 🌐 [INTERNET] Verificando conectividade...
14:50:19 - ✅ Internet OK (latência: 15ms)
14:50:20 - 📸 [EVIDÊNCIAS] Capturando screenshot PRÉ-save...
14:50:21 - [SAVE] >> Pressionando CTRL+S...
14:50:21 - [SAVE] << CTRL+S pressionado
14:50:22 - ⏳ [SALVAMENTO] Aguardando confirmação...
14:50:27 - ✅ [SALVAMENTO] Tela correta detectada! Salvamento confirmado em 5.2s
14:50:28 - 📸 [EVIDÊNCIAS] Capturando screenshot PÓS-save...
14:50:29 - ☁️ Atualizando Google Sheets...
14:50:30 - ✅ Item processado e confirmado!
```

---

## 🎯 RESUMO EXECUTIVO

### O que acontece quando aparece popup de quantidade negativa?

1. ✅ **RPA detecta o popup** automaticamente usando OpenCV
2. ✅ **Pressiona ENTER** para fechar o modal
3. ✅ **Continua validação** normalmente
4. ✅ **Quantidade negativa é PERMITIDA** (não é erro)
5. ✅ **Salva com Ctrl+S** normalmente
6. ✅ **Item é processado com sucesso**

### Quantidade negativa é erro?

**❌ NÃO!** Quantidade negativa é uma **operação válida** no Oracle. O popup é apenas uma **confirmação** que o RPA fecha automaticamente.

### O RPA para quando vê o popup?

**❌ NÃO!** O RPA **detecta**, **fecha** e **continua** automaticamente. Não há interrupção do fluxo.

---

**Documentação criada por:** Claude Code
**Data:** 2026-01-12
**Versão:** RPA Ciclo v4.3
**Status:** ✅ Completo e Validado
