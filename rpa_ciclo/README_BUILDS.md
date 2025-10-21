# 📦 Builds Disponíveis - RPA Ciclo

## ✅ Builds Gerados

Você tem 2 opções de build:

---

### 1. **ONEDIR** (Pasta com arquivos) - **COM Tesseract** ✅ RECOMENDADO

📁 **Local:** `dist/RPA_Ciclo_v2/`

```
dist/
  RPA_Ciclo_v2/
    RPA_Ciclo_v2.exe (13 MB)
    _internal/
      tesseract/
        tesseract.exe (OCR engine)
        tessdata/ (idiomas)
      ... (outros arquivos)
```

✅ **Vantagens:**
- Tesseract incluído (validação visual por OCR)
- Cliente não precisa instalar nada
- Funciona offline

❌ **Desvantagens:**
- Precisa enviar a pasta inteira
- Mais arquivos para gerenciar

**Como usar:**
1. Envie a pasta COMPLETA `RPA_Ciclo_v2\` ao cliente
2. Cliente copia para área de trabalho
3. Execute `RPA_Ciclo_v2.exe` dentro da pasta

---

### 2. **ONEFILE** (1 único exe) - **SEM Tesseract** ⚠️

📁 **Local:** `dist/RPA_Ciclo_v2_ONEFILE.exe`

```
dist/
  RPA_Ciclo_v2_ONEFILE.exe (60 MB)
```

✅ **Vantagens:**
- 1 único arquivo exe
- Mais fácil de enviar/distribuir
- Não precisa de pasta

❌ **Desvantagens:**
- Tesseract NÃO incluído
- Validação visual por OCR desabilitada
- Cliente precisaria instalar Tesseract manualmente (complicado)

**Como usar:**
1. Envie apenas `RPA_Ciclo_v2_ONEFILE.exe`
2. Cliente coloca na área de trabalho
3. Execute direto

---

## 🎯 Qual usar?

| Situação | Build Recomendado |
|----------|------------------|
| **Produção com OCR** | ONEDIR (pasta) |
| **Teste rápido sem OCR** | ONEFILE (exe único) |
| **Cliente técnico** | ONEDIR |
| **Cliente iniciante** | ONEFILE (mais simples) |

---

## 🧪 Versão de Teste (SEM Ctrl+S)

Para criar uma versão de teste que NÃO executa Ctrl+S:

1. Edite `main_ciclo.py`:
   ```python
   # Linha ~117: Adicione
   SEM_CTRL_S = True

   # Linha ~577: Mude planilha
   SPREADSHEET_ID = "14HqOFoAxzZWy0yH3vJC6_6xaY5YmU-pI4xxAyTn31wQ"  # TESTE

   # Linha ~134: Mude cache
   def __init__(self, arquivo="cache_teste_ciclo.json"):

   # Linha ~942: Comente Ctrl+S
   if not SEM_CTRL_S:
       pyautogui.hotkey("ctrl", "s")
   else:
       gui_log("TESTE: Ctrl+S simulado")
   ```

2. Execute build novamente

---

##  Rebuild Rápido

```bash
# ONEDIR (com Tesseract)
python -m PyInstaller --clean RPA_Ciclo_v2.spec

# ONEFILE (sem Tesseract)
python -m PyInstaller --clean RPA_Ciclo_ONEFILE.spec
```

---

## 📋 Checklist de Distribuição

### ONEDIR:
- [ ] Testar executável localmente
- [ ] Verificar se `_internal/tesseract/tesseract.exe` existe
- [ ] Compactar pasta `RPA_Ciclo_v2\` em .zip
- [ ] Enviar .zip ao cliente
- [ ] Instruir cliente a descompactar e executar

### ONEFILE:
- [ ] Testar executável localmente
- [ ] Avisar cliente que OCR estará desabilitado
- [ ] Enviar arquivo `.exe`
- [ ] Instruir cliente a copiar para área de trabalho e executar

---

## ⚙️ Tamanhos dos Arquivos

| Build | Tamanho | Observação |
|-------|---------|------------|
| ONEDIR (pasta completa) | ~150-200 MB | Com Tesseract e todas dependências |
| ONEDIR (exe principal) | ~13 MB | Apenas o executável |
| ONEFILE | ~60 MB | Tudo em 1 arquivo |

---

## 🔧 Troubleshooting

### "Tesseract não encontrado" (ONEDIR)
- Verifique se `_internal/tesseract/tesseract.exe` existe
- Cliente deve executar o exe DENTRO da pasta, não mover para outro lugar

### "Módulo não encontrado" (ONEFILE)
- Reconstrua com `--clean`
- Verifique `hidden_imports` no `.spec`

### Exe muito grande
- Normal! PyInstaller inclui todas as dependências
- ONEFILE é maior porque compacta tudo em 1 arquivo
