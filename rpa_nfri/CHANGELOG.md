# 📝 Changelog - RPA NFRi

## Versão 3.0 - Standalone com Delays Otimizados (09/10/2025)

### ✨ Novidades:

#### 1. **Delays Aumentados (+5 segundos em todos)**
- Sandra Valentim: 2s → **7s**
- Solução Fiscal: 2s → **7s**
- NFs Recebimento: 3s → **8s**
- Campo Data: 1.5s → **6.5s**
- Inserir data anterior: 1s → **6s**
- TAB próximo campo: 1s → **6s**
- Inserir data hoje: 1s → **6s**
- TAB final: 1s → **6s**
- ENTER gerar: 8s → **13s**
- Aguardar download: 3s → **8s**
- Clicar Excel: 4s → **9s**

#### 2. **Fluxo Completo Implementado**
Agora inclui o passo inicial:
1. ✅ **Clicar em "SANDRA VALENTIM - Restrito"** (NOVO!)
2. ✅ Clicar em "Solução Fiscal"
3. ✅ Clicar em "NFs do Recebimento Integrado"
4. ✅ Preencher datas (dia anterior → hoje)
5. ✅ TAB → TAB → ENTER
6. ✅ Baixar e processar Excel

#### 3. **Filtro de Colunas A até BB**
- Exporta apenas as **54 primeiras colunas** (A até BB)
- Remove colunas desnecessárias após BB
- Otimiza envio para Google Sheets

#### 4. **Executável 100% Standalone**
- ✅ Credenciais embutidas (CredenciaisOracle.json)
- ✅ Logos embutidos (Genesys + Tecumseh)
- ✅ Não precisa de arquivos externos
- ✅ Apenas 1 arquivo: `RPA_NFRi.exe`

---

## Versão 2.0 - Interface Gráfica Melhorada (09/10/2025)

### ✨ Novidades:

#### 1. **Interface Modernizada**
- Baseada no design do `rpa_bancada`
- Dois logos lado a lado (Genesys + Tecumseh)
- Botões grandes e coloridos
- Status com cores (verde/vermelho/laranja)

#### 2. **Recursos da Interface**
- 🚀 Botão "Iniciar RPA" (verde)
- ⏹️ Botão "Parar RPA" (vermelho)
- 📂 Botão "Abrir Downloads"
- ❓ Botão "Ajuda" com janela completa
- Log com timestamps em tempo real
- ScrolledText para melhor visualização

#### 3. **Credenciais Embutidas**
- `CredenciaisOracle.json` dentro do .exe
- Mais seguro e fácil de distribuir
- Token salvo junto ao executável

---

## Versão 1.0 - Versão Inicial (08/10/2025)

### ✨ Funcionalidades:

#### 1. **Automação Básica**
- Cliques automatizados nas coordenadas
- Preenchimento de datas
- Download do Excel
- Processamento com openpyxl
- Envio para Google Sheets

#### 2. **Interface Simples**
- Botões Iniciar/Parar
- Log de execução
- Status em tempo real

#### 3. **Integração Google**
- Autenticação OAuth2
- Envio automático para Sheets
- Planilha ID configurável

---

## 📊 Resumo das Versões:

| Versão | Descrição | Data |
|--------|-----------|------|
| **3.0** | Delays +5s, Filtro A-BB, Fluxo completo | 09/10/2025 |
| **2.0** | Interface moderna, Standalone | 09/10/2025 |
| **1.0** | Versão inicial | 08/10/2025 |

---

## 🚀 Próximas Melhorias (Sugestões):

- [ ] Configuração de coordenadas via interface
- [ ] Seleção de período de datas customizado
- [ ] Múltiplas planilhas destino
- [ ] Agendamento automático
- [ ] Notificações por email

---

**Desenvolvido para Tecumseh - Automação NFRi**
