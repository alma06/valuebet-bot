"""
bot_minimal.py - Bot de Telegram mínimo para pruebas en Render
"""
from telegram.ext import Application, CommandHandler
import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "AQUI_TU_TOKEN")

def start(update, context):
    update.message.reply_text("¡Bot mínimo funcionando!")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling(allowed_updates=None, close_loop=False)

if __name__ == "__main__":
    main()
