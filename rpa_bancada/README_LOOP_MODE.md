# RPA BANCADA - MODO LOOP INFINITO

## O que foi implementado

O RPA Bancada agora funciona em **modo loop infinito** com as seguintes funcionalidades:

### 1. Fluxo Completo do Loop

```
1. Autenticação Google Sheets (primeira vez)
   ↓
2. Abrir Bancada de Material (duplo clique)
   ↓
3. Clicar em "Detalhado"
   ↓
4. Clicar em "Localizar"
   ↓
5. Copiar todas as linhas
   ↓
6. Processar e salvar dados (Excel + Google Sheets)
   ↓
7. Fechar Bancada de Material (clique no X)
   ↓
8. Voltar ao passo 2 (loop infinito)
```

### 2. Autenticação Google Sheets

- Na **primeira execução**, o sistema vai pedir login no navegador
- O `token.json` será criado automaticamente
- Nas próximas execuções, usa o token salvo (não abre navegador)

### 3. Coordenadas Configuráveis

O arquivo `config.json` contém todas as coordenadas:

```json
{
  "coordenadas": {
    "tela_07_bancada_material": {
      "x": 598,
      "y": 284,
      "descricao": "Duplo clique em '4. Bancada de Material'"
    },
    "tela_08_fechar_bancada": {
      "x": 746,
      "y": 90,
      "descricao": "Clique no X para fechar a Bancada"
    },
    "bancada_detalhado": {
      "x": 273,
      "y": 358,
      "descricao": "Clique no botão Detalhado da Bancada"
    },
    "bancada_localizar": {
      "x": 524,
      "y": 689,
      "descricao": "Clique no botão Localizar da Bancada"
    },
    "bancada_celula_org": {
      "x": 318,
      "y": 174,
      "descricao": "Clique na primeira célula (Org) da grid"
    }
  },
  "tempos_espera": {
    "entre_cliques": 1.5,
    "apos_modal": 5.0,
    "apos_abrir_bancada": 3.0
  }
}
```

### 4. Arquivos Modificados

- ✅ `config.json` - Criado com coordenadas
- ✅ `main.py` - Adicionadas funções `abrir_bancada()` e `fechar_bancada()`
- ✅ `main.py` - Modificado para `single_run=False` (loop infinito)
- ✅ `main.py` - Adicionada autenticação Google Sheets no início
- ✅ `RPA_Bancada_GUI.py` - Atualizado para loop infinito
- ✅ `RPA_Bancada.spec` - Incluído `config.json` no build

### 5. Backup Criado

Um backup do arquivo original foi salvo em:
- `main_backup.py`

---

## Como fazer o BUILD

### 1. Navegue até a pasta do projeto:

```bash
cd C:/Users/ID135/OneDrive/Desktop/www/rpas/rpa_bancada
```

### 2. Execute o PyInstaller:

```bash
python -m PyInstaller RPA_Bancada.spec
```

### 3. O executável será criado em:

```
dist/RPA_Bancada.exe
```

### 4. Arquivos que devem estar junto ao executável:

- `CredenciaisOracle.json` (embedded no .exe)
- `config.json` (embedded no .exe)
- `token.json` (criado automaticamente na primeira execução)

---

## Como USAR

### 1. Pré-requisitos:

- Oracle Applications aberto
- Estar na tela principal do Oracle (onde aparece a opção "4. Bancada de Material")
- Resolução de tela: **1440x900** (recomendado)

### 2. Executar o RPA:

1. Abrir `RPA_Bancada.exe`
2. Clicar em "Iniciar RPA"
3. Na primeira vez, vai abrir o navegador para fazer login no Google
4. Após autenticação, o loop infinito começa

### 3. Para PARAR o RPA:

- **Opção 1:** Clicar no botão "Parar RPA"
- **Opção 2:** Mover o mouse para o canto superior esquerdo (FAILSAFE)

---

## Logs e Saídas

### Logs na Interface

O log mostrará cada passo:

```
[HH:MM:SS] 🔐 AUTENTICANDO GOOGLE SHEETS (PRIMEIRA VEZ)
[HH:MM:SS]    ✅ GOOGLE SHEETS AUTENTICADO!
[HH:MM:SS] 📂 Abrindo Bancada de Material (duplo clique)...
[HH:MM:SS]    ✅ Bancada aberta!
[HH:MM:SS] 🖱️ Clicando em 'Detalhado'...
[HH:MM:SS] 🖱️ Clicando em 'Localizar'...
[HH:MM:SS] 📋 Monitorando clipboard...
[HH:MM:SS] ✅ Dados capturados: 1,234 linhas x 8 colunas
[HH:MM:SS] 💾 Excel salvo: export-2026-01-07.xlsx
[HH:MM:SS] ✅ Dados enviados para Google Sheets!
[HH:MM:SS] 🔴 Fechando Bancada de Material...
[HH:MM:SS]    ✅ Bancada fechada!
[HH:MM:SS] 🔄 CICLO #2
[HH:MM:SS] 📂 Abrindo Bancada de Material (duplo clique)...
...
```

### Arquivos de Saída

- **Excel local:** `out/export-YYYY-MM-DD.xlsx` (um arquivo por dia, concatena dados)
- **Google Sheets:** Planilha configurada em `google_sheets_manager.py`

---

## Ajustar Coordenadas (se necessário)

Se as coordenadas não funcionarem na sua máquina:

### 1. Usar o mouse_position_helper.py

```bash
python mouse_position_helper.py
```

### 2. Anotar as coordenadas corretas

### 3. Editar o config.json

```json
{
  "coordenadas": {
    "tela_07_bancada_material": {
      "x": SEU_X_AQUI,
      "y": SEU_Y_AQUI
    },
    ...
  }
}
```

### 4. Fazer novo build

```bash
python -m PyInstaller RPA_Bancada.spec
```

---

## Troubleshooting

### Problema: "Clipboard vazio"

- **Causa:** Oracle demorou muito para copiar os dados
- **Solução:** Aumentar `POPUP_MAX` em `main.py` (linha ~49)

### Problema: "Bancada não abre"

- **Causa:** Coordenadas erradas ou resolução diferente
- **Solução:** Ajustar coordenadas no `config.json`

### Problema: "Google Sheets falha"

- **Causa:** Token expirado ou credenciais inválidas
- **Solução:** Deletar `token.json` e executar novamente (vai pedir login)

### Problema: "RPA não para quando clico em Parar"

- **Causa:** Thread pode estar em operação bloqueante
- **Solução:** Usar FAILSAFE (mover mouse para canto superior esquerdo)

---

## Versão

- **RPA Bancada Loop:** 1.0
- **Data:** 07/01/2026
- **Modo:** Loop Infinito
- **Resolução:** 1440x900 (recomendado)
