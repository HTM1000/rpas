# Manual de Uso - RPA Ciclo Automação (Executável)

## Índice
1. [Introdução](#introdução)
2. [Como Gerar o Executável](#como-gerar-o-executável)
3. [Primeiro Uso](#primeiro-uso)
4. [Como Usar](#como-usar)
5. [Modos de Execução](#modos-de-execução)
6. [Google Sheets](#google-sheets)
7. [Troubleshooting](#troubleshooting)

---

## Introdução

O **RPA Ciclo Automação** é um sistema standalone (executável único) que automatiza todo o ciclo de processos no Oracle, incluindo:

- ✅ Transferência de Subinventário
- ✅ Preenchimento automático de campos
- ✅ Seleção de funcionários
- ✅ Execução do RPA_Oracle
- ✅ Execução do RPA_Bancada
- ✅ Registro de logs no Google Sheets

**Vantagens do executável:**
- ✅ Não precisa instalar Python
- ✅ Não precisa instalar dependências
- ✅ Arquivo único e portável
- ✅ Todas as imagens e recursos incluídos

---

## Como Gerar o Executável

### Pré-requisitos
- Python 3.8 ou superior instalado
- Todas as dependências do projeto

### Passos para Build

1. **Navegue até a pasta do projeto:**
   ```bash
   cd C:\Users\ID135\OneDrive\Desktop\www\rpas\rpa_ciclo
   ```

2. **Execute o script de build:**
   ```bash
   build.bat
   ```

3. **Aguarde o processo:**
   - O script irá:
     - Verificar Python
     - Instalar PyInstaller (se necessário)
     - Instalar dependências
     - Limpar builds anteriores
     - Gerar o executável
     - Copiar arquivos necessários

4. **Verifique o resultado:**
   - O executável estará em: `dist\RPA_Ciclo.exe`
   - Todos os arquivos necessários estarão em `dist\`

### Distribuição

Para distribuir o executável:

1. Copie **toda a pasta `dist`** para outro computador
2. Certifique-se de que os seguintes arquivos estão presentes:
   - `RPA_Ciclo.exe` (executável principal)
   - `CredenciaisOracle.json` (credenciais Google)
   - Todos os arquivos da pasta `informacoes\` (se aplicável)

---

## Primeiro Uso

### 1. Preparação

Antes de executar pela primeira vez:

1. **Abra a pasta onde está o executável**
2. **Verifique se existe o arquivo `CredenciaisOracle.json`**
   - Este arquivo contém as credenciais do Google OAuth
   - É necessário para fazer login no Google Sheets

### 2. Primeira Execução

1. **Execute `RPA_Ciclo.exe`** (duplo clique)

2. **Login no Google:**
   - Na primeira vez, uma janela do navegador será aberta
   - Faça login com sua conta Google autorizada
   - Autorize o acesso aos Google Sheets
   - Após autorização, um arquivo `token.json` será criado

3. **Interface Carregada:**
   - A interface gráfica será exibida
   - Status: "Aguardando"
   - Logos da Genesys e Tecumseh visíveis

### 3. Arquivos Gerados

Após a primeira execução:
- `token.json` - Token de autenticação (válido por tempo limitado)
- `rpa_ciclo.log` - Arquivo de log local

---

## Como Usar

### Interface Gráfica

A interface possui 3 botões principais:

1. **🎯 Ciclo Único**
   - Executa o ciclo uma vez
   - Para automaticamente ao terminar
   - Ideal para testes

2. **🔄 Modo Contínuo**
   - Executa repetidamente
   - Aguarda 30 minutos entre ciclos
   - Ideal para operação automática
   - Requer parada manual

3. **⏹️ Parar RPA**
   - Para a execução em andamento
   - Disponível apenas quando RPA está rodando

### Botões Utilitários

- **📂 Abrir Logs** - Abre a pasta com o arquivo de log
- **☁️ Google Sheets** - Abre a planilha no navegador
- **❓ Ajuda** - Exibe ajuda detalhada

### Execução Passo a Passo

1. **Prepare o Oracle:**
   - Abra o Oracle Applications
   - Navegue até a tela inicial correta
   - Certifique-se de que a resolução está adequada

2. **Escolha o modo:**
   - Clique em "🎯 Ciclo Único" OU "🔄 Modo Contínuo"

3. **Confirme:**
   - Uma mensagem de confirmação será exibida
   - Verifique as pré-condições
   - Clique em "Sim" para iniciar

4. **Interface Minimiza:**
   - A janela será minimizada automaticamente
   - O RPA começará a executar

5. **Acompanhe pelos Logs:**
   - Os logs aparecerão em tempo real
   - Cada etapa é registrada

6. **Finalização:**
   - A interface será restaurada
   - Uma mensagem de conclusão será exibida
   - Verifique os resultados no Google Sheets

---

## Modos de Execução

### Modo Ciclo Único

**Quando usar:**
- Testes de funcionamento
- Execuções esporádicas
- Validação de coordenadas
- Primeiro uso

**Como funciona:**
1. Executa todas as 8 etapas
2. Registra no Google Sheets
3. Para automaticamente
4. Exibe mensagem de conclusão

**Duração aproximada:**
- 10-20 minutos (depende dos RPAs)

### Modo Contínuo

**Quando usar:**
- Operação automática diária
- Monitoramento contínuo
- Produção

**Como funciona:**
1. Executa todas as 8 etapas
2. Registra no Google Sheets
3. Aguarda 30 minutos
4. Repete automaticamente
5. Continua até ser parado manualmente

**Atenção:**
- Deixe o computador ligado
- Não feche o executável
- Não mova janelas durante execução
- Pressione "Parar" para interromper

---

## Google Sheets

### Configuração Automática

Na primeira execução, o RPA irá:
1. Autenticar com Google OAuth
2. Verificar se a aba "Ciclo Automacao" existe
3. Se não existir, criar automaticamente
4. Adicionar cabeçalhos das colunas

### Dados Registrados

Cada ciclo registra:

| Coluna | Descrição |
|--------|-----------|
| Data/Hora Início | Quando o ciclo começou |
| Data/Hora Fim | Quando o ciclo terminou |
| Ciclo # | Número sequencial do ciclo |
| Status | Sucesso, Falha, Pausado, Erro |
| Etapa Falha | Nome da etapa que falhou (se houver) |
| Tempo Execução (min) | Duração total em minutos |
| Observações | Mensagens adicionais |
| Operador | Nome do operador (padrão: "Sistema") |
| RPA Oracle | Status do RPA Oracle (Sucesso/Falha/Pendente) |
| RPA Bancada | Status do RPA Bancada (Sucesso/Falha/Pendente) |

### Acessar o Google Sheets

**Pelo executável:**
- Clique no botão "☁️ Google Sheets"

**Diretamente:**
- Acesse: https://docs.google.com/spreadsheets/d/14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk/edit
- Vá para a aba "Ciclo Automacao"

### Análise de Dados

No Google Sheets, você pode:
- ✅ Filtrar ciclos por status
- ✅ Ordenar por data
- ✅ Calcular tempo médio de execução
- ✅ Identificar etapas com mais falhas
- ✅ Gerar gráficos de desempenho

---

## Troubleshooting

### Executável não abre

**Problema:** Duplo clique no .exe não faz nada

**Soluções:**
1. Verifique o antivírus (pode estar bloqueando)
2. Execute como Administrador (botão direito > Executar como administrador)
3. Verifique se há arquivos faltando na pasta dist
4. Tente executar via CMD para ver erros:
   ```
   cd dist
   RPA_Ciclo.exe
   ```

### Erro de Login no Google

**Problema:** "Erro ao autenticar com Google"

**Soluções:**
1. Verifique se `CredenciaisOracle.json` existe
2. Delete o arquivo `token.json` e tente novamente
3. Certifique-se de que sua conta tem permissão
4. Verifique a conexão com internet

### Erro "Elemento não encontrado"

**Problema:** "❌ Falha na etapa: Transferência Subinventário"

**Soluções:**
1. Verifique a resolução da tela
2. Certifique-se de que o Oracle está aberto
3. Verifique se está na tela correta
4. Ajuste as coordenadas em `config.json`
5. Use `mouse_position_helper.py` para encontrar novas coordenadas

### RPA_Oracle/Bancada não executa

**Problema:** "❌ RPA_Oracle não encontrado"

**Soluções:**
1. Verifique se os executáveis existem:
   - `../rpa_oracle/dist/RPA_Oracle.exe`
   - `../rpa_bancada/dist/RPA_Bancada.exe`
2. Ou certifique-se de que os scripts Python existem:
   - `../rpa_oracle/RPA_Oracle.py`
   - `../rpa_bancada/main.py`
3. Verifique os caminhos em `config.json`

### Google Sheets não registra

**Problema:** Ciclo executa mas não aparece no Sheets

**Soluções:**
1. Verifique se está logado corretamente
2. Abra o Sheets manualmente e verifique permissões
3. Verifique o arquivo de log para erros específicos
4. Tente deletar `token.json` e fazer login novamente

### Coordenadas erradas

**Problema:** RPA clica no lugar errado

**Soluções:**
1. Verifique a resolução da tela (deve estar consistente)
2. Certifique-se de que janelas não foram movidas/redimensionadas
3. Use `mouse_position_helper.py` para recalibrar:
   ```bash
   python mouse_position_helper.py
   ```
4. Atualize as coordenadas em `config.json`
5. Teste com "Ciclo Único" antes de usar "Modo Contínuo"

### Executável está lento

**Problema:** RPA demora muito para iniciar/executar

**Soluções:**
1. Feche outros programas pesados
2. Verifique se o antivírus não está escaneando em tempo real
3. Aumente os tempos de espera em `config.json`
4. Verifique recursos do sistema (RAM, CPU)

### Modo Contínuo não repete

**Problema:** Após primeiro ciclo, não aguarda 30 min

**Soluções:**
1. Verifique se não pressionou "Parar"
2. Verifique o arquivo de log para erros
3. Certifique-se de que o computador não está entrando em modo de hibernação
4. Verifique o campo `ciclo_completo` em `config.json` (deve ser 1800)

---

## Logs e Diagnóstico

### Arquivo de Log

- **Localização:** Mesma pasta do executável
- **Nome:** `rpa_ciclo.log`
- **Formato:** Texto puro

**Como visualizar:**
1. Clique em "📂 Abrir Logs" no executável
2. Ou navegue até a pasta e abra `rpa_ciclo.log`

### Informações no Log

O log contém:
- ✅ Timestamp de cada ação
- ✅ Etapas executadas
- ✅ Erros e exceções
- ✅ Status de cada ciclo
- ✅ Mensagens de debug

**Exemplo de log bem-sucedido:**
```
10:30:15 - 🤖 RPA Ciclo Automação carregado
10:30:15 - ✅ Sistema pronto para iniciar
10:32:00 - ▶️ Iniciando RPA em modo execução única...
10:32:01 - ✅ Configurações carregadas
10:32:02 - 🔄 CICLO #1 - 2025-10-09 10:32:02
10:32:03 - 📋 ETAPA 1: Transferência de Subinventário
10:32:04 - 🖱️ Clique na opção Transferência de Subinventário
...
10:50:00 - ✅ CICLO #1 CONCLUÍDO COM SUCESSO!
```

---

## Boas Práticas

### Antes de Executar
- ✅ Feche programas desnecessários
- ✅ Verifique resolução da tela
- ✅ Certifique-se de que Oracle está aberto
- ✅ Desative proteção de tela
- ✅ Desative hibernação (para modo contínuo)

### Durante a Execução
- ❌ NÃO mova o mouse (se possível)
- ❌ NÃO mova/redimensione janelas
- ❌ NÃO feche o Oracle
- ✅ Deixe o RPA trabalhar sozinho
- ✅ Acompanhe pelos logs se necessário

### Após a Execução
- ✅ Verifique o Google Sheets
- ✅ Confira se os dados estão corretos
- ✅ Revise o arquivo de log para erros
- ✅ Faça backup do token.json

### Manutenção
- 🔄 Atualize coordenadas se mudar resolução
- 🔄 Renove o token se expirar (delete token.json)
- 🔄 Faça backup de config.json
- 🔄 Mantenha CredenciaisOracle.json seguro

---

## Contato e Suporte

Para problemas ou dúvidas:
1. Consulte este manual
2. Verifique o arquivo de log
3. Clique em "❓ Ajuda" no executável
4. Entre em contato com a equipe de TI

---

**Versão:** 2.0
**Data:** Outubro 2025
**Desenvolvido para:** Automação Oracle - Ciclo Completo
