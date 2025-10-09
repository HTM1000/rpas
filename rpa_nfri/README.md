# RPA NFRi - Notas Fiscais do Recebimento Integrado

Automação para extrair dados de NFRi do sistema web e enviar para Google Sheets.

## 📋 Pré-requisitos

1. Python 3.8 ou superior
2. Credenciais do Google Cloud (CredenciaisOracle.json)

## 🚀 Como Gerar o Executável

### Passo 1: Instalar Dependências

```bash
pip install -r requirements.txt
```

### Passo 2: Gerar o Executável

Execute o script de build:

```bash
build.bat
```

Ou manualmente:

```bash
pyinstaller RPA_NFRi.spec
```

O executável será criado em: `dist\RPA_NFRi.exe`

## 📦 Distribuição

Após gerar o executável, você precisa distribuir:

1. **RPA_NFRi.exe** (da pasta `dist`)
2. **CredenciaisOracle.json** (arquivo de credenciais do Google)

**IMPORTANTE:** Coloque ambos os arquivos na mesma pasta!

## 🔑 Primeira Execução - Login Google

Na primeira vez que você executar o RPA:

1. Uma janela do navegador será aberta
2. Faça login com sua conta Google
3. Autorize o aplicativo a acessar o Google Sheets
4. Um arquivo `token.json` será criado automaticamente
5. Nas próximas execuções, o login não será mais necessário

**Dica:** O arquivo `token.json` também pode ser distribuído junto com o executável para evitar login repetido.

## 📊 Configuração do Google Sheets

O RPA envia dados para a planilha configurada no código:

- **ID da Planilha:** `1GnHcBKhXWKfU4Pcucyqj1_Vv9jiIkbY4iJ4prugD9ZE`
- **Nome da Aba:** `Página1`

Para usar outra planilha, edite estas linhas no arquivo `main.py`:

```python
SPREADSHEET_ID = "SEU_ID_AQUI"
SHEET_NAME = "SUA_ABA_AQUI"
```

## 🎯 Como Usar

1. Abra o sistema web no navegador
2. Execute o **RPA_NFRi.exe**
3. Clique em **▶ Iniciar**
4. O RPA irá:
   - Navegar pelos menus
   - Gerar relatório Excel
   - Baixar o arquivo
   - Processar os dados
   - Enviar para Google Sheets

**Atalho:** Pressione **ESC** durante a execução para pausar o RPA.

## 📂 Estrutura de Arquivos

```
rpa_nfri/
├── main.py                    # Código principal
├── RPA_NFRi.spec             # Configuração PyInstaller
├── requirements.txt          # Dependências Python
├── build.bat                 # Script de build
├── CredenciaisOracle.json   # Credenciais Google (NÃO COMMITAR!)
├── token.json               # Token de autenticação (gerado automaticamente)
├── Logo.png                 # Logo da interface
├── Logo.ico                 # Ícone do executável
├── Topo.png                 # Imagem do topo
└── informacoes/             # Imagens de referência dos cliques
    ├── 158x337.jpg
    ├── 158x387.jpg
    ├── 165x285.jpg
    ├── 507x263.jpg
    ├── 690x190-tab-tab-enter.jpg
    └── 950x128-excel-baixado.jpg
```

## 🛠️ Coordenadas de Cliques

As coordenadas estão definidas no código:

```python
coords = {
    "solucao_fiscal": (158, 335),
    "nfs_recebimento": (163, 383),
    "botao_excel": (507, 263),
    "campo_data": (690, 190),
    "excel_baixado": (950, 128),
}
```

**Ajuste conforme necessário para sua resolução de tela!**

## ⚠️ Segurança

- **NUNCA** compartilhe o arquivo `CredenciaisOracle.json` publicamente
- **NUNCA** faça commit do `token.json` no Git
- Adicione ao `.gitignore`:
  ```
  CredenciaisOracle.json
  token.json
  ```

## 🐛 Troubleshooting

### Erro: "Nenhum arquivo NFRi encontrado"
- Verifique se o download foi concluído
- Confira a pasta Downloads do usuário

### Erro ao enviar para Google Sheets
- Verifique se o arquivo `CredenciaisOracle.json` está presente
- Refaça o login (delete `token.json` e execute novamente)
- Confirme que a conta tem permissão na planilha

### Cliques não estão funcionando
- Ajuste as coordenadas em `coords` conforme sua tela
- Verifique a resolução da tela
- Use o arquivo `mouse.py` do rpa_oracle para capturar novas coordenadas

## 📝 Licença

Uso interno - Tecumseh
