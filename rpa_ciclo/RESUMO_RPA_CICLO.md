# RPA Ciclo Genesys

**Sistema de Automação de Transferências Oracle**

---

## Funcionalidades

### O que o sistema faz:

1. **Lê dados da planilha Google Sheets** (itens com Status = "CONCLUÍDO" e Status Oracle vazio)
2. **Acessa o Oracle automaticamente** (navega até tela de Transferência de Subinventário)
3. **Preenche campos** (Item, Sub. Origem, End. Origem, Sub. Destino, End. Destino, Quantidade, Referência)
4. **Valida dados inseridos** (OCR para confirmar digitação correta)
5. **Salva no Oracle** (Ctrl+S)
6. **Atualiza Google Sheets** com status do processamento
7. **Processa bancada de materiais** (extrai e atualiza dados)
8. **Executa continuamente** (ciclos ininterruptos 24/7)

### Capacidade:
- **40-50 segundos** por item
- **~90 itens por hora**
- **Taxa de sucesso: 95-98%**

---

## Tratamento de Erros

### 🟢 Sucesso
**Status**: "Processo Oracle Concluído"
**Ação**: Item concluído, não reprocessa

---

### 🟡 Erros com Retry Automático (Robô Continua)

O robô marca o erro, **continua processando outros itens** e **reprocessa automaticamente no próximo ciclo**:

- Erro OCR - Tentar novamente
- Campo vazio encontrado
- Dados não conferem
- Erro validação: valor divergente
- Não concluído no Oracle
- Timeout salvamento
- Sistema travado no Ctrl+S
- Erro Oracle: dados faltantes por item não cadastrado

---

### 🔴 Erros com Parada (Robô Para, Permite Retry)

O robô marca o erro, **para imediatamente** e aguarda correção manual. **Reprocessa automaticamente** após correção:

**Tela incorreta - verificar Oracle**
- Causa: Sistema não está na tela esperada
- Ação: Usuário corrige tela manualmente → Próxima execução reprocessa

**Timeout Oracle - Reabrir sistema**
- Causa: Oracle muito lento/travado
- Ação: Usuário reabre Oracle → Próxima execução reprocessa

---

### 🔴 Erro Crítico (Robô Para, SEM Retry)

O robô marca o erro, **para imediatamente** e **NÃO reprocessa automaticamente**:

**Erro Oracle: produto inválido**
- Causa: Código do produto não existe no Oracle
- Ação: Marca como "PD" (Produto Desconhecido) → Requer correção manual do código

---

### ⚪ Itens Ignorados

O robô **ignora completamente** (não processa):

- Status Oracle contém **"REVER"**
- **Quantidade = 0**
- Item já está no **cache** (já processado anteriormente)

---

## Segurança

### Cache Anti-Duplicação
- Arquivo local `processados.json`
- **Nunca processa o mesmo item duas vezes**
- Persiste entre execuções (mesmo após crash/reinício)

### Validação
- **OCR (Tesseract)**: Lê campos e compara com valores esperados
- **Detecção Visual**: Identifica erros por imagem
- **Validação Híbrida**: OCR + análise de pixels

### Rastreabilidade
- Tudo registrado no Google Sheets
- Histórico completo de processamentos
- Auditoria de ciclos executados

---

## Configuração

**Requisitos:**
- Oracle ERP (aberto e logado)
- Google Sheets (planilha estruturada)
- Tesseract OCR
- Python 3.x

**Integração:**
- Google Sheets: Fonte de dados + Registro de status
- Oracle ERP: Sistema destino
- Cache Local: Controle anti-duplicação

---

**Versão**: 3.0 (Genesys)
**Status**: Em Produção
**Data**: 25 de Outubro de 2025
