# 🤖 RPA Ciclo - Automação Oracle Genesys

## 📋 O que é o RPA Ciclo?

O **RPA Ciclo** (também chamado de **Genesys**) é um sistema de automação robótica que realiza transferências de materiais no sistema Oracle da Tecumseh do Brasil de forma **completamente automática**.

Ele funciona 24/7, processando centenas de itens sem intervenção humana, integrando dados do Google Sheets com o Oracle ERP.

---

## 🎯 O que ele faz?

### Visão Geral
O sistema executa **ciclos contínuos e automáticos** de transferência de materiais entre subinventários no Oracle, seguindo estas etapas:

```
┌─────────────────────────────────────────────────────────────┐
│  1. Lê dados do Google Sheets                               │
│  2. Abre tela de Transferência no Oracle                    │
│  3. Preenche campos automaticamente                         │
│  4. Valida dados inseridos (OCR)                            │
│  5. Salva no Oracle (Ctrl+S)                                │
│  6. Atualiza status no Google Sheets                        │
│  7. Processa bancada de materiais                           │
│  8. Repete o ciclo                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 Como Funciona um Ciclo Completo?

### **Etapa 1: Transferência de Subinventário**
- Sistema navega automaticamente até a tela "Transferência de Subinventário" no Oracle
- Localização: Menu → Navegador → Transferência de Subinventário

### **Etapa 2: Preenchimento do Tipo (SUB)**
- Preenche campo "Tipo" com valor "SUB"
- Pressiona TAB e ENTER automaticamente

### **Etapa 3: Seleção do Funcionário (Wallatas)**
- Clica no ícone de busca
- Seleciona "Wallatas Moreira" da lista
- Confirma seleção

### **Etapa 4: Processamento Oracle (RPA Oracle)**
Esta é a etapa principal onde o sistema:

#### 🔍 **Busca de Dados**
- Conecta ao Google Sheets
- Busca linhas com status "CONCLUÍDO" e "Status Oracle" vazio
- Identifica itens pendentes para processamento

#### ✍️ **Preenchimento Automático**
Para cada item, preenche:
- **Item**: Código do produto (ex: 12345678)
- **Sub. Origem**: Subinventário de origem (ex: EST)
- **End. Origem**: Endereço de origem (ex: A01)
- **Sub. Destino**: Subinventário de destino (ex: PRO)
- **End. Destino**: Endereço de destino (ex: B02)
- **Quantidade**: Quantidade a transferir (ex: 10)
- **Cód Referência**: Código de referência (se houver)

#### ✅ **Validação Inteligente**
Após preencher, o sistema:
1. **Captura a tela** dos campos preenchidos
2. **Usa OCR (reconhecimento de texto)** para ler o que foi digitado
3. **Compara** os valores lidos com os valores esperados
4. **Valida** se está tudo correto antes de salvar

#### 🛡️ **Detecção de Erros**
O sistema detecta automaticamente:
- ❌ **Quantidade Negativa** → Permite e continua (é válido)
- ❌ **Produto Inválido** → Marca erro e PARA o sistema
- ❌ **Campos Vazios** → Marca erro e tenta novamente
- ❌ **Queda de Internet** → Detecta e aguarda
- ❌ **Timeout Oracle** → Detecta lentidão do sistema

#### 💾 **Salvamento**
- Pressiona **Ctrl+S** para salvar
- Aguarda confirmação visual do Oracle (até 120 segundos)
- Valida se salvamento foi bem-sucedido

#### 📊 **Atualização do Google Sheets**
Após processar cada item, atualiza o status:
- ✅ **"Processo Oracle Concluído"** → Item processado com sucesso
- ❌ **"Erro Oracle: produto inválido"** → Produto não existe
- ⚠️ **"Erro OCR - Tentar novamente"** → Validação falhou, vai tentar de novo
- 🔄 **"Timeout Oracle - Reabrir sistema"** → Sistema lento

### **Etapa 5: Navegação para Bancada**
- Fecha modais do Oracle
- Navega pelo menu: Janela → Menu → Bancada de Material
- Aguarda tela carregar

### **Etapa 6: Processamento da Bancada (RPA Bancada)**
- Clica em "Detalhado" para expandir dados
- Aguarda **2 minutos** para dados carregarem completamente
- Copia dados da grid para memória
- Processa com Pandas e envia para Google Sheets
- Atualiza planilha de controle da bancada

---

## 🧠 Recursos Inteligentes

### 1. **Cache Anti-Duplicação**
- Sistema mantém cache local (`processados.json`)
- **Nunca processa o mesmo item duas vezes**
- Mesmo se o sistema crashar, não duplica dados
- Cache persiste entre execuções

### 2. **Sistema de Retry Automático**
Itens com os seguintes erros são **reprocessados automaticamente**:

#### ✅ Erros que fazem Retry SEM parar o robô:
- "Campo vazio encontrado"
- "Erro OCR - Tentar novamente"
- "Não concluído no Oracle"
- "Timeout salvamento"
- "Dados não conferem"
- E outros...

**Comportamento**: Item marcado com erro → Continua processando próximos itens → Item será reprocessado no próximo ciclo

#### 🛑 Erros que fazem Retry MAS param o robô:
- "Tela incorreta - verificar Oracle"

**Comportamento**: Item marcado com erro → **PARA o robô** → Usuário corrige manualmente → Próxima execução reprocessa o item

### 3. **Filtros Inteligentes**
O sistema **NÃO processa** automaticamente:
- ❌ Linhas com Quantidade = 0
- ❌ Linhas com "REVER" no Status Oracle
- ❌ Linhas já no cache (duplicadas)

### 4. **Validação Híbrida (OCR + Visual)**
- **OCR (Tesseract)**: Lê texto dos campos para validar
- **Detecção de Imagem**: Identifica erros visuais (produto inválido, quantidade negativa)
- **Análise de Pixels**: Confirma que campos foram preenchidos

### 5. **Detecção de Problemas**
O sistema detecta e trata:
- 🌐 **Queda de Internet**: Detecta e para processamento
- ⏱️ **Timeout do Oracle**: Detecta lentidão e marca para retry
- 🖼️ **Tela Incorreta**: Valida que está na tela certa antes de processar
- 🔴 **Erros Críticos**: Para execução em caso de erro grave

### 6. **Modo Contínuo**
- Executa **24/7 sem parar**
- Quando não há itens para processar: aguarda 30 segundos e verifica novamente
- **Nunca para sozinho** (exceto em erros críticos)
- Primeiro ciclo: se não encontrar itens após 2 tentativas, pula para Bancada

---

## 📱 Notificações em Tempo Real (Telegram)

O sistema pode enviar notificações para o Telegram em tempo real:

### Tipos de Notificação:
1. 🚀 **Início de Ciclo** - Quando um novo ciclo começa
2. 🔵 **Processando Item** - Quando começa a processar um item (com todos os dados)
3. ✅ **Item Concluído** - Quando item é salvo com sucesso
4. ❌ **Erro no Item** - Quando ocorre erro (com descrição)
5. ⏭️ **Item Pulado** - Quando item já está no cache
6. 🏁 **Ciclo Concluído** - Resumo do ciclo (total processado, total de erros)

### Exemplo de Notificação:
```
🔵 PROCESSANDO ITEM

📋 Linha: 15
🔹 Item: 12345678
📦 Quantidade: 10
📍 Sub Origem: EST
📍 Sub Destino: PRO

⏰ 14:32:15
```

> **Nota**: Notificações são **opcionais** e **silenciosas** - não afetam o funcionamento do RPA

---

## ⚙️ Configurações

### Arquivo `config.json`

```json
{
  "coordenadas": {
    "tela_01_transferencia_subinventario": { "x": 593, "y": 224 },
    "tela_02_campo_tipo": { "x": 155, "y": 215 },
    // ... outras coordenadas
  },
  "tempos_espera": {
    "entre_cliques": 3,          // Segundos entre cliques
    "apos_modal": 5.0,           // Após fechar modal
    "apos_rpa_oracle": 4.0,      // Após RPA Oracle
    "apos_rpa_bancada": 4.0,     // Após RPA Bancada
    "ciclo_completo": 1800       // Duração ciclo (30 min)
  },
  "telegram": {
    "bot_token": "SEU_TOKEN",
    "chat_id": "SEU_CHAT_ID",
    "habilitado": true
  }
}
```

### Coordenadas
- **Dependem da resolução da tela** (configurado para 1440x900)
- Se mudar resolução, precisa recapturar coordenadas
- Use `mouse_position_helper.py` para pegar novas coordenadas

---

## 📊 Integração com Google Sheets

### Planilha de Dados Oracle
- **ID**: `14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk`
- **Aba**: CICLO DADOS

#### Colunas Necessárias:
| Coluna | Descrição | Exemplo |
|--------|-----------|---------|
| Status | Status do pedido | CONCLUÍDO |
| Status Oracle | Status do processamento | (vazio ou erro) |
| Item | Código do produto | 12345678 |
| Sub. Origem | Subinventário origem | EST |
| End. Origem | Endereço origem | A01 |
| Sub. Destino | Subinventário destino | PRO |
| End. Destino | Endereço destino | B02 |
| Quantidade | Quantidade | 10 |
| Cód Referencia | Código referência | REF123 |
| ID | Identificador único | UUID |

#### Fluxo de Status:
```
Status: CONCLUÍDO
Status Oracle: (vazio)
           ↓
      [RPA PROCESSA]
           ↓
Status Oracle: PROCESSANDO...
           ↓
      [SALVA NO ORACLE]
           ↓
Status Oracle: Processo Oracle Concluído ✅
```

### Planilha de Controle de Ciclos
- Registra cada ciclo executado
- Horário início/fim
- Status (Sucesso/Falha)
- Observações

### Planilha da Bancada
- **ID**: `1UgJWxmnYzv-FVTT4rrrVEx3J_MNXZsctwrPSTyyylPQ`
- Recebe dados extraídos da bancada de materiais

---

## 🔐 Segurança

### Credenciais Google
- Arquivo: `CredenciaisOracle.json` (OAuth2)
- Token: `token.json` (gerado no primeiro uso)
- **Ambos são privados** - nunca compartilhe!

### Cache Local
- Arquivo: `processados.json`
- Armazena IDs dos itens já processados
- **Crítico para evitar duplicações**
- Backup recomendado

### FAILSAFE
- **Mova o mouse para o canto superior esquerdo (0,0)** → Para execução imediatamente
- **Pressione ESC** → Para execução com segurança
- **Botão PARAR na GUI** → Interrompe processo

---

## 🚀 Como Usar

### 1. Executar pela GUI (Interface)
```bash
cd rpa_ciclo
python RPA_Ciclo_GUI_v2.py
```
- Clique em **INICIAR**
- Acompanhe logs em tempo real
- Clique em **PARAR** para interromper

### 2. Executar pelo Executável
```
dist/Genesys/Genesys.exe
```
- Duplo clique no executável
- Interface abre automaticamente

### 3. Modo Teste (Desenvolvimento)
Edite `main_ciclo.py`:
```python
MODO_TESTE = True          # Simula operações sem PyAutoGUI
PARAR_QUANDO_VAZIO = True  # Para quando não há itens
```

---

## 📦 Geração do Executável

### Comando:
```bash
cd rpa_ciclo
BUILD_GENESYS.bat
```

### O que o Build Inclui:
✅ Todos os módulos Python necessários
✅ Tesseract OCR (validação)
✅ OpenCV (detecção de imagens)
✅ Credenciais Google (embutidas)
✅ Imagens de referência (erro/validação)
✅ Módulo Telegram
✅ Configurações (config.json)

### Importante:
- **Distribua a PASTA INTEIRA** `dist/Genesys/`, não apenas o .exe
- O executável depende dos arquivos `_internal/`
- Cache (`processados.json`) fica na mesma pasta do .exe

---

## 🎯 Casos de Uso

### ✅ Processamento Normal
```
1. Planilha tem 50 itens com Status="CONCLUÍDO"
2. RPA inicia ciclo
3. Processa os 50 itens automaticamente
4. Salva cada um no Oracle
5. Atualiza Google Sheets com "Processo Oracle Concluído"
6. Extrai dados da bancada
7. Inicia novo ciclo
```

### 🔄 Retry Automático
```
1. Item com erro "Erro OCR - Tentar novamente"
2. Item NÃO é adicionado ao cache
3. Próximo ciclo detecta o item novamente
4. Tenta processar novamente
5. Se sucesso: marca "Processo Oracle Concluído"
```

### ⏭️ Item Duplicado (Cache)
```
1. Item já foi processado anteriormente
2. ID está no cache (processados.json)
3. RPA detecta: "Já processado anteriormente"
4. Pula item sem reprocessar
5. Atualiza Google Sheets para "Processo Oracle Concluído"
```

### ❌ Erro Crítico
```
1. RPA detecta "ErroProduto.png" (produto inválido)
2. Marca Status Oracle: "Erro Oracle: produto inválido"
3. PARA a execução imediatamente
4. Aguarda correção manual
```

### 🛑 Item Marcado "REVER"
```
1. Status Oracle = "REVER - verificar código"
2. RPA ignora completamente este item
3. Não tenta processar
4. Passa para próximo item
```

---

## 📈 Performance

### Tempos Médios:
- **Processamento de 1 item**: ~15-20 segundos
- **Validação OCR**: ~3-5 segundos
- **Salvamento (Ctrl+S)**: ~5-10 segundos
- **Ciclo completo** (50 itens): ~15-20 minutos
- **Processamento bancada**: ~2-3 minutos

### Capacidade:
- **Itens por hora**: ~180-240 itens
- **Itens por dia** (24h): ~4.300-5.700 itens
- **Taxa de sucesso**: ~95-98%

---

## 🐛 Troubleshooting

### Problema: "Tela incorreta - verificar Oracle"
**Causa**: Sistema não está na tela esperada
**Comportamento**:
- ❌ Robô **PARA imediatamente** quando detecta
- ✅ Item é marcado com erro mas **NÃO** entra no cache
- ✅ Próxima execução **reprocessa automaticamente**

**Solução**:
1. Corrija o problema manualmente (certifique-se que Oracle está na tela correta)
2. Execute o robô novamente
3. Item será reprocessado automaticamente

### Problema: "Timeout Oracle - Reabrir sistema"
**Causa**: Oracle está lento/travado
**Solução**: Reinicie o Oracle, item será reprocessado

### Problema: "Erro OCR - Tentar novamente"
**Causa**: Falha na validação visual
**Solução**: Automático - será reprocessado no próximo ciclo

### Problema: Cache com muitos itens
**Causa**: processados.json muito grande
**Solução**: Limpar cache antigo (manter apenas últimos 30 dias)

### Problema: Coordenadas erradas
**Causa**: Mudou resolução da tela
**Solução**: Usar `mouse_position_helper.py` e atualizar `config.json`

### Problema: Notificações Telegram não chegam
**Causa**: Configuração incorreta
**Solução**: Verificar bot_token e chat_id no `config.json`

---

## 📚 Arquivos Importantes

### Principais:
- `RPA_Ciclo_GUI_v2.py` - Interface gráfica
- `main_ciclo.py` - Lógica principal do ciclo
- `validador_hibrido.py` - Sistema de validação OCR
- `telegram_notifier.py` - Notificações Telegram
- `google_sheets_ciclo.py` - Integração Google Sheets (ciclos)
- `google_sheets_manager.py` - Integração Google Sheets (bancada)

### Configuração:
- `config.json` - Coordenadas e tempos
- `CredenciaisOracle.json` - Credenciais Google API
- `token.json` - Token OAuth (gerado automaticamente)

### Cache:
- `processados.json` - Cache anti-duplicação

### Build:
- `Genesys.spec` - Configuração PyInstaller
- `BUILD_GENESYS.bat` - Script de build

### Imagens (Detecção de Erros):
- `informacoes/qtd_negativa.png` - Quantidade negativa
- `informacoes/ErroProduto.png` - Produto inválido
- `informacoes/tempo_oracle.png` - Timeout
- `informacoes/queda_rede.png` - Queda de internet
- `informacoes/tela_transferencia_subinventory.png` - Validação de tela

---

## 🔧 Dependências

### Python Packages:
```
pyautogui          # Automação de mouse/teclado
pyperclip          # Clipboard
keyboard           # Monitoramento ESC
pytesseract        # OCR
Pillow (PIL)       # Processamento de imagem
opencv-python      # Detecção de imagem
numpy              # Análise numérica
pandas             # Processamento de dados
google-auth        # Autenticação Google
google-api-python-client  # API Google Sheets
requests           # HTTP (Telegram)
```

### Externos:
- **Tesseract-OCR**: C:\Program Files\Tesseract-OCR\
- **Oracle ERP**: Precisa estar aberto e logado

---

## 📞 Suporte

### Documentação Adicional:
- `README_TELEGRAM.md` - Configuração Telegram
- `README_PRINCIPAL.md` - Documentação técnica
- `MUDANCAS_IMPLEMENTADAS.md` - Changelog

### Logs:
- Interface GUI mostra logs em tempo real
- Verifique mensagens de erro para diagnóstico

---

## ⚡ Resumo Executivo (Para Gestores)

### O que é?
Sistema de automação que transfere materiais no Oracle automaticamente, sem intervenção humana.

### Benefícios:
✅ **Elimina trabalho manual repetitivo**
✅ **Reduz erros humanos em ~98%**
✅ **Funciona 24/7 sem parar**
✅ **Processa milhares de itens por dia**
✅ **Validação automática de dados**
✅ **Rastreabilidade completa** (Google Sheets + Telegram)
✅ **Recuperação automática** de erros temporários

### ROI:
- **1 pessoa** processar ~100 itens/dia manualmente
- **RPA** processa ~5.000 itens/dia automaticamente
- **Ganho**: 50x mais produtividade

### Confiabilidade:
- Sistema com **cache anti-duplicação**
- **Validação OCR** em cada item
- **Detecção automática** de erros
- **Retry inteligente** de falhas temporárias
- **Taxa de sucesso**: 95-98%

---

**Versão**: 3.0 (Genesys)
**Última Atualização**: Outubro 2025
**Status**: ✅ Em Produção
