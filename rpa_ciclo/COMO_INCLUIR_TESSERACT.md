# Como Incluir Tesseract no Executável

## ✅ Solução Automática (Recomendado)

O Tesseract agora é **incluído automaticamente** no executável!

### Pré-requisito (apenas na sua máquina de desenvolvimento)

1. **Instale o Tesseract** no seu computador:
   - Download: https://github.com/UB-Mannheim/tesseract/wiki
   - Instale em: `C:\Program Files\Tesseract-OCR`
   - Durante a instalação, marque a opção "Additional language data" para incluir idiomas

### Como gerar o executável COM Tesseract

```bash
# Execute o script de build completo
build_completo_com_ocr.bat
```

### O que acontece automaticamente:

1. ✅ O script verifica se Tesseract está instalado em `C:\Program Files\Tesseract-OCR`
2. ✅ Se encontrado, **TODOS** os arquivos necessários são incluídos no .exe:
   - `tesseract.exe` (engine OCR)
   - `tessdata/*.traineddata` (arquivos de idioma)
   - Outros arquivos de configuração
3. ✅ Cria a estrutura:
   ```
   dist/
     RPA_Ciclo_v2.exe
     tesseract/
       tesseract.exe
       tessdata/
         eng.traineddata
         por.traineddata
         ... (outros idiomas)
   ```

### Como enviar ao cliente:

**IMPORTANTE:** Envie a **PASTA COMPLETA** `dist\` ao cliente!

```
📦 Enviar ao cliente:
   dist/
     ├── RPA_Ciclo_v2.exe          ← Executável principal
     ├── tesseract/                 ← Pasta do Tesseract
     │   ├── tesseract.exe         ← OCR engine
     │   └── tessdata/             ← Idiomas
     │       ├── eng.traineddata
     │       ├── por.traineddata
     │       └── ...
     ├── Logo.png
     ├── CredenciaisOracle.json
     ├── config.json
     └── ... (outros arquivos)
```

### Instruções para o cliente:

1. **Copie TODA a pasta `dist\` para a área de trabalho**
2. Renomeie `dist\` para algo como `RPA_Ciclo\` (opcional)
3. Execute `RPA_Ciclo_v2.exe` **dentro dessa pasta**

**IMPORTANTE:** O cliente NÃO precisa instalar Tesseract! Tudo já está incluído!

---

## 🔧 Verificação no Cliente

Quando o cliente executar, o log mostrará:

```
[OK] Tesseract LOCAL encontrado: C:\Users\...\tesseract\tesseract.exe
[OK] pytesseract configurado com sucesso
```

Se aparecer:

```
[WARN] Tesseract-OCR não encontrado!
[WARN] OCR não funcionará.
```

Significa que a pasta `tesseract\` não está no mesmo diretório do executável.

---

## ⚠️ Troubleshooting

### Problema: "Tesseract não encontrado" no cliente

**Causa:** Estrutura de pastas incorreta

**Solução:** Certifique-se de que o cliente tem:
```
Área de Trabalho/
  RPA_Ciclo_v2.exe          ← Executável
  tesseract/                 ← DEVE estar aqui!
    tesseract.exe
    tessdata/
```

### Problema: Build não inclui Tesseract

**Causa:** Tesseract não instalado na sua máquina de desenvolvimento

**Solução:**
1. Instale Tesseract em `C:\Program Files\Tesseract-OCR`
2. Execute `build_completo_com_ocr.bat` novamente

---

## 📊 Tamanho do Executável

- **Sem Tesseract:** ~50 MB
- **Com Tesseract:** ~60-70 MB (depende dos idiomas incluídos)

O aumento é pequeno e vale a pena para ter validação visual por OCR!

---

## 🎯 Vantagens desta Abordagem

✅ Cliente não precisa instalar nada
✅ Funciona offline (não depende de internet)
✅ Portátil (pode mover para qualquer pasta)
✅ Um único pacote para distribuir
✅ Menos suporte necessário

---

## 🔍 Como o Código Detecta o Tesseract

O código em `main_ciclo.py` (linhas 46-56) procura automaticamente:

1. **Prioridade 1:** Tesseract na pasta local (`./tesseract/tesseract.exe`)
2. **Fallback:** Tesseract instalado no sistema (`C:\Program Files\Tesseract-OCR`)

Como você está incluindo na pasta local, **sempre funcionará** mesmo sem instalação!
