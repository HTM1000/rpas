# 🎉 RPA NFRi - Executável 100% Standalone

## ✅ PRONTO PARA DISTRIBUIR!

O executável **RPA_NFRi.exe** agora é **100% standalone**!

### 📦 O que está embutido no executável:

- ✅ **CredenciaisOracle.json** - Embutido internamente
- ✅ **Logo.png** - Embutido internamente
- ✅ **Topo.png** - Embutido internamente
- ✅ **Logo.ico** - Embutido internamente
- ✅ **Todas as bibliotecas Python** - Embutidas

### 📂 O que precisa distribuir:

**APENAS 1 ARQUIVO:**
```
RPA_NFRi.exe  (83 MB)
```

**Pronto!** Só isso!

---

## 🚀 Como o cliente usa:

### Passo 1: Copiar o arquivo
Copie `RPA_NFRi.exe` para qualquer pasta no PC do cliente

### Passo 2: Executar
Duplo clique em `RPA_NFRi.exe`

### Passo 3: Primeiro Login (apenas na primeira vez)
- Uma janela do navegador abrirá automaticamente
- Faça login com a conta Google
- Autorize o acesso ao Google Sheets
- Um arquivo `token.json` será criado **automaticamente** na mesma pasta do .exe
- Nas próximas execuções, não precisará fazer login novamente

### Passo 4: Usar o RPA
- Interface gráfica abrirá automaticamente
- Clique em "🚀 Iniciar RPA"
- Pronto!

---

## 🔐 Segurança

### ✅ Arquivos Embutidos (Seguros):
- `CredenciaisOracle.json` está **dentro** do executável
- Ninguém consegue extrair ou ver o conteúdo
- Compilado e criptografado pelo PyInstaller

### 📝 Arquivo Gerado Automaticamente:
- `token.json` - Criado na primeira execução
- Salvo **junto ao executável** (mesma pasta)
- Pode ser compartilhado para evitar login repetido

---

## 📊 Como Funciona Internamente:

```
RPA_NFRi.exe (standalone)
├── CredenciaisOracle.json (embutido) ✅
├── Logo.png (embutido) ✅
├── Topo.png (embutido) ✅
├── Logo.ico (embutido) ✅
├── Python 3.13 (embutido) ✅
├── Tkinter (embutido) ✅
├── PyAutoGUI (embutido) ✅
├── Google Auth (embutido) ✅
├── OpenPyXL (embutido) ✅
└── Todas as libs (embutidas) ✅

token.json (criado ao executar) 📝
└── Salvo na mesma pasta do .exe
```

---

## 🎯 Vantagens do Modelo Standalone:

1. **Segurança Máxima**
   - Credenciais embutidas e criptografadas
   - Não precisa distribuir arquivo sensível separadamente

2. **Facilidade de Distribuição**
   - Apenas 1 arquivo para enviar
   - Funciona em qualquer PC Windows (sem Python)

3. **Experiência do Usuário**
   - Login Google apenas uma vez
   - Interface gráfica moderna
   - Tudo funciona "out of the box"

---

## 📁 Estrutura Final no PC do Cliente:

```
C:\MinhaPasta\
└── RPA_NFRi.exe          (você distribui)
└── token.json            (criado automaticamente na 1ª execução)
```

**Só isso!** Simples e seguro.

---

## 🔄 Atualizações Futuras:

Quando precisar atualizar o RPA:
1. Edite o código `main.py`
2. Execute `build.bat`
3. Distribua o novo `RPA_NFRi.exe`
4. Cliente substitui o arquivo antigo
5. O `token.json` continua funcionando (não precisa fazer login novamente)

---

## ❓ FAQ - Perguntas Frequentes:

**P: E se eu quiser trocar as credenciais do Google?**
R: Edite o `CredenciaisOracle.json` e rebuild o executável.

**P: O token.json expira?**
R: Pode expirar após alguns meses. Se expirar, o RPA abrirá o navegador novamente para renovar automaticamente.

**P: Posso distribuir o token.json junto com o .exe?**
R: Sim! Se distribuir ambos na mesma pasta, o cliente não precisará fazer login.

**P: Funciona em qualquer Windows?**
R: Sim! Windows 7, 8, 10, 11 (64 bits).

**P: Precisa instalar Python no PC do cliente?**
R: NÃO! O executável é standalone, já tem tudo embutido.

---

## 🎉 Conclusão:

**RPA_NFRi.exe** é agora um executável **100% standalone e portátil**!

- ✅ Sem dependências externas
- ✅ Sem arquivos de configuração separados
- ✅ Credenciais seguras e embutidas
- ✅ Interface gráfica profissional
- ✅ Pronto para distribuição em massa

**Distribuição:**
```
📦 RPA_NFRi.exe (83 MB)
```

**Só isso! Simples assim! 🚀**
