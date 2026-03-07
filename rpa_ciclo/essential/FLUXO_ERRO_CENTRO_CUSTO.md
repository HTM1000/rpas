# 🔧 FLUXO COMPLETO: Detecção de Erro Centro de Custo no Oracle

**Data:** 2026-01-13
**Sistema:** RPA Ciclo v4.4
**Tipo:** Documentação de Fluxo

---

## 🎯 VISÃO GERAL

O Oracle pode exibir um **popup de erro de centro de custo** quando você tenta salvar um item que possui problemas de configuração no sistema.

**IMPORTANTE:** ❌ **Erro de centro de custo é CRÍTICO!** O Oracle **NÃO VAI SALVAR** o item quando este erro aparece. O popup precisa ser **detectado, fechado e o item marcado como erro**.

---

## 📋 QUANDO O ERRO APARECE

O erro pode aparecer em **DOIS MOMENTOS DIFERENTES**:

1. **ANTES do Ctrl+S**: Durante o preenchimento dos campos, o Oracle pode validar e exibir o erro
2. **APÓS o Ctrl+S**: Ao tentar salvar, o Oracle valida novamente e pode exibir o erro

**Por isso, o RPA verifica nos DOIS momentos!**

---

## 🔄 FLUXO COMPLETO DO PROCESSAMENTO

### 🔹 MOMENTO 1: Verificação ANTES do Ctrl+S

```
┌─────────────────────────────────────────────────┐
│  1. Campos foram preenchidos                   │
│  2. Validação OCR passou                       │
│  3. Evidência PRÉ capturada                    │
│  4. Internet verificada (OK)                   │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  5. VERIFICAR ERRO CENTRO CUSTO (PRÉ)          │
│     • Detectar imagem erro_centro_custo.png    │
│     • Confidence: 0.7 (70%)                    │
│     • Timeout: 3 segundos                      │
└─────────────────────────────────────────────────┘
                    ↓
        ┌───────────────────────┐
        │ Modal detectado?      │
        └───────────────────────┘
           SIM ↓       ↓ NÃO
    ┌──────────┘       └──────────┐
    ↓                              ↓
┌─────────────────────┐  ┌─────────────────────┐
│ ❌ ERRO DETECTADO!  │  │ ✅ Tudo OK          │
│ Pressiona ENTER     │  │ Continua fluxo      │
│ Marca como erro     │  │ Vai para Ctrl+S     │
│ Limpa com F6        │  └─────────────────────┘
│ Pula para próximo   │
└─────────────────────┘
```

**Log de Detecção PRÉ:**
```
[ERRO CC PRE] ═══════════════════════════════════════════════
[ERRO CC PRE] 🔍 Verificando se modal de erro centro de custo apareceu...
⚠️ [ERRO CC PRE] MODAL DE ERRO CENTRO DE CUSTO DETECTADO!
[ERRO CC PRE] >> Pressionando ENTER (fechar modal)...
[ERRO CC PRE] << ENTER pressionado
✅ [ERRO CC PRE] Modal fechado!
❌ [ERRO CC PRE] ERRO: Oracle não salvará o item (erro centro de custo)
```

---

### 🔹 MOMENTO 2: Verificação APÓS o Ctrl+S

```
┌─────────────────────────────────────────────────┐
│  1. Ctrl+S foi executado                       │
│  2. Aguarda tela voltar ao normal              │
│  3. Screenshot PÓS capturado                   │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  4. VERIFICAR ERRO CENTRO CUSTO (PÓS)          │
│     • Detectar imagem erro_centro_custo.png    │
│     • Confidence: 0.7 (70%)                    │
│     • Timeout: 3 segundos                      │
└─────────────────────────────────────────────────┘
                    ↓
        ┌───────────────────────┐
        │ Modal detectado?      │
        └───────────────────────┘
           SIM ↓       ↓ NÃO
    ┌──────────┘       └──────────┐
    ↓                              ↓
┌─────────────────────┐  ┌─────────────────────┐
│ ❌ ERRO DETECTADO!  │  │ ✅ Salvamento OK    │
│ Pressiona ENTER     │  │ Atualiza Sheets     │
│ Marca como erro     │  │ Item concluído      │
│ Limpa com F6        │  └─────────────────────┘
│ Pula para próximo   │
└─────────────────────┘
```

**Log de Detecção PÓS:**
```
[ERRO CC POS] ═══════════════════════════════════════════════
[ERRO CC POS] 🔍 Verificando se modal de erro centro de custo apareceu...
⚠️ [ERRO CC POS] MODAL DE ERRO CENTRO DE CUSTO DETECTADO!
[ERRO CC POS] >> Pressionando ENTER (fechar modal)...
[ERRO CC POS] << ENTER pressionado
✅ [ERRO CC POS] Modal fechado!
❌ [ERRO CC POS] ERRO: Oracle não salvará o item (erro centro de custo)
```

---

## 🔍 DETALHES TÉCNICOS

### Detecção do Popup

**Arquivo de Imagem:** `informacoes/erro_centro_custo.png`

**Método de Detecção:** OpenCV com template matching
- **Confiança mínima:** 70% (0.7)
- **Timeout:** 3 segundos
- **Multi-escala:** Detecta mesmo se popup estiver em tamanho diferente

**Por que confidence 0.7?**
A imagem capturada contém um código de item específico (ex: E2029A) que varia entre diferentes erros. Usamos confidence menor (0.7 ao invés de 0.8) para detectar o modal mesmo quando o código do item for diferente.

**Código da Função:**
```python
def verificar_e_fechar_modal_erro_centro_custo(timeout=3):
    """
    Verifica se o modal de erro de centro de custo apareceu e fecha com ENTER

    Returns:
        bool: True se modal foi detectado e fechado, False caso contrário

    IMPORTANTE: Erro de centro de custo impede o salvamento no Oracle.
    A imagem contém um código de item específico, mas detectamos com confidence
    menor (0.7) para ser mais flexível e detectar independente do código.
    """
    caminho = os.path.join(base_path, "informacoes", "erro_centro_custo.png")

    if not os.path.isfile(caminho):
        gui_log("[ERRO CC] ⚠️ Imagem erro_centro_custo.png não encontrada")
        return False

    gui_log("[ERRO CC] 🔍 Verificando se modal de erro centro de custo apareceu...")
    encontrado = detectar_imagem_opencv(caminho, confidence=0.7, timeout=timeout)

    if encontrado:
        gui_log("⚠️ [ERRO CC] MODAL DE ERRO CENTRO DE CUSTO DETECTADO!")
        time.sleep(0.5)
        gui_log("[ERRO CC] >> Pressionando ENTER (fechar modal)...")
        if not MODO_TESTE:
            pyautogui.press("enter")
        gui_log("[ERRO CC] << ENTER pressionado")
        time.sleep(1)
        gui_log("✅ [ERRO CC] Modal fechado!")
        gui_log("❌ [ERRO CC] ERRO: Oracle não salvará o item (erro centro de custo)")
        return True
    else:
        gui_log("[ERRO CC] ✅ Nenhum modal detectado")
        return False
```

---

## 🧹 LIMPEZA DO FORMULÁRIO

Quando o erro é detectado, o formulário é limpo com **F6** antes de continuar:

```python
# 1. Pausar hook do teclado (evita interceptação)
keyboard.unhook_all()

# 2. Tentar F6 até 3 vezes
for tentativa in range(3):
    try:
        pyautogui.press('f6')
        time.sleep(0.5)
        limpar_sucesso = True
        break
    except Exception as e_f6:
        gui_log(f"[ERRO CC] ⚠️ Erro na tentativa {tentativa+1}: {e_f6}")
        time.sleep(0.3)

# 3. Reativar hook do teclado
keyboard.hook(parar_callback)
```

**Por que pausar o hook?**
O sistema usa um hook global de teclado para detectar ESC. Durante o F6, precisamos pausar temporariamente para evitar que o hook intercepte a tecla.

---

## 📊 ATUALIZAÇÃO DO GOOGLE SHEETS

Quando o erro é detectado, o status é atualizado no Google Sheets:

```python
# Atualizar coluna "Status Oracle" (coluna T)
range_str = f"'Separação'!T{i}:T{i}"
service.spreadsheets().values().update(
    spreadsheetId=SPREADSHEET_ID,
    range=range_str,
    valueInputOption="RAW",
    body={"values": [["Erro Centro de Custo"]]}
).execute()
```

**Resultado no Sheets:**
```
Status Oracle = "Erro Centro de Custo"
```

---

## ⚠️ IMPORTANTE: NÃO ADICIONA AO CACHE

Quando detecta erro de centro de custo, o item **NÃO é adicionado ao cache** `processados.json`:

```python
# IMPORTANTE: NÃO adicionar ao cache (permite reprocessar)
gui_log("[ERRO CC] ⚠️ Item NÃO adicionado ao cache (pode ser reprocessado)")
```

**Por quê?**
- O erro pode ser temporário (problema de configuração no Oracle)
- Permite que o item seja reprocessado em ciclos futuros
- Se o erro for corrigido no Oracle, o item será processado com sucesso na próxima vez

---

## 🔄 FLUXOGRAMA VISUAL COMPLETO

```
┌─────────────────────────────────────────────┐
│  1. Preencher campos no Oracle             │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  2. Validação com OCR                      │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  3. Capturar evidência PRÉ                 │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  4. Verificar internet                      │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  5. VERIFICAR ERRO CC (PRÉ) - 3s timeout    │
└─────────────────────────────────────────────┘
                    ↓
        ┌───────────────────────┐
        │ Modal detectado PRÉ?  │
        └───────────────────────┘
           SIM ↓       ↓ NÃO
    ┌──────────┘       └──────────┐
    ↓                              ↓
┌─────────────────────┐  ┌─────────────────────┐
│ ❌ ERRO PRÉ         │  │ ✅ OK - Continua    │
│ → ENTER             │  └─────────────────────┘
│ → F6                │              ↓
│ → Status Oracle     │  ┌─────────────────────┐
│ → Próximo item      │  │  6. Executar Ctrl+S │
└─────────────────────┘  └─────────────────────┘
                                     ↓
                         ┌─────────────────────┐
                         │  7. Aguardar 35s    │
                         └─────────────────────┘
                                     ↓
                         ┌─────────────────────┐
                         │  8. Capturar PÓS    │
                         └─────────────────────┘
                                     ↓
                         ┌─────────────────────────────┐
                         │  9. VERIFICAR ERRO CC (PÓS) │
                         │     3s timeout              │
                         └─────────────────────────────┘
                                     ↓
                         ┌───────────────────────┐
                         │ Modal detectado PÓS?  │
                         └───────────────────────┘
                            SIM ↓       ↓ NÃO
                     ┌──────────┘       └──────────┐
                     ↓                              ↓
           ┌─────────────────────┐  ┌─────────────────────┐
           │ ❌ ERRO PÓS         │  │ ✅ Salvamento OK    │
           │ → ENTER             │  └─────────────────────┘
           │ → F6                │              ↓
           │ → Status Oracle     │  ┌─────────────────────┐
           │ → Próximo item      │  │  10. Atualizar      │
           └─────────────────────┘  │      Google Sheets  │
                                    └─────────────────────┘
                                                ↓
                                    ┌─────────────────────┐
                                    │  11. Remover cache  │
                                    └─────────────────────┘
                                                ↓
                                        ✅ ITEM PROCESSADO!
```

---

## 📝 LOGS DE EXEMPLO

### Caso 1: Erro Detectado ANTES do Ctrl+S

```
14:50:01 - 📝 Processando: E2029A | Qtd: 10 | Ref: 202501001
14:50:10 - ✅ [VALIDADOR] Validação OK
14:50:11 - 📸 [EVIDÊNCIAS] Screenshot PRÉ capturado
14:50:12 - ✅ [INTERNET] OK - Ping: 15ms
14:50:13 - [ERRO CC PRE] ═══════════════════════════════════════════════
14:50:13 - [ERRO CC PRE] 🔍 Verificando se modal de erro centro de custo apareceu...
14:50:14 - ⚠️ [ERRO CC PRE] MODAL DE ERRO CENTRO DE CUSTO DETECTADO!
14:50:14 - [ERRO CC PRE] >> Pressionando ENTER (fechar modal)...
14:50:14 - [ERRO CC PRE] << ENTER pressionado
14:50:15 - ✅ [ERRO CC PRE] Modal fechado!
14:50:15 - ❌ [ERRO CC PRE] ERRO: Oracle não salvará o item (erro centro de custo)
14:50:16 - [ERRO CC PRE] ═══════════════════════════════════════════════
14:50:16 - [ERRO CC PRE] 🧹 Pressionando F6 para limpar formulário...
14:50:17 - [ERRO CC PRE] >> Tentativa 1/3: Pressionando F6...
14:50:17 - [ERRO CC PRE] << F6 pressionado
14:50:18 - [ERRO CC PRE] ✅ Formulário limpo com F6
14:50:19 - ✅ [ERRO CC PRE] Status atualizado: 'Erro Centro de Custo'
14:50:20 - [ERRO CC PRE] ⚠️ Item NÃO adicionado ao cache (pode ser reprocessado)
14:50:21 - [ERRO CC PRE] ➡️ Continuando para próximo item...
```

---

### Caso 2: Erro Detectado APÓS o Ctrl+S

```
14:50:01 - 📝 Processando: E2029A | Qtd: 10 | Ref: 202501001
14:50:10 - ✅ [VALIDADOR] Validação OK
14:50:11 - 📸 [EVIDÊNCIAS] Screenshot PRÉ capturado
14:50:12 - ✅ [INTERNET] OK - Ping: 15ms
14:50:13 - [ERRO CC PRE] ═══════════════════════════════════════════════
14:50:13 - [ERRO CC PRE] 🔍 Verificando se modal de erro centro de custo apareceu...
14:50:16 - [ERRO CC PRE] ✅ Nenhum modal detectado
14:50:17 - [SAVE] >> Pressionando CTRL+S...
14:50:17 - [SAVE] << CTRL+S pressionado
14:50:18 - ⏳ [SALVAMENTO] Aguardando confirmação de salvamento...
14:50:23 - ✅ [SALVAMENTO] Tela correta detectada! Salvamento confirmado em 5.2s
14:50:24 - 📸 [EVIDÊNCIAS] Screenshot PÓS capturado
14:50:25 - [ERRO CC POS] ═══════════════════════════════════════════════
14:50:25 - [ERRO CC POS] 🔍 Verificando se modal de erro centro de custo apareceu...
14:50:26 - ⚠️ [ERRO CC POS] MODAL DE ERRO CENTRO DE CUSTO DETECTADO!
14:50:26 - [ERRO CC POS] >> Pressionando ENTER (fechar modal)...
14:50:26 - [ERRO CC POS] << ENTER pressionado
14:50:27 - ✅ [ERRO CC POS] Modal fechado!
14:50:27 - ❌ [ERRO CC POS] ERRO: Oracle não salvará o item (erro centro de custo)
14:50:28 - [ERRO CC POS] ═══════════════════════════════════════════════
14:50:28 - [ERRO CC POS] 🧹 Pressionando F6 para limpar formulário...
14:50:29 - [ERRO CC POS] >> Tentativa 1/3: Pressionando F6...
14:50:29 - [ERRO CC POS] << F6 pressionado
14:50:30 - [ERRO CC POS] ✅ Formulário limpo com F6
14:50:31 - ✅ [ERRO CC POS] Status atualizado: 'Erro Centro de Custo'
14:50:32 - [ERRO CC POS] ⚠️ Item NÃO adicionado ao cache (pode ser reprocessado)
14:50:33 - [ERRO CC POS] ➡️ Continuando para próximo item...
```

---

### Caso 3: Nenhum Erro (Sucesso)

```
14:50:01 - 📝 Processando: E2029A | Qtd: 10 | Ref: 202501001
14:50:10 - ✅ [VALIDADOR] Validação OK
14:50:11 - 📸 [EVIDÊNCIAS] Screenshot PRÉ capturado
14:50:12 - ✅ [INTERNET] OK - Ping: 15ms
14:50:13 - [ERRO CC PRE] ═══════════════════════════════════════════════
14:50:13 - [ERRO CC PRE] 🔍 Verificando se modal de erro centro de custo apareceu...
14:50:16 - [ERRO CC PRE] ✅ Nenhum modal detectado
14:50:17 - [SAVE] >> Pressionando CTRL+S...
14:50:17 - [SAVE] << CTRL+S pressionado
14:50:18 - ⏳ [SALVAMENTO] Aguardando confirmação de salvamento...
14:50:23 - ✅ [SALVAMENTO] Tela correta detectada! Salvamento confirmado em 5.2s
14:50:24 - 📸 [EVIDÊNCIAS] Screenshot PÓS capturado
14:50:25 - [ERRO CC POS] ═══════════════════════════════════════════════
14:50:25 - [ERRO CC POS] 🔍 Verificando se modal de erro centro de custo apareceu...
14:50:28 - [ERRO CC POS] ✅ Nenhum modal detectado
14:50:29 - ☁️ Atualizando Google Sheets...
14:50:30 - ✅ Item processado e confirmado!
```

---

## 🎯 RESUMO EXECUTIVO

### O que acontece quando aparece erro de centro de custo?

1. ✅ **RPA detecta o popup** automaticamente (ANTES ou APÓS Ctrl+S)
2. ✅ **Pressiona ENTER** para fechar o modal
3. ✅ **Limpa formulário com F6**
4. ✅ **Marca no Google Sheets** como "Erro Centro de Custo"
5. ✅ **NÃO adiciona ao cache** (permite reprocessar)
6. ✅ **Continua para próximo item**

### Erro de centro de custo é crítico?

**✅ SIM!** O Oracle **NÃO VAI SALVAR** o item quando este erro aparece. O RPA detecta, fecha o modal, marca como erro e continua.

### O RPA para quando vê o erro?

**❌ NÃO!** O RPA **detecta**, **fecha**, **marca** e **continua** automaticamente. Não há interrupção do fluxo.

### Por que verificar em DOIS momentos?

O erro pode aparecer:
- **ANTES do Ctrl+S**: Durante validação dos campos preenchidos
- **APÓS o Ctrl+S**: Durante tentativa de salvamento

Por isso verificamos nos **DOIS momentos** para garantir detecção completa!

---

## 📦 ARQUIVOS NECESSÁRIOS

### Imagem de Referência

**Caminho:** `informacoes/erro_centro_custo.png`

**IMPORTANTE:** A imagem deve existir na pasta `informacoes/` para que a detecção funcione. Se a imagem não existir, o sistema apenas loga um warning e continua sem erro.

### Código Implementado

**Arquivo:** `main_ciclo.py`

**Função:** `verificar_e_fechar_modal_erro_centro_custo()` (linhas 1412-1459)

**Integração 1 (PRÉ):** Linhas 2885-2966 (após verificação de internet, antes de Ctrl+S)

**Integração 2 (PÓS):** Linhas 3025-3106 (após screenshot PÓS, antes de checar sucesso_save)

---

## 🔧 CONFIGURAÇÃO

### Confidence Level

Configurado em `0.7` (70%) para ser mais flexível:

```python
encontrado = detectar_imagem_opencv(caminho, confidence=0.7, timeout=timeout)
```

**Por que 0.7 e não 0.8?**
A imagem de erro contém o código do item (ex: E2029A) que varia entre diferentes casos. Com 0.7, detectamos o modal mesmo quando o código for diferente.

### Timeout

Configurado em `3 segundos`:

```python
erro_centro_custo_detectado = verificar_e_fechar_modal_erro_centro_custo(timeout=3)
```

**Por que 3 segundos?**
Tempo suficiente para detectar o modal sem atrasar muito o processamento quando ele não aparece.

---

**Documentação criada por:** Claude Code
**Data:** 2026-01-13
**Versão:** RPA Ciclo v4.4
**Status:** ✅ Completo e Validado
