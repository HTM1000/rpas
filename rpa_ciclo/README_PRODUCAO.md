# RPA Ciclo - Versão de PRODUÇÃO

## ⚠️ IMPORTANTE - MODO PRODUÇÃO ATIVO

Este executável está configurado para **MODO PRODUÇÃO**:
- ✅ **PyAutoGUI ATIVO** - Controla mouse e teclado
- ✅ **Planilha Oracle PRODUÇÃO**: `14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk`
- ✅ **Planilha Bancada PRODUÇÃO**: `1UgJWxmnYzv-FVTT4rrrVEx3J_MNXZsctwrPSTyyylPQ`
- ✅ **Modo contínuo** - Não para quando vazio

## 📊 Planilhas de Produção

### RPA Oracle
- **URL**: https://docs.google.com/spreadsheets/u/3/d/14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk/edit?gid=0#gid=0
- **ID**: `14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk`
- **Aba**: Separação

### RPA Bancada
- **URL**: https://docs.google.com/spreadsheets/d/1UgJWxmnYzv-FVTT4rrrVEx3J_MNXZsctwrPSTyyylPQ/edit?gid=1419468409#gid=1419468409
- **ID**: `1UgJWxmnYzv-FVTT4rrrVEx3J_MNXZsctwrPSTyyylPQ`
- **GID**: 1419468409

## 🚀 Como Compilar

Execute o arquivo `build_prod.bat`:

```batch
build_prod.bat
```

O script irá:
1. Limpar builds anteriores
2. Verificar se MODO_TESTE = False
3. Verificar se a planilha de produção está configurada
4. Compilar com PyInstaller
5. Verificar se o executável foi criado

## ⚙️ Configurações de Produção

### main_ciclo.py (linha 44)
```python
MODO_TESTE = False  # PRODUÇÃO - PyAutoGUI ATIVO
PARAR_QUANDO_VAZIO = False  # Continua rodando
```

### main_ciclo.py (linha 290)
```python
SPREADSHEET_ID = "14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk"  # PRODUÇÃO
```

## 🔄 Diferenças TESTE vs PRODUÇÃO

| Configuração | TESTE | PRODUÇÃO |
|--------------|-------|----------|
| MODO_TESTE | `True` | `False` |
| PyAutoGUI | Desativado (simula) | **ATIVO** |
| PARAR_QUANDO_VAZIO | `True` | `False` |
| Planilha Oracle | 147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY | **14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk** |
| Controle de Mouse | ❌ Não controla | ✅ **Controla** |
| Loop Contínuo | Para quando vazio | Continua rodando |

## 📋 Checklist Pré-Execução

Antes de executar em PRODUÇÃO, certifique-se de:

- [ ] Oracle Applications está aberto e acessível
- [ ] Você está na tela inicial correta
- [ ] Resolução da tela está adequada (recomendado: 1440x900)
- [ ] Google Sheets de produção está configurado e acessível
- [ ] Credenciais OAuth estão atualizadas (CredenciaisOracle.json)
- [ ] Token OAuth está válido ou será regenerado
- [ ] Pastas de exportação existem:
  - `rpa_oracle/exportacoes/`
  - `rpa_bancada/out/`

## 🛡️ Segurança

- **FAILSAFE**: Mova o mouse para o canto superior esquerdo para parar
- **Botão Parar**: Use o botão "⏹️ Parar RPA" na interface
- **Backup Local**: Todos os dados são salvos localmente antes do Google Sheets
- **Cache Anti-Duplicação**: Evita processar a mesma linha duas vezes

## 📂 Estrutura de Arquivos

```
rpa_ciclo/
├── main_ciclo.py              # Módulo principal (PRODUÇÃO)
├── RPA_Ciclo_GUI_v2.py        # Interface gráfica
├── RPA_Ciclo_v2.spec          # Config PyInstaller
├── build_prod.bat             # Build PRODUÇÃO ⭐
├── config.json                # Coordenadas da tela
├── CredenciaisOracle.json     # OAuth credentials
└── dist/
    └── RPA_Ciclo_v2.exe       # Executável PRODUÇÃO

rpa_oracle/
├── exportacoes/               # CSV gerados pelo Oracle
└── processados.json           # Cache anti-duplicação

rpa_bancada/
└── out/                       # Excel gerados pela Bancada
```

## 🐛 Troubleshooting

### Executável não foi criado
- Verifique se `MODO_TESTE = False` em main_ciclo.py
- Verifique se PyInstaller está instalado: `python -m pip install pyinstaller`
- Verifique os erros no console

### Planilha errada sendo acessada
- Verifique a linha 290 de main_ciclo.py
- Deve conter: `14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk`

### PyAutoGUI não está funcionando
- Verifique se `MODO_TESTE = False`
- Teste a posição do mouse: `import pyautogui; print(pyautogui.position())`

### Google Sheets falha na autenticação
- Delete `token.json` e execute novamente
- Será solicitada nova autenticação no navegador
- Verifique se `CredenciaisOracle.json` está presente

## 📞 Informações

- **Versão**: 2.0 PRODUÇÃO
- **Data**: Outubro 2025
- **Modo**: PRODUÇÃO (PyAutoGUI ativo)
- **Desenvolvido para**: Automação completa do ciclo Oracle em produção

## ⚠️ AVISOS IMPORTANTES

1. **NÃO MEXA NO MOUSE/TECLADO** enquanto o RPA estiver em execução
2. Certifique-se de que a **resolução da tela** está correta
3. Mantenha o **Oracle Applications aberto** e acessível
4. O RPA irá **controlar mouse e teclado** automaticamente
5. Use **FAILSAFE** (mouse no canto) ou botão **Parar** para interromper

## 🔄 Para voltar ao modo TESTE

Edite `main_ciclo.py`:

```python
# Linha 44
MODO_TESTE = True  # TESTE
PARAR_QUANDO_VAZIO = True  # Para quando vazio

# Linha 290
SPREADSHEET_ID = "147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY"  # TESTE
```

Depois recompile com `build_gui_v2.bat` (teste) ou `build_prod.bat` (produção).
