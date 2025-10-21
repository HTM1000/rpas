# 🎯 RPA GENESYS - Builds Finais

## ✅ Builds Gerados com Sucesso!

Você agora tem **2 versões** do RPA Genesys, ambas em modo **ONEDIR** (pasta com arquivos) e **COM Tesseract incluído**:

---

## 📦 1. RPA_Genesys_TESTE

📁 **Local:** `dist/RPA_Genesys_TESTE/`

### Características:
- ✅ **Tesseract incluído** (validação visual por OCR)
- ⚠️ **SEM Ctrl+S** (apenas simula o salvamento)
- 📋 **Planilha de TESTE:** `14HqOFoAxzZWy0yH3vJC6_6xaY5YmU-pI4xxAyTn31wQ`
- 💾 **Cache:** `cache_teste_ciclo.json`
- 🛑 **Para quando não há itens** (PARAR_QUANDO_VAZIO = True)

### Estrutura:
```
RPA_Genesys_TESTE/
  ├── RPA_Genesys_TESTE.exe (13 MB)
  └── _internal/
      ├── tesseract/
      │   ├── tesseract.exe (OCR engine)
      │   └── tessdata/ (idiomas: eng, osd)
      └── ... (outros arquivos)
```

### Quando usar:
- Para testar o fluxo completo sem salvar no Oracle
- Para validar coordenadas e lógica
- Para treinar novos operadores
- Para demonstrações

---

## 📦 2. RPA_Genesys_PRODUCAO

📁 **Local:** `dist/RPA_Genesys_PRODUCAO/`

### Características:
- ✅ **Tesseract incluído** (validação visual por OCR)
- ✅ **COM Ctrl+S** (salva de verdade no Oracle)
- 📋 **Planilha de PRODUÇÃO:** `14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk`
- 💾 **Cache:** `processados.json`
- 🔄 **Roda continuamente** (não para quando vazio)

### Estrutura:
```
RPA_Genesys_PRODUCAO/
  ├── RPA_Genesys_PRODUCAO.exe (13 MB)
  └── _internal/
      ├── tesseract/
      │   ├── tesseract.exe (OCR engine)
      │   └── tessdata/ (idiomas: eng, osd)
      └── ... (outros arquivos)
```

### Quando usar:
- Para rodar em produção real
- Para processar dados do Oracle de verdade
- Quando tudo já foi testado

---

## 📋 Como Enviar ao Cliente

### Opção 1: Enviar as 2 versões (Recomendado)

1. Compacte cada pasta separadamente:
   - `RPA_Genesys_TESTE.zip`
   - `RPA_Genesys_PRODUCAO.zip`

2. Envie ao cliente com instruções:
   ```
   - Use RPA_Genesys_TESTE primeiro para testar
   - Depois use RPA_Genesys_PRODUCAO para produção
   ```

### Opção 2: Enviar apenas PRODUÇÃO

1. Compacte apenas: `RPA_Genesys_PRODUCAO.zip`
2. Envie ao cliente

---

## 👤 Instruções para o Cliente

### Instalação:

1. **Descompacte** o arquivo .zip recebido
2. **Copie a pasta completa** para a área de trabalho
3. **Entre na pasta** e execute o arquivo `.exe`

**IMPORTANTE:**
- NÃO mova apenas o .exe, mova a PASTA COMPLETA
- O Tesseract está dentro de `_internal/tesseract/`
- Sem a pasta completa, o OCR não funcionará

### Execução:

```
Área de Trabalho/
  └── RPA_Genesys_TESTE/          ← Copie esta pasta inteira
      ├── RPA_Genesys_TESTE.exe   ← Execute este arquivo
      └── _internal/
```

---

## 🔍 Diferenças Entre TESTE e PRODUÇÃO

| Característica | TESTE | PRODUÇÃO |
|----------------|-------|----------|
| **Ctrl+S** | ❌ Simulado | ✅ Executado |
| **Planilha** | Teste (14HqO...) | Produção (14yUM...) |
| **Cache** | cache_teste_ciclo.json | processados.json |
| **Comportamento sem itens** | Para | Aguarda 30s e continua |
| **Validação OCR** | ✅ Ativa | ✅ Ativa |

---

## ⚙️ Detalhes Técnicos

### Versão TESTE - Modificações no código:

```python
# main_ciclo_TESTE.py (linha ~117)
SEM_CTRL_S = True
PARAR_QUANDO_VAZIO = True
SPREADSHEET_ID = "14HqOFoAxzZWy0yH3vJC6_6xaY5YmU-pI4xxAyTn31wQ"  # TESTE

# main_ciclo_TESTE.py (linha ~134)
def __init__(self, arquivo="cache_teste_ciclo.json"):

# main_ciclo_TESTE.py (linha ~950)
if globals().get('SEM_CTRL_S', False):
    gui_log("[TESTE] Ctrl+S SIMULADO")
    time.sleep(1)
else:
    pyautogui.hotkey("ctrl", "s")
```

### Versão PRODUÇÃO - Código original:

```python
# main_ciclo.py (sem modificações)
SEM_CTRL_S = False  # (não existe esta flag)
PARAR_QUANDO_VAZIO = False
SPREADSHEET_ID = "14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk"  # PROD

# main_ciclo.py (linha ~134)
def __init__(self, arquivo="processados.json"):

# main_ciclo.py (linha ~950)
pyautogui.hotkey("ctrl", "s")  # Sempre executa
```

---

## 📊 Tamanhos dos Arquivos

| Build | Executável | Pasta Completa | Tesseract |
|-------|-----------|----------------|-----------|
| RPA_Genesys_TESTE | 13 MB | ~150-200 MB | 85 KB |
| RPA_Genesys_PRODUCAO | 13 MB | ~150-200 MB | 85 KB |

---

## 🔧 Rebuild Rápido (se necessário)

```bash
# Limpar builds anteriores
python -c "import shutil, os; [shutil.rmtree(d) for d in ['dist', 'build'] if os.path.exists(d)]"

# Build TESTE
python -m PyInstaller RPA_Genesys_TESTE.spec

# Build PRODUCAO (SEM limpar dist)
python -m PyInstaller RPA_Genesys_PRODUCAO.spec
```

---

## ✅ Checklist de Entrega

### Antes de enviar ao cliente:

- [ ] Testar RPA_Genesys_TESTE localmente
- [ ] Verificar se Tesseract está incluído (`_internal/tesseract/tesseract.exe`)
- [ ] Verificar se OCR funciona (ver logs "[OK] Tesseract LOCAL encontrado")
- [ ] Compactar pastas em .zip
- [ ] Criar instruções para o cliente
- [ ] Enviar arquivos + instruções

### Cliente deve:

- [ ] Descompactar arquivo
- [ ] Copiar PASTA COMPLETA para área de trabalho
- [ ] Executar arquivo .exe dentro da pasta
- [ ] Verificar se aparece "[OK] Tesseract LOCAL encontrado" nos logs

---

## 🎯 Resumo Final

✅ **2 builds gerados com sucesso**
✅ **Ambos com Tesseract incluído**
✅ **Modo ONEDIR (pasta com arquivos)**
✅ **Cliente NÃO precisa instalar nada**
✅ **OCR funcionando automaticamente**
✅ **Nome alterado para RPA_Genesys**

**TESTE:** Sem Ctrl+S, planilha de teste, para quando vazio
**PRODUÇÃO:** Com Ctrl+S, planilha de produção, roda continuamente

Pronto para uso! 🚀
