# 🔒 Lógica do Cache - Proteção Contra Duplicações

## ⚠️ IMPORTANTE: NUNCA limpe o cache manualmente!

O cache é sua **proteção principal** contra duplicações. Ele só deve ser limpo pelo sistema APÓS confirmar sucesso no Google Sheets.

---

## 🛡️ Como Funciona a Proteção

### 1. **Item é Processado no Oracle**
```
Item ID: 001
↓
Adiciona ao cache com status: "pendente"
↓
Tenta atualizar Google Sheets
```

### 2. **Cenário A: Google Sheets SUCESSO ✅**
```
✅ Google Sheets atualizado!
   ↓
✅ Remove do cache (marcar_concluido)
   ↓
✅ Item protegido pela coluna "Status Oracle"
```

### 3. **Cenário B: Google Sheets FALHA ❌**
```
❌ Google Sheets falhou (rate limit, internet, etc)
   ↓
💾 Item permanece no cache como "pendente"
   ↓
🔄 Thread de retry tenta novamente a cada 30s
   ↓
✅ Quando conseguir: remove do cache
```

---

## 🔄 Thread de Retry (Background)

**Executa a cada 30 segundos:**
```python
while True:
    time.sleep(30)

    pendentes = cache.get_pendentes()  # Busca items com status "pendente"

    # Processa no máximo 10 por vez (batch update)
    for id_item in pendentes[:10]:
        try:
            # Atualiza Google Sheets
            service.spreadsheets().values().batchUpdate(...)

            # SUCESSO! Remove do cache
            cache.marcar_concluido(id_item)

        except Exception:
            # FALHA! Mantém no cache, tenta de novo em 30s
            pass
```

**Vantagens:**
- ✅ Não perde nenhum item
- ✅ Retry automático até sucesso
- ✅ Não excede rate limit (batch de 10)

---

## 🎯 Dupla Proteção

### Proteção 1: Cache Local
```python
if cache.ja_processado(id_item):
    print("🛡️ Item já processado! Pulando...")
    continue
```

### Proteção 2: Google Sheets
```python
# Filtrar linhas para processar
for linha in planilha:
    status_oracle = linha["Status Oracle"]
    status = linha["Status"]

    # DUPLA VALIDAÇÃO
    if status_oracle == "" and "CONCLUÍDO" in status:
        linhas_processar.append(linha)  # OK para processar
    else:
        # JÁ FOI PROCESSADO! Pular
        continue
```

**Mesmo se o cache for deletado acidentalmente:**
- ✅ Proteção 2 (Sheets) ainda funciona
- ✅ Não processa items já marcados com "Processo Oracle Concluído"

---

## ⚠️ Quando NÃO Limpar Cache

### ❌ NUNCA limpe o cache nestas situações:

1. **Antes de um novo ciclo**
   - Cache mantém histórico de processados
   - Previne duplicações se rodar múltiplas vezes

2. **Após erro de internet**
   - Cache mantém items pendentes
   - Thread de retry vai sincronizar quando voltar

3. **Após erro de rate limit**
   - Cache mantém items pendentes
   - Thread de retry processa em lotes seguros

4. **Entre execuções**
   - Cache é persistente (arquivo JSON)
   - Proteção continua mesmo após reiniciar

---

## ✅ Quando É SEGURO Limpar Cache

### ✅ Pode limpar nestas situações:

1. **Teste inicial do zero**
   - Quer testar com dados limpos
   - Primeira execução em ambiente de teste

2. **Reset de ambiente de teste**
   - Limpou a planilha de teste manualmente
   - Quer recomeçar teste do zero

3. **Arquivo corrompido**
   - Erro de leitura do JSON
   - Cache não carrega corretamente

---

## 📊 Exemplo de Fluxo Completo

### Ciclo 1:
```
[Processamento]
ID 001 → Cache (pendente) → Sheets ✅ → Remove do cache
ID 002 → Cache (pendente) → Sheets ✅ → Remove do cache
ID 003 → Cache (pendente) → Sheets ❌ (rate limit!) → Mantém no cache
...
ID 050 → Cache (pendente) → Sheets ❌ (rate limit!) → Mantém no cache

[Cache ao final]
003, 004, ..., 050 (15 items pendentes)

[Thread de Retry - após 30s]
🔄 Processando 10 itens pendentes...
003-012 → Batch update ✅ → Removidos do cache

[Thread de Retry - após 60s]
🔄 Processando 5 itens pendentes...
013-050 → Batch update ✅ → Removidos do cache

[Cache ao final]
vazio (todos sincronizados!)
```

### Ciclo 2:
```
[Busca na planilha]
ID 001 → Status Oracle = "Processo Oracle Concluído" → PULA ✅
ID 002 → Status Oracle = "Processo Oracle Concluído" → PULA ✅
ID 051 → Status Oracle vazio + Status CONCLUÍDO → PROCESSA ✅
...

[Proteção funcionando!]
Items 001-050 já foram marcados no Sheets
Não são processados novamente
Taxa de duplicação: 0%
```

---

## 🎛️ Configurações de Proteção

### Em `teste_ciclo_completo.py` e `teste_ciclo_gui.py`:

```python
# Rate limiting
MAX_ITENS_POR_BATCH = 10  # Batch update (10 items por vez)
REQUISICOES_POR_MINUTO_MAX = 50  # Margem de segurança (limite real: 60)

# Thread de retry
INTERVALO_RETRY = 30  # segundos

# Cache
CACHE_FILE = "cache_teste_ciclo.json"  # Arquivo persistente
```

---

## 🚨 Sinais de Alerta

### ⚠️ Preste atenção nestes logs:

**PROBLEMA:**
```
[23:30:00] ⚠️ Erro ao atualizar Sheets (ID 001): Rate limit exceeded
[23:30:00] 💾 ID 001 permanece no cache. Thread de retry tentará novamente...
```
**Solução:** Normal! Thread de retry vai resolver.

**PROBLEMA:**
```
[23:30:30] [RETRY] Processando 50 itens pendentes...
[23:30:31] [RETRY] ✗ Batch update falhou: Rate limit exceeded
```
**Solução:** Muitos pendentes! Reduzir `MAX_ITENS_POR_BATCH` para 5.

**PROBLEMA:**
```
📈 Taxa de bloqueio: 30.0%  ← Deveria ser 100%!
```
**Solução:** Cache não está funcionando OU Google Sheets não foi atualizado.

---

## ✅ Validação da Proteção

**Como verificar se a proteção está funcionando:**

1. **Verificar Cache:**
   ```bash
   cat cache_teste_ciclo.json
   ```
   - Items pendentes: `"status_sheets": "pendente"`
   - Items removidos após sucesso

2. **Verificar Google Sheets:**
   - Abrir planilha de teste
   - Coluna "Status Oracle" = "Processo Oracle Concluído"
   - Items marcados não devem ser reprocessados

3. **Verificar Logs:**
   ```
   🛡️ [BLOQUEADO] ID 001 já foi processado! (1/1)
   ```
   - Taxa de bloqueio deve ser 100%

---

## 📝 Resumo

### ✅ FAÇA:
- ✅ Clique "NÃO" quando perguntar sobre limpar cache
- ✅ Deixe thread de retry fazer seu trabalho
- ✅ Confie na dupla proteção (cache + Sheets)

### ❌ NÃO FAÇA:
- ❌ Não limpe cache manualmente entre execuções
- ❌ Não delete `cache_teste_ciclo.json` durante processamento
- ❌ Não force processamento de items já marcados

---

**🔒 O cache é sua proteção! Deixe ele trabalhar para você!**
