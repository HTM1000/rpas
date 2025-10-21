# 🧪 Teste de Simulação OCR - SEM Ctrl+S

## 📋 Visão Geral

Este script permite **testar a validação OCR sem executar o Ctrl+S**, garantindo que você não salve dados indesejados no Oracle durante os testes.

### O que o teste faz

1. ✅ Conecta ao Google Sheets de teste
2. ✅ Busca primeira linha disponível (Status = "CONCLUÍDO", Status Oracle vazio)
3. ✅ **CENÁRIO 1**: Preenche campos CORRETAMENTE e valida com OCR
4. ✅ **CENÁRIO 2**: Preenche campos ERRADOS e valida com OCR
5. ✅ Gera relatório detalhado
6. ❌ **NÃO executa Ctrl+S** (não salva no Oracle!)

---

## 🚀 Como Executar

### Opção 1: Executar em Python

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Executar teste
python teste_ocr_simulacao.py
```

### Opção 2: Executar como .exe standalone

```bash
# 1. Compilar executável
build_teste_ocr.bat

# 2. Executar (na pasta dist\)
dist\Teste_OCR_Simulacao.exe
```

---

## 📦 Gerar Executável Standalone

### Passo 1: Build

```bash
build_teste_ocr.bat
```

Este script irá:
- ✅ Compilar `teste_ocr_simulacao.py` com PyInstaller
- ✅ Copiar Tesseract-OCR para `dist\tesseract\`
- ✅ Incluir `CredenciaisOracle.json`
- ✅ Criar executável **standalone**

### Passo 2: Distribuir

**Copie TODA a pasta `dist\` para a outra máquina:**

```
dist\
├── Teste_OCR_Simulacao.exe   ← Executável principal
├── tesseract\                ← OBRIGATÓRIO para OCR
│   ├── tesseract.exe
│   └── tessdata\
├── CredenciaisOracle.json    ← Credenciais Google
└── (outros arquivos...)
```

⚠️ **NÃO** distribua apenas o `.exe` sozinho!

### Passo 3: Executar na outra máquina

1. ✅ Certifique-se que o Oracle está aberto
2. ✅ Posicione a janela do Oracle na tela
3. ✅ Execute `Teste_OCR_Simulacao.exe`
4. ✅ Você terá 5 segundos para posicionar a tela
5. ✅ O teste será executado automaticamente

---

## 📊 O que Esperar

### CENÁRIO 1: Preenchimento Correto

```
📝 Preenchendo Item: 12345
📝 Preenchendo Referência: MOV
📝 Preenchendo Sub.Origem: RAWCENTR
📝 Preenchendo End.Origem: A-01-01
📝 Preenchendo Sub.Destino: RAWINDIR
📝 Preenchendo End.Destino: B-02-02
📝 Preenchendo Quantidade: 10

🔍 [OCR] Iniciando validação visual dos campos...
✅ [OCR] Item: '12345' == '12345' (CORRETO)
✅ [OCR] Quantidade: '10' == '10' (CORRETO)
✅ [OCR] Referência: 'MOV' == 'MOV' (CORRETO)
✅ [OCR] Sub.Origem: 'RAWCENTR' == 'RAWCENTR' (CORRETO)
✅ [OCR] End.Origem: 'A-01-01' == 'A-01-01' (CORRETO)
✅ [OCR] Sub.Destino: 'RAWINDIR' == 'RAWINDIR' (CORRETO)
✅ [OCR] End.Destino: 'B-02-02' == 'B-02-02' (CORRETO)

✅ [OCR] Validação visual OK - Todos os campos conferem!
✅ CENÁRIO 1: OCR APROVARIA - Ctrl+S seria executado (mas não executamos)
```

### CENÁRIO 2: Preenchimento Errado

```
📝 Preenchendo Item ERRADO: 99999 (esperado: 12345)
📝 Preenchendo Quantidade ERRADA: 9999 (esperado: 10)

🔍 [OCR] Iniciando validação visual dos campos...
⚠️ [OCR] Item: Esperado '12345', Lido '99999' (Similaridade: 0.0%)
⚠️ [OCR] Quantidade: Esperado '10', Lido '9999' (Similaridade: 0.0%)

❌ [OCR] Validação visual FALHOU. Erros encontrados:
   - Item (esperado: 12345, lido: 99999)
   - Quantidade (esperado: 10, lido: 9999)

✅ CENÁRIO 2: OCR BLOQUEARIA CORRETAMENTE - Ctrl+S seria abortado
```

### Relatório Final

```
====================================================================
   RELATÓRIO FINAL DO TESTE
====================================================================

📊 CENÁRIO 1 - Preenchimento Correto:
   Resultado: ✅ PASSOU
   Campos validados:
      ✅ Item: esperado='12345', lido='12345', confiança=100.0%
      ✅ Quantidade: esperado='10', lido='10', confiança=100.0%
      ✅ Referência: esperado='MOV', lido='MOV', confiança=100.0%
      ✅ Sub.Origem: esperado='RAWCENTR', lido='RAWCENTR', confiança=100.0%
      ✅ End.Origem: esperado='A-01-01', lido='A-01-01', confiança=100.0%
      ✅ Sub.Destino: esperado='RAWINDIR', lido='RAWINDIR', confiança=100.0%
      ✅ End.Destino: esperado='B-02-02', lido='B-02-02', confiança=100.0%

📊 CENÁRIO 2 - Preenchimento Errado:
   Resultado: ✅ BLOQUEOU CORRETAMENTE
   Campos validados:
      ❌ Item: esperado='12345', lido='99999', confiança=0.0%
      ❌ Quantidade: esperado='10', lido='9999', confiança=0.0%
      ✅ Referência: esperado='MOV', lido='MOV', confiança=100.0%
      (...)

====================================================================
   LIMPANDO CAMPOS DO ORACLE
====================================================================

🧹 Apagando todos os campos preenchidos durante o teste...
   🧹 Limpando Item...
   🧹 Limpando Referência...
   🧹 Limpando Sub.Origem...
   🧹 Limpando End.Origem...
   🧹 Limpando Sub.Destino...
   🧹 Limpando End.Destino...
   🧹 Limpando Quantidade...

✅ Campos limpos com sucesso!

====================================================================
   TESTE CONCLUÍDO
====================================================================

⚠️  Lembre-se: Nenhum Ctrl+S foi executado!
⚠️  Os dados NÃO foram salvos no Oracle
✅  Todos os campos foram limpos!

📁 Screenshots salvos para debug:
   - debug_ocr_Item.png
   - debug_ocr_Quantidade.png
   - debug_ocr_Referência.png
   - (...)
```

---

## 📁 Screenshots de Debug

O teste salva screenshots de cada campo validado:

- `debug_ocr_Item.png`
- `debug_ocr_Quantidade.png`
- `debug_ocr_Referência.png`
- `debug_ocr_Sub.Origem.png`
- `debug_ocr_End.Origem.png`
- `debug_ocr_Sub.Destino.png`
- `debug_ocr_End.Destino.png`

Use esses screenshots para:
- ✅ Ver exatamente o que o OCR está lendo
- ✅ Ajustar coordenadas se necessário
- ✅ Verificar qualidade da captura

---

## ⚙️ Configurações

### Ajustar Coordenadas

Se o OCR não estiver lendo corretamente, ajuste em `teste_ocr_simulacao.py`:

```python
coords = {
    "item": (101, 156),           # Ajustar X e Y
    "sub_origem": (257, 159),
    "end_origem": (335, 159),
    "sub_destino": (485, 159),
    "end_destino": (553, 159),
    "quantidade": (672, 159),
    "Referencia": (768, 159),
}
```

### Ajustar Dimensões dos Campos

```python
LARGURA_CAMPO = 100  # Aumentar se campo for maior
ALTURA_CAMPO = 20    # Ajustar conforme altura da fonte
```

### Ajustar Planilha de Teste

```python
PLANILHA_TESTE_ID = "147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY"
SHEET_NAME = "Separação"
```

---

## 🐛 Troubleshooting

### Erro: "pytesseract não disponível"

**Solução:**
```bash
pip install pytesseract
```

### Erro: "tesseract.exe not found"

**Solução:**
- Instale o Tesseract: `instalar_tesseract.bat`
- Ou copie a pasta `tesseract\` para junto do `.exe`

### OCR não encontra nenhum campo

**Causa:** Coordenadas incorretas ou Oracle não visível

**Solução:**
1. Verificar se Oracle está maximizado/visível
2. Ajustar coordenadas em `coords`
3. Verificar screenshots em `debug_ocr_*.png`

### Teste não executa automaticamente

**Causa:** Não encontrou linha disponível na planilha

**Solução:**
- Verificar se tem linha com Status = "CONCLUÍDO"
- Verificar se Status Oracle está vazio
- Conferir URL da planilha

---

## 📋 Pré-requisitos

### Software Necessário

- ✅ Python 3.8+ (para rodar script)
- ✅ Tesseract-OCR instalado (para OCR funcionar)
- ✅ Oracle aberto e visível na tela
- ✅ Acesso ao Google Sheets de teste

### Arquivos Necessários

- ✅ `CredenciaisOracle.json` (credenciais Google)
- ✅ `token.json` (gerado na primeira execução)
- ✅ Planilha de teste configurada

---

## 🎯 Próximos Passos

Após executar o teste com sucesso:

1. ✅ Verificar relatório final
2. ✅ Analisar screenshots de debug
3. ✅ Ajustar coordenadas/dimensões se necessário
4. ✅ Testar na máquina de produção
5. ✅ Compilar versão final do RPA com OCR

---

## ⚠️ IMPORTANTE

- ❌ **Este teste NÃO executa Ctrl+S**
- ❌ **Nenhum dado é salvo no Oracle**
- ❌ **Nenhuma linha é marcada como processada no Sheets**
- ✅ **É 100% seguro para testar**
- ✅ **Pode executar quantas vezes quiser**

---

**Desenvolvido por:** Claude Code
**Data:** 18/01/2025
**Versão:** 1.0
