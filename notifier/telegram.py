"""Simple Telegram notifier using Bot API HTTP endpoint.

Sends Markdown-formatted messages to a chat_id.
"""
import os
import aiohttp

class TelegramNotifier:
    def __init__(self, token: str = None, chat_id: str = None):
        # Use provided token/chat_id or read from environment variables BOT_TOKEN/CHAT_ID (fallback TELEGRAM_*)
        self.token = token or os.getenv('BOT_TOKEN') or os.getenv('TELEGRAM_TOKEN')
        self.chat_id = chat_id or os.getenv('CHAT_ID') or os.getenv('TELEGRAM_CHAT_ID')
        if not self.token:
            print('Warning: TELEGRAM token not set; messages will not be sent to Telegram.')

    async def send_message(self, text: str, chat_id: str = None):
        """Send a message to Telegram.
        
        Args:
            text: Message text
            chat_id: Target chat ID (optional, uses default if not provided)
        """
        target_chat = chat_id or self.chat_id
        
        if not self.token or not target_chat:
            print('--- Mensaje (no Telegram configurado) ---')
            print(text)
            print('----------------------------------------')
            return
        
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            'chat_id': target_chat,
            'text': text,
            'parse_mode': 'Markdown'
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    print(f"Telegram send failed: {resp.status} {body}")
                else:
                    # success
                    pass
