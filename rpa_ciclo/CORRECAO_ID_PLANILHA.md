# ✅ Correção - ID da Planilha (Erro 404)

## 🐛 Erro Encontrado:

```
HttpError 404: Requested entity was not found
```

## 🔍 Causa:

O ID da planilha no código estava **ERRADO**:

**❌ ID Antigo (ERRADO):**
```python
SPREADSHEET_ID = "14HqOFoAxzZWy0yH3vJC6_6xaY5YmU-pI4xxAyTn31wQ"
```

**✅ ID Correto:**
```python
SPREADSHEET_ID = "147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY"
```

## 🔗 URL da Planilha:

https://docs.google.com/spreadsheets/d/147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY/edit?gid=0#gid=0

## ✅ Correção Aplicada:

Arquivo modificado: `main_ciclo_TESTE.py` (linha 584)

```python
# ANTES
SPREADSHEET_ID = "14HqOFoAxzZWy0yH3vJC6_6xaY5YmU-pI4xxAyTn31wQ"  # PLANILHA TESTE

# DEPOIS
SPREADSHEET_ID = "147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY"  # PLANILHA TESTE
```

## 🔨 Build Refeito:

```bash
python -m PyInstaller RPA_Genesys_TESTE.spec
```

## 📦 Status Final:

- [x] ID da planilha corrigido
- [x] Build refeito com sucesso
- [x] Executável: `dist/RPA_Genesys_TESTE/RPA_Genesys_TESTE.exe`
- [x] Tesseract incluído
- [x] Pronto para uso!

## ⚠️ IMPORTANTE:

A versão **RPA_Genesys_PRODUCAO** ainda usa a planilha de PRODUÇÃO:

```python
SPREADSHEET_ID = "14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk"  # PRODUÇÃO
```

Se você quiser mudar a planilha de produção também, me avise!

---

## 🎯 Builds Finais (Atualizados):

### ✅ RPA_Genesys_TESTE
- **Planilha:** `147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY` ✅ CORRIGIDO
- **Ctrl+S:** Simulado (não executa)
- **Cache:** `cache_teste_ciclo.json`
- **Status:** Pronto para testar!

### ✅ RPA_Genesys_PRODUCAO
- **Planilha:** `14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk` (mantida)
- **Ctrl+S:** Executado (salva de verdade)
- **Cache:** `processados.json`
- **Status:** Pronto para produção!

---

**Data da correção:** 18/10/2025 14:15
**Status:** ✅ RESOLVIDO

**Pode testar novamente!** O erro 404 foi corrigido. 🚀
