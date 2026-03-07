# RPA BANCADA LOOP - Extração Contínua 🔄

Sistema de extração contínua da Bancada de Material do Oracle em **loop infinito**, com proteção anti-hibernação ultra-agressiva.

## 📋 O que faz?

Este RPA executa **indefinidamente** o seguinte ciclo:

1. **Navegar** até o menu da Bancada de Material
2. **Abrir** a Bancada (duplo clique)
3. **Extrair** dados:
   - Clicar em "Detalhado"
   - Pressionar Enter
   - Aguardar 2 minutos (carregamento)
   - Copiar todas as linhas
   - Monitorar clipboard até cópia completa
4. **Processar** dados:
   - Converter TSV para DataFrame
   - Salvar Excel local (`rpa_bancada/out/bancada-YYYY-MM-DD.xlsx`)
   - Enviar para Google Sheets
5. **Fechar** a janela da Bancada
6. **Repetir** (volta ao passo 1)

## 🚀 Como Usar

### Opção 1: Via arquivo .bat (RECOMENDADO)

```bash
cd C:/Users/ID135/OneDrive/Desktop/www/rpas/rpa_ciclo/essential
EXECUTAR_BANCADA_LOOP.bat
```

### Opção 2: Via Python

```bash
cd C:/Users/ID135/OneDrive/Desktop/www/rpas/rpa_ciclo/essential
python RPA_Bancada_Loop.py
```

## 🎮 Interface

A interface mostra:

- **Contador de ciclos** executados
- **Log em tempo real** de todas as operações
- **Botão INICIAR** - Começa o loop
- **Botão PARAR** - Interrompe o loop (ou pressione ESC)

## 🛡️ Proteção Anti-Hibernação (ULTRA-AGRESSIVA)

O sistema possui **três níveis** de proteção para garantir que o computador **NUNCA durma**:

### 1. Durante esperas (aguardar_com_pausa)
- Move o mouse 1px a cada 10 segundos

### 2. Durante cópia da bancada (movimento contínuo)
- Move o mouse **5px a cada 1 segundo**
- Pressiona **Shift a cada 15 segundos**

### 3. Sem pausas longas
- O loop é **contínuo** - não há espera entre ciclos
- Assim que fecha a bancada, já abre novamente

## ⚠️ Requisitos

1. **Oracle ERP aberto e logado**
2. **Estar na tela inicial do Oracle** (onde pode acessar o menu)
3. **Coordenadas configuradas** no `config.json`:
   - `navegador_janela` - Menu "Janela"
   - `navegador_menu` - Menu de navegação
   - `tela_07_bancada_material` - "4. Bancada de Material"
   - `bancada_detalhado` - Botão "Detalhado"
   - `bancada_celula_org` - Primeira célula da grid
   - `tela_08_fechar_bancada` - Botão X (fechar)

## 🛑 Como Parar

**3 formas de parar o RPA:**

1. Pressionar **ESC** a qualquer momento
2. Clicar no botão **"⏹ PARAR"**
3. Fechar a janela do aplicativo (confirmar quando perguntar)

## 📊 Saída de Dados

### Excel Local
- **Pasta:** `rpa_bancada/out/`
- **Nome:** `bancada-YYYY-MM-DD.xlsx`
- Sobrescreve o arquivo do dia atual a cada ciclo

### Google Sheets
- **Planilha:** Configurada em `google_sheets_manager.py`
- **SPREADSHEET_ID:** `1UgJWxmnYzv-FVTT4rrrVEx3J_MNXZsctwrPSTyyylPQ`
- Atualiza a planilha a cada ciclo

## ⏱️ Tempo por Ciclo

Estimativa de tempo **por ciclo completo**:

| Etapa | Tempo |
|-------|-------|
| Abrir bancada | ~10s |
| Clicar Detalhado + Enter | ~3s |
| Aguardar grid carregar | **2 minutos** |
| Copiar dados | ~30-60s (depende do tamanho) |
| Processar e salvar | ~5-10s |
| Fechar bancada | ~2s |
| **TOTAL** | **~3-4 minutos** |

## 🔧 Troubleshooting

### Problema: "Clipboard vazio após todas as tentativas"
**Solução:**
- A grid pode não ter carregado completamente
- Aumente o tempo de espera (2 minutos) no código se necessário
- Verifique se a bancada tem dados

### Problema: "Erro ao clicar em coordenada"
**Solução:**
- Verifique `config.json` - as coordenadas podem estar erradas
- Use `mouse_position_helper.py` para recapturar coordenadas
- Certifique-se que o Oracle está na resolução correta

### Problema: "Sistema está hibernando"
**Solução:**
- **IMPOSSÍVEL** - o sistema move o mouse constantemente
- Se acontecer, verifique configurações de energia do Windows
- Desative "Suspender" nas configurações de energia

## 📁 Arquivos do Sistema

```
essential/
├── RPA_Bancada_Loop.py          # Script principal
├── EXECUTAR_BANCADA_LOOP.bat    # Atalho para executar
├── config.json                   # Configurações (coordenadas, tempos)
├── google_sheets_manager.py      # Módulo Google Sheets (bancada)
└── rpa_bancada/
    └── out/
        └── bancada-YYYY-MM-DD.xlsx  # Excel gerado
```

## 🎯 Diferenças do RPA Ciclo Normal

| Aspecto | RPA Ciclo | RPA Bancada Loop |
|---------|-----------|------------------|
| **Escopo** | Oracle + Bancada (ciclo completo) | Apenas Bancada |
| **Repetição** | A cada 30 minutos | Infinito (sem espera) |
| **Anti-hibernação** | Durante bancada apenas | **Constante** |
| **Pausa** | 30 min entre ciclos | **Nenhuma** |
| **Processamento Oracle** | ✅ Sim | ❌ Não |

## 🚦 Status e Logs

O log mostra em tempo real:

```
[HH:MM:SS] 🔄 INICIANDO LOOP INFINITO DA BANCADA
[HH:MM:SS] ╔═══════════════════════════════════════════════╗
[HH:MM:SS] ║  CICLO #1                                      ║
[HH:MM:SS] ╚═══════════════════════════════════════════════╝
[HH:MM:SS] 🚀 ABRINDO BANCADA DE MATERIAL
[HH:MM:SS] 🖱️ [1/3] Clicando em 'Janela' para dar foco...
[HH:MM:SS] >> Clique em (340, 40) - Janela
...
[HH:MM:SS] ✅ Ciclo #1 concluído com sucesso!
```

## 💡 Dicas

1. **Deixe rodar de madrugada** - O sistema não precisa de supervisão
2. **Monitor de dados** - Verifique os arquivos Excel gerados periodicamente
3. **Google Sheets** - Acompanhe em tempo real pelo Sheets
4. **ESC sempre funciona** - Não importa onde esteja no ciclo

## ⚙️ Configurações Avançadas

Edite `RPA_Bancada_Loop.py` para ajustar:

```python
# Linha ~811: Tempo máximo de cópia
max_tempo=15 * 60  # 15 minutos (padrão)

# Linha ~812: Intervalo de verificação do clipboard
intervalo_check=3  # 3 segundos (padrão)

# Linha ~813: Tempo de estabilidade do clipboard
estabilidade_segundos=30  # 30 segundos (padrão)

# Linha ~751: Tempo de aguardar grid
aguardar_com_pausa(120, ...)  # 120s = 2 minutos (padrão)
```

## 📞 Suporte

Em caso de problemas:

1. Verifique o **log** na interface
2. Certifique-se que **todas as coordenadas** em `config.json` estão corretas
3. Teste manualmente cada etapa do processo
4. Verifique se **pyperclip**, **pandas** e **openpyxl** estão instalados

---

**Desenvolvido para Tecumseh do Brasil**
Sistema de Automação RPA - Bancada Loop v1.0
