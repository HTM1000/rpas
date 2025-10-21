# 🔍 Melhorias do OCR - Validação Visual

## ✅ O que foi melhorado:

### 1. **Screenshots de Debug Automáticos**

Agora o sistema **SEMPRE salva** imagens do que o OCR está lendo na pasta do executável:

```
RPA_Genesys_TESTE/
  ├── RPA_Genesys_TESTE.exe
  ├── debug_ocr_Item.png                    ← Imagem original capturada
  ├── debug_ocr_Item_processado.png         ← Imagem após processamento
  ├── debug_ocr_Sub_Origem.png
  ├── debug_ocr_Sub_Origem_processado.png
  ├── debug_ocr_End_Origem.png
  └── ... (uma para cada campo validado)
```

### 2. **Tamanhos de Captura Ajustados**

Aumentamos os tamanhos das áreas capturadas:

| Campo | Antes | Agora | Motivo |
|-------|-------|-------|--------|
| Item | 100x20 | **150x25** | Capturar códigos completos (ex: E2035) |
| Sub.Origem/Destino | 100x20 | **120x25** | Textos longos (RAWCENTR) |
| End.Origem/Destino | 100x20 | **100x25** | Altura aumentada |
| Quantidade | 80x20 | **80x25** | Altura aumentada |
| Referência | 80x20 | **80x25** | Altura aumentada |

### 3. **Processamento de Imagem**

Agora a imagem é processada antes do OCR:
- ✅ Convertida para **escala de cinza**
- ✅ **Contraste aumentado** em 2x
- ✅ Melhora a taxa de acerto do Tesseract

### 4. **Configurações do Tesseract Otimizadas**

```python
config='--psm 7 --oem 3'
```

- `--psm 7`: Linha única de texto
- `--oem 3`: Usa LSTM + tradicional (mais preciso)

### 5. **Logs Detalhados**

Agora mostra no log o que está esperando:

```
[OCR] Validando Item: esperado='E2035'
[DEBUG] Screenshot salvo: debug_ocr_Item.png
⚠️ [OCR] Item: Esperado 'E2035', Lido '2' (Similaridade: 20.0%)
```

---

## 🔧 Como Usar as Imagens de Debug

### Quando o OCR falhar:

1. **Execute o RPA_Genesys_TESTE**
2. **Abra a pasta** onde o executável está
3. **Procure os arquivos** `debug_ocr_*.png`
4. **Analise as imagens:**

#### Exemplo de Problema:

**debug_ocr_Item.png:**
```
┌──────────┐
│  2       │  ← Capturando só parte do campo!
└──────────┘
```

**Solução:** Coordenada está errada, precisa ajustar `coords["item"]`

---

**debug_ocr_Sub_Origem.png:**
```
┌──────────────────┐
│ Subn Criantar    │  ← Texto com ruído/desfocado
│ RAWCENTR         │
└──────────────────┘
```

**Solução:** Coordenada Y está pegando o label, precisa abaixar

---

## 🎯 Como Ajustar Coordenadas

Se o OCR continuar falhando, você precisa ajustar as coordenadas no código:

### Arquivo: `main_ciclo_TESTE.py` (linha ~610)

```python
coords = {
    "item": (101, 156),           # ← Ajustar X e Y
    "sub_origem": (257, 159),     # ← Ajustar X e Y
    "end_origem": (335, 159),
    "sub_destino": (485, 159),
    "end_destino": (553, 159),
    "quantidade": (672, 159),
    "Referencia": (768, 159),
}
```

### Como encontrar as coordenadas corretas:

1. **Tire um screenshot** da tela do Oracle com os campos preenchidos
2. **Abra no Paint** ou editor de imagens
3. **Passe o mouse** sobre o **canto superior esquerdo** do campo
4. **Anote as coordenadas** X e Y
5. **Atualize** no código
6. **Rebuild** o executável

---

## 📊 Exemplo de Logs Melhorados

**ANTES:**
```
⚠️ [OCR] Item: Lido '2'
❌ [OCR] Validação falhou
```

**AGORA:**
```
[OCR] Validando Item: esperado='E2035'
[DEBUG] Screenshot salvo: debug_ocr_Item.png
[DEBUG] Screenshot salvo: debug_ocr_Item_processado.png
⚠️ [OCR] Item: Esperado 'E2035', Lido '2' (Similaridade: 20.0%)
❌ [OCR] Validação visual FALHOU. Erros encontrados:
   - Item (esperado: E2035, lido: 2)
```

Agora você pode **ver exatamente** o que o OCR capturou e corrigir!

---

## 🚀 Próximos Passos

1. **Execute o RPA_Genesys_TESTE** novamente
2. **Veja as imagens** `debug_ocr_*.png` geradas
3. **Me mande** as imagens ou descreva o que vê
4. **Ajustaremos** as coordenadas juntos

---

**Build atualizado:** `dist/RPA_Genesys_TESTE/RPA_Genesys_TESTE.exe`
**Data:** 18/10/2025 14:45
**Status:** ✅ Pronto para testar com debug ativo
