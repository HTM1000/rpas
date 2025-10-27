# 🤖 Genesys RPA - Documentação Completa

> Sistema automatizado de processamento Oracle com ciclo contínuo, validação OCR e detecção de erros

---

## 📋 Índice

1. [Como Gerar o Executável](#-como-gerar-o-executável)
2. [Estrutura do Projeto](#-estrutura-do-projeto)
3. [Funcionalidades Implementadas](#-funcionalidades-implementadas)
4. [Distribuição e Instalação](#-distribuição-e-instalação)
5. [Configuração](#-configuração)
6. [Solução de Problemas](#-solução-de-problemas)

---

## 🚀 Como Gerar o Executável

### Método Rápido (Recomendado)

```bash
BUILD_GENESYS.bat
```

Este script automaticamente:
- ✅ Verifica Python e PyInstaller
- ✅ Verifica se as imagens de detecção existem
- ✅ Limpa builds anteriores
- ✅ Gera o executável com PyInstaller
- ✅ Valida o build
- ✅ Oferece opção de copiar para Desktop

### Limpeza Prévia (Opcional)

Para remover arquivos antigos e desnecessários:

```bash
LIMPAR_ARQUIVOS_ANTIGOS.bat
```

Remove:
- Arquivos `.spec` antigos
- Scripts Python de teste
- Arquivos `.bat` obsoletos
- Logs e cache

### Build Manual

```bash
python -m PyInstaller --clean -y Genesys.spec
```

---

## 📁 Estrutura do Projeto

### Arquivos Essenciais

```
rpa_ciclo/
├── 🐍 Código Fonte
│   ├── RPA_Ciclo_GUI_v2.py          # Interface gráfica
│   ├── main_ciclo.py                # Lógica principal (COM validações)
│   ├── google_sheets_ciclo.py       # Google Sheets (ciclo)
│   └── google_sheets_manager.py     # Google Sheets (bancada)
│
├── ⚙️ Configuração
│   ├── config.json                  # Coordenadas e tempos
│   ├── CredenciaisOracle.json       # Google API
│   └── Genesys.spec                 # Build PyInstaller
│
├── 🖼️ Recursos
│   ├── Logo.png, Logo.ico
│   ├── Tecumseh.png, Topo.png
│   └── informacoes/
│       ├── qtd_negativa.png         # Detecção erro quantidade
│       ├── ErroProduto.png          # Detecção erro produto
│       └── (outras imagens...)
│
└── 🔧 Scripts
    ├── BUILD_GENESYS.bat            # Build automatizado
    ├── LIMPAR_ARQUIVOS_ANTIGOS.bat  # Limpeza
    └── instalar_tesseract.bat       # Instalador OCR
```

### Estrutura do Build Gerado

```
dist/Genesys/
├── Genesys.exe                      # ⭐ EXECUTÁVEL PRINCIPAL
├── _internal/
│   ├── informacoes/
│   │   ├── qtd_negativa.png        # Validação Oracle
│   │   ├── ErroProduto.png         # Validação Oracle
│   │   └── (outras imagens...)
│   ├── tesseract/
│   │   ├── tesseract.exe           # OCR
│   │   └── tessdata/               # Idiomas OCR
│   └── (DLLs e dependências...)
├── config.json
├── CredenciaisOracle.json
└── Logo.png, Tecumseh.png, Topo.png
```

---

## ✨ Funcionalidades Implementadas

### 1. Validação de Imagens Oracle

#### `qtd_negativa.png` - Erro de Quantidade Negativa
- 🔍 **Detecta:** Modal de erro de quantidade negativa
- ⚡ **Ação:** Pressiona Enter + Ctrl+S para salvar mesmo assim
- ✅ **Comportamento:** Continua processamento normalmente

#### `ErroProduto.png` - Erro de Produto
- 🔍 **Detecta:** Modal de erro de produto inválido
- 🛑 **Ação:** Marca linha como "PD" (Pendente) e PARA a aplicação
- ⚠️ **Comportamento:** Aplicação encerra para correção manual

**Localização no código:** `main_ciclo.py:600-667`

### 2. Sistema de Retry de OCR

Quando a validação OCR falha:

1. **Marca no Google Sheets:** "Erro OCR - Tentar novamente"
2. **NÃO adiciona ao cache:** Permite reprocessamento
3. **Próximo ciclo:** Linha é detectada e processada novamente
4. **Automático:** Não requer intervenção manual

**Fluxo:**
```
Item com erro OCR
  → Status: "Erro OCR - Tentar novamente"
  → Cache: NÃO adicionado
  → Próximo ciclo: Nova tentativa automática
  → Sucesso: Status: "Processo Oracle Concluído"
```

**Localização no código:** `main_ciclo.py:835, 1098-1112`

### 3. Correção da Etapa 6 (Navegação)

**Fluxo correto restaurado:**

1. ✅ Limpar formulário
2. ✅ Fechar modal "Subinventory Transfer (BC2)" (X)
3. ✅ Fechar modal "Transferencia do Subinventario (BC2)" (X)
4. ✅ **Clicar em "Janela"** para dar foco
5. ✅ Clicar no menu de navegação
6. ✅ Duplo clique em "4. Bancada de Material"

**Melhorias:**
- 🔍 Logs de debug em cada passo
- 🛡️ Tratamento de FAILSAFE (mouse no canto)
- ⚡ Verificação dupla de `_rpa_running`

**Coordenadas (config.json):**
- Janela: `x=340, y=40`
- Menu: `x=376, y=127`
- Bancada: `x=598, y=284` (duplo clique)

**Localização no código:** `main_ciclo.py:1199-1350`

---

## 📦 Distribuição e Instalação

### ⚠️ REGRA DE OURO

**❌ NUNCA distribua apenas o .exe**

**✅ SEMPRE distribua a PASTA COMPLETA `dist/Genesys/`**

### Por quê?

O executável depende de:
- 📁 `_internal/informacoes/` - Imagens de detecção de erros
- 📁 `_internal/tesseract/` - OCR para validação visual
- 📄 `config.json` - Coordenadas e configurações
- 📄 `CredenciaisOracle.json` - Credenciais Google

### Como Distribuir

**Opção 1: Copiar pasta completa**
```bash
xcopy "dist\Genesys" "C:\Users\ID135\Desktop\Genesys" /E /I /Y
```

**Opção 2: Compactar em ZIP**
1. Compacte `dist/Genesys/` inteira
2. Envie o ZIP
3. Extraia no destino
4. Execute `Genesys.exe`

**Opção 3: Usar o script de build**
```bash
BUILD_GENESYS.bat
```
→ Escolha "S" quando perguntar se quer copiar para Desktop

---

## ⚙️ Configuração

### config.json

```json
{
  "coordenadas": {
    "navegador_janela": {
      "x": 340,
      "y": 40,
      "descricao": "Clique em 'Janela' para dar foco"
    },
    "navegador_menu": {
      "x": 376,
      "y": 127,
      "descricao": "Clique no menu de navegação"
    },
    "tela_07_bancada_material": {
      "x": 598,
      "y": 284,
      "descricao": "Duplo clique em '4. Bancada de Material'",
      "duplo_clique": true
    }
  },
  "tempos_espera": {
    "entre_cliques": 3,
    "apos_modal": 5.0,
    "apos_rpa_oracle": 4.0,
    "apos_rpa_bancada": 4.0
  }
}
```

### Ajustar Coordenadas

Use o helper incluído:
```bash
python mouse_position_helper.py
```

Mova o mouse para a posição desejada e veja as coordenadas em tempo real.

---

## 🐛 Solução de Problemas

### Build

#### "qtd_negativa.png não encontrado"
```bash
# Verifique se existe:
dir informacoes\qtd_negativa.png

# Se não existir, adicione a imagem na pasta informacoes/
```

#### "ErroProduto.png não encontrado"
```bash
# Verifique se existe:
dir informacoes\ErroProduto.png

# Se não existir, adicione a imagem na pasta informacoes/
```

#### "PyInstaller não encontrado"
```bash
python -m pip install pyinstaller
```

### Execução

#### "Aplicação fecha ao clicar em Janela"

**Causa:** FAILSAFE do PyAutoGUI (mouse no canto 0,0)

**Solução:**
1. Verifique os logs:
   ```
   [DEBUG] _rpa_running=True | Tentando clicar em 'Janela'
   [DEBUG] Coordenadas de 'Janela': x=340, y=40
   🛑 [PASSO 4/6] FAILSAFE ACIONADO ao clicar em 'Janela'!
   ```

2. Se FAILSAFE foi acionado:
   - Mantenha o mouse longe do canto superior esquerdo (0,0)
   - Verifique se as coordenadas não passam por (0,0)

3. Se não foi FAILSAFE:
   - Verifique qual erro apareceu nos logs
   - Coordenadas podem estar incorretas

#### "Erro OCR - Dados não conferem"

**Causa:** Validação visual falhou

**Solução:**
- Linha será marcada como "Erro OCR - Tentar novamente"
- Será reprocessada automaticamente no próximo ciclo
- Se persistir, verifique se os dados estão visíveis na tela

#### "Detectado ERRO DE PRODUTO"

**Esperado:** Aplicação deve parar

**Comportamento:**
1. Linha marcada como "PD" (Pendente)
2. Aplicação encerra
3. Corrija o produto manualmente
4. Execute novamente

---

## 📊 Tabela Comparativa de Erros

| Situação | Comportamento | Status Sheets | Cache | Retry |
|----------|--------------|---------------|-------|-------|
| **ErroProduto.png detectado** | 🛑 PARA aplicação | "PD" | Não adiciona | Manual |
| **Erro validação OCR** | ⏭️ Pula linha | "Erro OCR - Tentar novamente" | Não adiciona | ✅ Automático |
| **qtd_negativa.png** | ✅ Continua | "Processo Oracle Concluído" | Adiciona | Não precisa |
| **Sucesso** | ✅ Continua | "Processo Oracle Concluído" | Adiciona | - |

---

## 🔄 Fluxo Completo de um Ciclo

```
1. Transferência Subinventário
2. Preencher Tipo (SUB)
3. Selecionar Funcionário (Wallatas)
4. ━━━ RPA ORACLE ━━━
   ├─ Buscar linhas no Google Sheets
   ├─ Para cada linha:
   │  ├─ Preencher dados no Oracle
   │  ├─ Validar com OCR
   │  ├─ Executar Ctrl+S
   │  ├─ Verificar erros (qtd_negativa.png, ErroProduto.png)
   │  └─ Atualizar Google Sheets
   └─ Fim RPA Oracle
5. ━━━ NAVEGAÇÃO ━━━
   ├─ Limpar formulário
   ├─ Fechar modal 1 (X)
   ├─ Fechar modal 2 (X)
   ├─ Clicar em "Janela"
   ├─ Clicar no menu
   └─ Abrir Bancada
6. ━━━ RPA BANCADA ━━━
   ├─ Clicar em Detalhado
   ├─ Pressionar Enter
   ├─ Aguardar 2 minutos
   ├─ Copiar dados da grid
   ├─ Processar e enviar para Google Sheets
   └─ Fim RPA Bancada
7. Fechar Bancada
8. ━━━ REINICIAR CICLO ━━━
```

---

## 📝 Notas Técnicas

### Requisitos

- **Python:** 3.8+
- **PyInstaller:** Instalado automaticamente pelo script
- **Tesseract OCR:** `C:\Program Files\Tesseract-OCR\` (para validação visual)

### Dependências Python

```
pyautogui
pyperclip
keyboard
google-auth
google-auth-oauthlib
google-api-python-client
pytesseract
Pillow
pandas
```

### Modo Teste

No arquivo `main_ciclo.py`, altere:

```python
MODO_TESTE = True   # Simula movimentos sem pyautogui
PARAR_QUANDO_VAZIO = True  # Para quando não há itens
```

---

## 📞 Suporte e Manutenção

### Logs

Os logs aparecem na interface gráfica em tempo real. Para debug avançado:

```python
# Procure por:
[DEBUG] _rpa_running=...
[PASSO X/6] ...
```

### Arquivos Importantes

- `processados.json` - Cache anti-duplicação
- `token.json` - Token Google Sheets (gerado automaticamente)

### Backup

Faça backup de:
- ✅ `config.json`
- ✅ `CredenciaisOracle.json`
- ✅ `processados.json`

---

## 🎯 Changelog

### Versão 3.0 (Janeiro 2025)

**Novas Funcionalidades:**
- ✅ Validação com imagens `qtd_negativa.png` e `ErroProduto.png`
- ✅ Sistema de retry automático para erros de OCR
- ✅ Logs de debug detalhados na Etapa 6

**Correções:**
- 🔧 Fluxo da Etapa 6 restaurado (incluindo clique em "Janela")
- 🔧 Tratamento de FAILSAFE do PyAutoGUI
- 🔧 Imagens incluídas no build PyInstaller

**Arquivos Atualizados:**
- `main_ciclo.py` - Lógica principal
- `Genesys.spec` - Build com novas imagens
- `BUILD_GENESYS.bat` - Script de build automatizado

---

## 📄 Licença

Uso interno - Tecumseh do Brasil

---

**Desenvolvido com ❤️ para automação de processos Oracle**

**Última atualização:** Janeiro 2025
