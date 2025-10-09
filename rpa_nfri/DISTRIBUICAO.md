# 📦 Instruções de Distribuição - RPA NFRi

## ✅ Executável 100% Standalone Gerado!

O executável **RPA_NFRi.exe** foi criado em:
```
C:\Users\ID135\OneDrive\Desktop\www\rpas\rpa_nfri\dist\RPA_NFRi.exe
```

**Tamanho:** ~83 MB

---

## 🎉 NOVIDADE: Executável Standalone!

### ✨ O que mudou:

**ANTES:** Precisava distribuir 2 arquivos
- ❌ RPA_NFRi.exe
- ❌ CredenciaisOracle.json

**AGORA:** Apenas 1 arquivo!
- ✅ **RPA_NFRi.exe** (tudo embutido!)

### 🔐 Credenciais Embutidas:

O arquivo `CredenciaisOracle.json` agora está **embutido dentro do executável**!

- ✅ Mais seguro (criptografado)
- ✅ Mais fácil de distribuir (1 arquivo só)
- ✅ Impossível de extrair ou visualizar

---

## 📋 Checklist de Distribuição

Para distribuir o RPA, você precisa enviar:

### Arquivo Único:
- **Arquivo:** `RPA_NFRi.exe` (83 MB)
- **Localização:** `C:\Users\ID135\OneDrive\Desktop\www\rpas\rpa_nfri\dist\`

### (Opcional) Para evitar login:
- **Arquivo:** `token.json` - se você já tiver gerado
- Distribua junto com o .exe para que o cliente não precise fazer login Google

⚠️ **IMPORTANTE:** Se distribuir o token.json, coloque na mesma pasta do .exe

---

## 🚀 Como Distribuir

### Opção 1: Pasta Compactada (Recomendado)

1. Crie uma pasta chamada `RPA_NFRi`
2. Copie para dentro dela:
   - `RPA_NFRi.exe` (da pasta `dist`)
   - `CredenciaisOracle.json`
3. Compacte a pasta em `.zip`
4. Distribua o arquivo `.zip`

### Opção 2: Distribuição Manual

Envie os 2 arquivos separadamente e instrua o usuário a colocá-los na mesma pasta.

---

## 🔑 Primeira Execução - Login Google

### Passo a Passo:

1. **Executar o RPA pela primeira vez**
   - Duplo clique em `RPA_NFRi.exe`

2. **Login automático será solicitado**
   - Uma janela do navegador abrirá automaticamente
   - Faça login com a conta Google autorizada
   - Autorize o aplicativo a acessar Google Sheets

3. **Token gerado**
   - Um arquivo `token.json` será criado automaticamente
   - Esse arquivo fica salvo na mesma pasta do executável
   - Nas próximas execuções, o login não será mais necessário

### 💡 Dica de Distribuição:

Se você já tem o `token.json` gerado, pode distribuir **3 arquivos**:
- `RPA_NFRi.exe`
- `CredenciaisOracle.json`
- `token.json`

Isso evita que o usuário final precise fazer o login do Google!

---

## ⚙️ Configuração da Planilha

O RPA está configurado para enviar dados para:

- **ID da Planilha:** `1GnHcBKhXWKfU4Pcucyqj1_Vv9jiIkbY4iJ4prugD9ZE`
- **Nome da Aba:** `Página1`
- **URL:** [https://docs.google.com/spreadsheets/d/1GnHcBKhXWKfU4Pcucyqj1_Vv9jiIkbY4iJ4prugD9ZE/edit?gid=0#gid=0](https://docs.google.com/spreadsheets/d/1GnHcBKhXWKfU4Pcucyqj1_Vv9jiIkbY4iJ4prugD9ZE/edit?gid=0#gid=0)

### Permissões necessárias:

- A conta Google que fizer login deve ter **permissão de edição** na planilha
- Ou a planilha deve estar configurada como "Qualquer pessoa com o link pode editar"

---

## 🎯 Como Usar o RPA

1. **Preparação:**
   - Abra o sistema web (Sistemas Integrados)
   - Faça login no sistema
   - Deixe a tela na página inicial

2. **Executar o RPA:**
   - Duplo clique em `RPA_NFRi.exe`
   - Clique no botão **▶ Iniciar**
   - Confirme que está tudo pronto

3. **Automação:**
   - O RPA irá minimizar e começar a trabalhar
   - Ele irá:
     - ✅ Clicar em "Solução Fiscal"
     - ✅ Clicar em "NFs do Recebimento Integrado"
     - ✅ Gerar relatório Excel
     - ✅ Baixar o arquivo
     - ✅ Processar os dados
     - ✅ Enviar para Google Sheets

4. **Finalização:**
   - Uma mensagem de sucesso será exibida
   - O RPA volta para a tela principal

### ⌨️ Atalhos:

- **ESC** - Pausar/Parar o RPA durante a execução

---

## 🛠️ Ajustar Coordenadas (Se Necessário)

Se os cliques não estiverem funcionando corretamente (diferença de resolução de tela):

1. Use o arquivo `mouse.py` para capturar novas coordenadas:
   ```bash
   python mouse.py
   ```

2. Edite o arquivo `main.py` na seção `coords`:
   ```python
   coords = {
       "solucao_fiscal": (158, 335),
       "nfs_recebimento": (163, 383),
       "botao_excel": (507, 263),
       "campo_data": (690, 190),
       "excel_baixado": (950, 128),
   }
   ```

3. Rebuild o executável:
   ```bash
   build.bat
   ```

---

## 🔒 Segurança

### ⚠️ NÃO COMPARTILHE:

- ❌ `CredenciaisOracle.json` publicamente
- ❌ `token.json` em repositórios Git

### ✅ COMPARTILHE APENAS:

- ✅ Com usuários autorizados da sua organização
- ✅ Em canais seguros (não por email público)

---

## 🐛 Solução de Problemas

### Erro: "Nenhum arquivo NFRi encontrado"
- ✅ Verifique se o download foi concluído
- ✅ Confira a pasta Downloads do usuário
- ✅ Aguarde alguns segundos e tente novamente

### Erro ao enviar para Google Sheets
- ✅ Verifique se `CredenciaisOracle.json` está na mesma pasta
- ✅ Delete `token.json` e faça login novamente
- ✅ Confirme que a conta tem permissão na planilha

### Cliques não funcionam
- ✅ Ajuste as coordenadas conforme sua resolução de tela
- ✅ Use `mouse.py` para capturar novas coordenadas
- ✅ Verifique se o sistema está na tela correta

### O executável não abre
- ✅ Verifique se o Windows Defender não bloqueou
- ✅ Clique com botão direito → Propriedades → Desbloquear
- ✅ Execute como Administrador

---

## 📞 Suporte

Em caso de dúvidas ou problemas, entre em contato com a equipe de TI.

---

**Desenvolvido para Tecumseh**
Versão: 1.0
Data: Outubro 2025
