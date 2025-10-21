# 🚀 RPA CICLO - VERSÃO DE PRODUÇÃO

## ✅ STATUS: PRONTO PARA USO

O executável **RPA_Ciclo_v2.exe** foi compilado com sucesso e está pronto para **PRODUÇÃO**.

## 📦 Localização do Executável

```
rpa_ciclo/
└── dist/
    ├── RPA_Ciclo_v2.exe           ⭐ EXECUTÁVEL DE PRODUÇÃO
    └── LEIA-ME_PRODUCAO.txt       📖 Instruções rápidas
```

## ⚙️ Configurações Aplicadas

### ✅ MODO PRODUÇÃO ATIVO

| Configuração | Valor | Descrição |
|--------------|-------|-----------|
| **MODO_TESTE** | `False` | PyAutoGUI **ATIVO** (controla mouse/teclado) |
| **PARAR_QUANDO_VAZIO** | `False` | Loop contínuo, não para quando vazio |
| **Planilha Oracle** | `14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk` | **PRODUÇÃO** |
| **Planilha Bancada** | `1UgJWxmnYzv-FVTT4rrrVEx3J_MNXZsctwrPSTyyylPQ` | **PRODUÇÃO** |

### 📊 Planilhas Configuradas

#### **RPA Oracle** (Separação)
- **URL**: https://docs.google.com/spreadsheets/u/3/d/14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk/edit?gid=0#gid=0
- **ID**: `14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk`
- **Aba**: Separação
- **Usado por**: RPA_Oracle (processamento de linhas)

#### **RPA Bancada** (Extrações)
- **URL**: https://docs.google.com/spreadsheets/d/1UgJWxmnYzv-FVTT4rrrVEx3J_MNXZsctwrPSTyyylPQ/edit?gid=1419468409#gid=1419468409
- **ID**: `1UgJWxmnYzv-FVTT4rrrVEx3J_MNXZsctwrPSTyyylPQ`
- **GID**: 1419468409
- **Usado por**: RPA_Bancada (exportação de dados)

## 🎯 Diferenças: TESTE vs PRODUÇÃO

| Item | TESTE | PRODUÇÃO |
|------|-------|----------|
| **PyAutoGUI** | ❌ Desativado (simula) | ✅ **ATIVO** |
| **Controle Mouse/Teclado** | ❌ Não controla | ✅ **CONTROLA** |
| **Planilha Oracle** | 147AN4Kn... (teste) | **14yUMc12i...** (prod) |
| **Planilha Bancada** | N/A | **1UgJWxmn...** (prod) |
| **Para quando vazio** | ✅ Sim | ❌ **Loop contínuo** |
| **Arquivo .bat** | `build_gui_v2.bat` | **`build_prod.bat`** |

## 📂 Arquivos Criados

### Executáveis e Scripts
- ✅ `dist/RPA_Ciclo_v2.exe` - Executável de PRODUÇÃO
- ✅ `build_prod.bat` - Script para recompilar versão de produção
- ✅ `build_gui_v2.bat` - Script para compilar versão de teste

### Documentação
- ✅ `README_PRODUCAO.md` - Documentação completa de produção
- ✅ `README_GUI_V2.md` - Documentação do GUI
- ✅ `dist/LEIA-ME_PRODUCAO.txt` - Instruções rápidas
- ✅ `SUMARIO_PRODUCAO.md` - Este arquivo

### Código Fonte
- ✅ `main_ciclo.py` - **Módulo principal (PRODUÇÃO configurado)**
- ✅ `RPA_Ciclo_GUI_v2.py` - Interface gráfica
- ✅ `RPA_Ciclo_v2.spec` - Configuração PyInstaller

## 🚀 Como Executar

### 1. Preparação
```
1. Abra Oracle Applications
2. Navegue até: Transferência de Subinventário
3. Certifique-se de ter acesso às planilhas de produção
```

### 2. Execução
```
1. Duplo clique em: dist/RPA_Ciclo_v2.exe
2. Escolha o modo:
   - 🎯 Ciclo Único (uma execução)
   - 🔄 Modo Contínuo (loop automático)
3. Confirme que está pronto
4. Não mexa no mouse/teclado!
```

### 3. Parar
```
- Mova o mouse para o canto superior esquerdo (FAILSAFE)
- OU clique no botão "⏹️ Parar RPA"
```

## 🔧 Para Recompilar

### Versão de PRODUÇÃO
```batch
cd C:\Users\ID135\OneDrive\Desktop\www\rpas\rpa_ciclo
build_prod.bat
```

### Versão de TESTE
```batch
# 1. Edite main_ciclo.py:
#    MODO_TESTE = True
#    SPREADSHEET_ID = "147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY"

# 2. Compile:
build_gui_v2.bat
```

## 📊 Funcionalidades do GUI

### Botões Principais
- **🎯 Ciclo Único** - Executa uma vez e para
- **🔄 Modo Contínuo** - Repete automaticamente
- **⏹️ Parar RPA** - Interrompe execução

### Utilitários
- **📊 Movimentações Oracle** - Abre pasta `rpa_oracle/exportacoes/`
- **📋 Excel Bancada** - Abre pasta `rpa_bancada/out/`
- **❓ Ajuda** - Manual de uso completo

### Histórico
- **📂 Lista de Excel** - Todos os arquivos gerados (Oracle + Bancada)
- **Duplo clique** - Abre arquivo selecionado
- **🔄 Atualizar** - Recarrega lista

## ⚠️ AVISOS IMPORTANTES

### ⚠️ ANTES DE EXECUTAR
1. ✅ **Oracle Applications aberto** e acessível
2. ✅ **Resolução adequada** (recomendado: 1440x900)
3. ✅ **Google Sheets acessíveis** (credenciais válidas)
4. ✅ **Não mexer no mouse/teclado** durante execução

### ⚠️ DURANTE A EXECUÇÃO
1. ❌ **NÃO MEXA** no mouse ou teclado
2. ✅ **Acompanhe** pelo log na interface
3. ✅ **Use FAILSAFE** se precisar parar (mouse no canto)
4. ✅ **Minimize outras janelas** para evitar interferências

### ⚠️ SEGURANÇA
1. ✅ **Backup automático** - Dados salvos localmente
2. ✅ **Cache anti-duplicação** - Evita processar mesma linha 2x
3. ✅ **FAILSAFE ativo** - Mouse no canto para emergências
4. ✅ **Logs detalhados** - Rastreamento completo de ações

## 📈 Fluxo de Execução

```
1. Transferência de Subinventário (abertura)
   ↓
2. Preenchimento do campo Tipo (SUB)
   ↓
3. Seleção de Funcionário (Wallatas Moreira)
   ↓
4. Confirmação
   ↓
5. RPA_Oracle (processa linhas do Google Sheets)
   ↓
6. Navegação pós-Oracle
   ↓
7. Abertura da Bancada de Material
   ↓
8. RPA_Bancada (extrai dados e salva em Excel)
   ↓
9. Fechamento da Bancada
   ↓
10. Reinicia (apenas no modo contínuo)
```

## 🐛 Troubleshooting

### Problema: Executável não abre
**Solução**: Verifique se todos os arquivos estão na pasta dist:
- RPA_Ciclo_v2.exe
- Arquivos de imagem (Logo.png, Tecumseh.png, etc.)
- config.json
- CredenciaisOracle.json

### Problema: Google Sheets falha
**Solução**:
1. Delete `token.json`
2. Execute novamente
3. Faça login no navegador quando solicitado

### Problema: PyAutoGUI não funciona
**Solução**: Verifique se `MODO_TESTE = False` em main_ciclo.py

### Problema: Planilha errada sendo acessada
**Solução**: Verifique linha 290 de main_ciclo.py:
```python
SPREADSHEET_ID = "14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk"
```

## 📞 Informações

- **Versão**: 2.0 PRODUÇÃO
- **Data Compilação**: Outubro 2025
- **Modo**: PRODUÇÃO (PyAutoGUI ativo)
- **Build**: `build_prod.bat`
- **Desenvolvido para**: Automação completa do ciclo Oracle em produção

---

## ✅ TUDO PRONTO!

O executável **`dist/RPA_Ciclo_v2.exe`** está pronto para uso em **PRODUÇÃO** com as planilhas corretas configuradas.

**Bom trabalho! 🚀**
