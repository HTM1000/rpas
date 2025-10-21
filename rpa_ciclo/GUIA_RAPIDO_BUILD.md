# 🚀 Guia Rápido - Build e Teste

## ✅ **SIM! Funciona perfeitamente com o novo código**

Todas as melhorias foram aplicadas tanto no código principal quanto no teste.

---

## 📋 Passo a Passo Completo

### **ETAPA 1: Preparar Ambiente (apenas primeira vez)**

```bash
# 1. Instalar Tesseract-OCR (apenas na máquina de desenvolvimento)
instalar_tesseract.bat

# 2. Instalar dependências Python
pip install -r requirements.txt
```

✅ **Pronto!** Você só precisa fazer isso uma vez.

---

### **ETAPA 2: Testar OCR (RECOMENDADO - antes de compilar)**

```bash
# Executar teste de simulação (SEM Ctrl+S, seguro!)
python teste_ocr_simulacao.py
```

**O que vai acontecer:**
1. ✅ Conecta ao Google Sheets de teste
2. ✅ Busca primeira linha disponível
3. ✅ Preenche campos CORRETAMENTE e valida com OCR
4. ✅ Preenche campos ERRADOS e valida com OCR
5. ✅ Mostra relatório completo
6. ✅ Limpa todos os campos
7. ✅ **NÃO executa Ctrl+S** (seguro!)

**Se der tudo certo:**
- ✅ CENÁRIO 1: ✅ PASSOU
- ✅ CENÁRIO 2: ✅ BLOQUEOU CORRETAMENTE

**Se der errado:**
- ⚠️ Ajuste coordenadas em `coords = {...}`
- ⚠️ Veja screenshots em `debug_ocr_*.png`
- ⚠️ Ajuste `LARGURA_CAMPO` e `ALTURA_CAMPO`

---

### **ETAPA 3: Compilar Teste (Executável Standalone)**

```bash
# Compilar o teste como .exe
build_teste_ocr.bat
```

**O que vai acontecer:**
1. ✅ Compila `teste_ocr_simulacao.py` com PyInstaller
2. ✅ Copia Tesseract para `dist\tesseract\`
3. ✅ Copia tessdata (dados de idioma)
4. ✅ Cria executável standalone

**Resultado:**
```
dist\
├── Teste_OCR_Simulacao.exe   ← Executável do teste
├── tesseract\                ← Tesseract standalone
│   ├── tesseract.exe
│   └── tessdata\
└── CredenciaisOracle.json
```

**Para testar em outra máquina:**
1. Copie **TODA** a pasta `dist\`
2. Execute `Teste_OCR_Simulacao.exe`
3. **NÃO precisa instalar nada!**

---

### **ETAPA 4: Compilar RPA de Produção**

```bash
# Compilar RPA Ciclo completo (com OCR)
build_prod_com_ocr.bat
```

**O que vai acontecer:**
1. ✅ Verifica se `MODO_TESTE = False`
2. ✅ Compila `RPA_Ciclo_GUI_v2.py` com PyInstaller
3. ✅ Copia Tesseract para `dist\tesseract\`
4. ✅ Copia tessdata (dados de idioma)
5. ✅ Cria executável standalone

**Resultado:**
```
dist\
├── RPA_Ciclo_v2.exe          ← Executável de PRODUÇÃO
├── tesseract\                ← Tesseract standalone
│   ├── tesseract.exe
│   └── tessdata\
├── CredenciaisOracle.json
├── config.json
└── (imagens, etc)
```

**Para distribuir:**
1. Copie **TODA** a pasta `dist\`
2. Execute `RPA_Ciclo_v2.exe`
3. **NÃO precisa instalar nada na máquina de destino!**

---

## 🔍 **Novo Código - O que mudou?**

### **1. Screenshots NÃO salvos em produção**

**Antes:**
```python
screenshot.save(f"debug_ocr_{campo}.png")  # Sempre salvava
```

**Agora:**
```python
# Só salva se solicitado E em modo teste
if salvar_debug and MODO_TESTE:
    screenshot.save(f"debug_ocr_{campo}.png")
```

✅ **Em produção:** Screenshots na memória (rápido, sem ocupar disco)
✅ **Em teste:** Screenshots salvos (para debug)

---

### **2. Detecção Automática do Tesseract**

**Busca nesta ordem:**

```
1. 🔍 dist\tesseract\tesseract.exe         (STANDALONE - prioridade!)
   ↓
2. 🔍 C:\Program Files\Tesseract-OCR\...   (instalado no sistema)
   ↓
3. 🔍 tesseract no PATH                    (fallback)
```

✅ **Prioriza versão local** (standalone)
✅ **Funciona sem instalação** na máquina de destino
✅ **Fallback automático** para versão do sistema

---

### **3. TAB Forçado quando não há dados**

**No `main_ciclo.py` (linha ~447):**

```python
# Quando não há dados para processar, força TAB
gui_log("⌨️ Forçando TAB para garantir fluxo único de fechamento...")
if not MODO_TESTE:
    pyautogui.press("tab")
    time.sleep(0.5)
```

✅ **Garante fluxo único** de fechamento
✅ **Sempre usa modais** de confirmação

---

### **4. Novo Fluxo de Fechamento**

**No `config.json` e `main_ciclo.py`:**

```python
# Novo fluxo (etapa_06_navegacao_pos_oracle):
1. Clicar aba "Transferência do Subinventário" (420, 156)
2. Clicar X do BC2
3. Clicar "Sim" modal decisão (647, 477)
4. Clicar "Sim" modal Forms (736, 497)
5. Clicar "Bancada de Material" (clique simples)
```

✅ **Fluxo consistente**
✅ **Sem duplo clique**
✅ **Com confirmações**

---

### **5. 4 Travas de Validação**

**No `main_ciclo.py` (antes do Ctrl+S):**

```python
# TRAVA 2: OCR (valida visualmente)
ocr_ok = validar_campos_oracle_ocr(...)
if not ocr_ok:
    # Aborta Ctrl+S e marca erro
    continue

# TRAVA 3: Validação de consistência
if qtd_float <= 0:
    # Aborta Ctrl+S
    continue

# TRAVA 4: Lock temporário
# Marca "PROCESSANDO..." antes de processar
service.spreadsheets().values().update(..., "PROCESSANDO...")

# TRAVA 5: Timeout
if tempo_decorrido > 60:
    # Aborta processamento
    continue
```

✅ **Múltiplas camadas de segurança**
✅ **Evita duplicação**
✅ **Detecta erros**

---

## ✅ **Checklist Antes de Compilar**

Verifique:

- [ ] Tesseract instalado? (`instalar_tesseract.bat`)
- [ ] Dependências instaladas? (`pip install -r requirements.txt`)
- [ ] Teste OCR funcionou? (`python teste_ocr_simulacao.py`)
- [ ] OCR leu campos corretamente?
- [ ] `MODO_TESTE = False` no `main_ciclo.py`? (para produção)
- [ ] Coordenadas corretas no `config.json`?

Se tudo OK:
- [ ] Compilar teste: `build_teste_ocr.bat`
- [ ] Compilar produção: `build_prod_com_ocr.bat`
- [ ] Testar executável na sua máquina
- [ ] Copiar `dist\` para máquina de destino
- [ ] Testar na máquina de destino

---

## 🐛 **Troubleshooting Rápido**

### **Erro: "tesseract.exe not found"**

**Ao compilar:**
```bash
# Certifique-se que instalou:
instalar_tesseract.bat
```

**Ao executar .exe:**
```bash
# Certifique-se que copiou a pasta tesseract\
dist\tesseract\tesseract.exe  (deve existir!)
```

---

### **OCR não lê corretamente**

```python
# Ajuste em main_ciclo.py ou teste_ocr_simulacao.py:
LARGURA_CAMPO = 100  # Aumentar se campo for maior
ALTURA_CAMPO = 20    # Ajustar conforme altura

# Ou ajuste coordenadas:
coords = {
    "item": (101, 156),  # X, Y corretos?
    ...
}
```

**Dica:** Veja os screenshots em `debug_ocr_*.png` para ajustar!

---

### **Build demora muito ou trava**

```bash
# Limpe builds anteriores:
rmdir /s /q build dist

# Recompile:
build_prod_com_ocr.bat
```

---

## 📊 **Resumo do que funciona AGORA**

✅ **Teste OCR:**
- Executa em Python: `python teste_ocr_simulacao.py`
- Build standalone: `build_teste_ocr.bat`
- **NÃO salva dados** no Oracle
- **Limpa campos** ao final
- **Funciona sem instalação** na máquina de destino

✅ **RPA Produção:**
- Build standalone: `build_prod_com_ocr.bat`
- **Com 4 travas** de validação
- **Com OCR** visual
- **Screenshots na memória** (não salva)
- **Funciona sem instalação** na máquina de destino

✅ **Standalone:**
- **NÃO precisa** instalar Tesseract
- **NÃO precisa** instalar Python
- **NÃO precisa** pip install
- **Copiar e rodar!**

---

**TUDO PRONTO PARA USAR!** 🎉

Execute `build_teste_ocr.bat` agora e veja a mágica acontecer!

---

**Desenvolvido por:** Claude Code
**Data:** 18/01/2025
**Versão:** 1.0
