# Clique no Botão LIMPAR - Logs Detalhados

## 📋 Problema Identificado

Quando validação falha ou sistema trava, o formulário Oracle fica com dados pendentes e o RPA não consegue continuar para próxima linha sem limpar primeiro.

## ✅ Solução Implementada

Adicionamos **logs extremamente detalhados** para o clique no botão LIMPAR em **TODOS os pontos de falha**:

### Pontos onde LIMPAR é clicado:

1. ❌ **Validação Híbrida FALHOU** (campos incorretos)
2. ⚠️ **Sistema TRAVADO** no Ctrl+S (120s sem mudança)

---

## 📊 Logs Detalhados do Clique LIMPAR

### Quando Validação Falha

```
❌ [VALIDADOR] Validação FALHOU - dados não conferem!
[VALIDADOR] Tipo de erro: CAMPO_VAZIO - campos vazios
[VALIDADOR] Marcando linha como 'Erro Oracle: dados faltantes por item não cadastrado'

[VALIDADOR] ═══════════════════════════════════════════════
[VALIDADOR] 🧹 Clicando no botão LIMPAR para fechar formulário...
[VALIDADOR] Coordenadas LIMPAR: X=332, Y=66
[VALIDADOR] >> Clicando em (332, 66)...
[VALIDADOR] << Clique executado
[VALIDADOR] ✅ Botão Limpar clicado com sucesso
[VALIDADOR] Aguardando 3 segundos para formulário limpar...
[VALIDADOR] ✅ Formulário deve estar limpo agora
[VALIDADOR] ═══════════════════════════════════════════════

✅ Status atualizado: 'Erro Oracle: dados faltantes por item não cadastrado'
[VALIDADOR] Pulando para próxima linha (esta será reprocessada)
```

### Quando Sistema Trava no Ctrl+S

```
⚠️ [SALVAMENTO] TRAVADO - Sem mudança nos pixels por 120s
   Tempo total decorrido: 120.5s
   Campo Item ainda preenchido: True (4.2%)
❌ [SAVE] SISTEMA TRAVADO após 120.5s - linha não foi salva
[SAVE] Tipo: TRAVADO

[SAVE] ═══════════════════════════════════════════════
[SAVE] 🧹 Clicando no botão LIMPAR para forçar limpeza do formulário...
[SAVE] Coordenadas LIMPAR: X=332, Y=66
[SAVE] >> Clicando em (332, 66)...
[SAVE] << Clique executado
[SAVE] ✅ Botão Limpar clicado com sucesso
[SAVE] Aguardando 3 segundos para formulário limpar...
[SAVE] ✅ Formulário deve estar limpo agora
[SAVE] ═══════════════════════════════════════════════

✅ Status atualizado no Sheets: 'Sistema travado no Ctrl+S (120s sem mudança) - Verificar Oracle/Conexão'
[SAVE] Pulando para próxima linha (esta será reprocessada)
```

---

## 🔍 Informações no Log

Cada clique no LIMPAR agora mostra:

1. **Coordenadas exatas:** `X=332, Y=66`
2. **Momento do clique:** `>> Clicando em (X, Y)...`
3. **Confirmação:** `<< Clique executado`
4. **Sucesso:** `✅ Botão Limpar clicado com sucesso`
5. **Espera:** `Aguardando 3 segundos` (aumentado de 2s para 3s)
6. **Validação:** `✅ Formulário deve estar limpo agora`

---

## 🐛 Se o Clique NÃO Funcionar

Se você ver no log que o clique foi executado mas o formulário NÃO limpou, as possíveis causas são:

### 1. Coordenadas Incorretas

**Sintoma:**
```
[VALIDADOR] >> Clicando em (332, 66)...
[VALIDADOR] << Clique executado
[VALIDADOR] ✅ Botão Limpar clicado com sucesso
```
Mas formulário continua com dados.

**Solução:**
Recapturar coordenadas do botão LIMPAR:

```python
import pyautogui
import time

print("Posicione o mouse NO CENTRO do botão LIMPAR em 3 segundos...")
time.sleep(3)
x, y = pyautogui.position()
print(f"Coordenadas: X={x}, Y={y}")
```

Atualize em `config.json`:
```json
"tela_06_limpar": {
  "x": X_CAPTURADO,
  "y": Y_CAPTURADO,
  "descricao": "Clique no botão Limpar"
}
```

### 2. Botão Fora de Foco

**Sintoma:**
Clique executa mas nada acontece (janela Oracle não está em primeiro plano).

**Solução:**
Adicionar clique de foco antes do LIMPAR. Edite `main_ciclo.py`:

```python
# Dar foco na janela Oracle antes de clicar LIMPAR
try:
    # Clicar em algum lugar da janela para dar foco
    pyautogui.click(500, 300)  # Ajustar coordenadas
    time.sleep(0.5)
except:
    pass

# Agora clicar no LIMPAR
pyautogui.click(x_limpar, y_limpar)
```

### 3. Delay Insuficiente

**Sintoma:**
Clique funciona mas RPA continua antes do formulário limpar.

**Solução:**
Aumentar delay após clique. **JÁ FIZEMOS ISSO** (aumentamos de 2s para 3s).

Se ainda insuficiente, edite em `main_ciclo.py`:

```python
time.sleep(5)  # Aumentar para 5 segundos
```

### 4. Modal Bloqueando

**Sintoma:**
Há um modal (popup) na frente do botão LIMPAR.

**Solução:**
Primeiro fechar modal, depois clicar LIMPAR:

```python
# Fechar possível modal (ESC ou Enter)
pyautogui.press('esc')
time.sleep(1)

# Depois clicar LIMPAR
pyautogui.click(x_limpar, y_limpar)
```

---

## ⚙️ Configuração Atual

### Coordenadas do Botão LIMPAR

```json
{
  "tela_06_limpar": {
    "x": 332,
    "y": 66,
    "descricao": "Clique no botão Limpar"
  }
}
```

### Timing do Clique

- **Delay após clique:** 3 segundos (aumentado!)
- **Logs antes:** Coordenadas, intenção
- **Logs durante:** Momento do clique
- **Logs depois:** Confirmação, espera

---

## 📸 Como Testar

### 1. Forçar Erro de Validação

Edite uma linha no Google Sheets para ter **dados inválidos** (ex: item que não existe).

Execute o RPA e observe os logs:

```bash
cd rpa_ciclo
python RPA_Ciclo_GUI_v2.py
```

**Procure por:**
```
[VALIDADOR] 🧹 Clicando no botão LIMPAR...
[VALIDADOR] Coordenadas LIMPAR: X=332, Y=66
[VALIDADOR] >> Clicando em (332, 66)...
[VALIDADOR] << Clique executado
```

### 2. Forçar Travamento

Desconecte internet temporariamente após Ctrl+S.

Aguarde 120 segundos.

**Procure por:**
```
[SAVE] 🧹 Clicando no botão LIMPAR para forçar limpeza...
[SAVE] Coordenadas LIMPAR: X=332, Y=66
[SAVE] >> Clicando em (332, 66)...
[SAVE] << Clique executado
```

### 3. Verificar Formulário

Após ver os logs do clique LIMPAR, **visualmente confirme** que o formulário Oracle foi limpo (todos os campos vazios).

---

## 🛠️ Tratamento de Erros

Se o clique FALHAR (exceção Python), você verá logs detalhados:

```
[VALIDADOR] ❌ ERRO CRÍTICO ao clicar em Limpar: [mensagem do erro]
[VALIDADOR] Tipo do erro: [tipo da exceção]
[VALIDADOR] Traceback: [stack trace completo]
```

Isso ajuda a diagnosticar:
- Coordenadas fora da tela
- PyAutoGUI bloqueado
- Janela Oracle fechada
- Outros problemas

---

## 📋 Checklist de Verificação

Quando o RPA falhar em uma linha, verifique no log:

- [ ] Viu mensagem `🧹 Clicando no botão LIMPAR`?
- [ ] Viu coordenadas `X=332, Y=66`?
- [ ] Viu `>> Clicando em (X, Y)...`?
- [ ] Viu `<< Clique executado`?
- [ ] Viu `✅ Botão Limpar clicado com sucesso`?
- [ ] Viu `Aguardando 3 segundos`?
- [ ] Formulário Oracle foi limpo visualmente?

**Se TODOS os itens acima = SIM mas formulário NÃO limpou:**
→ Problema são as **coordenadas** do botão LIMPAR (recapture!)

**Se algum item = NÃO:**
→ Problema na **lógica de execução** (verifique código)

---

## 🚀 Resumo das Melhorias

| Aspecto                  | Antes                  | Depois                          |
|--------------------------|------------------------|---------------------------------|
| **Logs do clique**       | Mínimos                | Extremamente detalhados         |
| **Coordenadas no log**   | Não                    | Sim (X, Y sempre mostrado)      |
| **Delay após clique**    | 2 segundos             | 3 segundos (50% mais tempo)     |
| **Tratamento de erro**   | Genérico               | Traceback completo              |
| **Validação visual**     | Não                    | Mensagem "deve estar limpo"     |

---

## 📞 Próximos Passos

1. **Execute o RPA** e force um erro (item inválido ou desconecte internet)
2. **Copie os logs** da seção LIMPAR
3. **Verifique visualmente** se o formulário limpou
4. **Se NÃO limpou:** Recapture coordenadas do botão LIMPAR
5. **Teste novamente** até confirmar que funciona

---

**Autor:** Claude Code
**Data:** 2025-10-24
**Status:** ✅ Logs detalhados implementados
**Coordenadas atuais:** X=332, Y=66
