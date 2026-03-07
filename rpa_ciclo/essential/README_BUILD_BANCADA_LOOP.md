# 🔄 BUILD BANCADA LOOP - Executável Standalone

Guia completo para criar o executável **Bancada_Loop.exe** standalone.

---

## 🎯 O que é?

O **Bancada_Loop.exe** é um executável standalone que roda em loop infinito extraindo dados da Bancada de Material do Oracle:

- ✅ **Loop infinito** (sem espera entre ciclos)
- ✅ **GUI moderna** (igual ao RPA Ciclo)
- ✅ **Anti-hibernação ultra-agressiva**
- ✅ **Excel local + Google Sheets**
- ✅ **Contador de ciclos** em tempo real
- ✅ **Histórico de arquivos** gerados

---

## 📦 Como fazer o BUILD

### 1️⃣ Certifique-se que tem tudo

Arquivos **obrigatórios** na pasta `essential/`:

```
essential/
├── RPA_Bancada_Loop_GUI.py      ← GUI principal
├── RPA_Bancada_Loop.py          ← Lógica do loop
├── google_sheets_manager.py     ← Integração Google Sheets
├── CredenciaisOracle.json       ← Credenciais Google API
├── config.json                   ← Configurações (coordenadas)
├── Bancada_Loop.spec            ← Configuração PyInstaller
└── BUILD_BANCADA_LOOP.bat       ← Script de build
```

Arquivos **opcionais** (para UI bonita):
```
├── Logo.png           ← Logo Genesys
├── Logo.ico           ← Ícone da janela
├── Tecumseh.png       ← Logo Tecumseh
└── Topo.png           ← Ícone taskbar
```

### 2️⃣ Execute o BUILD

**Opção A: Duplo clique**
```
Duplo clique em: BUILD_BANCADA_LOOP.bat
```

**Opção B: Linha de comando**
```bash
cd C:/Users/ID135/OneDrive/Desktop/www/rpas/rpa_ciclo/essential
BUILD_BANCADA_LOOP.bat
```

### 3️⃣ Aguarde o build

O script vai:

1. ✅ Verificar Python e PyInstaller
2. ✅ Validar arquivos obrigatórios
3. ✅ Limpar builds anteriores
4. ✅ Executar PyInstaller
5. ✅ Validar executável criado
6. ✅ Perguntar se quer copiar para Desktop

**Tempo estimado:** ~2-3 minutos

### 4️⃣ Resultado

Se tudo der certo:

```
dist/
└── Bancada_Loop/
    ├── Bancada_Loop.exe           ← EXECUTÁVEL PRINCIPAL
    ├── _internal/                 ← Dependências (Python, libs, etc)
    ├── config.json                ← Coordenadas
    ├── CredenciaisOracle.json     ← Credenciais
    ├── Logo.png                   ← Imagens (se existirem)
    ├── Tecumseh.png
    └── Topo.png
```

---

## 🚀 Como DISTRIBUIR

### ⚠️ IMPORTANTE

**NUNCA distribua apenas o .exe!**

A pasta **completa** `Bancada_Loop/` é necessária.

### Distribuição correta:

1. Copie a pasta **completa**: `dist/Bancada_Loop/`
2. Cole no computador de destino (ex: Desktop)
3. Execute: `Bancada_Loop.exe`

### Estrutura final no destino:

```
Desktop/
└── Bancada_Loop/
    ├── Bancada_Loop.exe       ← Duplo clique aqui
    ├── _internal/             ← Não mexer!
    ├── config.json
    ├── CredenciaisOracle.json
    └── ...
```

---

## 🖥️ Como USAR o executável

### 1️⃣ Pré-requisitos

- ✅ Oracle ERP **aberto e logado**
- ✅ Estar na **tela inicial** do Oracle
- ✅ **Coordenadas corretas** no `config.json`

### 2️⃣ Executar

Duplo clique em: `Bancada_Loop.exe`

### 3️⃣ Interface

A interface vai mostrar:

```
╔═══════════════════════════════════════════════╗
║  RPA BANCADA LOOP                             ║
║  🔄 EXTRAÇÃO CONTÍNUA DA BANCADA              ║
╠═══════════════════════════════════════════════╣
║  [▶️ INICIAR LOOP]  [⏹️ Parar Loop (ESC)]     ║
╠═══════════════════════════════════════════════╣
║  Ciclos Executados: 0                         ║
╠═══════════════════════════════════════════════╣
║  Status: Aguardando                           ║
╠═══════════════════════════════════════════════╣
║  📋 LOG DE ATIVIDADES                         ║
║  [Logs em tempo real aqui...]                 ║
╠═══════════════════════════════════════════════╣
║  📁 HISTÓRICO DE ARQUIVOS EXCEL               ║
║  [Lista de arquivos gerados...]               ║
╚═══════════════════════════════════════════════╝
```

### 4️⃣ Iniciar o Loop

1. Clique em **"▶️ INICIAR LOOP"**
2. O sistema começa a executar:
   - Abrir Bancada
   - Extrair dados
   - Salvar Excel local
   - Enviar Google Sheets
   - Fechar Bancada
   - **REPETIR** (sem pausa)

### 5️⃣ Parar o Loop

**3 formas:**

1. Pressione **ESC**
2. Clique **"⏹️ Parar Loop (ESC)"**
3. Feche a janela (confirmar)

---

## 📊 Saída de Dados

### Excel Local

- **Pasta:** `Bancada_Loop/rpa_bancada/out/`
- **Nome:** `bancada-YYYY-MM-DD.xlsx`
- Sobrescreve o arquivo do dia a cada ciclo

### Google Sheets

- **Planilha ID:** `1UgJWxmnYzv-FVTT4rrrVEx3J_MNXZsctwrPSTyyylPQ`
- Atualiza a cada ciclo

---

## 🔧 Troubleshooting

### ❌ Build falhou

**Erro:** `PyInstaller not found`
```bash
pip install pyinstaller
```

**Erro:** `Arquivo XXX.py não encontrado`
- Certifique-se que está na pasta `essential/`
- Verifique se todos os arquivos estão presentes

### ❌ Executável não abre

**Windows Defender bloqueou:**
- Clique direito → Propriedades → Desbloquear
- Ou adicione exceção no Defender

**Erro ao abrir:**
- Verifique se distribuiu a **pasta completa**
- Não distribua apenas o .exe!

### ❌ Clipboard vazio

- Grid da bancada não carregou
- Aumente tempo de espera (2 minutos padrão)
- Edite `RPA_Bancada_Loop.py` linha ~751

### ❌ Erro ao clicar coordenadas

- Coordenadas erradas no `config.json`
- Use `mouse_position_helper.py` para recapturar
- Certifique-se que Oracle está na resolução correta

### ❌ Sistema hibernou

- **Impossível!** - proteção anti-hibernação ativa
- Verifique configurações de energia do Windows
- Desative "Suspender" nas configurações

---

## ⚙️ Configurações

### Alterar coordenadas

Edite: `Bancada_Loop/config.json`

```json
{
  "coordenadas": {
    "navegador_janela": {"x": 340, "y": 40},
    "navegador_menu": {"x": 376, "y": 127},
    "tela_07_bancada_material": {"x": 598, "y": 284, "duplo_clique": true},
    "bancada_detalhado": {"x": 273, "y": 358},
    "bancada_celula_org": {"x": 318, "y": 174},
    "tela_08_fechar_bancada": {"x": 746, "y": 90}
  }
}
```

### Alterar tempos de espera

Edite: `Bancada_Loop/config.json`

```json
{
  "tempos_espera": {
    "entre_cliques": 1.5,
    "apos_modal": 5.0
  }
}
```

---

## 📝 Notas Importantes

### ✅ O que ESTÁ incluído

- ✅ Python completo (embedded)
- ✅ Todas as bibliotecas (pandas, pyautogui, etc)
- ✅ Google API clients
- ✅ Imagens e logos
- ✅ Configurações

### ❌ O que NÃO está incluído

- ❌ Tesseract OCR (não precisa - bancada não usa OCR)
- ❌ OpenCV (não precisa - sem validação de imagem)
- ❌ Sistema de evidências (específico do Ciclo completo)

### 🔒 Segurança

- `CredenciaisOracle.json` está **embutido** no executável
- `token.json` será criado **na primeira execução** (fora do .exe)
- Token fica na mesma pasta do executável
- Se deletar `token.json`, vai pedir login novamente

---

## 🆚 Diferenças RPA Ciclo vs Bancada Loop

| Aspecto | RPA Ciclo | Bancada Loop |
|---------|-----------|--------------|
| **Escopo** | Oracle + Bancada | Apenas Bancada |
| **Loop** | A cada 30 min | Infinito |
| **Pausa** | 30 min entre ciclos | **Nenhuma** |
| **Oracle** | ✅ Processa | ❌ Não processa |
| **Bancada** | ✅ Extrai | ✅ Extrai |
| **Tamanho** | ~150 MB | ~80 MB |

---

## 📞 Suporte

### Build não funciona?

1. Verifique Python instalado: `python --version`
2. Instale PyInstaller: `pip install pyinstaller`
3. Certifique-se que está em `essential/`
4. Execute: `BUILD_BANCADA_LOOP.bat`

### Executável não funciona?

1. Distribua **pasta completa** (não só .exe)
2. Verifique `config.json` e `CredenciaisOracle.json`
3. Certifique-se que Oracle está aberto
4. Recapture coordenadas se necessário

---

**Desenvolvido para Tecumseh do Brasil**
RPA Bancada Loop v1.0 - Sistema de Extração Contínua
