# 📦 Executável Standalone - SEM Instalação

## ✅ **IMPORTANTE: NÃO precisa instalar nada na máquina de destino!**

O executável do RPA Ciclo é **100% standalone** quando compilado com `build_prod_com_ocr.bat`.

---

## 🎯 O que significa "standalone"?

✅ **NÃO** precisa instalar Python
✅ **NÃO** precisa instalar Tesseract-OCR
✅ **NÃO** precisa instalar bibliotecas (pip install)
✅ **NÃO** precisa configurar PATH
✅ **NÃO** precisa permissões de administrador

**Basta copiar a pasta `dist\` e executar!**

---

## 📁 Estrutura do Executável Standalone

```
dist/
├── RPA_Ciclo_v2.exe          ← Executável principal (TUDO está aqui dentro)
├── tesseract/                ← Tesseract-OCR standalone (NÃO instalado no sistema)
│   ├── tesseract.exe
│   └── tessdata/
│       ├── eng.traineddata
│       ├── por.traineddata
│       └── (outros idiomas...)
├── CredenciaisOracle.json    ← Credenciais Google
├── config.json               ← Configurações do RPA
└── (outros arquivos de imagens, etc)
```

---

## 🚀 Como Distribuir

### Passo 1: Compilar na sua máquina (onde tem Tesseract instalado)

```bash
build_prod_com_ocr.bat
```

Este script irá:
- ✅ Compilar o RPA com PyInstaller
- ✅ **Copiar o Tesseract de `C:\Program Files\Tesseract-OCR` para `dist\tesseract\`**
- ✅ **Copiar tessdata (dados de idioma)**
- ✅ Incluir TODAS as bibliotecas Python dentro do .exe

### Passo 2: Copiar TODA a pasta `dist\` para a máquina de destino

⚠️ **Copie TUDO, não apenas o .exe!**

```
# Pode usar pendrive, rede, OneDrive, etc
# Copie a pasta dist\ completa para:
C:\RPA_Ciclo\
```

### Passo 3: Executar na máquina de destino

```bash
# Apenas execute o .exe:
C:\RPA_Ciclo\RPA_Ciclo_v2.exe
```

**Pronto! Funciona sem precisar instalar nada!**

---

## 🔍 Como o OCR Funciona Standalone

### Detecção Automática do Tesseract

O RPA procura o Tesseract nesta ordem:

```python
1. 🔍 Procura na pasta local (dist\tesseract\tesseract.exe)
   ↓
   ✅ ENCONTROU? Usa este! (STANDALONE - não precisa instalar)
   ↓
   ❌ NÃO ENCONTROU?
   ↓
2. 🔍 Procura no sistema (C:\Program Files\Tesseract-OCR\tesseract.exe)
   ↓
   ✅ ENCONTROU? Usa este! (instalado no sistema)
   ↓
   ❌ NÃO ENCONTROU?
   ↓
3. 🔍 Procura no PATH (tesseract)
   ↓
   ✅ ENCONTROU? Usa este!
   ↓
   ❌ NÃO ENCONTROU?
   ↓
4. ⚠️ OCR DESABILITADO (mas RPA funciona sem OCR)
```

### Vantagens da Detecção Automática

✅ **Prioriza a versão local** (standalone)
✅ **Fallback para versão instalada** (se existir)
✅ **Não quebra se Tesseract não estiver** (desabilita OCR gracefully)
✅ **Zero configuração manual**

---

## 💾 Otimização de Memória

### Screenshots NÃO são salvos em produção

Em **modo produção** (`MODO_TESTE = False`):
- ✅ OCR captura screenshot **apenas na memória**
- ✅ **NÃO salva** arquivos .png no disco
- ✅ Screenshot é **descartado imediatamente** após validação
- ✅ **Zero ocupação de espaço em disco**

Em **modo teste** (`MODO_TESTE = True`):
- ✅ Screenshots são salvos para debug (`debug_ocr_*.png`)
- ✅ Útil para ajustar coordenadas e dimensões

### Código de Otimização

```python
# NÃO salva screenshots em produção
sucesso, texto, conf = verificar_campo_ocr(
    x, y, largura, altura, valor_esperado,
    nome_campo="Item",
    salvar_debug=False  # ← Em produção, sempre False
)
```

---

## 🎛️ Configurações de Memória

### Tesseract usa pouca memória

- **Captura de tela**: ~20 KB por campo (100x20 pixels)
- **OCR em memória**: ~5 MB de RAM temporária
- **Total por linha**: ~10 MB (7 campos)
- **Limpa automaticamente**: Memória liberada após validação

### PyInstaller One-File

O `.exe` é **one-file** (tudo em um arquivo):
- ✅ Extrai temporariamente para `%TEMP%`
- ✅ Limpa automaticamente ao fechar
- ✅ Não deixa "sujeira" no sistema

---

## 📊 Comparação: Com vs Sem Instalação

| Aspecto | Tesseract Instalado | Tesseract Standalone |
|---------|---------------------|---------------------|
| **Precisa instalar?** | ✅ Sim (administrador) | ❌ Não |
| **Configurar PATH?** | ✅ Sim | ❌ Não |
| **Funciona em múltiplas máquinas?** | ⚠️ Precisa instalar em cada | ✅ Copiar pasta e pronto |
| **Tamanho do distribuível** | 🟢 Menor (~50 MB) | 🟡 Maior (~120 MB) |
| **Portabilidade** | 🔴 Baixa | 🟢 Alta |
| **Facilidade de deploy** | 🔴 Baixa | 🟢 Alta |

**Recomendação:** Use **standalone** para facilitar distribuição!

---

## 🐛 Troubleshooting

### "Tesseract-OCR não encontrado"

**Causa:** Pasta `tesseract\` não está junto com o .exe

**Solução:**
```bash
# Verifique se existe:
dist\tesseract\tesseract.exe
dist\tesseract\tessdata\

# Se não existir, recompile com:
build_prod_com_ocr.bat
```

### OCR não está funcionando

**Verificar logs:**
```
[OK] Tesseract LOCAL encontrado: C:\RPA_Ciclo\tesseract\tesseract.exe
[OK] pytesseract configurado com sucesso
```

Se aparecer:
```
[WARN] Tesseract-OCR não encontrado!
```

Então a pasta `tesseract\` não foi copiada corretamente.

### OCR funciona mas lê errado

**NÃO é problema de instalação!**

É problema de:
- ⚙️ Coordenadas incorretas
- ⚙️ Dimensões dos campos muito pequenas
- ⚙️ Qualidade da tela/fonte

**Solução:** Ajustar em `main_ciclo.py`:
```python
LARGURA_CAMPO = 100  # Aumentar
ALTURA_CAMPO = 20    # Ajustar
```

---

## 📦 Tamanho dos Arquivos

### Breakdown do executável standalone

```
RPA_Ciclo_v2.exe:          ~45 MB  (Python + bibliotecas)
tesseract/:
  ├── tesseract.exe        ~50 MB
  └── tessdata/            ~25 MB
TOTAL:                     ~120 MB
```

### Otimizações possíveis

Se quiser reduzir tamanho:

1. **Remover idiomas desnecessários** de `tessdata\`:
   ```bash
   # Manter apenas português e inglês:
   tessdata\eng.traineddata  (~5 MB)
   tessdata\por.traineddata  (~5 MB)
   # Deletar outros (~15 MB economizados)
   ```

2. **Usar UPX no PyInstaller** (já ativado):
   ```python
   # No .spec:
   upx=True  # Compacta executável
   ```

---

## ✅ Checklist de Distribuição

Antes de distribuir, verifique:

- [ ] Executável compilado com `build_prod_com_ocr.bat`
- [ ] Pasta `dist\tesseract\` existe e tem `tesseract.exe`
- [ ] Pasta `dist\tesseract\tessdata\` existe e tem `.traineddata`
- [ ] `CredenciaisOracle.json` está em `dist\`
- [ ] `config.json` está em `dist\`
- [ ] Testou na sua máquina: OCR funciona?
- [ ] Logs mostram: "Tesseract LOCAL encontrado"

Se tudo OK:
- [ ] Copiar **TODA** a pasta `dist\` para máquina de destino
- [ ] Executar e verificar logs novamente

---

## 🎓 Resumo Executivo

### Para o desenvolvedor (você)

1. ✅ Instale Tesseract uma vez: `instalar_tesseract.bat`
2. ✅ Compile o executável: `build_prod_com_ocr.bat`
3. ✅ Distribua a pasta `dist\` completa

### Para o usuário final (máquina de produção)

1. ✅ Recebe a pasta `dist\` (via rede, pendrive, etc)
2. ✅ Executa `RPA_Ciclo_v2.exe`
3. ✅ **Funciona!** (sem instalar nada)

---

## 📝 Notas Importantes

- ⚠️ O `.exe` é **grande** (~120 MB) mas é **completo**
- ✅ **Não precisa** Python, Tesseract ou bibliotecas instaladas
- ✅ **Portável**: Pode rodar de pendrive ou rede
- ✅ **Standalone**: 100% autocontido
- ✅ **Zero configuração**: Funciona "out of the box"

---

**Desenvolvido por:** Claude Code
**Data:** 18/01/2025
**Versão:** 1.0
