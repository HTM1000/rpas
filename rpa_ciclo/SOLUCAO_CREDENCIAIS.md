# 🔐 Solução para Credenciais Google Sheets

## 🐛 Problema Encontrado:

Erro 404 ao buscar Google Sheets - faltam arquivos de credenciais

## 📋 Arquivos Necessários:

1. **CredenciaisOracle.json** - Credenciais OAuth do Google
2. **token.json** - Token de acesso (gerado após primeira autenticação)

## ✅ Status Atual:

- [x] `CredenciaisOracle.json` - Incluído em `_internal/` no build
- [ ] `token.json` - **NÃO** incluído (precisa ser gerado ou copiado)

## 🎯 Soluções Possíveis:

### Opção 1: Cliente Gera o Token (Recomendado)

**O que acontece:**
1. Cliente executa o .exe pela primeira vez
2. Abre o navegador para autenticar no Google
3. `token.json` é gerado automaticamente
4. Nas próximas execuções, usa o token salvo

**Vantagem:** Mais seguro, token único por cliente
**Desvantagem:** Cliente precisa fazer autenticação OAuth

---

### Opção 2: Incluir token.json no Build

**Passos:**

1. Adicionar `token.json` ao spec:

```python
# Em RPA_Genesys_TESTE.spec e RPA_Genesys_PRODUCAO.spec
added_files = [
    # ... outros arquivos ...
    ('token.json', '.'),  # Adicionar esta linha
]
```

2. Rebuild:

```bash
python -m PyInstaller RPA_Genesys_TESTE.spec
python -m PyInstaller RPA_Genesys_PRODUCAO.spec
```

**Vantagem:** Cliente não precisa autenticar
**Desvantagem:**
- Token pode expirar
- Menos seguro (todos os clientes usam mesmo token)
- **Você precisa renovar o token quando expirar**

---

### Opção 3: Cliente Copia token.json Manualmente

**Instruções para o cliente:**

1. Receber 2 arquivos:
   - `RPA_Genesys_TESTE.zip` (ou PRODUCAO)
   - `token.json` (enviado separadamente, de forma segura)

2. Descompactar o .zip

3. Copiar `token.json` para dentro da pasta do executável:
   ```
   RPA_Genesys_TESTE/
     ├── RPA_Genesys_TESTE.exe
     ├── token.json          ← Copiar aqui
     └── _internal/
   ```

4. Executar o .exe

**Vantagem:** Controle total sobre o token
**Desvantagem:** Cliente precisa fazer passo manual

---

## 🔍 Verificar se é Realmente o Token

O erro 404 pode ser:

1. **Token.json faltando** ❓
2. **ID da planilha errado** ❓
3. **Permissões insuficientes** ❓

### Como verificar:

Execute o .exe e veja o log. Se aparecer:

```
FileNotFoundError: token.json
```

Então é problema do token.

Se aparecer:

```
HttpError 404: Requested entity was not found
```

Então pode ser:
- ID da planilha errado
- Planilha não compartilhada com a conta de serviço
- Credenciais inválidas

---

## 🎯 Recomendação Final:

**Para TESTE:** Use Opção 2 (incluir token.json no build)
- Cliente testa sem complicação
- Token de teste pode ser compartilhado

**Para PRODUÇÃO:** Use Opção 1 (cliente gera token)
- Mais seguro
- Token único por instalação

---

## 🔨 Aplicar Solução 2 (Incluir Token):

Execute estes comandos:

```bash
# 1. Backup do token atual
cp token.json token.json.backup

# 2. Já está feito - o arquivo existe!

# 3. Rebuild apenas teste (já tem CredenciaisOracle.json)
python -m PyInstaller RPA_Genesys_TESTE.spec
```

**IMPORTANTE:** O `token.json` NÃO deve ser commitado no Git por segurança!
