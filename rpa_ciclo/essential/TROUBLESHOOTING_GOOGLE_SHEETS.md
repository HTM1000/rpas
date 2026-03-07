# 🔧 Troubleshooting - Falha ao Atualizar Planilha Genesys

## ❌ Possíveis Causas e Soluções

### 1. 🔐 **Token Expirado/Inválido** (Mais Comum)

**Sintomas:**
```
❌ Erro ao registrar ciclo no Google Sheets: invalid_grant
❌ Erro ao renovar token: Token has been expired or revoked
```

**Causa:**
- Token OAuth2 expirou (válido por ~7 dias de inatividade)
- Credenciais foram revogadas manualmente no Google

**Solução:**
```bash
# 1. Deletar token antigo
del token.json

# 2. Executar novamente - vai abrir navegador para reautenticar
python RPA_Ciclo_GUI_v2.py
```

Ou se estiver usando executável:
```bash
# Deletar token na pasta do .exe
cd dist\Genesys
del token.json

# Executar novamente
Genesys.exe
```

**Quando o navegador abrir:**
1. Faça login com a conta Google correta
2. Clique em "Permitir" (Allow)
3. Token será regenerado automaticamente

---

### 2. 🚫 **Permissões Insuficientes**

**Sintomas:**
```
❌ Erro ao registrar ciclo no Google Sheets: insufficient permissions
❌ The caller does not have permission
```

**Causa:**
- Conta Google não tem acesso à planilha
- Token foi gerado com conta diferente

**Solução:**

**A. Verificar qual conta tem acesso:**
1. Abra a planilha: https://docs.google.com/spreadsheets/d/14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk
2. Clique em "Compartilhar"
3. Verifique quais e-mails têm acesso de **Editor**

**B. Adicionar permissão:**
1. Clique em "Compartilhar"
2. Adicione o e-mail usado no RPA
3. Defina como **Editor** (não Leitor!)
4. Clique em "Enviar"

**C. Reautenticar com conta correta:**
```bash
del token.json
python RPA_Ciclo_GUI_v2.py
```

---

### 3. 📋 **ID da Planilha Errado**

**Sintomas:**
```
❌ Erro ao registrar ciclo: Requested entity was not found
❌ Unable to parse range
```

**Causa:**
- ID da planilha no código está errado

**Verificar:**
Abra `google_sheets_ciclo.py` e verifique a linha 26:

```python
SPREADSHEET_ID = "14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk"
```

**Extrair ID correto da URL:**
```
https://docs.google.com/spreadsheets/d/14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk/edit
                                      ↑────────────────────────────────────────↑
                                               Este é o SPREADSHEET_ID
```

---

### 4. 📊 **Aba "Ciclo Automacao" Não Existe**

**Sintomas:**
```
❌ Erro ao registrar ciclo: Unable to parse range: 'Ciclo Automacao'!A:J
```

**Causa:**
- Aba não foi criada automaticamente
- Nome da aba está errado

**Solução Automática:**
O código cria automaticamente na primeira execução. Se falhar:

**Solução Manual:**
1. Abra a planilha no navegador
2. Clique em "+" no canto inferior esquerdo
3. Renomeie a nova aba para: **Ciclo Automacao** (exatamente assim!)
4. Adicione os cabeçalhos na linha 1:

| A | B | C | D | E | F | G | H | I | J |
|---|---|---|---|---|---|---|---|---|---|
| Data/Hora Início | Data/Hora Fim | Ciclo # | Status | Etapa Falha | Tempo Execução (min) | Observações | Operador | RPA Oracle | RPA Bancada |

---

### 5. ⚡ **Quota da API Excedida**

**Sintomas:**
```
❌ Quota exceeded for quota metric 'Write requests' and limit 'Write requests per minute per user'
❌ Rate Limit Exceeded
```

**Causa:**
- Muitas requisições em pouco tempo
- Google Sheets API tem limites:
  - **60 requisições/minuto/usuário**
  - **100 requisições/100 segundos/usuário**

**Solução:**
```python
# Aguardar 1 minuto e tentar novamente
import time
time.sleep(60)
```

**Prevenção:**
- Evitar rodar múltiplas instâncias do RPA simultaneamente
- Aguardar entre ciclos

---

### 6. 🌐 **Erro de Conexão/Internet**

**Sintomas:**
```
❌ Erro ao registrar ciclo: Failed to establish a new connection
❌ Connection timeout
❌ Name or service not known
```

**Causa:**
- Sem internet
- Firewall bloqueando
- Proxy corporativo

**Verificar:**
```bash
# Testar conexão com Google
ping www.google.com

# Testar se consegue acessar API
curl https://sheets.googleapis.com
```

**Solução:**
1. Verificar cabo de rede / WiFi
2. Verificar configurações de proxy
3. Desabilitar temporariamente firewall/antivírus
4. Adicionar exceção no firewall para Python/executável

---

### 7. 🗂️ **Arquivo CredenciaisOracle.json Corrompido/Ausente**

**Sintomas:**
```
❌ FileNotFoundError: Arquivo de credenciais não encontrado: CredenciaisOracle.json
❌ JSONDecodeError: Expecting value
```

**Causa:**
- Arquivo de credenciais não foi incluído no executável
- Arquivo está corrompido

**Solução:**

**Se rodando Python:**
```bash
# Verificar se arquivo existe
dir CredenciaisOracle.json

# Se não existir, copiar de backup
copy CredenciaisOracle_BACKUP.json CredenciaisOracle.json
```

**Se usando executável:**
- Recompilar com `BUILD_GENESYS.bat` (inclui credenciais automaticamente)

---

### 8. 🔄 **Conflito de Versão da API**

**Sintomas:**
```
❌ ImportError: cannot import name 'build' from 'googleapiclient.discovery'
❌ ModuleNotFoundError: No module named 'google'
```

**Causa:**
- Bibliotecas Google desatualizadas ou corrompidas

**Solução:**
```bash
# Reinstalar bibliotecas Google
pip uninstall google-api-python-client google-auth-httplib2 google-auth-oauthlib
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

---

## 🧪 Como Testar Manualmente

### Teste 1: Verificar Autenticação
```bash
cd rpa_ciclo/essential
python -c "from google_sheets_ciclo import authenticate_google; service = authenticate_google(); print('✅ Autenticação OK')"
```

### Teste 2: Verificar Acesso à Planilha
```bash
python -c "from google_sheets_ciclo import authenticate_google; service = authenticate_google(); result = service.spreadsheets().get(spreadsheetId='14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk').execute(); print('✅ Planilha acessível:', result['properties']['title'])"
```

### Teste 3: Registrar Ciclo de Teste
```bash
python
>>> from google_sheets_ciclo import registrar_ciclo
>>> from datetime import datetime
>>> registrar_ciclo(999, "Teste", datetime.now(), datetime.now(), observacoes="Teste manual")
```

Se aparecer `✅ Ciclo #999 registrado no Google Sheets`, está funcionando!

---

## 📋 Checklist de Diagnóstico

Execute estes comandos em ordem:

```bash
# 1. Verificar token existe
dir token.json

# 2. Verificar credenciais existem
dir CredenciaisOracle.json

# 3. Verificar internet
ping www.google.com

# 4. Verificar bibliotecas instaladas
pip show google-api-python-client

# 5. Testar autenticação
python -c "from google_sheets_ciclo import authenticate_google; authenticate_google()"
```

---

## 🔍 Logs Detalhados

Para ver logs detalhados do que está acontecendo:

```python
# Editar google_sheets_ciclo.py
# Adicionar no início:
import logging
logging.basicConfig(level=logging.DEBUG)
```

Isso mostrará todas as requisições HTTP para diagnosticar o problema.

---

## 🆘 Solução Rápida (Reset Completo)

Se nada funcionou, reset completo:

```bash
# 1. Deletar token
del token.json

# 2. Revogar acesso no Google
# Abrir: https://myaccount.google.com/permissions
# Remover permissão "Genesys RPA" ou similar

# 3. Reinstalar bibliotecas
pip install --upgrade --force-reinstall google-api-python-client google-auth-httplib2 google-auth-oauthlib

# 4. Executar novamente
python RPA_Ciclo_GUI_v2.py
```

---

## 📊 Verificar Planilha Manualmente

Acesse a planilha diretamente:
https://docs.google.com/spreadsheets/d/14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk

Verificar:
- ✅ Você tem acesso de **Editor** (não só Leitor)
- ✅ Aba "Ciclo Automacao" existe
- ✅ Cabeçalhos estão na linha 1
- ✅ Não há células mescladas

---

## 🚨 Erros Comuns e Soluções Rápidas

| Erro | Solução Rápida |
|------|----------------|
| `invalid_grant` | `del token.json` e reautenticar |
| `insufficient permissions` | Adicionar e-mail como Editor na planilha |
| `entity not found` | Verificar SPREADSHEET_ID |
| `Unable to parse range` | Criar aba "Ciclo Automacao" |
| `Quota exceeded` | Aguardar 1 minuto |
| `Connection timeout` | Verificar internet/firewall |
| `CredenciaisOracle.json not found` | Recompilar executável |

---

## 📞 Ainda com Problema?

Se após todas as tentativas ainda não funcionar:

1. **Copiar erro completo** (mensagem + stack trace)
2. **Verificar logs** da execução
3. **Executar teste manual** (teste 3 acima)
4. **Verificar permissões** da conta Google

---

**Data:** 2026-01-08
**Versão:** 1.0
