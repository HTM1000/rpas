# RPA Ciclo - Versão TESTE vs PRODUÇÃO

## 📋 Resumo

Este documento explica as diferenças entre as versões **TESTE** e **PRODUÇÃO** do RPA Ciclo.

---

## 🔄 Diferenças entre TESTE e PRODUÇÃO

| Característica | **PRODUÇÃO** | **TESTE** |
|---------------|------------|---------|
| **Planilha Google Sheets** | `14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk` | `147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY` |
| **Build Script** | `BUILD_GENESYS.bat` | `BUILD_GENESYS_TESTE.bat` |
| **Executável** | `Genesys.exe` | `Genesys_TESTE.exe` |
| **Pasta dist** | `dist/Genesys/` | `dist/Genesys_TESTE/` |
| **Módulo Google Sheets** | `google_sheets_ciclo.py` | `google_sheets_ciclo_TESTE.py` |
| **Cache** | `processados.json` (compartilhado se mesma pasta) | `processados.json` (próprio) |

---

## 📋 Dependências

Todas as dependências estão listadas em `requirements.txt`. Os scripts de build instalam automaticamente.

**Para instalar manualmente:**
```bash
cd rpa_ciclo
pip install -r requirements.txt
```

**Principais dependências:**
- `keyboard` - Monitoramento da tecla ESC
- `requests` - Notificações Telegram
- `pyautogui`, `pyperclip` - Automação GUI
- `pytesseract`, `opencv-python`, `Pillow` - OCR e validação por imagem
- `pandas` - Processamento de dados da bancada
- `google-auth`, `google-api-python-client` - Integração Google Sheets

---

## 🚀 Como Gerar os Builds

### 📦 Build de PRODUÇÃO

```bash
cd rpa_ciclo
BUILD_GENESYS.bat
```

**O script faz automaticamente:**
1. Verifica Python instalado
2. **Instala dependências do requirements.txt**
3. Instala PyInstaller se necessário
4. Valida imagens necessárias
5. Limpa builds anteriores
6. Gera executável com PyInstaller
7. Valida build gerado

**Resultado:**
- Executável: `dist/Genesys/Genesys.exe`
- Usa planilha de produção
- Indicador no console: `[PROD] Usando google_sheets_ciclo.py - Planilha de PRODUÇÃO`

---

### 🧪 Build de TESTE

```bash
cd rpa_ciclo
BUILD_GENESYS_TESTE.bat
```

**Resultado:**
- Executável: `dist/Genesys_TESTE/Genesys_TESTE.exe`
- Usa planilha de teste
- Indicador no console: `[TESTE] Usando google_sheets_ciclo_TESTE.py - Planilha de TESTE`

---

## ⚙️ Funcionalidades Implementadas (Ambas Versões)

### ✅ Tecla ESC para Parar

- Pressione **ESC** durante a execução para parar o RPA gracefully
- O sistema detecta a tecla e para o ciclo atual
- Implementado via `keyboard.hook()` no `main_ciclo.py`

**Linha de código:**
```python
keyboard.hook(parar_callback)  # linha ~3617 em main_ciclo.py
```

### ✅ Notificações Telegram

- Configuradas via `config.json`:
  ```json
  "telegram": {
    "bot_token": "8300855810:AAEC4OTval-NLjnquKsd49aOG7b4NJZo5mU",
    "chat_id": "-4669835847",
    "habilitado": true
  }
  ```

- Módulo: `telegram_notifier.py`
- Notificações enviadas:
  - 🚀 Início de ciclo
  - 🔵 Processamento de item
  - ✅ Item concluído com sucesso
  - ❌ Erro no item
  - ⏭️ Item pulado
  - 🛑 Erro crítico
  - ✅/⚠️ Ciclo concluído (com contadores)

**Como usar no código:**
```python
from telegram_notifier import inicializar_telegram

telegram = inicializar_telegram()
telegram.notificar_ciclo_inicio(ciclo_numero=1)
telegram.notificar_sucesso_item(linha=5, item="ITEM-123")
```

### ✅ Validação por Imagem

- Valida tela antes do preenchimento (`tela_transferencia_subinventory.png`)
- Detecta queda de rede (`queda_rede.png`)
- Detecta erros do Oracle:
  - `qtd_negativa.png` - Quantidade negativa (continua)
  - `ErroProduto.png` - Produto inválido (PARA)
  - `tempo_oracle.png` - Timeout do Oracle

### ✅ OCR Tesseract

- Validação visual dos campos do Oracle
- Fallback para pyautogui se OpenCV não disponível
- Tesseract embedded no executável

---

## 🧪 Como Testar

### Teste Local (Desenvolvimento)

```bash
cd rpa_ciclo

# Teste com planilha de TESTE
python google_sheets_ciclo_TESTE.py

# Rodar GUI (usará versão TESTE se google_sheets_ciclo_TESTE.py existir)
python RPA_Ciclo_GUI_v2.py
```

### Teste com Executável

1. Gere o build de teste: `BUILD_GENESYS_TESTE.bat`
2. Execute: `dist\Genesys_TESTE\Genesys_TESTE.exe`
3. Verifique o console para confirmar:
   ```
   [TESTE] Usando google_sheets_ciclo_TESTE.py - Planilha de TESTE
   ```

---

## 📝 Arquivos Criados/Modificados

### ✅ Novos Arquivos

1. **`google_sheets_ciclo_TESTE.py`**
   - Cópia de `google_sheets_ciclo.py` com `SPREADSHEET_ID` de teste
   - ID: `147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY`

2. **`Genesys_TESTE.spec`**
   - Configuração PyInstaller para build de teste
   - Inclui `google_sheets_ciclo_TESTE.py` no bundle
   - Gera executável `Genesys_TESTE.exe`

3. **`BUILD_GENESYS_TESTE.bat`**
   - Script de build para versão de teste
   - Valida imagens necessárias
   - Copia para Desktop (opcional)

4. **`README_TESTE_vs_PROD.md`** (este arquivo)
   - Documentação das diferenças entre TESTE e PROD

### ✅ Arquivos Modificados

1. **`main_ciclo.py`** (linhas 79-92)
   - Tenta importar `google_sheets_ciclo_TESTE` primeiro
   - Fallback para `google_sheets_ciclo` (produção)
   - Mostra indicador no console `[TESTE]` ou `[PROD]`

---

## 🎯 Estratégia de Import Inteligente

O `main_ciclo.py` usa uma estratégia de import em cascata:

```python
# Tenta importar a versão TESTE primeiro, se não existir usa a produção
try:
    from google_sheets_ciclo_TESTE import registrar_ciclo, atualizar_ciclo
    print("[TESTE] Usando google_sheets_ciclo_TESTE.py - Planilha de TESTE")
except ImportError:
    try:
        from google_sheets_ciclo import registrar_ciclo, atualizar_ciclo
        print("[PROD] Usando google_sheets_ciclo.py - Planilha de PRODUÇÃO")
    except ImportError:
        print("⚠️ Google Sheets (ciclo) não disponível")
```

**Resultado:**
- Build de TESTE → Inclui `google_sheets_ciclo_TESTE.py` → Usa planilha de teste
- Build de PROD → NÃO inclui `google_sheets_ciclo_TESTE.py` → Usa planilha de produção

---

## 🔧 Configuração do Telegram

Edite `config.json` para configurar o Telegram:

```json
{
  "telegram": {
    "bot_token": "SEU_BOT_TOKEN_AQUI",
    "chat_id": "SEU_CHAT_ID_AQUI",
    "habilitado": true
  }
}
```

**Como obter:**
1. **Bot Token:** Crie um bot com [@BotFather](https://t.me/BotFather)
2. **Chat ID:** Use [@userinfobot](https://t.me/userinfobot) ou [@RawDataBot](https://t.me/RawDataBot)

---

## ⚠️ Importante

1. **SEMPRE distribua a pasta completa**, não apenas o `.exe`:
   - `Genesys.exe` / `Genesys_TESTE.exe`
   - `_internal/` (dependências, imagens, tesseract)
   - `config.json`
   - `CredenciaisOracle.json`
   - Imagens: `Logo.png`, `Tecumseh.png`, `Topo.png`

2. **Cache é compartilhado** se ambas versões rodarem na mesma pasta:
   - `processados.json` é criado na pasta do executável
   - Se quiser caches separados, rode em pastas diferentes

3. **Token Google OAuth** é compartilhado:
   - `token.json` é criado na pasta do executável
   - Ambas versões usam as mesmas credenciais do Google

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'keyboard'"

**Causa:** Dependências não instaladas

**Solução:**
```bash
cd rpa_ciclo
pip install -r requirements.txt
```

Ou instalar apenas o keyboard:
```bash
pip install keyboard
```

### "Google Sheets (ciclo) não disponível"

- Verifique se `CredenciaisOracle.json` existe
- Execute `python google_sheets_ciclo_TESTE.py` para testar conexão
- Instale dependências do Google: `pip install google-auth google-api-python-client`

### "Telegram não disponível"

- Verifique `config.json` → `telegram.habilitado = true`
- Teste com: `python testar_config_telegram.py`
- Instale requests: `pip install requests`

### Não está usando a versão TESTE

- Confirme que o build incluiu `google_sheets_ciclo_TESTE.py`
- Verifique no console se aparece `[TESTE]` ou `[PROD]`
- Rebuild usando: `BUILD_GENESYS_TESTE.bat`

### ESC não está funcionando

- O listener ESC só é ativado após iniciar o RPA
- Verifique se não há outro programa capturando a tecla ESC
- No Windows, pode precisar executar como Administrador

### Erro de build do PyInstaller

1. Limpe builds anteriores: `rmdir /S /Q build dist`
2. Reinstale dependências: `pip install -r requirements.txt`
3. Atualize PyInstaller: `pip install --upgrade pyinstaller`
4. Execute o build novamente

---

## 📚 Referências

- **Planilha de Produção:** https://docs.google.com/spreadsheets/d/14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk
- **Planilha de Teste:** https://docs.google.com/spreadsheets/d/147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY
- **Telegram API:** https://core.telegram.org/bots/api
- **PyInstaller Docs:** https://pyinstaller.org/

---

## 📝 Checklist de Deploy

### TESTE
- [ ] Gerar build: `BUILD_GENESYS_TESTE.bat`
- [ ] Confirmar mensagem `[TESTE]` no console ao rodar
- [ ] Testar notificações Telegram
- [ ] Testar ESC para parar
- [ ] Verificar se grava na planilha de teste

### PRODUÇÃO
- [ ] Gerar build: `BUILD_GENESYS.bat`
- [ ] Confirmar mensagem `[PROD]` no console ao rodar
- [ ] Testar notificações Telegram
- [ ] Testar ESC para parar
- [ ] Verificar se grava na planilha de produção

---

**Última atualização:** 27/10/2025
**Versão:** 3.0 (com Validação por Imagem + TESTE vs PROD)
