# RPA_Ciclo - Versão Standalone

## ✅ O que mudou?

O **RPA_Ciclo** agora é **100% independente** e não precisa de nenhum outro módulo externo para funcionar!

### ❌ **ANTES** (com dependências):
```
rpas/
├── rpa_ciclo/          ← Precisava dos outros
│   └── main_ciclo.py
├── rpa_bancada/        ← Dependência externa
│   └── main_v2.py
└── rpa_oracle/         ← Dependência externa
    └── RPA_Oracle.py
```

### ✅ **AGORA** (standalone):
```
rpa_ciclo/              ← Funciona sozinho!
├── main_ciclo.py       ← Tudo aqui dentro
├── config.json         ← Todas as coordenadas
└── RPA_Ciclo.exe       ← .exe funciona em qualquer máquina
```

---

## 🎯 O que o RPA_Ciclo faz?

### **Fluxo Completo:**

1. ✅ **Transferência Subinventário** - Abre modal
2. ✅ **Preencher Tipo** - Digita "SUB"
3. ✅ **Selecionar Funcionário** - Wallatas Moreira (9 setas + Enter)
4. ✅ **RPA Oracle** - Processa linhas do Google Sheets
   - Busca linhas com Status = "CONCLUÍDO" e Status Oracle vazio
   - Preenche no Oracle: Item, Sub, End, Quantidade, Referência
   - Valida regras (quantidade zero, transações proibidas)
   - Salva com Ctrl+S
   - Atualiza Google Sheets
5. ✅ **Navegação** - Vai para Bancada de Material
6. ✅ **Bancada** (extração de dados - standalone!)
   - Clica em "Detalhado"
   - Clica em "Localizar"
   - Aguarda processamento (180s)
   - Copia todas as linhas (Shift+F10 → Copiar)
   - Verifica se dados foram copiados
7. ✅ **Fechar Bancada** - Fecha a janela

---

## 🔧 Configuração (config.json)

Todas as coordenadas estão no `config.json`:

```json
{
  "coordenadas": {
    "tela_01_transferencia_subinventario": { "x": 593, "y": 234 },
    "tela_02_campo_tipo": { "x": 155, "y": 217 },
    "tela_03_pastinha_funcionario": { "x": 32, "y": 120 },
    "tela_06_janela_navegador": { "x": 340, "y": 40 },
    "tela_06_navegador": { "x": 385, "y": 135 },
    "tela_07_bancada_material": { "x": 568, "y": 294 },
    "tela_08_fechar_bancada": { "x": 754, "y": 97 },

    "bancada_detalhado": { "x": 273, "y": 358 },
    "bancada_localizar": { "x": 524, "y": 689 },
    "bancada_celula_org": { "x": 318, "y": 174 }
  },
  "tempos_espera": {
    "entre_cliques": 3,
    "apos_modal": 5.0,
    "apos_rpa_oracle": 4.0,
    "apos_rpa_bancada": 4.0
  }
}
```

**✏️ Para ajustar coordenadas:**
1. Use uma ferramenta como **Mouse Position Tracker**
2. Anote as coordenadas X e Y
3. Edite o `config.json`

---

## 📦 Dependências Necessárias

### **Para rodar o .py:**
```bash
pip install pyautogui google-auth google-auth-oauthlib google-api-python-client pyperclip
```

### **Para gerar o .exe:**
```bash
pip install pyinstaller
```

---

## 🏗️ Como gerar o executável

### **1. Usando o batch (recomendado):**
```bash
build_prod.bat
```

### **2. Manual (PyInstaller):**
```bash
pyinstaller --clean RPA_Ciclo_v2.spec
```

O executável será gerado em: `dist/RPA_Ciclo.exe`

---

## ▶️ Como executar

### **Modo Python:**
```bash
python main_ciclo.py
```

### **Modo Executável:**
```bash
dist\RPA_Ciclo.exe
```

### **Com GUI:**
```bash
python RPA_Ciclo_GUI_v2.py
```

---

## 🔍 Logs e Monitoramento

Durante a execução, você verá logs detalhados:

```
🔄 CICLO #1 - 2025-10-18 14:30:00
============================================================
📋 ETAPA 1: Transferência Subinventário
🖱️ Duplo clique na opção Transferência de Subinventário
⏳ Aguardando abertura do modal (5s)...

📋 ETAPA 2: Preenchimento Tipo
🖱️ Clique no campo Tipo
⌨️ Digitando: SUB
...

📋 ETAPA 5: Processamento no Oracle
📋 5 linhas encontradas para processar
▶ Linha 2: ITEM001 | Qtd=10 | Ref=MOV123
✅ Linha 2 processada e salva no Oracle
...

🤖 ETAPA 7: Extração de dados da Bancada
✅ pyperclip disponível para copiar dados
🖱️ Clique no botão Detalhado da Bancada
🖱️ Clique no botão Localizar da Bancada
⏳ Aguardando processamento do Localizar (180 segundos)...
👀 Verificando dados copiados...
✅ Dados copiados com sucesso!
📊 150 linhas, 25.34 KB

✅ CICLO #1 CONCLUÍDO COM SUCESSO!
```

---

## ⚠️ Modo Teste

Para testar sem executar ações reais:

1. Abra `main_ciclo.py`
2. Encontre a linha:
   ```python
   MODO_TESTE = False
   ```
3. Mude para:
   ```python
   MODO_TESTE = True
   ```

No modo teste:
- ✅ Simula movimentos sem pyautogui
- ✅ Logs mostram o que seria feito
- ✅ Não afeta o Oracle
- ✅ Útil para debug

---

## 🐛 Solução de Problemas

### **Problema: "pyperclip não disponível"**
**Solução:**
```bash
pip install pyperclip
```

### **Problema: Coordenadas erradas**
**Solução:**
1. Use uma ferramenta de captura de coordenadas
2. Edite `config.json` com as coordenadas corretas
3. Teste com MODO_TESTE = True primeiro

### **Problema: "Clipboard vazio"**
**Solução:**
- Aumente o tempo de espera em `tempos_espera.apos_rpa_bancada`
- Verifique se a grid do Oracle está carregada
- O Oracle pode estar lento, aguarde mais tempo

### **Problema: Erro no Google Sheets**
**Solução:**
- Verifique se `CredenciaisOracle.json` está presente
- Verifique se `token.json` está válido
- Execute a autenticação novamente

---

## 📊 Diferenças entre Versões

| Aspecto | Versão Anterior | Versão Standalone |
|---------|----------------|-------------------|
| **Dependências** | Precisa rpa_bancada/ e rpa_oracle/ | Nenhuma (tudo integrado) |
| **Arquivos** | 3 projetos separados | 1 projeto único |
| **Build .exe** | Complexo (múltiplos .exes) | Simples (1 .exe) |
| **Deploy** | Precisa copiar 3 pastas | Só copiar rpa_ciclo/ |
| **Manutenção** | Difícil (3 códigos) | Fácil (1 código) |

---

## 📝 Arquivos Importantes

| Arquivo | Descrição |
|---------|-----------|
| `main_ciclo.py` | Código principal (standalone) |
| `config.json` | Configurações e coordenadas |
| `google_sheets_ciclo.py` | Integração com Google Sheets |
| `RPA_Ciclo_GUI_v2.py` | Interface gráfica |
| `build_prod.bat` | Script para gerar .exe |
| `RPA_Ciclo_v2.spec` | Configuração do PyInstaller |
| `CredenciaisOracle.json` | Credenciais Google Sheets |
| `token.json` | Token de autenticação (gerado) |
| `processados.json` | Cache anti-duplicação (gerado) |

---

## 🎉 Vantagens da Versão Standalone

1. ✅ **Sem dependências externas** - Funciona sozinho
2. ✅ **Fácil deploy** - Só copiar a pasta
3. ✅ **Build simples** - Um comando gera o .exe
4. ✅ **Manutenção fácil** - Tudo em um lugar
5. ✅ **Menos erros** - Não precisa sincronizar 3 projetos
6. ✅ **Mais rápido** - Sem overhead de imports externos

---

## 📞 Suporte

Se encontrar problemas:

1. ✅ Verifique os logs no terminal
2. ✅ Teste com `MODO_TESTE = True`
3. ✅ Verifique o `config.json`
4. ✅ Confirme que todas as dependências estão instaladas

---

**Data:** 2025-10-18
**Versão:** 2.0 (Standalone)
**Status:** ✅ Pronto para produção
