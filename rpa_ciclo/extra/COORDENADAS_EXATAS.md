# Coordenadas Exatas dos Campos Oracle

## 📐 Mapeamento Visual Completo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Formulário Oracle - Transferência de Subinventário                         │
│  Linha Y=155 a Y=177 (Altura: 22 pixels)                                    │
└─────────────────────────────────────────────────────────────────────────────┘

Linha Horizontal Única (Y=155 → Y=177):
─────────────────────────────────────────────────────────────────────────────

  67              208       316       422       530       639       737
  ↓               ↓         ↓         ↓         ↓         ↓         ↓
  ┌─────────────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌──────┐ ┌───────┐
  │   Item      │ │Sub.Ori│ │End.Ori│ │ParaSub│ │ParaLoc│ │ Qtd  │ │  Ref  │
  │             │ │       │ │       │ │       │ │       │ │      │ │       │
  │  118px      │ │ 101px │ │ 101px │ │ 103px │ │ 100px │ │ 89px │ │ 100px │
  └─────────────┘ └───────┘ └───────┘ └───────┘ └───────┘ └──────┘ └───────┘
  185             309       417       525       630       728      837


Legenda:
─────────
Item      = campo_item       [67,  155, 118, 22]
Sub.Ori   = campo_sub_o      [208, 155, 101, 22]  ← Subinventário Origem
End.Ori   = campo_end_o      [316, 155, 101, 22]  ← Endereço Origem
ParaSub   = campo_sub_d      [422, 155, 103, 22]  ← Para Subinventário (Destino)
ParaLoc   = campo_end_d      [530, 155, 100, 22]  ← Para Localização (Destino)
Qtd       = campo_quantidade [639, 155,  89, 22]
Ref       = campo_referencia [737, 155, 100, 22]
```

---

## 📊 Tabela Detalhada de Coordenadas

### Formato: `[X_inicial, Y_inicial, Largura, Altura]`

| Campo                  | Nome Código      | X   | Y   | Largura | Altura | X_final | Y_final |
|------------------------|------------------|-----|-----|---------|--------|---------|---------|
| **Item**               | `campo_item`     | 67  | 155 | 118     | 22     | 185     | 177     |
| **Subinvent. Origem**  | `campo_sub_o`    | 208 | 155 | 101     | 22     | 309     | 177     |
| **Endereço Origem**    | `campo_end_o`    | 316 | 155 | 101     | 22     | 417     | 177     |
| **Para Sub (Destino)** | `campo_sub_d`    | 422 | 155 | 103     | 22     | 525     | 177     |
| **Para Loc (Destino)** | `campo_end_d`    | 530 | 155 | 100     | 22     | 630     | 177     |
| **Quantidade**         | `campo_quantidade` | 639 | 155 | 89    | 22     | 728     | 177     |
| **Referência**         | `campo_referencia` | 737 | 155 | 100   | 22     | 837     | 177     |

---

## 🎯 Pixels Centrais (para Clipboard - Ctrl+A+Ctrl+C)

Para clicar no **centro** de cada campo ao usar validação por clipboard:

```python
# Formato: (X_centro, Y_centro) = (X + Largura/2, Y + Altura/2)

campo_item_centro       = (126, 166)  # (67  + 118/2, 155 + 22/2)
campo_sub_o_centro      = (258, 166)  # (208 + 101/2, 155 + 22/2)
campo_end_o_centro      = (366, 166)  # (316 + 101/2, 155 + 22/2)
campo_sub_d_centro      = (473, 166)  # (422 + 103/2, 155 + 22/2)
campo_end_d_centro      = (580, 166)  # (530 + 100/2, 155 + 22/2)
campo_quantidade_centro = (683, 166)  # (639 +  89/2, 155 + 22/2)
campo_referencia_centro = (787, 166)  # (737 + 100/2, 155 + 22/2)
```

---

## 📋 JSON para config.json

```json
"campos_oracle_validacao": {
  "descricao": "Coordenadas completas dos campos para validação híbrida (x, y, largura, altura)",
  "observacao": "Todos os campos: Y=155, Altura=22 (Y_final=177)",
  "campo_item":       [67,  155, 118, 22],
  "campo_quantidade": [639, 155,  89, 22],
  "campo_referencia": [737, 155, 100, 22],
  "campo_sub_o":      [208, 155, 101, 22],
  "campo_end_o":      [316, 155, 101, 22],
  "campo_sub_d":      [422, 155, 103, 22],
  "campo_end_d":      [530, 155, 100, 22]
}
```

---

## 🔍 Validação de Campos por Tipo de Referência

### Referência MOV / Outros (Origem)
Valida campos de **ORIGEM**:
- ✅ Item (67, 155, 118, 22)
- ✅ Quantidade (639, 155, 89, 22)
- ✅ Referência (737, 155, 100, 22)
- ✅ **Subinvent. Origem** (208, 155, 101, 22)
- ✅ **Endereço Origem** (316, 155, 101, 22)

### Referência COD (Destino)
Valida campos de **DESTINO**:
- ✅ Item (67, 155, 118, 22)
- ✅ Quantidade (639, 155, 89, 22)
- ✅ Referência (737, 155, 100, 22)
- ✅ **Para Sub** (422, 155, 103, 22)
- ✅ **Para Loc** (530, 155, 100, 22)

---

## 🧮 Cálculos de Referência

### Áreas dos Campos (em pixels²)

| Campo              | Largura | Altura | Área (px²) | % da linha* |
|--------------------|---------|--------|------------|-------------|
| Item               | 118     | 22     | 2.596      | 15.3%       |
| Subinvent. Origem  | 101     | 22     | 2.222      | 13.1%       |
| Endereço Origem    | 101     | 22     | 2.222      | 13.1%       |
| Para Sub           | 103     | 22     | 2.266      | 13.4%       |
| Para Loc           | 100     | 22     | 2.200      | 13.0%       |
| Quantidade         | 89      | 22     | 1.958      | 11.6%       |
| Referência         | 100     | 22     | 2.200      | 13.0%       |

*% considerando largura total de 770px (67 a 837)

### Espaçamentos entre Campos

| Entre campos                      | Pixels | Observação           |
|-----------------------------------|--------|----------------------|
| Item → Subinv. Origem             | 23     | (208 - 185)          |
| Subinv. Origem → Endereço Origem  | 7      | (316 - 309)          |
| Endereço Origem → Para Sub        | 5      | (422 - 417)          |
| Para Sub → Para Loc               | 5      | (530 - 525)          |
| Para Loc → Quantidade             | 9      | (639 - 630)          |
| Quantidade → Referência           | 9      | (737 - 728)          |

---

## 📸 Como Capturar Coordenadas

Se precisar recapturar as coordenadas:

```python
import pyautogui
import time
from PIL import ImageGrab

# 1. Capturar coordenadas manualmente
print("Posicione o mouse no CANTO SUPERIOR ESQUERDO do campo em 3s...")
time.sleep(3)
x1, y1 = pyautogui.position()
print(f"Canto superior esquerdo: X={x1}, Y={y1}")

print("Posicione o mouse no CANTO INFERIOR DIREITO do campo em 3s...")
time.sleep(3)
x2, y2 = pyautogui.position()
print(f"Canto inferior direito: X={x2}, Y={y2}")

largura = x2 - x1
altura = y2 - y1

print(f"\n✅ Coordenadas do campo:")
print(f"   [{x1}, {y1}, {largura}, {altura}]")
print(f"   X: {x1} → {x2} (largura: {largura}px)")
print(f"   Y: {y1} → {y2} (altura: {altura}px)")

# 2. Capturar screenshot do campo
img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
img.save(f"campo_{x1}_{y1}.png")
print(f"   Screenshot salvo: campo_{x1}_{y1}.png")
```

---

## ⚙️ Uso no Código

### No validador_hibrido.py

```python
# Função principal
validar_campo_oracle_hibrido(
    x=67,          # X inicial
    y=155,         # Y inicial
    largura=118,   # Largura
    altura=22,     # Altura
    valor_esperado="E2029B",
    nome_campo="Item"
)
```

### No main_ciclo.py

```python
# Carregar do config.json
coords_validacao = {
    "campo_item": (67, 155, 118, 22),
    "campo_quantidade": (639, 155, 89, 22),
    # ... outros campos
}

# Validar todos os campos
validar_campos_oracle_completo(
    coords_validacao,
    item, quantidade, referencia,
    sub_o, end_o, sub_d, end_d
)
```

---

## 🎨 Diagrama ASCII Detalhado

```
Pixel X:  0    67   185 208 309 316 417 422 525 530 630 639 728 737 837
          |     |    |   |   |   |   |   |   |   |   |   |   |   |   |
Y=155 ────┼─────┬────┼───┬───┼───┬───┼───┬───┼───┬───┼───┬───┼───┬───┼────
          │     │████│   │███│   │███│   │███│   │███│   │███│   │███│
          │     │████│   │███│   │███│   │███│   │███│   │███│   │███│
          │     │████│   │███│   │███│   │███│   │███│   │███│   │███│
Y=177 ────┼─────┴────┼───┴───┼───┴───┼───┴───┼───┴───┼───┴───┼───┴───┼────
          |     |    |   |   |   |   |   |   |   |   |   |   |   |   |

          Item=118px  101px 101px 103px 100px  89px 100px
```

---

## 📝 Notas Importantes

1. **Todos os campos estão na mesma linha horizontal**
   - Y inicial: **155**
   - Y final: **177**
   - Altura: **22 pixels**

2. **Não há sobreposição de campos**
   - Cada campo tem seu espaço exclusivo
   - Espaçamentos entre campos variam de 5 a 23 pixels

3. **Ordem da esquerda para direita:**
   1. Item (67-185)
   2. Subinvent. Origem (208-309)
   3. Endereço Origem (316-417)
   4. Para Sub (422-525)
   5. Para Loc (530-630)
   6. Quantidade (639-728)
   7. Referência (737-837)

4. **Resolução testada:**
   - Essas coordenadas foram medidas na resolução específica do Oracle
   - Se mudar a resolução ou scaling do Windows, recapture as coordenadas

---

## ✅ Verificação Rápida

Execute este código para verificar se as coordenadas estão corretas:

```python
from validador_hibrido import validar_campo_preenchido

# Testar campo Item
preenchido, percentual, detalhes = validar_campo_preenchido(67, 155, 118, 22)
print(f"Campo Item preenchido: {preenchido} ({percentual:.2%})")

# Testar campo Quantidade
preenchido, percentual, detalhes = validar_campo_preenchido(639, 155, 89, 22)
print(f"Campo Quantidade preenchido: {preenchido} ({percentual:.2%})")
```

Se retornar percentuais entre 2% e 20%, as coordenadas estão corretas!

---

**Última atualização:** 2025-10-24
**Validado por:** Usuário
**Status:** ✅ Coordenadas confirmadas e testadas
