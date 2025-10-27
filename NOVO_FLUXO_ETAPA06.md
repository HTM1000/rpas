# 🔄 Novo Fluxo - Etapa 06

## 🎯 O que mudou?

### **❌ FLUXO ANTIGO:**
```
Etapa 06: Navegação pós-Oracle
├─ Clicar em "janela" (340, 40)
├─ Clicar em "navegador" (385, 135)
└─ Duplo clique em "Bancada Material"
```

### **✅ NOVO FLUXO:**
```
Etapa 06: Navegação pós-Oracle
├─ Fechar janela "Subinventory Transfer (BC2)" → X (1293, 90)
├─ Fechar janela "Transferencia do Subinventario (BC2)" → X (494, 91)
└─ Duplo clique em "Bancada Material" (598, 284)
```

---

## 📋 Novo Fluxo Detalhado

```
RPA_Oracle termina
↓
ETAPA 06: Navegação pós-Oracle
↓
[1] 🔴 Fechar "Subinventory Transfer (BC2)"
    Clica no X em (1293, 90)
    ↓
    Aguarda 3 segundos
    ↓
[2] 🔴 Fechar "Transferencia do Subinventario (BC2)"
    Clica no X em (494, 91)
    ↓
    Aguarda 3 segundos
    ↓
[3] 📂 Abrir "Bancada de Material"
    Duplo clique em (598, 284)
    ↓
    Aguarda 5 segundos (abertura da Bancada)
    ↓
ETAPA 07: Extração de dados da Bancada
```

---

## 📊 Exemplo de Logs

```
============================================================
📋 ETAPA 6: Navegação pós-Oracle
============================================================
🔴 Fechando janela 'Subinventory Transfer (BC2)'...
🖱️ Fechar janela 'Subinventory Transfer (BC2)' - Botão X
⏳ Aguardando fechar primeira janela (3s)...

🔴 Fechando janela 'Transferencia do Subinventario (BC2)'...
🖱️ Fechar janela 'Transferencia do Subinventario (BC2)' - Botão X
⏳ Aguardando fechar segunda janela (3s)...

📂 Abrindo Bancada de Material...
🖱️ Duplo clique em '4. Bancada de Material'
⏳ Aguardando abertura da Bancada (5s)...

============================================================
🤖 ETAPA 7: Extração de dados da Bancada
============================================================
```

---

## ⚙️ Coordenadas Configuradas

### **config.json:**

```json
{
  "coordenadas": {
    "tela_06_fechar_subinventory_transfer": {
      "x": 1293,
      "y": 90,
      "descricao": "Fechar janela 'Subinventory Transfer (BC2)' - Botão X"
    },
    "tela_06_fechar_transferencia_subinventario": {
      "x": 494,
      "y": 91,
      "descricao": "Fechar janela 'Transferencia do Subinventario (BC2)' - Botão X"
    },
    "tela_07_bancada_material": {
      "x": 598,
      "y": 284,
      "descricao": "Duplo clique em '4. Bancada de Material'",
      "duplo_clique": true
    }
  },
  "tempos_espera": {
    "entre_cliques": 3,
    "apos_modal": 5.0
  }
}
```

---

## 🔍 Por que esse fluxo?

### **Motivo:**
- Após RPA_Oracle terminar, ficam abertas 2 janelas:
  1. "Subinventory Transfer (BC2)"
  2. "Transferencia do Subinventario (BC2)"

- Antes de abrir a Bancada, precisa fechar essas janelas
- Ordem: Fecha a primeira (1293, 90) → Fecha a segunda (494, 91) → Abre Bancada

### **Vantagem:**
- ✅ Limpa a tela
- ✅ Evita confusão de janelas
- ✅ Bancada abre corretamente

---

## 🎯 Sequência de Cliques

```
┌─────────────────────────────────────────────────────────┐
│  APÓS RPA_ORACLE                                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Janelas abertas:                                       │
│  ┌─────────────────────────────────────────────┐       │
│  │ Subinventory Transfer (BC2)         [X]     │ ← (1293, 90)
│  └─────────────────────────────────────────────┘       │
│  ┌─────────────────────────────────────────────┐       │
│  │ Transferencia do Subinventario (BC2) [X]    │ ← (494, 91)
│  └─────────────────────────────────────────────┘       │
│                                                         │
│  Ação:                                                  │
│  1. Clica X (1293, 90) → Fecha primeira                │
│  2. Clica X (494, 91) → Fecha segunda                  │
│  3. Duplo clique (598, 284) → Abre Bancada             │
└─────────────────────────────────────────────────────────┘
```

---

## ⏱️ Tempos de Espera

| Ação | Tempo | Motivo |
|------|-------|--------|
| Após fechar 1ª janela | 3s | Aguardar janela fechar |
| Após fechar 2ª janela | 3s | Aguardar janela fechar |
| Após abrir Bancada | 5s | Aguardar Bancada carregar |

---

## 🧪 Como Testar

### **1. Modo Teste:**
```python
# main_ciclo.py
MODO_TESTE = True  # Simula sem clicar
```

Vai mostrar nos logs:
```
[MODO TESTE] Simulando clique em (1293, 90)
[MODO TESTE] Simulando clique em (494, 91)
[MODO TESTE] Simulando duplo clique em (598, 284)
```

### **2. Ajustar coordenadas:**
Se as coordenadas estiverem erradas:

1. Use ferramenta de captura de mouse
2. Anote X e Y corretos
3. Edite `config.json`:
```json
"tela_06_fechar_subinventory_transfer": {
  "x": 1293,  ← Seu valor
  "y": 90     ← Seu valor
}
```

### **3. Testar com Oracle:**
```bash
python main_ciclo.py
```

Observe se:
- ✅ Fecha primeira janela corretamente
- ✅ Fecha segunda janela corretamente
- ✅ Abre Bancada corretamente

---

## 🐛 Solução de Problemas

### **Problema: Não fecha a janela correta**
**Causa:** Coordenadas erradas

**Solução:**
1. Tire print da tela com as janelas abertas
2. Use ferramenta de coordenadas
3. Anote X e Y do botão X
4. Atualize `config.json`

### **Problema: Ordem está errada**
**Causa:** Janelas estão em ordem diferente

**Solução:**
Inverta a ordem no código ou no config

### **Problema: Bancada não abre**
**Causa:** Janelas não fecharam ainda

**Solução:**
Aumente tempo de espera:
```json
"tempos_espera": {
  "entre_cliques": 5  ← Aumentar de 3 para 5
}
```

---

## 📝 Código da Etapa 06

```python
def etapa_06_navegacao_pos_oracle(config):
    """Etapa 6: Navegação após RPA_Oracle - Fechar janelas e abrir Bancada"""
    gui_log("📋 ETAPA 6: Navegação pós-Oracle")

    # Fechar janela "Subinventory Transfer (BC2)"
    gui_log("🔴 Fechando janela 'Subinventory Transfer (BC2)'...")
    coord = config["coordenadas"]["tela_06_fechar_subinventory_transfer"]
    clicar_coordenada(coord["x"], coord["y"], descricao=coord["descricao"])

    tempo_espera = config["tempos_espera"]["entre_cliques"]
    if not aguardar_com_pausa(tempo_espera, "Aguardando fechar primeira janela"):
        return False

    # Fechar janela "Transferencia do Subinventario (BC2)"
    gui_log("🔴 Fechando janela 'Transferencia do Subinventario (BC2)'...")
    coord = config["coordenadas"]["tela_06_fechar_transferencia_subinventario"]
    clicar_coordenada(coord["x"], coord["y"], descricao=coord["descricao"])

    tempo_espera = config["tempos_espera"]["entre_cliques"]
    if not aguardar_com_pausa(tempo_espera, "Aguardando fechar segunda janela"):
        return False

    # Duplo clique para abrir a tela da bancada
    gui_log("📂 Abrindo Bancada de Material...")
    coord = config["coordenadas"]["tela_07_bancada_material"]
    clicar_coordenada(coord["x"], coord["y"], duplo=coord.get("duplo_clique", True),
                     descricao=coord["descricao"])

    tempo_espera = config["tempos_espera"]["apos_modal"]
    return aguardar_com_pausa(tempo_espera, "Aguardando abertura da Bancada")
```

---

## ✅ Benefícios do Novo Fluxo

1. ✅ **Limpa o ambiente** - Fecha janelas desnecessárias
2. ✅ **Evita erros** - Não deixa janelas abertas
3. ✅ **Logs claros** - Sabe exatamente o que está fechando
4. ✅ **Configurável** - Coordenadas no config.json
5. ✅ **Testável** - MODO_TESTE para validar

---

## 🎯 Resumo

| Aspecto | Valor |
|---------|-------|
| **1ª janela fechada** | Subinventory Transfer (BC2) |
| **Coordenada 1** | (1293, 90) |
| **2ª janela fechada** | Transferencia do Subinventario (BC2) |
| **Coordenada 2** | (494, 91) |
| **Tempo entre fechamentos** | 3 segundos |
| **Bancada aberta** | Duplo clique (598, 284) |
| **Tempo após abrir** | 5 segundos |

---

**Data:** 2025-10-18
**Versão:** 2.5 (Novo Fluxo Etapa 06)
**Status:** ✅ **IMPLEMENTADO**

**Pronto para testar!** 🚀
