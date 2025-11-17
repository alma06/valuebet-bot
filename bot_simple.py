"""
bot_simple.py - Bot básico de Telegram para recibir comandos
"""
import os
import asyncio
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    user_id = update.effective_user.id
    await update.message.reply_text(
        f"✅ **Value Bet Bot Activado**\n\n"
        f"👤 Tu ID: `{user_id}`\n"
        f"🎯 Recibirás alertas automáticas cuando encuentre value bets\n\n"
        f"📊 El bot analiza:\n"
        f"• NBA Basketball\n"
        f"• Soccer (EPL, La Liga)\n"
        f"• MLB Baseball\n\n"
        f"🔄 Actualización: cada 10 minutos\n"
        f"⏰ Alertas: cuando el evento esté < 4 horas\n\n"
        f"✅ Sistema profesional con análisis avanzado activo"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /status"""
    await update.message.reply_text(
        "✅ **Bot en línea**\n\n"
        "🔄 Monitoreando eventos 24/7\n"
        "📊 Análisis profesional activo\n"
        "⏰ Próxima actualización: < 10 minutos"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help"""
    await update.message.reply_text(
        "**Comandos disponibles:**\n\n"
        "/start - Activar bot\n"
        "/status - Ver estado del bot\n"
        "/help - Ver esta ayuda\n\n"
        "Las alertas llegan automáticamente cuando el bot encuentra value bets."
    )

async def main():
    """Iniciar bot"""
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("help", help_command))
    
    logger.info("Bot simple iniciado")
    await app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    asyncio.run(main())
