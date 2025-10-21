# Ajustes da Bancada - RPA_Ciclo

## 📋 Ajustes Realizados

### **1. Coordenadas Corrigidas (config.json)**

| Elemento | Antes | Agora | Status |
|----------|-------|-------|--------|
| Bancada Material | (568, 294) | **(598, 294)** | ✅ Corrigido |
| Botão X (Fechar) | (754, 97) | **(755, 95)** | ✅ Corrigido |

---

### **2. Etapa 07 - Extração de Dados Reescrita**

#### **Problema Anterior:**
- ❌ Aguardava apenas 30 segundos
- ❌ Não tinha múltiplas tentativas de leitura
- ❌ Clicava em "Localizar" ao invés de pressionar Enter

#### **Solução Implementada (baseada em main.py):**

✅ **Passo 1:** Clicar em "Detalhado"
✅ **Passo 2:** Pressionar **Enter** (não clica em Localizar!)
✅ **Passo 3:** Aguardar **2 MINUTOS** antes de clicar na célula
✅ **Passo 4:** Clicar na célula Org
✅ **Passo 5:** Limpar clipboard
✅ **Passo 6:** Shift+F10 (menu contexto)
✅ **Passo 7:** Navegar menu (3x seta ↓) + Enter
✅ **Passo 8:** Aguardar 3s para iniciar cópia
✅ **Passo 9:** **AGUARDAR 15 MINUTOS** (900s) para Oracle processar
✅ **Passo 10:** Ler clipboard com até **20 tentativas** (1.5s cada)

---

### **3. Função `ler_clipboard_bancada` Adicionada**

```python
def ler_clipboard_bancada(max_tentativas=20, espera=1.5):
    """
    Lê o clipboard SEM enviar Ctrl+C.
    Aguarda o Oracle terminar a cópia em background.
    """
    for tentativa in range(max_tentativas):
        txt = (pyperclip.paste() or "").strip()
        if txt and len(txt) > 50:
            return txt
        time.sleep(espera)
    return ""
```

**Características:**
- 🔄 Até 20 tentativas
- ⏱️ 1.5s entre tentativas
- ✅ Não envia Ctrl+C (Oracle copia em background)
- 📊 Logs de progresso a cada tentativa

---

### **4. Logs Melhorados**

A etapa 07 agora mostra logs detalhados:

```
============================================================
🤖 ETAPA 7: Extração de dados da Bancada
============================================================
✅ pyperclip disponível para copiar dados
📍 [1/9] Clicando em 'Detalhado'...
⌨️ [2/9] Pressionando Enter...
⏳ [3/9] Aguardando 2 minutos para grid carregar...
📍 [4/9] Clicando na célula Org...
🧹 [5/9] Limpando clipboard...
⌨️ [6/9] Abrindo menu de contexto (Shift+F10)...
⌨️ [7/9] Navegando menu para 'Copiar Todas as Linhas'...
   Seta para baixo 1/3
   Seta para baixo 2/3
   Seta para baixo 3/3
   Pressionando Enter para copiar...
⏳ [8/9] Aguardando Oracle iniciar cópia em background (3s)...
⏳ [9/9] Aguardando Oracle processar dados (15 minutos)...
💡 O Oracle pode levar vários minutos para copiar dados grandes
💡 Não interrompa o processo - aguarde até o final
⏳ Aguardando... 15 minutos restantes
⏳ Aguardando... 14 minutos restantes
... (progresso a cada minuto)
📋 Lendo clipboard (até 20 tentativas, 1.5s cada)...
✅ Clipboard lido na tentativa 1: 125,430 caracteres
============================================================
✅ DADOS COPIADOS COM SUCESSO!
📊 Total: 1,234 linhas
📦 Tamanho: 122.46 KB (125,430 caracteres)
============================================================
👀 Preview (500 chars): Org.\tSub.\tEndereço\tItem...
```

---

### **5. Etapa 06 - Coordenadas do Config**

Agora usa coordenadas do `config.json` ao invés de hardcoded:

```python
# ANTES (hardcoded)
clicar_coordenada(831, 333, duplo=True)

# AGORA (do config)
coord = config["coordenadas"]["tela_07_bancada_material"]
clicar_coordenada(coord["x"], coord["y"], duplo=coord.get("duplo_clique", True))
```

---

## 🔑 Diferenças Chave: Por que funciona agora?

| Aspecto | Antes (Não funcionava) | Agora (Funciona!) |
|---------|------------------------|-------------------|
| **Tempo de espera** | 30 segundos | ✅ **15 MINUTOS** |
| **Localizar** | Clicava no botão | ✅ Pressiona **Enter** |
| **Aguardar grid** | Imediato | ✅ **2 minutos** |
| **Tentativas clipboard** | 1 tentativa | ✅ **20 tentativas** |
| **Logs** | Básicos | ✅ **Detalhados** (9 passos) |
| **Preview dados** | Não tinha | ✅ Mostra **preview** |

---

## ⚙️ Configurações Importantes

### **Tempo de Espera Oracle (15 minutos)**

Se precisar ajustar, edite em `main_ciclo.py` linha ~768:

```python
tempo_espera_oracle = 15 * 60  # 15 minutos = 900 segundos
```

**Valores recomendados:**
- Dados pequenos (< 1000 linhas): 5 minutos
- Dados médios (1000-5000 linhas): 10 minutos
- Dados grandes (> 5000 linhas): **15 minutos** (recomendado)

### **Aguardar Grid Carregar (2 minutos)**

Se precisar ajustar, edite em `main_ciclo.py` linha ~720:

```python
if not aguardar_com_pausa(120, "Carregamento da grid (2 minutos)"):
```

**Valores recomendados:**
- Oracle rápido: 60 segundos (1 minuto)
- Oracle normal: **120 segundos (2 minutos)** (recomendado)
- Oracle lento: 180 segundos (3 minutos)

---

## 🧪 Como Testar

### **1. Teste Python Direto:**
```bash
cd rpa_ciclo
python main_ciclo.py
```

### **2. Gerar e Testar .exe:**
```bash
build_prod.bat
dist\RPA_Ciclo.exe
```

### **3. Observar os Logs:**

Durante a execução, acompanhe os logs para verificar:
- ✅ Se as coordenadas estão corretas
- ✅ Se os 15 minutos de espera estão sendo respeitados
- ✅ Se o clipboard está sendo lido corretamente
- ✅ Se os dados foram copiados com sucesso

---

## 📊 Fluxo Completo da Etapa 07

```
┌─────────────────────────────────────────────────────┐
│  ETAPA 7: EXTRAÇÃO DE DADOS DA BANCADA             │
├─────────────────────────────────────────────────────┤
│                                                     │
│  [1/9] Clicar em "Detalhado"                       │
│                                                     │
│  [2/9] Pressionar Enter                            │
│        (não clica em Localizar!)                   │
│                                                     │
│  [3/9] ⏳ Aguardar 2 MINUTOS                        │
│        (grid carregar)                             │
│                                                     │
│  [4/9] Clicar na célula Org                        │
│                                                     │
│  [5/9] Limpar clipboard                            │
│                                                     │
│  [6/9] Shift+F10 (menu)                            │
│                                                     │
│  [7/9] 3x Seta ↓ + Enter                           │
│        (Copiar Todas as Linhas)                    │
│                                                     │
│  [8/9] ⏳ Aguardar 3s                               │
│        (iniciar cópia)                             │
│                                                     │
│  [9/9] ⏳ Aguardar 15 MINUTOS                       │
│        (Oracle processar)                          │
│        Mostra progresso a cada minuto              │
│                                                     │
│  [10] 📋 Ler clipboard                             │
│        Até 20 tentativas (1.5s cada)               │
│                                                     │
│  ✅ SUCESSO!                                        │
│  Mostra: linhas, tamanho, preview                  │
└─────────────────────────────────────────────────────┘
```

---

## 🐛 Solução de Problemas

### **Problema: "Clipboard vazio após todas as tentativas"**

**Possíveis causas:**
1. Oracle não terminou de copiar (aguardar mais tempo)
2. Grid não tem dados
3. Coordenadas erradas

**Solução:**
- Aumentar tempo de espera de 15 para 20 minutos
- Verificar se grid tem dados visíveis
- Verificar coordenadas no config.json

### **Problema: "Erro ao clicar em Bancada Material"**

**Solução:**
- Coordenada corrigida para (598, 294)
- Se ainda errar, capture a coordenada correta e edite config.json

### **Problema: "Não mostra logs detalhados"**

**Solução:**
- Certifique-se de estar usando a versão atualizada
- Verifique se `gui_log` está funcionando
- Execute com GUI para ver logs em tempo real

---

## 📝 Resumo dos Arquivos Modificados

| Arquivo | O que mudou |
|---------|-------------|
| `config.json` | ✏️ Coordenadas corrigidas (Bancada Material e Botão X) |
| `main_ciclo.py` | ✏️ Etapa 07 reescrita com lógica do main.py |
| `main_ciclo.py` | ➕ Função `ler_clipboard_bancada` adicionada |
| `main_ciclo.py` | ✏️ Etapa 06 usa coordenadas do config |
| `AJUSTES_BANCADA.md` | ➕ Esta documentação |

---

## ✅ Checklist de Verificação

Antes de rodar em produção, verifique:

- [ ] Coordenadas no config.json estão corretas
- [ ] Build do .exe funciona sem erros
- [ ] Teste com dados pequenos primeiro
- [ ] Acompanhe os logs durante execução
- [ ] Verifique se clipboard tem dados ao final
- [ ] Oracle tem espaço em disco suficiente
- [ ] Não há outros processos travando o clipboard

---

**Data:** 2025-10-18
**Versão:** 2.1 (Ajustes Bancada)
**Status:** ✅ **Pronto para Teste**

**Próximo passo:** Testar com dados reais e ajustar tempo de espera se necessário
