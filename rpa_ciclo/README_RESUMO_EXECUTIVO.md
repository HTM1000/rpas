# 🤖 RPA Ciclo Genesys - Resumo Executivo

## 🎯 O que o Sistema Faz?

### Processo Automático:

1. **Lê dados do Google Sheets** (planilha com itens pendentes)
2. **Acessa o Oracle automaticamente** (navega até tela de Transferência de Subinventário)
3. **Preenche todos os campos** (Item, Origem, Destino, Quantidade, Referência)
4. **Valida os dados inseridos** (usa OCR para confirmar que digitou corretamente)
5. **Salva no Oracle** (Ctrl+S)
6. **Atualiza status no Google Sheets** (marca como "Processo Oracle Concluído")
7. **Processa bancada de materiais** (extrai dados e atualiza planilha de controle)
8. **Inicia novo ciclo** (repete o processo continuamente)

### Funcionamento Contínuo:
- Executa **ciclos ininterruptos**
- Quando não há itens: aguarda 30 segundos e verifica novamente
- **Nunca para sozinho** (exceto em casos de erro crítico)

---

## 📊 Capacidade e Performance

### Números:
- **~40-50 segundos** por item processado
- **~90 itens por hora**
- **Taxa de sucesso: 95-98%**

### Benefícios:
- ✅ **Elimina trabalho manual repetitivo**
- ✅ **Reduz erros humanos** (validação automática)
- ✅ **Rastreabilidade completa** (tudo registrado no Google Sheets)
- ✅ **Recuperação automática** de erros temporários

---

## 🔍 Como o Sistema Identifica Itens para Processar

### Busca na Planilha Google Sheets:
O sistema processa itens que atendem **simultaneamente**:
1. **Status = "CONCLUÍDO"** (coluna Status)
2. **Status Oracle = vazio** (coluna Status Oracle)

### Exemplo:
```
| Status     | Status Oracle | Ação do RPA           |
|------------|---------------|-----------------------|
| CONCLUÍDO  | (vazio)       | ✅ PROCESSA           |
| CONCLUÍDO  | Concluído     | ⏭️ IGNORA (já feito) |
| PENDENTE   | (vazio)       | ⏭️ IGNORA (não liberado) |
```

---

## ⚙️ Tratamento de Erros e Status Oracle

### 🟢 Status de Sucesso:

| Status Oracle | Significado | Ação do RPA |
|---------------|-------------|-------------|
| **Processo Oracle Concluído** | Item processado e salvo com sucesso | ⏭️ Ignora (não reprocessa) |

---

### 🟡 Status de Retry Automático (Continua Processando Outros Itens):

Estes erros **não param o robô**. O item é marcado com erro, o robô **continua processando os próximos itens**, e o item com erro será **automaticamente reprocessado no próximo ciclo**:

| Status Oracle | Causa | Comportamento |
|---------------|-------|---------------|
| **Erro OCR - Tentar novamente** | Validação visual falhou | ✅ Continua → Retry próximo ciclo |
| **Campo vazio encontrado** | Oracle deixou campo em branco | ✅ Continua → Retry próximo ciclo |
| **Dados não conferem** | OCR detectou divergência | ✅ Continua → Retry próximo ciclo |
| **Erro validação: valor divergente** | Valor digitado diferente do esperado | ✅ Continua → Retry próximo ciclo |
| **Não concluído no Oracle** | Salvamento não foi confirmado | ✅ Continua → Retry próximo ciclo |
| **Timeout salvamento** | Ctrl+S demorou muito (>120s) | ✅ Continua → Retry próximo ciclo |
| **Sistema travado no Ctrl+S** | Oracle não respondeu ao salvar | ✅ Continua → Retry próximo ciclo |
| **Erro Oracle: dados faltantes por item não cadastrado** | Item não existe no cadastro | ✅ Continua → Retry próximo ciclo |

**Resumo**: Item fica marcado para retry → Robô continua processando outros itens → Próximo ciclo tenta novamente

---

### 🔴 Status de Retry com Parada (Para Robô, Aguarda Correção):

Estes erros **param o robô imediatamente** para correção manual. Após correção, o item será **automaticamente reprocessado** na próxima execução:

| Status Oracle | Causa | Comportamento |
|---------------|-------|---------------|
| **Tela incorreta - verificar Oracle** | Sistema não está na tela esperada | 🛑 **PARA robô** → Usuário corrige → Retry próxima execução |
| **Timeout Oracle - Reabrir sistema** | Oracle muito lento/travado | 🛑 **PARA robô** → Usuário reabre Oracle → Retry próxima execução |

**Fluxo**:
1. Detecta erro (tela incorreta ou timeout Oracle)
2. Marca item com erro (não adiciona ao cache)
3. **PARA robô imediatamente**
4. Usuário corrige problema manualmente (tela correta ou reinicia Oracle)
5. Próxima execução: item é reprocessado automaticamente

---

### 🔴 Status de Erro Crítico (Para Robô, SEM Retry):

Estes erros **param o robô** e **NÃO permitem retry automático** (requerem intervenção manual):

| Status Oracle | Causa | Comportamento |
|---------------|-------|---------------|
| **Erro Oracle: produto inválido** | Código do produto não existe no Oracle | 🛑 **PARA robô** → Marca como "PD" → SEM retry |

**Fluxo**:
1. Detecta produto inválido
2. Marca item como "PD" (Produto Desconhecido)
3. Adiciona ao cache (não será reprocessado)
4. **PARA robô completamente**
5. Requer correção manual do código do produto

---

### ⚪ Status Ignorados (Não Processa):

| Status Oracle | Significado | Ação do RPA |
|---------------|-------------|-------------|
| **REVER** (ou contém "REVER") | Item marcado para revisão manual | ⏭️ Ignora completamente |
| **PROCESSANDO...** (com item no cache) | Já foi processado anteriormente | ⏭️ Ignora, atualiza para "Concluído" |

---

### 📋 Filtros Adicionais:

O sistema **NÃO processa** automaticamente:
- ❌ Linhas com **Quantidade = 0**
- ❌ Linhas com **"REVER"** no Status Oracle (qualquer variação)
- ❌ Linhas que já estão no **cache** (duplicação)

---

## 🔄 Resumo Visual do Comportamento

```
┌─────────────────────────────────────────────────────────┐
│  SUCESSO                                                │
│  "Processo Oracle Concluído"                            │
└─────────────────────────────────────────────────────────┘
         ✅ Item concluído
         ⏭️ Não reprocessa


┌─────────────────────────────────────────────────────────┐
│  ERRO COM RETRY AUTOMÁTICO                              │
│  "Erro OCR", "Campo vazio", "Timeout", etc.             │
└─────────────────────────────────────────────────────────┘
         ⚠️ Marca erro
         ✅ Continua processando próximos itens
         🔄 Retry no próximo ciclo


┌─────────────────────────────────────────────────────────┐
│  ERRO COM PARADA (Requer Correção Manual)               │
│  "Tela incorreta" ou "Timeout Oracle"                   │
└─────────────────────────────────────────────────────────┘
         ⚠️ Marca erro
         🛑 PARA robô
         👤 Usuário corrige manualmente
         🔄 Retry na próxima execução


┌─────────────────────────────────────────────────────────┐
│  ERRO CRÍTICO (SEM Retry)                               │
│  "Erro Oracle: produto inválido"                        │
└─────────────────────────────────────────────────────────┘
         ❌ Marca como "PD"
         🛑 PARA robô
         🚫 NÃO reprocessa (entra no cache)
         👤 Requer correção manual


┌─────────────────────────────────────────────────────────┐
│  IGNORADOS                                               │
│  "REVER", Quantidade=0, Já no cache                      │
└─────────────────────────────────────────────────────────┘
         ⏭️ Pula item
         ✅ Continua processando próximos
```

---

## 🔐 Segurança e Confiabilidade

### Cache Anti-Duplicação:
- Sistema mantém **cache local** (`processados.json`)
- **Nunca processa o mesmo item duas vezes**
- Cache persiste mesmo após crash/reinício
- Proteção contra duplicação no Oracle

### Validação Automática:
- **OCR (Tesseract)**: Lê campos preenchidos e compara com valores esperados
- **Detecção Visual**: Identifica erros através de imagens (produto inválido, quantidade negativa)
- **Validação Híbrida**: Combina OCR + análise de pixels para máxima precisão

### Rastreabilidade:
- **Tudo registrado no Google Sheets** (hora, status, erros)
- **Histórico completo** de cada processamento
- **Auditoria** de todos os ciclos executados

---

## 🛡️ Failsafe e Controles

### Parada de Emergência:
- **Pressione ESC** → Para execução imediatamente
- **Mouse no canto (0,0)** → Acionamento automático do failsafe
- **Botão PARAR na interface** → Interrompe processo com segurança

### Detecção Automática de Problemas:
- 🌐 **Queda de Internet**: Detecta e para processamento
- ⏱️ **Timeout do Oracle**: Detecta lentidão e marca para retry
- 🖼️ **Tela Incorreta**: Para execução para correção manual
- 🔴 **Produto Inválido**: Para execução (erro crítico)

---
## 🔧 Configuração Técnica

### Requisitos:
- **Oracle ERP** (aberto e logado)
- **Google Sheets** (com planilha estruturada)
- **Tesseract OCR** (validação automática)
- **Python 3.x** (execução)

### Integração:
- **Planilha Google Sheets**: Fonte de dados + Registro de status
- **Oracle ERP**: Sistema destino (transferências)
- **Cache Local**: Arquivo JSON para controle anti-duplicação

---

**Versão**: 3.0 (Genesys)
**Status**: ✅ Em Produção
**Última Atualização**: 25 de Outubro de 2025
