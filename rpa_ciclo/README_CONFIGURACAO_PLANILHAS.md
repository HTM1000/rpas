# Configuração de Planilhas Oracle - TESTE vs PROD

## 📋 Problema Resolvido

O RPA Ciclo usa **DUAS planilhas diferentes**:

1. **Planilha de LOGS** - Onde grava histórico dos ciclos (aba "Ciclo Automacao")
2. **Planilha de ITENS ORACLE** - Onde busca os itens para processar (aba "Separação")

---

## ✅ Solução Implementada

### **Arquivos de Configuração Separados:**

#### **`config.json`** - PRODUÇÃO
```json
{
  "planilhas": {
    "oracle_itens": "14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk",
    "comentario": "Planilha Oracle onde estão os itens para processar (aba Separação)"
  }
}
```

#### **`config_TESTE.json`** - TESTE
```json
{
  "planilhas": {
    "oracle_itens": "147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY",
    "comentario": "Planilha Oracle TESTE onde estão os itens para processar (aba Separação)"
  }
}
```

---

## 🔄 Como Funciona

### **Build de TESTE** (`Genesys_TESTE.exe`)

1. Importa `google_sheets_ciclo_TESTE.py` → Define `MODO_TESTE_ATIVO = True`
2. `carregar_config()` carrega **`config_TESTE.json`**
3. Lê `planilhas.oracle_itens` = `147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY`
4. **Busca itens** da planilha de TESTE (aba "Separação")
5. **Grava logs** na planilha de TESTE (aba "Ciclo Automacao")

**Console mostrará:**
```
[TESTE] Usando google_sheets_ciclo_TESTE.py - Planilha de LOGS TESTE
✅ Configurações carregadas de: config_TESTE.json
📊 Planilha Oracle Itens: 147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY
📊 Usando planilha Oracle (do config): 147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY
```

---

### **Build de PRODUÇÃO** (`Genesys.exe`)

1. Importa `google_sheets_ciclo.py` → Define `MODO_TESTE_ATIVO = False`
2. `carregar_config()` carrega **`config.json`**
3. Lê `planilhas.oracle_itens` = `14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk`
4. **Busca itens** da planilha de PRODUÇÃO (aba "Separação")
5. **Grava logs** na planilha de PRODUÇÃO (aba "Ciclo Automacao")

**Console mostrará:**
```
[PROD] Usando google_sheets_ciclo.py - Planilha de LOGS PRODUÇÃO
✅ Configurações carregadas de: config.json
📊 Planilha Oracle Itens: 14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk
📊 Usando planilha Oracle (do config): 14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk
```

---

## 📝 Arquivos Modificados

### **1. `main_ciclo.py`**

**Linhas 81-95:** Detecta modo TESTE ou PROD
```python
MODO_TESTE_ATIVO = False
try:
    from google_sheets_ciclo_TESTE import registrar_ciclo, atualizar_ciclo
    MODO_TESTE_ATIVO = True
    print("[TESTE] Usando google_sheets_ciclo_TESTE.py")
except ImportError:
    from google_sheets_ciclo import registrar_ciclo, atualizar_ciclo
    print("[PROD] Usando google_sheets_ciclo.py")
```

**Linhas 326-364:** Carrega config correto
```python
def carregar_config():
    config_filename = "config_TESTE.json" if MODO_TESTE_ATIVO else "config.json"
    # ... busca e carrega o arquivo correto
```

**Linhas 1630-1639:** Lê planilha Oracle do config
```python
if "planilhas" in config and "oracle_itens" in config["planilhas"]:
    SPREADSHEET_ID = config["planilhas"]["oracle_itens"]
else:
    SPREADSHEET_ID = "14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk"  # Fallback PROD
```

---

### **2. `config.json`** (PRODUÇÃO)
- Adicionada seção `planilhas.oracle_itens` com ID de PRODUÇÃO

### **3. `config_TESTE.json`** (TESTE)
- Criado com ID de TESTE: `147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY`

### **4. `Genesys_TESTE.spec`**
- Linha 25: Incluído `config_TESTE.json` no build ao invés de `config.json`

---

## 🚀 Como Gerar os Builds

### **TESTE:**
```bash
cd rpa_ciclo
BUILD_GENESYS_TESTE.bat
```

### **PRODUÇÃO:**
```bash
cd rpa_ciclo
BUILD_GENESYS.bat
```

---

## ✅ Verificação

Para confirmar que está usando a planilha correta, verifique o console ao executar:

**TESTE:**
```
[TESTE] Usando google_sheets_ciclo_TESTE.py - Planilha de LOGS TESTE
✅ Configurações carregadas de: config_TESTE.json
📊 Planilha Oracle Itens: 147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY
```

**PRODUÇÃO:**
```
[PROD] Usando google_sheets_ciclo.py - Planilha de LOGS PRODUÇÃO
✅ Configurações carregadas de: config.json
📊 Planilha Oracle Itens: 14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk
```

---

## 🔧 Troubleshooting

### "Ainda está usando planilha errada"

1. Confirme que o build incluiu o arquivo correto:
   - TESTE: Deve ter `config_TESTE.json` em `_internal/`
   - PROD: Deve ter `config.json` em `_internal/`

2. Verifique o console ao iniciar - deve mostrar qual config foi carregado

3. Verifique o ID da planilha mostrado no log

### "Config não encontrado"

- Certifique-se de que o `.spec` inclui o arquivo correto
- Verifique se o arquivo existe na pasta `rpa_ciclo/`
- Faça rebuild: `BUILD_GENESYS_TESTE.bat`

---

**Última atualização:** 27/10/2025
**Versão:** 3.0 (com separação TESTE vs PROD)
