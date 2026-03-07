# 🔍 OVERVIEW COMPLETO - FLUXO DE QUANTIDADE NEGATIVA

**Data:** 13/01/2026
**Status:** ANÁLISE DE PROBLEMA REPORTADO

---

## ❌ PROBLEMA REPORTADO

> "ele não deu o enter no negativo, ele tentou verificar os itens"

**Sintomas:**
- ✅ Modal quantidade negativa aparece
- ❌ ENTER não é pressionado
- ❌ Modal fica aberto
- ✅ RPA "tenta verificar os itens" (validador híbrido)

---

## 📊 FLUXO ATUAL (DETALHADO)

### 1️⃣ PREENCHER QUANTIDADE (linhas 2947-2981)

```python
# Captura baseline de pixels amarelos ANTES
pixels_amarelos_antes = contar_pixels_cor("amarelo")  # Ex: 120 pixels

# Preenche quantidade
pyautogui.press("delete")
pyautogui.click(coords["quantidade"])
pyautogui.write(quantidade)  # Ex: "10"

# Sai do campo (TAB) - AQUI MODAL PODE APARECER
pyautogui.press("tab")
time.sleep(1)  # Aguarda 1 segundo
```

**Importante:** Modal pode aparecer imediatamente OU com delay após TAB.

---

### 2️⃣ DETECÇÃO DIFERENCIAL (linhas 2983-3029)

```python
# Detecta se modal apareceu comparando pixels
modal_qtd_neg = detectar_modal_diferencial(
    cor_esperada="amarelo",
    pixels_antes=pixels_amarelos_antes,  # 120
    threshold_aumento=500  # Precisa aumentar 500+ pixels
)

if modal_qtd_neg:
    # MODAL DETECTADO
    gui_log("⚠️ [QTD NEG] MODAL DETECTADO")

    # ✅ ENTER (linha 2998-2999)
    if not MODO_TESTE:
        pyautogui.press("enter")
    time.sleep(1)

    # ✅ F6 (linha 3007-3008)
    if not MODO_TESTE:
        pyautogui.press('f6')
    time.sleep(1.5)

    # ✅ Atualiza Sheets (linha 3014-3019)
    service.spreadsheets().values().update(...)

    # ✅ PULA (linha 3025)
    continue  # ← Próximo item
else:
    # MODAL NÃO DETECTADO - continua normal
    gui_log("[QTD NEG] ✅ Nenhum modal detectado")
```

**MODO_TESTE:** False (linha 173) - então PyAutoGUI ESTÁ ativo!

---

### 3️⃣ VERIFICAR TIMEOUT (linhas 3031-3045)

```python
if verificar_tempo_oracle_rapido():
    gui_log("⏱️ TIMEOUT DETECTADO")
    return False
```

---

### 4️⃣ VALIDADOR HÍBRIDO (linhas 3047-3200+)

```python
if VALIDADOR_HIBRIDO_DISPONIVEL:
    gui_log("[VALIDADOR] Aguardando 1 segundo...")
    time.sleep(1)

    # Valida TODOS os campos visualmente (OCR)
    validacao_ok, tipo_erro = validar_campos_oracle_completo(
        coords_validacao, item, quantidade, ...
    )

    if not validacao_ok:
        if tipo_erro == "QTD_NEGATIVA":
            # ❌ DETECTOU QUANTIDADE NEGATIVA AQUI TAMBÉM!
            mensagem_status = "Quantidade Negativa"

            # F6 para limpar
            pyautogui.press('f6')

            # Atualiza Sheets
            service.spreadsheets().values().update(...)

            # PULA
            continue
```

**PROBLEMA IDENTIFICADO:** Se o modal aparecer com delay, a detecção diferencial pode não capturar, mas o validador híbrido vai detectar depois!

---

## 🐛 POSSÍVEIS CAUSAS DO BUG

### Causa 1: Modal Aparece Devagar
```
TAB pressionado → sleep(1) → Detecção diferencial → Modal aparece DEPOIS
```
- Detecção diferencial: NÃO detecta (modal ainda não apareceu)
- Validador híbrido: Detecta (modal já está na tela)
- **Mas validador não dá ENTER primeiro!**

---

### Causa 2: Threshold Muito Alto (500 pixels)
```
Baseline: 120 pixels amarelos
Modal aparece: 450 pixels amarelos (+330)
Aumento: 330 < 500 → NÃO DETECTA
```
- Detecção diferencial: NÃO detecta (aumento insuficiente)
- Validador híbrido: Detecta visualmente
- **Mas validador não dá ENTER primeiro!**

---

### Causa 3: Modal Aparece Só ao Validar
```
TAB → Nada acontece
Validador tenta ler campos → Oracle processa → Modal aparece
```
- Detecção diferencial: NÃO detecta (ainda sem modal)
- Validador híbrido: Detecta durante leitura
- **Mas validador não dá ENTER primeiro!**

---

## ❌ BUG NO VALIDADOR HÍBRIDO

**DESCOBERTA CRÍTICA:** O validador híbrido detecta quantidade negativa (linha 3076-3079) mas **NÃO PRESSIONA ENTER ANTES DO F6**!

```python
if tipo_erro == "QTD_NEGATIVA":
    mensagem_status = "Quantidade Negativa"
    gui_log("[VALIDADOR] Quantidade negativa detectada")

    # ❌ FALTA ENTER AQUI!
    # Vai direto para F6 (linha 3097)
    pyautogui.press('f6')  # ← Modal ainda está aberto!
```

**Comparar com detecção diferencial:**
```python
if modal_qtd_neg:
    # ✅ TEM ENTER
    pyautogui.press("enter")  # ← Fecha modal primeiro
    time.sleep(1)
    pyautogui.press('f6')     # ← Aí limpa
```

---

## 🔧 ANÁLISE DE LOGS NECESSÁRIA

Para diagnosticar, preciso saber:

1. **Logs da detecção diferencial:**
   ```
   [QUANTIDADE] Baseline amarelo: ??? pixels
   [MODAL DIFF] Pixels amarelo ANTES: ???
   [MODAL DIFF] Pixels amarelo DEPOIS: ???
   [MODAL DIFF] Aumento: ??? pixels
   ```

   **Se aumento < 500:** Não detectou (threshold muito alto)
   **Se aumento >= 500:** Detectou mas algo falhou

2. **Logs do validador:**
   ```
   [VALIDADOR] Aguardando 1 segundo...
   [VALIDADOR] Validação FALHOU - dados não conferem!
   [VALIDADOR] Tipo de erro: QTD_NEGATIVA
   ```

   **Se apareceu isso:** Modal foi detectado pelo validador, não pela detecção diferencial

3. **Logs do ENTER:**
   ```
   [QTD NEG] >> Pressionando ENTER (fechar modal)...
   [QTD NEG] << ENTER pressionado
   ```

   **Se NÃO apareceu:** Detecção diferencial não detectou o modal

---

## ✅ SOLUÇÕES POSSÍVEIS

### Solução 1: Adicionar ENTER no Validador Híbrido

Quando validador detectar QTD_NEGATIVA, pressionar ENTER antes do F6:

```python
if tipo_erro == "QTD_NEGATIVA":
    mensagem_status = "Quantidade Negativa"

    # ✅ ADICIONAR: Fechar modal primeiro
    gui_log("[VALIDADOR] >> Pressionando ENTER para fechar modal...")
    pyautogui.press("enter")
    time.sleep(1)
    gui_log("[VALIDADOR] << ENTER pressionado")

    # Aí sim limpar com F6
    gui_log("[VALIDADOR] 🧹 Pressionando F6...")
    pyautogui.press('f6')
```

---

### Solução 2: Diminuir Threshold da Detecção Diferencial

De 500 para 300 pixels:

```python
modal_qtd_neg = detectar_modal_diferencial(
    cor_esperada="amarelo",
    pixels_antes=pixels_amarelos_antes,
    threshold_aumento=300  # ← Era 500
)
```

---

### Solução 3: Aumentar Timeout Antes da Detecção

Aguardar 2 segundos ao invés de 1:

```python
pyautogui.press("tab")
time.sleep(2)  # ← Era 1 segundo
```

---

### Solução 4: Detectar Novamente Antes do Validador

Fazer segunda verificação antes do validador híbrido:

```python
# Antes do validador, verificar novamente
if contar_pixels_cor("amarelo") > pixels_amarelos_antes + 500:
    # Modal apareceu com delay
    pyautogui.press("enter")
    time.sleep(1)
    pyautogui.press('f6')
    time.sleep(1.5)
    # Atualizar Sheets e continue
```

---

## 🎯 RECOMENDAÇÃO IMEDIATA

**APLICAR SOLUÇÃO 1** (mais simples e garante que sempre fecha modal):

1. Adicionar ENTER no validador híbrido quando detectar QTD_NEGATIVA
2. Adicionar ENTER no validador híbrido quando detectar ERRO_CENTRO_CUSTO
3. Garantir que modal SEMPRE fecha antes de F6

**Localização:** `main_ciclo.py`, linhas ~3076-3083 (QTD_NEGATIVA) e ~3080-3083 (ERRO_CENTRO_CUSTO)

---

## 📋 CHECKLIST DE CORREÇÃO

- [ ] Adicionar ENTER antes F6 no validador para QTD_NEGATIVA
- [ ] Adicionar ENTER antes F6 no validador para ERRO_CENTRO_CUSTO
- [ ] Testar com item quantidade negativa
- [ ] Verificar logs: ENTER deve aparecer ANTES de F6
- [ ] Confirmar que modal fecha
- [ ] Confirmar que pula para próximo item

---

## 🔍 PRÓXIMO PASSO

**PRECISO DOS LOGS** para confirmar qual das causas é o problema:

1. Abra o RPA
2. Execute com um item quantidade negativa
3. Copie os logs completos desde:
   ```
   [QUANTIDADE] Baseline amarelo: XXX pixels
   ```
   Até:
   ```
   [QTD NEG] ⏭️ Pulando para próximo item
   ```
   OU
   ```
   [VALIDADOR] Tipo de erro: QTD_NEGATIVA
   ```

Com os logs, posso identificar exatamente onde o fluxo está falhando!

---

**AGUARDANDO LOGS PARA DIAGNÓSTICO PRECISO** 🔍
