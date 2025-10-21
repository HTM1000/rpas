# RPA Ciclo - GUI Modernizado v2.0

## 🎯 Visão Geral

Interface gráfica modernizada para o RPA Ciclo que integra os processos do **RPA_Oracle** e **RPA_Bancada** em um único fluxo automatizado.

## ✨ Novidades da v2.0

### 📂 Histórico de Excel Gerados
- **Visualização completa** de todos os arquivos Excel gerados
- Mostra arquivos tanto do **RPA_Oracle** (exportações) quanto do **RPA_Bancada** (out)
- **Duplo clique** em um arquivo para abrir diretamente
- Ordenados por data (mais recentes primeiro)
- Limitado aos 50 arquivos mais recentes
- Botão "🔄 Atualizar" para recarregar a lista

### 📊 Acesso Rápido às Movimentações

#### 📊 Movimentações Oracle
- Abre a pasta `rpa_oracle/exportacoes/`
- Contém todos os CSV exportados pelo RPA_Oracle
- Formato: `export_sessao_YYYYMMDD_HHMMSS.csv`

#### 📋 Excel Bancada
- Abre a pasta `rpa_bancada/out/`
- Contém todos os Excel gerados pela Bancada
- Formato: `bancada_YYYYMMDD_HHMMSS.xlsx`

#### ☁️ Google Sheets
- **Sheets Oracle**: Abre a planilha de Separação (dados processados pelo RPA_Oracle)
- **Sheets Ciclo**: Abre a planilha de histórico de execuções do ciclo

### 🎨 Interface Modernizada
- Design inspirado no GUI da Bancada
- Separadores visuais entre seções
- Cores distintas para cada botão de função
- Layout mais organizado e intuitivo
- Informações consolidadas em uma única tela

## 🚀 Como Usar

### 1. Compilar o Executável

Execute o arquivo `build_gui_v2.bat`:

```batch
build_gui_v2.bat
```

O executável será criado em: `dist/RPA_Ciclo_v2.exe`

### 2. Executar

1. **Abra o Oracle Applications**
2. **Navegue até a tela inicial** da Transferência de Subinventário
3. **Execute** `RPA_Ciclo_v2.exe`
4. **Escolha o modo**:
   - 🎯 **Ciclo Único**: Executa uma vez e para
   - 🔄 **Modo Contínuo**: Repete automaticamente

### 3. Acompanhar Execução

O log mostra todas as etapas em tempo real:
- Transferência de Subinventário
- Preenchimento do Tipo (SUB)
- Seleção de Funcionário
- Execução do RPA_Oracle
- Navegação pós-Oracle
- Execução do RPA_Bancada
- Fechamento da Bancada

### 4. Visualizar Histórico

- **Após a execução**, o histórico de Excel é atualizado automaticamente
- **Duplo clique** em um arquivo para abrir
- Use **"🔄 Atualizar"** para recarregar a lista

## 📊 Estrutura de Arquivos

```
rpa_ciclo/
├── RPA_Ciclo_GUI_v2.py       # GUI modernizado (novo)
├── RPA_Ciclo_v2.spec          # Configuração PyInstaller
├── build_gui_v2.bat           # Script de compilação
├── main_ciclo.py              # Lógica principal do ciclo
├── config.json                # Configurações de coordenadas
└── dist/
    └── RPA_Ciclo_v2.exe       # Executável gerado

rpa_oracle/
└── exportacoes/
    └── export_sessao_*.csv    # Arquivos gerados pelo Oracle

rpa_bancada/
└── out/
    └── bancada_*.xlsx         # Arquivos gerados pela Bancada
```

## 🔧 Requisitos

- Windows 10/11
- Python 3.8+ (para desenvolvimento)
- Oracle Applications aberto e acessível
- RPA_Oracle e RPA_Bancada configurados
- Google Sheets com credenciais configuradas

## ⚙️ Configurações

### config.json
Contém as coordenadas para cliques na tela:
- Transferência de Subinventário
- Campo Tipo
- Seleção de Funcionário
- Navegação pós-Oracle
- Fechamento da Bancada

### CredenciaisOracle.json
Credenciais do Google Sheets para acesso às planilhas.

## 🛡️ Segurança

- **FAILSAFE**: Mova o mouse para o canto superior esquerdo para parar
- **Botão Parar**: Interrupção manual a qualquer momento
- **Backup local**: Todos os dados são salvos localmente antes do Google Sheets

## 🐛 Troubleshooting

### Elementos não encontrados
- Verifique a **resolução da tela** (recomendado: 1440x900)
- Ajuste as coordenadas em `config.json`

### Histórico não atualiza
- Clique em **"🔄 Atualizar"**
- Verifique se as pastas existem:
  - `rpa_oracle/exportacoes/`
  - `rpa_bancada/out/`

### Google Sheets falha
- Verifique `CredenciaisOracle.json`
- Verifique `token.json` (pode precisar reautenticar)
- Dados continuam salvos localmente

### Arquivos não abrem
- Verifique se o arquivo ainda existe na pasta
- Use os botões de pasta para navegar manualmente

## 📞 Suporte

- **Versão**: 2.0
- **Data**: Outubro 2025
- **Desenvolvido para**: Automação completa do ciclo Oracle

## 🎯 Diferenças entre os Modos

### 🎯 Ciclo Único
- ✅ Executa todas as etapas uma vez
- ✅ Para automaticamente ao terminar
- ✅ Ideal para testes e execuções pontuais

### 🔄 Modo Contínuo
- ✅ Executa todas as etapas repetidamente
- ✅ Loop contínuo sem pausa entre ciclos
- ✅ Ideal para operação automática prolongada
- ⚠️ Requer parada manual

## 📈 Histórico de Versões

### v2.0 (Outubro 2025)
- ✨ Histórico de Excel gerados (Oracle + Bancada)
- ✨ Botões de acesso rápido às pastas
- ✨ Links diretos para Google Sheets
- ✨ Interface modernizada
- ✨ Layout reorganizado
- ✨ Duplo clique para abrir arquivos

### v1.0 (Anterior)
- ✅ Execução básica do ciclo
- ✅ Modos único e contínuo
- ✅ Log de execução
- ✅ Integração com Google Sheets
