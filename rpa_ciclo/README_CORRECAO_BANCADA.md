# Correção da Integração RPA_Ciclo + RPA_Bancada

## 📋 O que foi corrigido?

A integração entre **RPA_Ciclo** e **RPA_Bancada** foi melhorada com:

### 1. **Melhor Tratamento de Erros**
- Verificação de diretórios antes de importar
- Logs detalhados de cada etapa
- Tratamento de exceções específicas
- Mensagens de erro mais claras

### 2. **Verificação de Dependências**
- Verifica se pandas está instalado
- Verifica se pyperclip está instalado
- Mostra avisos se algo estiver faltando
- Continua mesmo com dependências opcionais faltantes

### 3. **Logging Aprimorado**
- Logs antes e depois de cada operação
- Separadores visuais para facilitar leitura
- Indica o resultado de cada etapa
- Mostra caminho completo dos arquivos

### 4. **Fallback para Subprocess**
- Se a importação direta falhar, tenta executar como subprocess
- Garante que o RPA_Bancada seja executado de qualquer forma

---

## 🔄 Como funciona o fluxo completo?

### **Etapas do RPA_Ciclo:**

1. **Transferência Subinventário** - Abre o modal
2. **Preenchimento Tipo** - Digita "SUB"
3. **Seleção Funcionário** - Seleciona Wallatas Moreira
4. **RPA Oracle** - Processa linhas do Google Sheets no Oracle
5. **Navegação** - Navega até a tela da Bancada
6. **RPA Bancada** - Extrai dados da grid do Oracle
7. **Fechamento Bancada** - Fecha a janela

### **Diferença entre Oracle e Bancada:**

| Aspecto | RPA Oracle | RPA Bancada |
|---------|-----------|-------------|
| **O que faz** | Preenche formulários | Extrai dados de grid |
| **Origem** | Google Sheets | Tela do Oracle |
| **Destino** | Oracle | Excel + Google Sheets |
| **Método** | pyautogui (clicar/digitar) | pyperclip (copiar) |
| **Dados** | Item, Sub, End, Qtd, Ref | Org, Sub, End, Item, Desc, Rev, UDM, Estoque |

---

## ✅ Como verificar se está tudo OK?

### **1. Verificar Dependências**
```bash
cd rpa_ciclo
python verificar_dependencias_bancada.py
```

**Resultado esperado:**
```
============================================================
RESUMO
============================================================
[OK] Instaladas: 7
[OPT] Opcionais faltantes: 0
[ERR] Faltantes criticas: 0

Todas as dependencias estao instaladas!
```

### **2. Testar Importação do RPA_Bancada**
```bash
cd rpa_ciclo
python -c "import sys; sys.path.insert(0, '../rpa_bancada'); import main_v2; print('Import OK')"
```

**Resultado esperado:**
```
[OK] Google Sheets manager importado com sucesso
Import OK
```

---

## 🐛 Solução de Problemas

### **Problema: "ModuleNotFoundError: No module named 'pandas'"**
**Solução:**
```bash
pip install pandas pyperclip openpyxl
```

### **Problema: "Diretório rpa_bancada não encontrado"**
**Solução:**
Verifique se a estrutura de pastas está correta:
```
rpas/
├── rpa_ciclo/
│   └── main_ciclo.py
├── rpa_bancada/
│   ├── main_v2.py
│   ├── diagnostic_helper.py
│   └── google_sheets_manager.py
└── rpa_oracle/
    └── RPA_Oracle.py
```

### **Problema: "Erro ao executar RPA_Bancada"**
**Solução:**
1. Verifique os logs no terminal
2. Procure por mensagens de erro específicas
3. Verifique se o Oracle está aberto na tela da Bancada
4. Verifique se as coordenadas estão corretas para sua tela

---

## 📝 Logs Importantes

Durante a execução, você verá logs como:

```
🤖 ETAPA 7: Execução do RPA_Bancada_v2
📂 Diretório bancada: C:\...\rpas\rpa_bancada
✅ Adicionado ao path: C:\...\rpas\rpa_bancada
✅ pandas disponível
✅ pyperclip disponível
📥 Importando módulo main_v2...
✅ Módulo RPA_Bancada importado com sucesso
🔗 Configurando callback de log...
✅ Callback de log configurado
============================================================
▶️ Iniciando RPA_Bancada em modo single_run...
============================================================
```

Se algo der errado, você verá:
```
❌ Erro ao importar RPA_Bancada: <detalhes do erro>
⚠️ Tentando executar como subprocess...
```

---

## 🎯 Próximos Passos

1. ✅ Dependências verificadas
2. ✅ Código corrigido com melhor tratamento de erros
3. 🔄 **Teste o RPA_Ciclo completo**
4. 📊 Analise os logs para identificar qualquer problema restante

---

## 📞 Suporte

Se encontrar algum problema:

1. **Verifique os logs** - Eles mostram exatamente onde está o erro
2. **Execute verificar_dependencias_bancada.py** - Garante que tudo está instalado
3. **Teste cada RPA separadamente** primeiro:
   - `rpa_oracle/RPA_Oracle.py`
   - `rpa_bancada/main_v2.py`
4. Depois teste o **RPA_Ciclo completo**

---

**Data da Correção:** 2025-10-18
**Arquivos Modificados:**
- `rpa_ciclo/main_ciclo.py` (função `etapa_07_executar_rpa_bancada`)
**Arquivos Criados:**
- `rpa_ciclo/verificar_dependencias_bancada.py`
- `rpa_ciclo/README_CORRECAO_BANCADA.md`
