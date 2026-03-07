# 🧪 Como Testar a Detecção de Modais

**Data:** 2026-01-13
**Versão:** RPA Ciclo v4.4

---

## 📝 Scripts Disponíveis

### 1. `testar_deteccao_modais.py` - Captura Tela ao Vivo
**Uso:** Captura a tela atual e testa detecção

**Como usar:**
```bash
# 1. Abra o Oracle com o modal VISÍVEL na tela
# 2. Execute:
python testar_deteccao_modais.py

# 3. Pressione ENTER quando o modal estiver visível
# 4. O script vai capturar e testar automaticamente
```

**Vantagens:**
- ✅ Teste rápido e direto
- ✅ Não precisa salvar screenshots manualmente
- ✅ Ideal para testes durante desenvolvimento

---

### 2. `testar_deteccao_arquivo.py` - Testa Imagem Salva
**Uso:** Testa detecção em uma imagem já salva

**Como usar:**

**Opção A - Arrastar e Soltar:**
```
1. Tire um screenshot do Oracle com o modal
2. Salve como PNG/JPG
3. Arraste e solte a imagem em cima de testar_deteccao_arquivo.py
4. Veja os resultados
```

**Opção B - Via Comando:**
```bash
python testar_deteccao_arquivo.py "C:\caminho\para\screenshot.png"
```

**Opção C - Interativo:**
```bash
python testar_deteccao_arquivo.py
# Digite o caminho quando solicitado
```

**Vantagens:**
- ✅ Teste com imagens históricas
- ✅ Pode testar múltiplas vezes sem refazer
- ✅ Ideal para comparar diferentes screenshots

---

## 🎯 O Que os Scripts Testam

Ambos os scripts testam a detecção de:

1. **Modal de Quantidade Negativa** (`qtd_negativa.png`)
2. **Modal de Erro Centro de Custo** (`erro_centro_custo.png`)

---

## 📊 Interpretando os Resultados

### Score (Confiança de Detecção)

O script testa automaticamente com vários níveis de confidence:

```
Confidence 90%: Score 45% ❌ Não
Confidence 80%: Score 45% ❌ Não
Confidence 70%: Score 45% ❌ Não
Confidence 60%: Score 45% ❌ Não
Confidence 50%: Score 45% ❌ Não
Confidence 40%: Score 45% ✅ DETECTADO
```

**Interpretação:**

| Score | O que significa | Ação recomendada |
|-------|----------------|-------------------|
| **≥ 80%** | 🟢 Excelente! | Use confidence 0.7 (70%) |
| **70-80%** | 🟡 Muito bom | Use confidence 0.6 (60%) |
| **60-70%** | 🟡 Bom | Use confidence 0.5 (50%) |
| **50-60%** | 🟠 Razoável | Use confidence 0.4 (40%) |
| **40-50%** | 🟠 Baixo | Use confidence 0.3 (30%) - última opção |
| **< 40%** | 🔴 Muito baixo | ⚠️ Imagem de referência pode estar errada |

---

## 🖼️ Arquivos Gerados

Após rodar os scripts, você terá:

### 1. Screenshot Original
```
screenshot_teste_20260113_143025.png
```
- Captura da tela no momento do teste
- Use para comparar com as imagens de referência

### 2. Imagem com Marcações (Debug)
```
debug_QUANTIDADE_NEGATIVA_20260113_143025.png
debug_ERRO_CENTRO_CUSTO_20260113_143025.png
```
- Mostra ONDE o OpenCV tentou detectar
- Retângulo vermelho = posição encontrada
- Texto mostra o score obtido

### 3. Resultado Final (apenas testar_deteccao_arquivo.py)
```
resultado_deteccao_20260113_143025.png
```
- Imagem com TODOS os modais marcados
- Verde = alta confiança (>70%)
- Laranja = média confiança (50-70%)
- Vermelho = baixa confiança (<50%)

---

## 🔍 Como Analisar os Resultados

### Passo 1: Verificar o Score

Execute o script e olhe os logs:

```
🔍 ERRO CENTRO DE CUSTO
======================================================================
📏 Template: 300x150
📏 Screenshot: 1920x1080

📊 SCORES:
----------------------------------------------------------------------
Confidence 90%: Score 65% ❌ Não
Confidence 80%: Score 65% ❌ Não
Confidence 70%: Score 65% ❌ Não
Confidence 60%: Score 65% ✅ DETECTADO
----------------------------------------------------------------------
✅ DETECTÁVEL com confidence de 60% ou menor
📍 Posição: (823, 456)
```

**Conclusão:** Use `confidence=0.6` no código!

---

### Passo 2: Abrir Imagem de Debug

Abra o arquivo `debug_*.png` gerado:

**O que verificar:**
1. ✅ O retângulo vermelho está **EM CIMA** do modal correto?
2. ✅ O retângulo cobre a **área correta** do modal?
3. ❌ O retângulo está em lugar **errado**?
4. ❌ O retângulo está **muito grande ou pequeno**?

**Se o retângulo está no lugar errado:**
- A imagem de referência pode estar desatualizada
- Capture um novo screenshot do modal
- Substitua a imagem antiga

---

### Passo 3: Comparar Imagens

Abra lado a lado:
1. Screenshot capturado pelo script
2. Imagem de referência (`qtd_negativa.png` ou `erro_centro_custo.png`)

**Verificar:**
- ✅ As imagens são **visualmente similares**?
- ❌ Há diferenças de **tamanho, cor ou texto**?
- ❌ A imagem de referência tem **código de item diferente**?

---

## 🛠️ Soluções para Problemas Comuns

### Problema 1: Score Baixo (< 40%)

**Causa:** Imagem de referência muito diferente do modal real

**Solução:**
1. Capture um novo screenshot do modal quando ele aparecer
2. Recorte APENAS a área do modal (sem bordas da tela)
3. Salve como PNG com boa qualidade
4. Substitua o arquivo `qtd_negativa.png` ou `erro_centro_custo.png`
5. Teste novamente

---

### Problema 2: Detecta em Lugar Errado

**Causa:** Imagem de referência tem elementos que aparecem em outros lugares

**Solução:**
1. Certifique-se de capturar apenas o MODAL (não a tela toda)
2. Inclua elementos únicos do modal (bordas, título, ícones)
3. Evite incluir áreas que se repetem (fundo branco, linhas genéricas)

---

### Problema 3: Não Detecta Mesmo com Score Bom

**Causa:** Confidence configurado muito alto no código

**Solução:**
1. Veja qual confidence o teste recomendou
2. Edite `main_ciclo.py`:
   ```python
   # Linha 1443 - Erro Centro de Custo
   encontrado = detectar_imagem_opencv(caminho, confidence=0.5, ...)
   #                                                         ^^^
   #                                                         Use o valor recomendado
   ```
3. Faça o BUILD novamente

---

### Problema 4: Template Maior que a Tela

**Causa:** Imagem de referência foi capturada em resolução maior

**Solução:**
- O OpenCV redimensiona automaticamente
- Você verá um log: `⚠️ Template redimensionado`
- Não precisa fazer nada, vai funcionar normalmente

---

## 📋 Checklist de Teste

Antes de fazer o BUILD final:

- [ ] Testei detecção de **quantidade negativa**
- [ ] Testei detecção de **erro centro de custo**
- [ ] Score foi ≥ 50% em ambos
- [ ] Retângulos nas imagens de debug estão corretos
- [ ] Ajustei `confidence` no código se necessário
- [ ] Imagens de referência estão atualizadas

---

## 💡 Dicas Importantes

### Dica 1: Capture Sempre com o Modal Completo
```
❌ Ruim: Modal cortado, faltando bordas
✅ Bom: Modal completo incluindo título e bordas
```

### Dica 2: Use Boa Qualidade
```
❌ Ruim: JPG com compressão, baixa resolução
✅ Bom: PNG sem compressão, alta resolução
```

### Dica 3: Capture do Oracle Real
```
❌ Ruim: Screenshot de documentação ou email
✅ Bom: Screenshot do Oracle rodando no ambiente real
```

### Dica 4: Evite Elementos Variáveis
```
❌ Ruim: Incluir código do item (E2029A, E3045B...)
✅ Bom: Focar em texto fixo (título, mensagem, botões)
```

---

## 🎯 Exemplo Prático

### Cenário: Testar Modal de Erro Centro de Custo

**Passo 1:** Provocar o erro no Oracle
```
1. Abrir Oracle
2. Preencher item que causa erro de centro de custo
3. Pressionar Ctrl+S
4. Modal aparece!
```

**Passo 2:** Executar teste
```bash
python testar_deteccao_modais.py
# Aguardar... modal ainda visível...
# Pressionar ENTER
```

**Passo 3:** Analisar resultados
```
🔍 ERRO CENTRO DE CUSTO
Score 55% - Detectado em confidence 50%

✅ Use confidence 0.5 (50%) no código!
```

**Passo 4:** Aplicar no código
```python
# main_ciclo.py linha 1443
encontrado = detectar_imagem_opencv(caminho, confidence=0.5, timeout=5)
```

**Passo 5:** BUILD e testar!
```bash
BUILD_GENESYS.bat
```

---

## 🚀 Comandos Rápidos

```bash
# Teste capturando tela ao vivo
python testar_deteccao_modais.py

# Teste com arquivo específico
python testar_deteccao_arquivo.py screenshot_erro.png

# Teste interativo (digita caminho)
python testar_deteccao_arquivo.py
```

---

**Criado por:** Claude Code
**Data:** 2026-01-13
**Versão:** v4.4
**Status:** ✅ Guia Completo de Testes
