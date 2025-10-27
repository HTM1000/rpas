"""
Módulo de notificação Telegram para RPA Ciclo
Envia logs de processamento por item para o Telegram
"""

import requests
import json
from datetime import datetime

class TelegramNotifier:
    def __init__(self, bot_token=None, chat_id=None):
        """
        Inicializa o notificador Telegram

        Args:
            bot_token: Token do bot do Telegram (obtido via @BotFather)
            chat_id: ID do chat/usuário que receberá as mensagens (pode ser string ou int)
        """
        self.bot_token = bot_token

        # Converter chat_id para string se necessário (Telegram aceita string ou int)
        if chat_id is not None:
            self.chat_id = str(chat_id)
        else:
            self.chat_id = None

        # Enabled se ambos estiverem presentes e não vazios
        self.enabled = bool(bot_token and chat_id and str(bot_token).strip() and str(chat_id).strip())

    def enviar_mensagem(self, mensagem, parse_mode="HTML"):
        """
        Envia mensagem para o Telegram

        Args:
            mensagem: Texto da mensagem
            parse_mode: Formato da mensagem (HTML ou Markdown)

        Returns:
            bool: True se enviado com sucesso
        """
        if not self.enabled:
            return False

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": mensagem,
                "parse_mode": parse_mode
            }

            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                return True
            else:
                return False

        except:
            return False

    def notificar_inicio_item(self, linha, item, quantidade, sub_o, sub_d):
        """
        Notifica início de processamento de um item

        Args:
            linha: Número da linha no Google Sheets
            item: Código do item
            quantidade: Quantidade a processar
            sub_o: Subinventário origem
            sub_d: Subinventário destino
        """
        if not self.enabled:
            return False

        mensagem = f"""
🔵 <b>PROCESSANDO ITEM</b>

📋 <b>Linha:</b> {linha}
🔹 <b>Item:</b> {item}
📦 <b>Quantidade:</b> {quantidade}
📍 <b>Sub Origem:</b> {sub_o}
📍 <b>Sub Destino:</b> {sub_d}

⏰ {datetime.now().strftime('%H:%M:%S')}
"""
        return self.enviar_mensagem(mensagem.strip())

    def notificar_sucesso_item(self, linha, item, mensagem_extra=""):
        """
        Notifica sucesso no processamento de um item

        Args:
            linha: Número da linha no Google Sheets
            item: Código do item
            mensagem_extra: Informação adicional (opcional)
        """
        if not self.enabled:
            return False

        msg = f"""
✅ <b>ITEM CONCLUÍDO</b>

📋 <b>Linha:</b> {linha}
🔹 <b>Item:</b> {item}
"""
        if mensagem_extra:
            msg += f"\n💬 {mensagem_extra}"

        msg += f"\n\n⏰ {datetime.now().strftime('%H:%M:%S')}"

        return self.enviar_mensagem(msg.strip())

    def notificar_erro_item(self, linha, item, erro):
        """
        Notifica erro no processamento de um item

        Args:
            linha: Número da linha no Google Sheets
            item: Código do item
            erro: Descrição do erro
        """
        if not self.enabled:
            return False

        mensagem = f"""
❌ <b>ERRO NO ITEM</b>

📋 <b>Linha:</b> {linha}
🔹 <b>Item:</b> {item}
⚠️ <b>Erro:</b> {erro}

⏰ {datetime.now().strftime('%H:%M:%S')}
"""
        return self.enviar_mensagem(mensagem.strip())

    def notificar_skip_item(self, linha, item, motivo):
        """
        Notifica que um item foi pulado

        Args:
            linha: Número da linha no Google Sheets
            item: Código do item
            motivo: Motivo do skip
        """
        if not self.enabled:
            return False

        mensagem = f"""
⏭️ <b>ITEM PULADO</b>

📋 <b>Linha:</b> {linha}
🔹 <b>Item:</b> {item}
📝 <b>Motivo:</b> {motivo}

⏰ {datetime.now().strftime('%H:%M:%S')}
"""
        return self.enviar_mensagem(mensagem.strip())

    def notificar_ciclo_inicio(self, ciclo_numero):
        """
        Notifica início de um ciclo

        Args:
            ciclo_numero: Número do ciclo
        """
        if not self.enabled:
            return False

        mensagem = f"""
🚀 <b>CICLO INICIADO</b>

🔢 <b>Ciclo #{ciclo_numero}</b>

⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
"""
        return self.enviar_mensagem(mensagem.strip())

    def notificar_ciclo_concluido(self, ciclo_numero, total_processados, total_erros):
        """
        Notifica conclusão de um ciclo

        Args:
            ciclo_numero: Número do ciclo
            total_processados: Total de itens processados com sucesso
            total_erros: Total de itens com erro
        """
        if not self.enabled:
            return False

        status_icon = "✅" if total_erros == 0 else "⚠️"

        mensagem = f"""
{status_icon} <b>CICLO CONCLUÍDO</b>

🔢 <b>Ciclo #{ciclo_numero}</b>
✅ <b>Processados:</b> {total_processados}
❌ <b>Erros:</b> {total_erros}

⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
"""
        return self.enviar_mensagem(mensagem.strip())

    def notificar_erro_critico(self, erro_descricao):
        """
        Notifica erro crítico que parou o sistema

        Args:
            erro_descricao: Descrição do erro crítico
        """
        if not self.enabled:
            return False

        mensagem = f"""
🛑 <b>ERRO CRÍTICO</b>

⚠️ <b>Sistema parado!</b>

📝 <b>Erro:</b> {erro_descricao}

⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
"""
        return self.enviar_mensagem(mensagem.strip())


def carregar_config_telegram():
    """
    Carrega configurações do Telegram do arquivo config.json

    Returns:
        dict: Configurações do Telegram ou None se não existir
    """
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            return config.get("telegram", None)
    except:
        return None


# Instância global do notificador (será inicializada no main_ciclo.py)
telegram_notifier = None

def inicializar_telegram():
    """
    Inicializa o notificador Telegram com base no config.json

    Returns:
        TelegramNotifier: Instância do notificador
    """
    global telegram_notifier

    config = carregar_config_telegram()

    if config:
        bot_token = config.get("bot_token")
        chat_id = config.get("chat_id")

        # Debug: mostrar o que foi carregado
        print(f"[DEBUG] Config Telegram carregado:")
        print(f"  bot_token type: {type(bot_token)}, value: {bot_token}")
        print(f"  chat_id type: {type(chat_id)}, value: {chat_id}")
        print(f"  bot_token and chat_id = {bool(bot_token and chat_id)}")

        telegram_notifier = TelegramNotifier(bot_token, chat_id)

        print(f"[DEBUG] Notificador criado:")
        print(f"  enabled: {telegram_notifier.enabled}")
    else:
        print("[DEBUG] Config do Telegram não encontrado no config.json")
        telegram_notifier = TelegramNotifier()

    return telegram_notifier
