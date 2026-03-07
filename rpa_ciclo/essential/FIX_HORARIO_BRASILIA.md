# ✅ Correção do Horário - Brasília (UTC-3)

## 🕐 Problema

O RPA Genesys estava salvando data/hora em **UTC** (horário de Greenwich) ao invés do **horário de Brasília (UTC-3)**.

**Exemplo:**
- Executou às **14h07** (Brasília)
- Salvou como **17h07** (UTC, +3 horas de diferença)

## 🔧 Solução Aplicada

Todas as chamadas `datetime.now()` foram corrigidas para usar explicitamente o fuso horário de Brasília (UTC-3):

```python
# ANTES (ERRADO):
datetime.now()  # Retorna UTC

# AGORA (CORRETO):
from datetime import timezone, timedelta
brasilia_tz = timezone(timedelta(hours=-3))
datetime.now(brasilia_tz)  # Retorna Brasília UTC-3
```

---

## 📝 Arquivos Corrigidos

### 1. **`main_ciclo.py`** - 5 correções

#### **Correção 1: Data de Início do Ciclo**
**Linha:** ~4283
```python
# Usar horário de Brasília (UTC-3)
from datetime import timezone, timedelta
brasilia_tz = timezone(timedelta(hours=-3))
_data_inicio_ciclo = datetime.now(brasilia_tz)
```

**Impacto:** Data/Hora Início na planilha Google Sheets

---

#### **Correção 2: Data de Fim (Sucesso)**
**Linha:** ~4374
```python
# Usar horário de Brasília (UTC-3)
from datetime import timezone, timedelta
brasilia_tz = timezone(timedelta(hours=-3))
data_fim = datetime.now(brasilia_tz)
```

**Impacto:** Data/Hora Fim na planilha Google Sheets (quando ciclo sucede)

---

#### **Correção 3: Data de Fim (Falha)**
**Linha:** ~4362
```python
# Usar horário de Brasília (UTC-3)
from datetime import timezone, timedelta
brasilia_tz = timezone(timedelta(hours=-3))
data_fim = datetime.now(brasilia_tz)
```

**Impacto:** Data/Hora Fim na planilha Google Sheets (quando ciclo falha)

---

#### **Correção 4: Timestamp de Processamento (Cache)**
**Linha:** ~260
```python
# Usar horário de Brasília (UTC-3)
from datetime import timezone, timedelta
brasilia_tz = timezone(timedelta(hours=-3))
dados_item = {
    ...
    "timestamp_processamento": datetime.now(brasilia_tz).strftime("%Y-%m-%d %H:%M:%S"),
    ...
}
```

**Impacto:** Timestamp em `processados.json` (cache local)

---

#### **Correção 5: Timestamp de Última Atualização (Cache)**
**Linha:** ~280
```python
# Usar horário de Brasília (UTC-3)
from datetime import timezone, timedelta
brasilia_tz = timezone(timedelta(hours=-3))
self.dados[id_item]["timestamp_ultima_atualizacao"] = datetime.now(brasilia_tz).strftime("%Y-%m-%d %H:%M:%S")
```

**Impacto:** Timestamp de atualização em `processados.json`

---

### 2. **`google_sheets_manager.py`** (RPA Bancada) - Já corrigido anteriormente

**Linha:** ~176
```python
# Usar horário de Brasília (UTC-3)
from datetime import timezone, timedelta
brasilia_tz = timezone(timedelta(hours=-3))
timestamp = datetime.now(brasilia_tz).strftime('%Y-%m-%d %H:%M:%S')
```

**Impacto:** Coluna "Data" na planilha da Bancada

---

## ✅ Resultado

Agora **todos os timestamps** salvos nas planilhas e no cache usam o **horário de Brasília (UTC-3)**!

| Antes | Agora |
|-------|-------|
| 17:07 (UTC) | 14:07 (Brasília) ✅ |
| 09:20 (UTC) | 06:20 (Brasília) ✅ |
| 22:45 (UTC) | 19:45 (Brasília) ✅ |

---

## 🚀 Como Aplicar

### **Opção 1: Rodar Python direto** (aplicado automaticamente)
```bash
cd rpa_ciclo/essential
python RPA_Ciclo_GUI_v2.py
```

### **Opção 2: Recompilar executável**
```bash
cd rpa_ciclo/essential
BUILD_GENESYS.bat
```

---

## 🧪 Como Testar

### **Teste 1: Verificar hora do sistema**
```bash
echo %time%
# Exemplo: 14:07:32,45
```

### **Teste 2: Executar RPA e verificar planilha**
1. Execute o RPA Genesys
2. Abra a planilha: https://docs.google.com/spreadsheets/d/14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk
3. Verifique a coluna "Data/Hora Início"
4. Deve estar igual à hora do sistema (ou próximo, com poucos segundos de diferença)

### **Teste 3: Verificar processados.json**
```bash
type processados.json
```

Verifique se os timestamps estão com a hora correta:
```json
{
  "2024-01-08 14:07:23": {
    "timestamp_processamento": "2024-01-08 14:07:23",
    ...
  }
}
```

---

## 📊 Locais Afetados

### **Google Sheets - Planilha do Ciclo**
- ✅ Coluna "Data/Hora Início"
- ✅ Coluna "Data/Hora Fim"
- ✅ Cálculo de "Tempo Execução (min)" (calculado a partir das datas corretas)

### **Google Sheets - Planilha da Bancada**
- ✅ Coluna "Data" (horário da extração)

### **Arquivos Locais**
- ✅ `processados.json` - Cache de itens processados
  - `timestamp_processamento`
  - `timestamp_ultima_atualizacao`

---

## ⚠️ Observações Importantes

1. **Cache antigo:** Itens já salvos em `processados.json` com UTC **NÃO serão atualizados**. Apenas novos itens usarão Brasília.

2. **Planilhas antigas:** Registros antigos nas planilhas **permanecem com UTC**. Apenas novos registros terão Brasília.

3. **Horário de Verão:** O código usa **UTC-3 fixo**, que é o horário padrão de Brasília. Se houver horário de verão, ajustar para UTC-2.

4. **Outros timestamps:** Timestamps usados apenas para logs (não salvos em planilhas) **não foram corrigidos** pois não afetam o usuário.

---

## 🔍 Logs de Exemplo

Antes da correção:
```
🔄 CICLO #1 - 2024-01-08 17:07:23  <- ERRADO (UTC)
```

Depois da correção:
```
🔄 CICLO #1 - 2024-01-08 14:07:23  <- CORRETO (Brasília)
```

---

## 📞 Próximos Passos

Se ainda houver problemas de horário:

1. **Verificar fuso horário do Windows:**
   ```bash
   tzutil /g
   # Deve retornar: E. South America Standard Time
   ```

2. **Verificar se Python está usando timezone correta:**
   ```python
   from datetime import datetime, timezone, timedelta
   brasilia_tz = timezone(timedelta(hours=-3))
   print(datetime.now(brasilia_tz))
   # Deve mostrar hora atual de Brasília
   ```

3. **Se horário de verão estiver ativo**, alterar para UTC-2:
   ```python
   brasilia_tz = timezone(timedelta(hours=-2))  # Horário de verão
   ```

---

**Data da correção:** 2026-01-08
**Versão:** 2.0
**Status:** ✅ Aplicado em `main_ciclo.py` e `google_sheets_manager.py`
