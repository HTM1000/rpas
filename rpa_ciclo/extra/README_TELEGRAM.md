# Configuração de Notificações Telegram

Este guia explica como configurar notificações do Telegram para receber atualizações do RPA Ciclo em tempo real.

## 🚀 Configuração Rápida

### 1. Criar um Bot no Telegram

1. Abra o Telegram e procure por **@BotFather**
2. Envie o comando `/newbot`
3. Escolha um nome para o bot (ex: "RPA Ciclo Monitor")
4. Escolha um username (ex: "rpa_ciclo_bot")
5. O BotFather enviará um **token** (ex: `8300855810:AAEC4OTval-NLjnquKsd49aOG7b4NJZo5mU`)
6. **COPIE ESSE TOKEN** - você vai precisar dele!

### 2. Obter seu Chat ID

Existem duas formas:

#### Opção A: Usando @userinfobot (Mais Fácil)
1. Procure por **@userinfobot** no Telegram
2. Envie qualquer mensagem para ele
3. Ele responderá com seu **Chat ID** (um número como `123456789`)

#### Opção B: Manualmente
1. Envie qualquer mensagem para o bot que você criou
2. Abra no navegador: `https://api.telegram.org/bot<SEU_TOKEN>/getUpdates`
   - Substitua `<SEU_TOKEN>` pelo token que recebeu do BotFather
3. Procure por `"chat":{"id":123456789` - esse número é seu Chat ID

### 3. Configurar o config.json

Abra o arquivo `config.json` e adicione/edite a seção `telegram`:

```json
{
  "telegram": {
    "bot_token": "8300855810:AAEC4OTval-NLjnquKsd49aOG7b4NJZo5mU",
    "chat_id": "123456789",
    "habilitado": true
  }
}
```

**Importante:**
- `bot_token`: Cole o token que recebeu do BotFather
- `chat_id`: Cole o ID que obteve do @userinfobot
- `habilitado`: Mantenha como `true` para receber notificações

### 4. Instalar a biblioteca requests (se necessário)

O módulo de notificação usa a biblioteca `requests` do Python:

```bash
pip install requests
```

## 📱 Tipos de Notificações

O sistema enviará as seguintes notificações:

### 1. Início do Ciclo
```
🚀 CICLO INICIADO

🔢 Ciclo #1

⏰ 25/10/2025 14:30:00
```

### 2. Início de Processamento de Item
```
🔵 PROCESSANDO ITEM

📋 Linha: 5
🔹 Item: 12345678
📦 Quantidade: 10
📍 Sub Origem: EST
📍 Sub Destino: PRO

⏰ 14:32:15
```

### 3. Item Concluído com Sucesso
```
✅ ITEM CONCLUÍDO

📋 Linha: 5
🔹 Item: 12345678

⏰ 14:32:45
```

### 4. Item com Erro
```
❌ ERRO NO ITEM

📋 Linha: 5
🔹 Item: 12345678
⚠️ Erro: Erro Oracle: produto inválido

⏰ 14:32:45
```

### 5. Item Pulado (já processado)
```
⏭️ ITEM PULADO

📋 Linha: 5
🔹 Item: 12345678
📝 Motivo: Já processado anteriormente (encontrado no cache)

⏰ 14:32:45
```

### 6. Ciclo Concluído
```
✅ CICLO CONCLUÍDO

🔢 Ciclo #1
✅ Processados: 15
❌ Erros: 2

⏰ 25/10/2025 14:45:00
```

### 7. Erro Crítico
```
🛑 ERRO CRÍTICO

⚠️ Sistema parado!

📝 Erro: Timeout Oracle - sistema não responde

⏰ 25/10/2025 14:50:00
```

## 🔧 Desabilitar Notificações

Para desabilitar as notificações temporariamente sem remover a configuração:

```json
{
  "telegram": {
    "bot_token": "SEU_TOKEN",
    "chat_id": "SEU_CHAT_ID",
    "habilitado": false
  }
}
```

Ou simplesmente deixe os campos vazios:

```json
{
  "telegram": {
    "bot_token": "",
    "chat_id": "",
    "habilitado": false
  }
}
```

## ⚠️ Segurança

**IMPORTANTE:**
- **NUNCA compartilhe seu bot token** - qualquer pessoa com esse token pode enviar mensagens usando seu bot
- **NÃO commite o config.json com tokens** para repositórios públicos
- O arquivo `config.json` já está no `.gitignore` para evitar vazamento de credenciais

## 🧪 Testando a Configuração

Após configurar, execute o RPA Ciclo. Você deverá receber uma notificação de "CICLO INICIADO" no Telegram.

Se não receber:
1. Verifique se o `bot_token` e `chat_id` estão corretos
2. Verifique se `habilitado` está como `true`
3. Verifique se você enviou pelo menos uma mensagem para o bot
4. Verifique se a biblioteca `requests` está instalada: `pip install requests`
5. Verifique os logs do RPA para erros relacionados ao Telegram

## 📋 Troubleshooting

### Erro: "Telegram não configurado"
- Verifique se `bot_token` e `chat_id` não estão vazios no `config.json`
- Verifique se `habilitado` está como `true`

### Erro: "401 Unauthorized"
- Seu `bot_token` está incorreto
- Solicite um novo token do @BotFather

### Erro: "400 Bad Request: chat not found"
- Seu `chat_id` está incorreto
- Certifique-se de enviar uma mensagem para o bot primeiro
- Verifique o Chat ID usando @userinfobot

### Mensagens não chegam
- Verifique se você iniciou uma conversa com o bot (envie `/start`)
- Verifique se o bot não está bloqueado
- Tente enviar uma mensagem de teste diretamente pela API:
  ```
  https://api.telegram.org/bot<SEU_TOKEN>/sendMessage?chat_id=<SEU_CHAT_ID>&text=Teste
  ```

## 📚 Mais Informações

- [Documentação oficial do Telegram Bot API](https://core.telegram.org/bots/api)
- [Como criar um bot no Telegram](https://core.telegram.org/bots#6-botfather)
