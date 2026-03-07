# 📋 MUDANÇA: Remoção da Coluna REV. do Envio ao Google Sheets

**Data:** 2026-01-12
**Versão:** RPA Ciclo v4.1
**Status:** ✅ Implementado e Testado

---

## 🎯 Objetivo

Remover a coluna **REV.** do envio ao Google Sheets (AppSheet), mantendo apenas 9 colunas no total (Codigo, Data + 7 colunas principais).

### Antes da Mudança:
```
A:J (10 colunas)
Codigo, Data, ORG., SUB., ENDEREÇO, ITEM, DESCRIÇÃO ITEM, REV., UDM PRINCIPAL, EM ESTOQUE
```

### Depois da Mudança:
```
A:I (9 colunas)
Codigo, Data, ORG., SUB., ENDEREÇO, ITEM, DESCRIÇÃO ITEM, UDM PRINCIPAL, EM ESTOQUE
```

---

## 🔧 Alterações Realizadas

### 1. Arquivo: `google_sheets_manager.py`

#### Linha 14 - Range atualizado:
```python
# ANTES
RANGE_NAME = 'A:J'  # Colunas A até J (Codigo, Data + 8 colunas principais)

# DEPOIS
RANGE_NAME = 'A:I'  # Colunas A até I (Codigo, Data + 7 colunas principais - REV removido)
```

#### Linha 84-86 - Documentação atualizada:
```python
# ANTES
Colunas finais: Codigo, Data, ORG., SUB., ENDEREÇO, ITEM, DESCRIÇÃO ITEM, REV., UDM PRINCIPAL, EM ESTOQUE

# DEPOIS
Colunas finais: Codigo, Data, ORG., SUB., ENDEREÇO, ITEM, DESCRIÇÃO ITEM, UDM PRINCIPAL, EM ESTOQUE
Nota: REV. é capturado dos dados mas NÃO enviado para o Google Sheets
```

#### Linha 137 - Lista de colunas:
```python
# ANTES
required_columns = ['ORG.', 'SUB.', 'ENDEREÇO', 'ITEM', 'DESCRIÇÃO ITEM', 'REV.', 'UDM PRINCIPAL', 'EM ESTOQUE']

# DEPOIS
required_columns = ['ORG.', 'SUB.', 'ENDEREÇO', 'ITEM', 'DESCRIÇÃO ITEM', 'UDM PRINCIPAL', 'EM ESTOQUE']
```

#### Linha 182 - Range do Sheets:
```python
# ANTES
range_name = f'{sheet_name}!A:J'

# DEPOIS
range_name = f'{sheet_name}!A:I'
```

#### Linha 167 - Comentário:
```python
# ANTES
# Filtrar apenas as 8 colunas principais + adicionar Codigo e Data

# DEPOIS
# Filtrar apenas as 7 colunas principais + adicionar Codigo e Data
```

### 2. Arquivo: `main_ciclo.py`

#### Linha 3456 - Comentário explicativo:
```python
# Manter apenas as 8 colunas desejadas (REV. será capturado aqui mas removido antes de enviar ao Sheets)
colunas_finais = ['ORG.', 'SUB.', 'ENDEREÇO', 'ITEM', 'DESCRIÇÃO ITEM', 'REV.', 'UDM PRINCIPAL', 'EM ESTOQUE']
```

**Nota:** No `main_ciclo.py`, mantemos REV. na lista porque os dados ainda são processados internamente com essa coluna. A remoção só acontece no `google_sheets_manager.py` antes do envio.

---

## ✅ Testes Realizados

### Teste 1: Validação Local
**Script:** `testar_bancada_sem_rev.py`

**Resultado:**
```
✅ SUCESSO: Coluna REV. foi REMOVIDA corretamente!

🔍 Verificando colunas esperadas...
   ✅ Codigo
   ✅ Data
   ✅ ORG.
   ✅ SUB.
   ✅ ENDEREÇO
   ✅ ITEM
   ✅ DESCRIÇÃO ITEM
   ✅ UDM PRINCIPAL
   ✅ EM ESTOQUE

✅ Ordem das colunas está correta!
```

### Teste 2: Envio Real ao Google Sheets
**Script:** `testar_envio_sem_rev.py`

**Resultado:**
```
✅ TESTE CONCLUIDO COM SUCESSO!

Verificacoes realizadas:
   - Coluna REV. foi removida do envio
   - 9 colunas enviadas (Codigo, Data + 7 principais)
   - Ordem das colunas: A:I

[OK] Google Sheets atualizado: 6 linhas
```

**Planilha:** https://docs.google.com/spreadsheets/d/1UgJWxmnYzv-FVTT4rrrVEx3J_MNXZsctwrPSTyyylPQ

**Confirmação Visual:** ✅ Coluna REV. NÃO aparece no Google Sheets

---

## 🔄 Fluxo de Processamento Atualizado

```
┌─────────────────────────────────────────────────┐
│  1. RPA Bancada captura dados do Oracle        │
│     (TODAS as colunas, incluindo REV.)          │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│  2. main_ciclo.py processa DataFrame            │
│     Colunas: ORG., SUB., ENDEREÇO, ITEM,        │
│              DESCRIÇÃO, REV., UDM, ESTOQUE       │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│  3. google_sheets_manager.py filtra             │
│     REMOVE: REV.                                │
│     ADICIONA: Codigo, Data                      │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│  4. Envia para Google Sheets (A:I)              │
│     Codigo, Data, ORG., SUB., ENDEREÇO,         │
│     ITEM, DESCRIÇÃO, UDM, ESTOQUE               │
└─────────────────────────────────────────────────┘
```

---

## 📊 Estrutura Final no Google Sheets

| Coluna | Nome             | Tipo   | Exemplo           |
|--------|------------------|--------|-------------------|
| A      | Codigo           | Number | 1, 2, 3, ...      |
| B      | Data             | Text   | 2026-01-12 10:30  |
| C      | ORG.             | Text   | ORG01             |
| D      | SUB.             | Text   | SUB01             |
| E      | ENDEREÇO         | Text   | END001            |
| F      | ITEM             | Text   | E2029A            |
| G      | DESCRIÇÃO ITEM   | Text   | Compressor XYZ    |
| H      | UDM PRINCIPAL    | Text   | PC                |
| I      | EM ESTOQUE       | Number | 150               |

**Total:** 9 colunas (A até I)

---

## 🚀 Build e Deployment

### Arquivos Modificados:
- ✅ `essential/google_sheets_manager.py`
- ✅ `essential/main_ciclo.py`

### Scripts de Teste Criados:
- ✅ `essential/testar_bancada_sem_rev.py`
- ✅ `essential/testar_envio_sem_rev.py`

### Build:
```bash
cd C:\Users\ID135\OneDrive\Desktop\www\rpas\rpa_ciclo\essential
BUILD_GENESYS.bat
```

### Validação Pós-Build:
1. [ ] Executável gerado em `dist/Genesys/Genesys.exe`
2. [ ] Testar execução completa do ciclo
3. [ ] Verificar Google Sheets após execução (coluna REV. não deve aparecer)

---

## 📝 Notas Importantes

1. **REV. ainda é capturado:** Os dados da coluna REV. ainda são lidos do Oracle durante a extração da bancada
2. **REV. não é enviado:** A coluna é removida automaticamente antes do envio ao Google Sheets
3. **Backward compatible:** Se houver dados antigos no Excel local (com REV.), não haverá problemas
4. **AppSheet atualizado:** Após esta mudança, o AppSheet deve refletir apenas 9 colunas

---

## ⚠️ Possíveis Impactos

### Impactos no AppSheet:
- Se o AppSheet estava configurado para usar a coluna REV., será necessário **atualizar o schema** do AppSheet
- Remover referências à coluna REV. em fórmulas ou views do AppSheet

### Compatibilidade:
- ✅ Arquivos Excel locais: Não afetados (podem continuar com REV.)
- ✅ Google Sheets antigos: Serão sobrescritos com novo formato (sem REV.)
- ✅ Cache processados.json: Não afetado

---

## 🔗 Links Úteis

**Google Sheets (Bancada):**
https://docs.google.com/spreadsheets/d/1UgJWxmnYzv-FVTT4rrrVEx3J_MNXZsctwrPSTyyylPQ

**Documentação Principal:**
`CLAUDE.md` - Visão geral do sistema

---

**Mudança implementada por:** Claude Code
**Data de implementação:** 2026-01-12
**Status:** ✅ Testado e Aprovado
