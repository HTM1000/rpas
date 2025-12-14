# RPA Inventário

Sistema de automação de inventário usando Selenium para Tecumseh do Brasil.

## Características

- **Interface Gráfica Moderna**: Layout similar ao RPA Ciclo com logos Genesys e Tecumseh
- **Automação Web com Selenium**: Identificação inteligente de elementos por texto, ID, XPATH
- **Build Standalone**: Geração de executável completo com PyInstaller
- **Controle de Parada**: ESC para parar a qualquer momento
- **Logs Detalhados**: Acompanhamento em tempo real da execução

## Estrutura do Projeto

```
rpa_inventario/
├── RPA_Inventario_GUI.py    # Interface gráfica principal
├── main_inventario.py        # Lógica de automação com Playwright
├── config.json               # Configurações (URLs, coordenadas, delays)
├── requirements.txt          # Dependências Python
├── BUILD_INVENTARIO.bat      # Script de build para Windows
├── Inventario.spec           # Configuração do PyInstaller
├── Logo.png                  # Logo Genesys
├── Tecumseh.png              # Logo Tecumseh
├── Topo.png                  # Ícone da janela
└── Logo.ico                  # Ícone do executável
```

## Instalação e Uso

### Modo Desenvolvimento

1. **Instalar dependências**:
   ```bash
   pip install -r requirements.txt
   ```

   Ou use o script:
   ```bash
   INSTALAR_DEPENDENCIAS.bat
   ```

2. **Configurar**:
   - Edite `config.json` com a URL e configurações necessárias

3. **Executar**:
   ```bash
   python RPA_Inventario_GUI.py
   ```

### Build Standalone

1. **Executar o build**:
   ```bash
   BUILD_INVENTARIO.bat
   ```

2. **Distribuir**:
   - Copie a pasta completa `dist/RPA_Inventario/`
   - Não distribua apenas o .exe, a pasta _internal é necessária

## Configuração (config.json)

```json
{
  "url": "https://seu-sistema.com",
  "headless": false,
  "timeout_padrao": 30000,
  "delays": {
    "entre_cliques": 2,
    "apos_preencher": 1,
    "apos_login": 3
  }
}
```

## Selenium - Identificação de Elementos

O Selenium permite identificar elementos de várias formas:

```python
# Por texto visível (botões, links)
clicar_por_texto(driver, "Entrar", "botão de login")

# Por ID
clicar_por_id(driver, "btnLogin", "botão de login")

# Por XPATH
clicar_por_xpath(driver, "//button[@class='login-btn']", "botão login")

# Preencher campos por nome
preencher_campo(driver, "username", "meu_usuario", "campo usuário", por="name")

# Preencher campos por ID
preencher_campo(driver, "email", "user@email.com", "campo email", por="id")

# Preencher campos por XPATH
preencher_campo(driver, "//input[@placeholder='Senha']", "123456", "senha", por="xpath")

# Preencher campos por label
preencher_campo(driver, "Email", "user@email.com", "campo email", por="label")
```

## Controles da Interface

- **🎯 Iniciar RPA**: Inicia a automação
- **⏹️ Parar RPA**: Para a execução
- **ESC**: Parada de emergência
- **❓ Ajuda**: Exibe instruções detalhadas

## Status do Projeto

- ✅ Interface gráfica implementada
- ✅ Estrutura base com Playwright
- ✅ Sistema de build standalone
- ⏳ Lógica de automação (a ser implementada conforme necessidade)

## Próximos Passos

1. Configurar URL do sistema em `config.json`
2. Implementar lógica de automação específica em `main_inventario.py`
3. Adicionar coordenadas necessárias em `config.json`
4. Testar em modo desenvolvimento
5. Gerar build standalone e distribuir

## Dependências Principais

- **Selenium**: Automação web robusta e madura
- **WebDriver Manager**: Gerenciador automático de drivers Chrome
- **Tkinter**: Interface gráfica (built-in)
- **Pillow**: Processamento de imagens
- **Keyboard**: Controle de atalhos (ESC)
- **PyInstaller**: Build de executável

## Notas Técnicas

- Build em modo **onedir** (pasta com executável + dependências)
- Selenium incluído no build via `collect_all`
- Chrome WebDriver baixado automaticamente pelo webdriver-manager
- Interface compatível com Windows (testado em Win10/11)
- Requer Google Chrome instalado no sistema

## Autor

Desenvolvido para Tecumseh do Brasil - Sistema RPA Inventário
