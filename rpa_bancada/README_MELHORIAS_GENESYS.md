# 🚀 Melhorias do RPA Ciclo Integradas ao RPA Bancada

Versão atualizada com tecnologias do **Genesys (RPA Ciclo)** para melhor performance e confiabilidade.

## 📋 O Que Mudou?

### 1. ⌨️ **Pressiona Enter ao Invés de Clicar em "Localizar"**
**ANTES:**
```python
move_click(*COORD_LOCALIZAR)  # Clicava no botão
```

**AGORA:**
```python
pag.press('enter')  # Pressiona Enter (mais rápido e confiável)
```

**Por quê?**
- Mais rápido
- Não depende de coordenadas do botão "Localizar"
- Mesma funcionalidade (Oracle aceita Enter após "Detalhado")

---

### 2. 🎯 **Monitoramento Inteligente do Clipboard**
**ANTES:**
```python
# Aguardava 15 minutos fixos
time.sleep(POPUP_MAX)  # 900 segundos
texto = ler_clipboard_sem_ctrlc()
```

**AGORA:**
```python
# Detecta automaticamente quando Oracle terminou de copiar
texto = monitorar_clipboard_inteligente(
    max_tempo=15 * 60,        # Máximo 15 minutos
    intervalo_check=3,        # Verifica a cada 3 segundos
    estabilidade_segundos=30  # Considera completo após 30s sem mudança
)
```

**Como funciona?**
1. Oracle abre modal "Exportação em andamento" quando começa a copiar
2. Sistema monitora o clipboard a cada 3 segundos
3. Detecta quando o conteúdo para de crescer (estabiliza)
4. Após 30 segundos sem mudança, considera a cópia completa
5. Retorna os dados **imediatamente** (não espera 15 minutos inteiros!)

**Vantagens:**
- ✅ **Mais rápido**: Não espera 15 minutos se terminar antes
- ✅ **Mais confiável**: Detecta quando realmente terminou
- ✅ **Feedback em tempo real**: Mostra progresso da cópia
- ✅ **Detecta falhas**: Sabe se Oracle travou ou não está copiando

**Logs durante monitoramento:**
```
🔍 MONITORAMENTO INTELIGENTE DO CLIPBOARD
⏱️ Tempo máximo: 15 minutos
🔄 Verificação a cada: 3 segundos
✅ Estabilidade requerida: 30 segundos

📊 [45s] Clipboard cresceu +15,234 chars (total: 45,678 chars)
📊 [48s] Clipboard cresceu +12,456 chars (total: 58,134 chars)
⏸️ [51s] Clipboard estável por 3s (58,134 chars)
⏸️ [54s] Clipboard estável por 6s (58,134 chars)
...
⏸️ [81s] Clipboard estável por 30s (58,134 chars)

✅ CLIPBOARD ESTABILIZADO - CÓPIA COMPLETA!
📊 Linhas: 1,234
📦 Tamanho: 56.78 KB (58,134 caracteres)
⏱️ Tempo total: 81s (1min 21s)
```

---

### 3. 🖱️ **Movimento Contínuo do Mouse (Anti-Hibernação ULTRA)**
**ANTES:**
```python
# Apenas Keep-Awake básico (Shift a cada 50 segundos)
keep_awake_thread = threading.Thread(target=keep_awake_loop)
```

**AGORA:**
```python
# Movimento contínuo do mouse + teclado
stop_mouse_event = iniciar_movimento_mouse_continuo()
# Move mouse 5px a cada 1 segundo
# Pressiona Shift a cada 15 segundos
```

**O que faz?**
- Move o mouse 5 pixels para cima/baixo alternadamente a cada 1 segundo
- Pressiona Shift a cada 15 segundos
- Previne **hibernação**, **screensaver** e **bloqueio de tela**

**Por quê?**
- Durante o monitoramento do clipboard (que pode levar até 15 minutos)
- Garante que o Windows/Oracle não hibernem
- Garante que o Oracle não perca foco da janela

**Controle automático:**
- Inicia automaticamente quando começa a monitorar clipboard
- Para automaticamente quando termina (sucesso, erro ou interrupção)

---

### 4. 📊 **Etapas Numeradas e Logs Melhorados**
**ANTES:**
```
🖱️ Clicando em 'Detalhado'...
🖱️ Clicando em 'Localizar'...
```

**AGORA:**
```
📍 [1/9] Clicando em 'Detalhado'...
⌨️ [2/9] Pressionando Enter...
⏳ [3/9] Aguardando 120 segundos para grid carregar dados...
📍 [4/9] Clicando na célula Org...
🧹 [5/9] Limpando clipboard antes de copiar...
⌨️ [6/9] Abrindo menu de contexto (Shift+F10)...
⌨️ [7/9] Navegando menu para 'Copiar Todas as Linhas'...
🎯 [8/9] Iniciando monitoramento inteligente do clipboard...
📋 [9/9] PROCESSANDO DADOS DA BANCADA
```

**Vantagens:**
- Fácil identificar em qual etapa está
- Fácil debugar se algo der errado
- Mostra progresso claro (X de 9)

---

## 🔄 Fluxo Completo Atualizado

### **CICLO COMPLETO (~3-5 minutos por ciclo)**

1. **[1/9] Clicar em "Detalhado"** (273, 358)
2. **[2/9] Pressionar Enter** (ao invés de clicar Localizar)
3. **[3/9] Aguardar 2 minutos** (grid carregar)
4. **[4/9] Clicar célula "Org"** (318, 174)
5. **[5/9] Limpar clipboard** (garantir dados novos)
6. **[6/9] Shift+F10** (menu contexto)
7. **[7/9] 3x Down + Enter** (Copiar Todas as Linhas)
8. **[8/9] Monitoramento inteligente**
   - Inicia movimento contínuo do mouse
   - Monitora clipboard a cada 3s
   - Detecta quando estabiliza (30s sem mudança)
   - **Termina automaticamente quando completo!**
   - Para movimento do mouse
9. **[9/9] Processar dados**
   - Salvar Excel local
   - Enviar Google Sheets
10. **Fechar Bancada** (746, 90)
11. **Aguardar 2 segundos e repetir**

---

## ⏱️ Ganho de Performance

### **ANTES:**
- **Tempo fixo por ciclo:** ~17 min 30 seg
  - 2 min (grid carregar)
  - **15 min (aguardo fixo)**
  - 30 seg (automação)

### **AGORA:**
- **Tempo variável por ciclo:** ~3-5 minutos (típico)
  - 2 min (grid carregar)
  - **1-3 min (monitoramento inteligente)** ⚡
  - 30 seg (automação)

### **Ganho:**
- **70-80% mais rápido** em cenários típicos
- **12-14 minutos economizados por ciclo!**
- Se Oracle for rápido (30 seg de cópia), termina em 3 minutos ao invés de 17!

---

## 🛠️ Configurações Atualizadas

### `config.json`
```json
{
  "tempos_espera": {
    "entre_cliques": 1.5,
    "apos_modal": 5.0,
    "apos_abrir_bancada": 3.0,
    "apos_localizar": 120,  // ✅ NOVO: Tempo para grid carregar (2 min)
    "comentario": "apos_localizar = tempo para grid carregar dados (~2min)"
  }
}
```

### `google_sheets_manager.py`
```python
# ✅ CORRIGIDO: Agora usa horário de Brasília (UTC-3)
brasilia_tz = timezone(timedelta(hours=-3))
timestamp = datetime.now(brasilia_tz).strftime('%Y-%m-%d %H:%M:%S')
```

---

## 📦 Arquivos Modificados

1. **`main.py`** - Lógica principal atualizada
   - Função `monitorar_clipboard_inteligente()` - Nova
   - Função `iniciar_movimento_mouse_continuo()` - Nova
   - Função `run_once()` - Refatorada
   - Removido `ler_clipboard_sem_ctrlc()` - Obsoleta

2. **`config.json`** - Nova configuração `apos_localizar`

3. **`google_sheets_manager.py`** - Corrigido fuso horário

---

## 🚀 Como Usar

### **Executável (.exe):**
```bash
BUILD_BANCADA.bat
```

### **Python direto:**
```bash
python RPA_Bancada_GUI.py
```

---

## 🧪 Teste Rápido

Criado modo teste para validar coordenadas:

```bash
TESTAR_RAPIDO.bat
```

---

## ✅ Benefícios Resumidos

| Característica | Antes | Agora |
|---|---|---|
| **Tempo por ciclo** | 17 min 30s | 3-5 min ⚡ |
| **Detecção automática** | ❌ | ✅ |
| **Feedback em tempo real** | ❌ | ✅ |
| **Anti-hibernação** | Básico | ULTRA ⚡ |
| **Horário correto** | UTC (errado) | Brasília ✅ |
| **Etapas numeradas** | ❌ | ✅ (1/9 ... 9/9) |
| **Clique em Localizar** | Sim | Enter (mais rápido) ⚡ |

---

## 🎯 Origem das Melhorias

Todas as melhorias foram portadas do **RPA Ciclo (Genesys)**, especificamente da função `etapa_07_executar_rpa_bancada()` do arquivo `main_ciclo.py`.

Local: `rpa_ciclo/essential/main_ciclo.py` (linhas 3729-3989)

---

## 📝 Notas Importantes

1. **Monitoramento inteligente** é a chave para o ganho de performance
2. **Movimento contínuo do mouse** garante que o Windows/Oracle não hibernem
3. **Horário de Brasília** corrigido no Google Sheets
4. **Pressiona Enter** ao invés de clicar (mais confiável)
5. **FAILSAFE ativo**: Mova mouse para canto superior esquerdo para parar

---

**Data da atualização:** 2026-01-08
**Versão:** 2.0 (com tecnologias Genesys)
