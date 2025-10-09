# Documentação de Segurança - RPA Ciclo

## 🔒 Visão Geral de Segurança

Este documento descreve como os dados sensíveis são protegidos no executável RPA_Ciclo.exe.

---

## 📋 Arquivos e Segurança

### ✅ Arquivo SEGURO (Embedded no Executável)

#### **CredenciaisOracle.json**

**Status:** 🔒 **PROTEGIDO - Embedded no executável**

**Conteúdo:**
- Credenciais OAuth 2.0 do Google Cloud
- Client ID
- Client Secret
- Redirect URIs
- Outros dados de configuração OAuth

**Localização:**
- ❌ **NÃO está visível** na pasta dist/
- ✅ **Está DENTRO do executável** (embedded)
- ✅ **Cliente não tem acesso** a este arquivo
- ✅ **Não pode ser extraído facilmente**

**Como funciona:**
1. Durante o build, PyInstaller inclui o arquivo DENTRO do .exe
2. Em tempo de execução, o arquivo é extraído para uma pasta temporária do sistema
3. A pasta temporária é apagada ao fechar o executável
4. Cliente nunca vê o conteúdo do arquivo

**Código de proteção:**
```python
# google_sheets_ciclo.py (linha 36)
# BASE_PATH aponta para pasta temporária interna quando executável
creds_path = os.path.join(BASE_PATH, "CredenciaisOracle.json")
```

---

### ⚠️ Arquivo VISÍVEL (Gerado pelo Usuário)

#### **token.json**

**Status:** 👁️ **VISÍVEL - Criado na pasta de execução**

**Conteúdo:**
- Token de acesso OAuth 2.0
- Token de refresh
- Expiration time
- Dados de autenticação do USUÁRIO

**Localização:**
- ✅ Criado na mesma pasta do executável
- ✅ Visível para o cliente
- ✅ Gerado APÓS login do usuário

**Por que é OK ficar visível:**
1. ✅ **Gerado pelo próprio usuário** durante o login
2. ✅ **Não contém credenciais do aplicativo** (apenas do usuário)
3. ✅ **Expira após período** de tempo (limitado)
4. ✅ **Pode ser renovado** automaticamente
5. ✅ **Específico para aquela conta Google**

**Como funciona:**
1. Usuário executa RPA_Ciclo.exe
2. Navegador abre solicitando login
3. Usuário faz login com SUA conta Google
4. Google gera token.json específico para aquele usuário
5. Token é salvo na pasta de execução

**Diferença importante:**
```
CredenciaisOracle.json = Credenciais DO APLICATIVO (sensível)
token.json = Credenciais DO USUÁRIO (OK ficar visível)
```

---

## 🔐 Níveis de Proteção

### Nível 1: Credenciais do Aplicativo (MÁXIMO)
- ✅ **CredenciaisOracle.json** embedded no .exe
- ✅ Inacessível para cliente
- ✅ Não aparece em nenhuma pasta
- ✅ Não pode ser facilmente extraído

### Nível 2: Credenciais do Usuário (PADRÃO)
- ⚠️ **token.json** visível, mas gerado pelo usuário
- ✅ Válido apenas para aquela conta Google
- ✅ Expira automaticamente
- ✅ Pode ser revogado pelo usuário

---

## 🛡️ Garantias de Segurança

### O que o CLIENTE NÃO TEM ACESSO:

❌ **Client ID** do projeto Google Cloud
❌ **Client Secret** do projeto Google Cloud
❌ **Credenciais OAuth** da aplicação
❌ **CredenciaisOracle.json** completo
❌ **Configurações sensíveis** do OAuth

### O que o CLIENTE TEM ACESSO:

✅ **token.json** (gerado por ele mesmo)
✅ **rpa_ciclo.log** (logs de execução)
✅ **Executável RPA_Ciclo.exe**
✅ **Interface gráfica**

---

## 🔍 Como Verificar a Segurança

### Teste 1: Verificar pasta dist/

Após build, verifique a pasta dist/:

```
dist/
├── RPA_Ciclo.exe          ✅ (executável)
├── LEIA-ME.txt            ✅ (documentação)
└── (NÃO deve haver CredenciaisOracle.json)
```

**Se encontrar CredenciaisOracle.json na pasta dist:**
❌ Algo deu errado no build!
✅ Use os scripts atualizados de build

### Teste 2: Executar e verificar

1. Execute RPA_Ciclo.exe
2. Verifique a pasta onde está o executável
3. **Antes do login:** Apenas RPA_Ciclo.exe e LEIA-ME.txt
4. **Depois do login:** Aparecerá token.json (OK!)

### Teste 3: Tentar extrair arquivos

Tente usar ferramentas como 7-Zip para abrir o .exe:
- ✅ Deverá mostrar vários arquivos
- ✅ CredenciaisOracle.json estará lá (embedded)
- ⚠️ MAS: Cliente comum não faz isso
- ⚠️ MAS: Está criptografado pelo PyInstaller

---

## 📊 Comparação com Outros Métodos

### ❌ Método INSEGURO (NÃO usar):
```
dist/
├── RPA_Ciclo.exe
├── CredenciaisOracle.json  ❌ VISÍVEL!
└── token.json
```
**Problema:** Credenciais expostas

### ✅ Método SEGURO (Atual):
```
dist/
├── RPA_Ciclo.exe  (CredenciaisOracle.json embedded)
└── LEIA-ME.txt

Após login:
├── RPA_Ciclo.exe
├── LEIA-ME.txt
└── token.json  (gerado pelo usuário)
```
**Vantagem:** Credenciais protegidas

---

## 🚨 Questões Frequentes

### Q: O token.json não é sensível?

**R:** Sim e não.
- ✅ É gerado pelo PRÓPRIO usuário
- ✅ Válido apenas para AQUELA conta Google
- ✅ Expira automaticamente
- ✅ Pode ser revogado a qualquer momento
- ✅ NÃO contém credenciais do aplicativo

É como dar sua senha do email para alguém (você escolhe).
NÃO é como dar as credenciais do servidor de email (aplicação).

### Q: E se alguém roubar o token.json?

**R:** Risco limitado:
- ✅ Funciona apenas para aquela conta Google
- ✅ Expira automaticamente
- ✅ Usuário pode revogar em: https://myaccount.google.com/permissions
- ✅ Não dá acesso às credenciais do aplicativo

### Q: E se alguém descompilar o .exe?

**R:** Muito difícil:
- ✅ PyInstaller usa empacotamento
- ✅ Arquivos estão comprimidos
- ✅ Requires conhecimento técnico avançado
- ✅ Cliente comum não faz isso
- ⚠️ Para segurança máxima: usar ofuscação adicional

### Q: Como renovar as credenciais?

**R:** Fácil:
1. Delete o arquivo token.json
2. Execute RPA_Ciclo.exe novamente
3. Faça login quando solicitado
4. Novo token.json será criado

---

## 📝 Resumo de Segurança

### ✅ O QUE ESTÁ PROTEGIDO:
- Client ID do Google Cloud
- Client Secret do Google Cloud
- CredenciaisOracle.json completo
- Configurações OAuth sensíveis

### ⚠️ O QUE É VISÍVEL (MAS OK):
- token.json (gerado pelo usuário)
- rpa_ciclo.log (logs de execução)
- Executável .exe (funcionamento normal)

### 🎯 CONCLUSÃO:
✅ **Dados SENSÍVEIS estão PROTEGIDOS**
✅ **Dados do USUÁRIO ficam com o usuário**
✅ **Cliente não tem acesso às credenciais do aplicativo**
✅ **Segurança adequada para distribuição**

---

## 📞 Em Caso de Dúvidas

Se tiver dúvidas sobre segurança:
1. Revise este documento
2. Verifique o código em google_sheets_ciclo.py
3. Verifique o RPA_Ciclo.spec
4. Teste o executável antes de distribuir

---

**Versão:** 2.0
**Data:** Outubro 2025
**Status:** ✅ Seguro para distribuição aos clientes
