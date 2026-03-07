# 🧪 RPA BANCADA - MODO TESTE

Executável de teste para validar coordenadas do mouse antes de rodar em produção.

## 🎯 Objetivo

Testar as coordenadas dos cliques do mouse **sem processar dados reais**, permitindo validar se o RPA está clicando nos lugares certos.

## ⚙️ Características do Modo Teste

✅ **Cliques rápidos** - Sem esperas longas (3 seg ao invés de 2 min + 15 min)
✅ **NÃO conecta Google Sheets** - Economiza tempo e não grava dados
✅ **NÃO processa dados reais** - Apenas simula as operações
✅ **Executa exatamente 3 ciclos** - Para automaticamente após 3 ciclos
✅ **Mostra coordenadas** - Exibe onde o mouse vai clicar
✅ **Console visível** - Acompanhe o progresso em tempo real

## 🚀 Como Usar

### 1. Compilar o Executável de Teste

```bash
cd C:\Users\ID135\OneDrive\Desktop\www\rpas\rpa_bancada
BUILD_BANCADA_TESTE.bat
```

### 2. Preparar o Ambiente

1. Abra o **Oracle Applications**
2. Navegue até a tela que contém **"4. Bancada de Material"**
3. Certifique-se que a resolução está em **1440x900** (recomendado)
4. Deixe a janela do Oracle **visível e em foco**

### 3. Executar o Teste

```bash
cd dist\RPA_Bancada_TESTE
RPA_Bancada_TESTE.exe
```

Ou clique duas vezes no executável.

### 4. O que vai acontecer

O programa vai aguardar **3 segundos** para você posicionar as janelas, depois vai:

**CICLO #1:**
1. 📂 Abrir Bancada (duplo clique em 598, 284)
2. 🖱️ Clicar em "Detalhado" (273, 358)
3. 🖱️ Clicar em "Localizar" (524, 689)
4. ⏳ Aguardar 3 segundos (simula carregamento)
5. 🖱️ Clicar na célula "Org" (318, 174)
6. ⌨️ Simular menu contexto (não pressiona teclas)
7. ⏳ Aguardar 3 segundos (simula processamento)
8. 💾 Simular salvamento (não salva arquivo)
9. 🔴 Fechar Bancada (746, 90)

**CICLO #2:** Repete tudo
**CICLO #3:** Repete tudo e **PARA**

### 5. Verificar Resultados

Durante a execução, observe se o mouse está clicando nos lugares corretos:

- [ ] Duplo clique abre a **Bancada de Material**?
- [ ] Clique acerta o botão **"Detalhado"**?
- [ ] Clique acerta o botão **"Localizar"**?
- [ ] Clique acerta a célula **"Org"** na grid?
- [ ] Clique acerta o **"X"** para fechar a bancada?

## ⚠️ FAILSAFE

Se algo der errado, **mova o mouse para o canto superior esquerdo** da tela para parar imediatamente.

Ou pressione **Ctrl+C** no console.

## 📊 Tempo de Execução

- **Por ciclo:** ~10 segundos
- **3 ciclos:** ~30 segundos

## 🔧 Ajustar Coordenadas

Se alguma coordenada estiver errada, edite o arquivo `config.json`:

```json
{
  "coordenadas": {
    "tela_07_bancada_material": {"x": 598, "y": 284},
    "tela_08_fechar_bancada": {"x": 746, "y": 90},
    "bancada_detalhado": {"x": 273, "y": 358},
    "bancada_localizar": {"x": 524, "y": 689},
    "bancada_celula_org": {"x": 318, "y": 174}
  }
}
```

Depois recompile:

```bash
BUILD_BANCADA_TESTE.bat
```

## 📁 Arquivos

- **main_teste.py** - Código fonte do modo teste
- **RPA_Bancada_TESTE.spec** - Configuração PyInstaller
- **BUILD_BANCADA_TESTE.bat** - Script de compilação
- **config.json** - Coordenadas e configurações

## ✅ Validação Aprovada?

Se todos os cliques estiverem corretos, você pode usar o **executável de PRODUÇÃO** com confiança:

```bash
BUILD_BANCADA.bat
```

Ou rode a versão com GUI:

```bash
python RPA_Bancada_GUI.py
```

## 🆘 Problemas Comuns

**Mouse não clica no lugar certo:**
- Verifique a resolução da tela (deve ser 1440x900)
- Verifique o zoom do Windows (deve ser 100%)
- Use `mouse_position_helper.py` para capturar coordenadas corretas

**Programa para imediatamente:**
- Verifique se o `config.json` está na mesma pasta do executável
- Verifique se PyAutoGUI está instalado (`pip install pyautogui`)

**Erro de permissão:**
- Execute como Administrador

---

🎯 **Objetivo:** Validar coordenadas antes de rodar em produção
⏱️ **Duração:** ~30 segundos (3 ciclos)
🔒 **Seguro:** Não processa dados reais nem conecta ao Google Sheets
