# 🚀 Como Gerar o Executável Genesys v4.0

## 📋 Pré-requisitos

1. **Python 3.8+** instalado
2. **Tesseract OCR** instalado em: `C:\Program Files\Tesseract-OCR\`
3. Todas as dependências instaladas (o script instala automaticamente)

---

## ⚡ Processo Rápido (1 comando!)

Abra o terminal na pasta `essential`:

```bash
cd C:\Users\ID135\OneDrive\Desktop\www\rpas\rpa_ciclo\essential
BUILD_GENESYS.bat
```

**Pronto!** O script faz tudo sozinho:
- ✅ Instala dependências
- ✅ Verifica módulos e imagens
- ✅ Limpa builds anteriores
- ✅ Gera executável com PyInstaller
- ✅ Valida que tudo foi incluído
- ✅ Oferece copiar para Desktop

---

## 📁 Resultado

O executável estará em:
```
rpa_ciclo/essential/dist/Genesys/
├── Genesys.exe          ← Executável principal
├── _internal/           ← Dependências e módulos
│   ├── informacoes/     ← Imagens de detecção
│   ├── internet_monitor.py
│   ├── screen_validator.py
│   ├── evidencias_manager.py
│   ├── drive_uploader.py
│   └── tesseract/       ← OCR engine
├── config.json
├── CredenciaisOracle.json
└── Logo.png, Tecumseh.png, Topo.png
```

⚠️ **IMPORTANTE:** Distribua a **PASTA COMPLETA** `Genesys`, não apenas o .exe!

---

## 🔧 O Que o Build Inclui (v4.0)

### **Sistema de Evidências Completo:**
- ✅ Monitor de Internet com Circuit Breaker
- ✅ Screenshots PRÉ e PÓS salvamento
- ✅ Validação de campos vazios (estratégia simplificada)
- ✅ Evidências JSON com checksums SHA256
- ✅ Upload automático para Google Drive

### **Verificações Críticas:**
- ✅ Não salva sem internet (requisito crítico!)
- ✅ Cache ANTES de Ctrl+S (previne duplicação)
- ✅ Validação visual com OCR
- ✅ Detecção de erros do Oracle (imagens)

---

## 🌐 Pasta de Evidências

Quando o RPA rodar, criará automaticamente:

**Local (próximo ao .exe):**
```
evidencias/
└── 06012026/           # Data de hoje (DDMMAAAA)
    ├── ITEM_100_REF001.json
    ├── ITEM_100_REF001_PRE_save.png
    └── ITEM_100_REF001_POS_save.png
```

**Google Drive:**
https://drive.google.com/drive/folders/1SRH4yOJc2DrG0aQspAek7RMH8w6yG_Yj

Mesma estrutura, upload automático!

---

## ❌ Erros Comuns

### "Erro: internet_monitor.py não encontrado"
**Solução:** Certifique-se de que está na pasta `essential/` onde estão os módulos novos.

### "Erro: tela_transferencia_subinventory.png não encontrada"
**Solução:** Esta imagem é obrigatória. Capture a tela limpa do Oracle antes de buildar.

### "PyInstaller não encontrado"
**Solução:** O script instala automaticamente. Se falhar, rode:
```bash
pip install pyinstaller
```

### "Tesseract não encontrado"
**Solução:** Instale Tesseract OCR:
- Download: https://github.com/UB-Mannheim/tesseract/wiki
- Instalar em: `C:\Program Files\Tesseract-OCR\`

---

## 🧪 Testar o Executável

1. Vá para `dist\Genesys\`
2. Execute `Genesys.exe`
3. Verifique se mensagens aparecem no console:
   ```
   ✅ [EVIDÊNCIAS] Monitor de Internet inicializado
   ✅ [EVIDÊNCIAS] Gerenciador inicializado
   ✅ [EVIDÊNCIAS] Drive Uploader inicializado
   ✅ [EVIDÊNCIAS] Sistema completo de evidências ativado
   ```
4. Teste com 1-2 itens
5. Verifique pasta `evidencias/DDMMAAAA/`
6. Confira no Drive se fez upload

---

## 📦 Distribuir para Produção

1. **Copie a pasta completa** `dist\Genesys\`
2. **NÃO distribua** apenas o .exe
3. **Mantenha a estrutura** de pastas intacta
4. **Certifique-se** de que `CredenciaisOracle.json` está incluído

---

## 🆘 Suporte

Se tiver problemas:
1. Verifique logs no console durante o build
2. Confira se todos os módulos foram incluídos (o script valida automaticamente)
3. Teste em modo desenvolvimento primeiro:
   ```bash
   python RPA_Ciclo_GUI_v2.py
   ```

---

**Desenvolvido por:** Claude Code
**Data:** 06/01/2026
**Versão:** Genesys v4.0 - Sistema Completo de Evidências
