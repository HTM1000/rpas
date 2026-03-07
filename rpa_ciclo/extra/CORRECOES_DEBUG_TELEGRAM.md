# Correções Implementadas - Debug e Telegram

## Data: 27/10/2025

## 🎯 Problemas Resolvidos

### 1. **Telegram não enviando notificações**
**Problema:** O RPA não estava enviando notificações para o Telegram durante o processamento.

**Causa:**
- Erros eram silenciados com `except: pass`
- Falta de logs de debug para identificar problemas
- Inicialização do notificador sem verificação de sucesso

**Solução:**
- ✅ Adicionados logs detalhados em todas as notificações
- ✅ Mensagem de teste enviada na inicialização
- ✅ Verificação de `enabled` antes de enviar
- ✅ Erros são capturados e logados (não mais silenciados)

### 2. **Erro "Tela Divergente" sem evidências**
**Problema:** O RPA reportava "tela divergente" mas não salvava evidências para análise.

**Causa:**
- Função `detectar_imagem_opencv` não salvava screenshots quando falhava
- Impossível verificar o que estava errado na detecção

**Solução:**
- ✅ Screenshots automáticos salvos em caso de falha
- ✅ Salva 3 arquivos de debug:
  - `debug_tela_atual_TIMESTAMP.png` - Tela capturada no momento da falha
  - `debug_template_usado_TIMESTAMP.png` - Imagem de referência usada
  - `debug_comparacao_TIMESTAMP.png` - Comparação lado a lado
- ✅ Logs detalhados com:
  - Dimensões da tela e do template
  - Confiança alcançada vs. confiança esperada
  - Tentativas de multi-escala
- ✅ Notificação Telegram quando ocorre erro de tela divergente

---

## 📝 Mudanças Detalhadas

### Arquivo: `main_ciclo.py`

#### 1. Função `detectar_imagem_opencv` (linha ~988)

**ANTES:**
```python
def detectar_imagem_opencv(caminho_imagem, confidence=0.8, timeout=5):
    # ... detecção ...
    gui_log(f"[OPENCV] ❌ Imagem NÃO detectada após {timeout}s")
    return False  # SEM salvar debug
```

**DEPOIS:**
```python
def detectar_imagem_opencv(caminho_imagem, confidence=0.8, timeout=5, salvar_debug=True):
    # ... detecção ...

    # Logs detalhados
    gui_log(f"[OPENCV] 🔍 Iniciando detecção de: {nome_imagem}")
    gui_log(f"[OPENCV]    Dimensões template: {template_w}x{template_h}")
    gui_log(f"[OPENCV]    Confiança mínima: {confidence:.2%}")

    # ... tentativas ...

    # SE FALHAR: Salvar evidências
    gui_log(f"[OPENCV] ❌ Imagem NÃO detectada após {timeout}s")
    gui_log(f"[OPENCV] 📊 Melhor confiança alcançada: {melhor_score_global:.2%}")

    if salvar_debug:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Salvar tela capturada
        cv2.imwrite(f"debug_tela_atual_{timestamp}.png", ultima_screenshot)

        # Salvar template usado
        cv2.imwrite(f"debug_template_usado_{timestamp}.png", ultimo_template_usado)

        # Salvar comparação lado a lado
        cv2.imwrite(f"debug_comparacao_{timestamp}.png", comparacao)

        gui_log(f"[DEBUG] 📁 Verifique os arquivos debug_*.png")
```

#### 2. Função `aguardar_salvamento_concluido` (linha ~987)

**ADICIONADO:**
```python
# FALHA: Tela não voltou ao estado correto
tempo_total = time.time() - tempo_inicio
gui_log(f"❌ [SALVAMENTO] FALHOU - Tela não voltou ao estado correto após {tempo_total:.1f}s")

# Notificar via Telegram
try:
    if _telegram_notifier and _telegram_notifier.enabled:
        _telegram_notifier.notificar_erro_critico(
            f"TELA DIVERGENTE\n\n"
            f"A tela não voltou ao estado esperado após salvamento.\n"
            f"Tempo esperado: {tempo_total:.1f}s\n\n"
            f"Verifique os arquivos debug_*.png para análise."
        )
except:
    pass
```

#### 3. Notificações de Início de Item (linha ~1856)

**ANTES:**
```python
if _telegram_notifier:
    try:
        _telegram_notifier.notificar_inicio_item(i, item, quantidade, sub_o, sub_d)
    except:
        pass  # ERRO SILENCIADO
```

**DEPOIS:**
```python
if _telegram_notifier:
    try:
        if _telegram_notifier.enabled:
            resultado = _telegram_notifier.notificar_inicio_item(i, item, quantidade, sub_o, sub_d)
            gui_log(f"📱 [TELEGRAM] Notificação de início enviada: {resultado}")
        else:
            gui_log("⚠️ [TELEGRAM] Notificador desabilitado (token/chat_id não configurados)")
    except Exception as e:
        gui_log(f"⚠️ [TELEGRAM] Erro ao notificar início: {e}")
else:
    gui_log("⚠️ [TELEGRAM] Notificador não inicializado")
```

#### 4. Inicialização do Telegram (linha ~3595)

**ANTES:**
```python
if TELEGRAM_DISPONIVEL:
    try:
        _telegram_notifier = inicializar_telegram()
    except:
        _telegram_notifier = None  # ERRO SILENCIADO
```

**DEPOIS:**
```python
if TELEGRAM_DISPONIVEL:
    try:
        _telegram_notifier = inicializar_telegram()
        if _telegram_notifier and _telegram_notifier.enabled:
            gui_log("✅ [TELEGRAM] Notificador inicializado com sucesso")
            gui_log(f"   Bot Token: {_telegram_notifier.bot_token[:20]}...")
            gui_log(f"   Chat ID: {_telegram_notifier.chat_id}")
            # Enviar mensagem de teste
            resultado = _telegram_notifier.enviar_mensagem("🤖 RPA Ciclo iniciado!")
            gui_log(f"   Teste de envio: {resultado}")
        else:
            gui_log("⚠️ [TELEGRAM] Notificador criado mas desabilitado (verifique config.json)")
    except Exception as e:
        gui_log(f"⚠️ [TELEGRAM] Erro ao inicializar: {e}")
        _telegram_notifier = None
else:
    gui_log("⚠️ [TELEGRAM] Módulo telegram_notifier não disponível")
    _telegram_notifier = None
```

---

## 🔍 Como Usar o Debug

### Analisando Falha de Detecção

Quando o RPA reportar "Tela Divergente", você encontrará 3 arquivos:

1. **`debug_tela_atual_20251027_131226.png`**
   - O que estava na tela no momento da verificação
   - Compare visualmente com a tela esperada

2. **`debug_template_usado_20251027_131226.png`**
   - A imagem de referência que o RPA estava procurando
   - Pode estar redimensionada se a resolução mudou

3. **`debug_comparacao_20251027_131226.png`**
   - Lado a lado: tela atual vs. template esperado
   - Facilita identificar diferenças

### Verificando Logs do Telegram

Agora você verá no log da GUI:

```
✅ [TELEGRAM] Notificador inicializado com sucesso
   Bot Token: 8300855810:AAEC4OTv...
   Chat ID: -4669835847
   Teste de envio: True

📱 [TELEGRAM] Notificação de início enviada: True
📱 [TELEGRAM] Notificação de sucesso enviada: True
```

Se algo der errado:
```
⚠️ [TELEGRAM] Erro ao notificar início: Connection timeout
⚠️ [TELEGRAM] Notificador desabilitado (token/chat_id não configurados)
```

---

## ⚙️ Configuração do Telegram

No arquivo `config.json`:

```json
{
  "telegram": {
    "bot_token": "8300855810:AAEC4OTval-NLjnquKsd49aOG7b4NJZo5mU",
    "chat_id": "-4669835847",
    "habilitado": true
  }
}
```

**Verificações:**
- ✅ `bot_token` está correto?
- ✅ `chat_id` está correto (com `-` se for grupo)?
- ✅ `habilitado` está como `true`?
- ✅ Bot foi adicionado ao grupo/chat?

---

## 🚀 Próximos Passos

1. **Rebuild do executável** com as correções:
   ```bash
   cd C:\Users\ID135\OneDrive\Desktop\www\rpas\rpa_ciclo
   BUILD_GENESYS.bat
   ```

2. **Teste o novo executável:**
   - Verifique se recebe mensagem "🤖 RPA Ciclo iniciado!" no Telegram
   - Execute um ciclo e confirme notificações por item
   - Se ocorrer erro de tela, verifique os arquivos `debug_*.png`

3. **Análise de Problemas:**
   - Se Telegram não enviar: verifique logs `[TELEGRAM]` na GUI
   - Se tela divergente: analise arquivos `debug_*.png`
   - Compare dimensões reportadas nos logs com a resolução da tela

---

## 📊 Melhorias de Performance

- **Logs mais informativos:** Score de confiança, dimensões, tentativas
- **Debug visual:** Imagens lado a lado facilitam diagnóstico
- **Notificações em tempo real:** Acompanhe processamento pelo celular
- **Rastreabilidade:** Timestamp em todos os arquivos de debug

---

## 🔧 Troubleshooting

### Telegram não envia mensagens

**Sintoma:**
```
⚠️ [TELEGRAM] Erro ao notificar início: Connection timeout
```

**Soluções:**
1. Verifique conexão com internet
2. Teste manualmente: `python teste_telegram_simples.py`
3. Confirme que o bot está ativo no @BotFather
4. Verifique se o chat_id está correto

### Tela sempre divergente

**Sintoma:**
```
[OPENCV] 📊 Melhor confiança alcançada: 45.32% (esperado >= 80.00%)
```

**Soluções:**
1. Verifique `debug_comparacao_*.png` - compare visualmente
2. Imagem de referência pode estar desatualizada
3. Resolução da tela pode ter mudado
4. Oracle pode ter alteração visual (janela, fonte, cor)
5. Recapture: `python capturar_tela_referencia.py`

### Debug não salva arquivos

**Sintoma:**
Não aparece `debug_*.png` mesmo com erro

**Soluções:**
1. Verifique permissões da pasta
2. Verifique se OpenCV está disponível (log no início)
3. Espaço em disco suficiente
4. Antivírus pode estar bloqueando

---

## 📌 Arquivos Modificados

- ✅ `main_ciclo.py` - Função `detectar_imagem_opencv` (debug screenshots)
- ✅ `main_ciclo.py` - Função `aguardar_salvamento_concluido` (notificação Telegram)
- ✅ `main_ciclo.py` - Notificações de início/erro/sucesso (logs detalhados)
- ✅ `main_ciclo.py` - Função `main` (inicialização Telegram com verificação)

---

## ✅ Checklist de Testes

Após rebuild, teste:

- [ ] Recebe mensagem "🤖 RPA Ciclo iniciado!" no Telegram
- [ ] Recebe notificação "🔵 PROCESSANDO ITEM" ao iniciar item
- [ ] Recebe notificação "✅ ITEM CONCLUÍDO" ao finalizar item
- [ ] Recebe notificação "❌ ERRO NO ITEM" em caso de erro
- [ ] Recebe notificação "🛑 ERRO CRÍTICO" em tela divergente
- [ ] Arquivos `debug_*.png` são criados em caso de falha
- [ ] Logs `[TELEGRAM]` aparecem na GUI
- [ ] Logs `[OPENCV]` mostram dimensões e confiança

---

**Autor:** Claude Code
**Versão:** 3.1 - Debug Avançado e Telegram Integrado
