# 🔍 Verificação Visual com OCR - RPA Ciclo

## 📋 Visão Geral

O RPA Ciclo agora inclui **validação visual com OCR (Optical Character Recognition)** para garantir que os dados digitados no Oracle estejam corretos antes de executar o `Ctrl+S`.

### Como Funciona

1. ✅ Campos são preenchidos no Oracle com `pyautogui`
2. 🔍 **OCR captura screenshot de cada campo**
3. 📝 **Tesseract-OCR lê o texto na tela**
4. ✔️ **Compara com o valor esperado**
5. ⚠️ **Se não conferir, aborta Ctrl+S e marca linha como erro**
6. ✅ **Se conferir, prossegue com salvamento**

---

## 🚀 Instalação

### Opção 1: Instalação Automática (Recomendado)

```bash
# Execute o script de instalação
instalar_tesseract.bat
```

O script irá:
- ✅ Baixar o Tesseract-OCR automaticamente
- ✅ Instalar em `C:\Program Files\Tesseract-OCR`
- ✅ Adicionar ao PATH do sistema (opcional)

### Opção 2: Instalação Manual

1. **Baixe o Tesseract-OCR:**
   - URL: https://github.com/UB-Mannheim/tesseract/wiki
   - Versão recomendada: 5.3.3 (64-bit)

2. **Execute o instalador:**
   - Instale em: `C:\Program Files\Tesseract-OCR`
   - Marque todas as opções padrão
   - Inclua os dados de idioma (tessdata)

3. **Verifique a instalação:**
   ```bash
   tesseract --version
   ```

### Opção 3: Instalação via Chocolatey

```bash
choco install tesseract
```

---

## 🔧 Dependências Python

O RPA Ciclo já inclui as dependências necessárias no `requirements.txt`:

```txt
pytesseract>=0.3.10
Pillow>=9.0.0
```

Para instalar:

```bash
pip install -r requirements.txt
```

---

## 📦 Build do Executável Standalone com OCR

### Método 1: Build Automático com OCR

```bash
build_prod_com_ocr.bat
```

Este script irá:
- ✅ Verificar se Tesseract está instalado
- ✅ Compilar o executável com PyInstaller
- ✅ **Copiar o Tesseract-OCR para `dist\tesseract\`**
- ✅ **Copiar dados de idioma (tessdata)**
- ✅ Criar executável **100% standalone**

### Método 2: Build Manual

1. **Instale o Tesseract** (ver seção de instalação)

2. **Compile o executável:**
   ```bash
   python -m PyInstaller --clean RPA_Ciclo_v2.spec
   ```

3. **Copie o Tesseract para a pasta dist:**
   ```bash
   mkdir dist\tesseract
   xcopy "C:\Program Files\Tesseract-OCR\tesseract.exe" dist\tesseract\
   xcopy "C:\Program Files\Tesseract-OCR\tessdata" dist\tesseract\tessdata\ /E /I /Y
   ```

### ⚠️ IMPORTANTE: Distribuição

Ao distribuir o executável, você DEVE copiar:
- ✅ `dist\RPA_Ciclo_v2.exe`
- ✅ **`dist\tesseract\` (pasta completa)**

**NÃO** distribua apenas o `.exe` sozinho!

---

## 🎯 Como o OCR é Usado

### No Código

```python
# 🔒 TRAVA 2: Verificação visual com OCR
gui_log("👁️ [VISUAL] Iniciando verificação visual com OCR...")

# Validar campos usando OCR
ocr_ok = validar_campos_oracle_ocr(
    coords, item, quantidade, referencia,
    sub_o, end_o, sub_d, end_d
)

if not ocr_ok:
    gui_log("❌ [OCR] Validação visual falhou! Abortando Ctrl+S")
    # Reverte lock no Google Sheets
    # Marca linha como "OCR - Dados não conferem"
    continue  # Pula para próxima linha
```

### Campos Validados

O OCR valida os seguintes campos **ANTES** do `Ctrl+S`:

1. ✅ **Item** - Código do item
2. ✅ **Quantidade** - Quantidade a transferir
3. ✅ **Referência** - Código de referência (MOV ou COD)
4. ✅ **Sub.Origem** - Subinventário de origem
5. ✅ **End.Origem** - Endereço de origem
6. ✅ **Sub.Destino** - Subinventário de destino (se não for COD)
7. ✅ **End.Destino** - Endereço de destino (se não for COD)

### Tolerância de Erro

- **Similaridade >= 80%**: Campo aceito ✅
- **Similaridade < 80%**: Campo rejeitado ❌

O OCR permite pequenos erros de leitura (ex: confundir "0" com "O"), mas rejeita diferenças significativas.

---

## 📊 Logs de OCR

### Exemplo de Log com Sucesso

```
🔍 [OCR] Iniciando validação visual dos campos...
✅ [OCR] Item: '12345' == '12345' (CORRETO)
✅ [OCR] Quantidade: '10' == '10' (CORRETO)
✅ [OCR] Referência: 'MOV123' == 'MOV123' (CORRETO)
✅ [OCR] Sub.Origem: 'RAWCENTR' == 'RAWCENTR' (CORRETO)
✅ [OCR] End.Origem: 'A-01-01' == 'A-01-01' (CORRETO)
✅ [OCR] Sub.Destino: 'RAWINDIR' == 'RAWINDIR' (CORRETO)
✅ [OCR] End.Destino: 'B-02-02' == 'B-02-02' (CORRETO)
✅ [OCR] Validação visual OK - Todos os campos conferem!
💾 [CTRL+S] Executando salvamento no Oracle...
```

### Exemplo de Log com Falha

```
🔍 [OCR] Iniciando validação visual dos campos...
✅ [OCR] Item: '12345' == '12345' (CORRETO)
⚠️ [OCR] Quantidade: Esperado '10', Lido '1O' (Similaridade: 50.0%)
❌ [OCR] Validação visual FALHOU. Erros encontrados:
   - Quantidade (esperado: 10, lido: 1O)
❌ [OCR] Validação visual falhou! Abortando Ctrl+S
🔒 [LOCK] Revertendo lock: Status Oracle = "OCR - Dados não conferem"
```

---

## ⚙️ Configuração Avançada

### Ajustar Dimensões dos Campos

Se o OCR não estiver lendo corretamente, ajuste as dimensões em `main_ciclo.py`:

```python
def validar_campos_oracle_ocr(coords, item, quantidade, ...):
    # Dimensões padrão dos campos (ajustar conforme necessário)
    LARGURA_CAMPO = 100  # Aumentar se campo for maior
    ALTURA_CAMPO = 20    # Ajustar conforme altura da fonte
```

### Ajustar Tolerância de Similaridade

Para ser mais ou menos rigoroso:

```python
# Se similaridade for > 80%, considera aceitável
if confianca >= 0.8:  # Mudar para 0.7 (mais tolerante) ou 0.9 (mais rigoroso)
    gui_log(f"✅ [OCR] {nome_campo}: Similaridade aceitável")
    return (True, texto_lido, confianca)
```

### Desabilitar OCR Temporariamente

O OCR é desabilitado automaticamente se:
- ❌ `pytesseract` não estiver instalado
- ❌ Tesseract-OCR não for encontrado

Neste caso, a validação visual é pulada (mas outras travas continuam ativas).

---

## 🐛 Troubleshooting

### Erro: "pytesseract não disponível"

**Causa**: Biblioteca Python não instalada

**Solução**:
```bash
pip install pytesseract
```

### Erro: "tesseract.exe not found"

**Causa**: Tesseract-OCR não instalado ou não encontrado

**Solução 1** (Path incorreto no código):
```python
# Adicione manualmente em main_ciclo.py:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

**Solução 2** (Reinstalar):
```bash
instalar_tesseract.bat
```

### OCR lendo valores incorretos

**Causa**: Fonte do Oracle pequena, qualidade da tela ruim, ou coordenadas incorretas

**Solução**:
1. Aumentar `LARGURA_CAMPO` e `ALTURA_CAMPO`
2. Verificar se coordenadas em `coords` estão corretas
3. Aumentar zoom do Oracle (Ctrl + "+")
4. Verificar resolução da tela

### OCR muito lento

**Causa**: Tesseract processa muitos campos

**Solução**:
- Reduzir número de validações OCR (comentar campos menos críticos)
- Usar modo `--psm 7` (já está configurado) para single line
- Considerar validar apenas campos críticos (Item, Quantidade)

### Build sem OCR

Se o build foi feito sem copiar o Tesseract:

**Solução**:
```bash
# Recompilar com script correto
build_prod_com_ocr.bat
```

---

## 📈 Benefícios do OCR

1. ✅ **Detecção de erros de digitação** do pyautogui
2. ✅ **Validação visual** antes de salvar dados críticos
3. ✅ **Prevenção de dados incorretos** no Oracle
4. ✅ **Rastreabilidade** (logs mostram exatamente o que foi lido)
5. ✅ **Camada extra de segurança** além das validações lógicas

---

## 🎓 Comparação: Com e Sem OCR

| Aspecto | Sem OCR | Com OCR |
|---------|---------|---------|
| Validação | Apenas lógica (campos vazios, regras de negócio) | Lógica + Visual (lê o que está na tela) |
| Detecção de erros do pyautogui | ❌ Não detecta | ✅ Detecta |
| Confiança | 🟡 Média | 🟢 Alta |
| Performance | 🟢 Rápido | 🟡 Médio (+0.5s por linha) |
| Complexidade | 🟢 Simples | 🟡 Requer Tesseract |
| Distribuição | 🟢 .exe simples | 🟡 .exe + pasta tesseract |

---

## 📝 Checklist de Instalação

Antes de usar o OCR, verifique:

- [ ] Tesseract-OCR instalado em `C:\Program Files\Tesseract-OCR`
- [ ] `pytesseract` instalado (`pip install pytesseract`)
- [ ] `Pillow` instalado (`pip install Pillow`)
- [ ] Tesseract funciona no terminal (`tesseract --version`)
- [ ] Build incluiu pasta `tesseract\` em `dist\`
- [ ] `tessdata` (dados de idioma) foi copiado

---

## 🚀 Próximos Passos

Após configurar o OCR:

1. ✅ Executar em **modo teste** (`MODO_TESTE = True`)
2. ✅ Verificar logs de OCR
3. ✅ Ajustar dimensões/coordenadas se necessário
4. ✅ Testar com dados reais
5. ✅ Compilar versão de produção com `build_prod_com_ocr.bat`
6. ✅ Distribuir `dist\` completo (incluindo pasta `tesseract\`)

---

**Desenvolvido por:** Claude Code
**Data:** 18/01/2025
**Versão:** 1.0
