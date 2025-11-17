"""Bot temporal para capturar chat ID y enviar mensaje"""
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os
from dotenv import load_dotenv

load_dotenv()

async def handle_any_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Captura cualquier mensaje y envía respuesta"""
    chat_id = update.effective_chat.id
    username = update.effective_user.username or "N/A"
    
    print(f"\n✅ CHAT ID DETECTADO: {chat_id}")
    print(f"   Username: @{username}")
    
    await update.message.reply_text(
        "🎉 ¡PERFECTO! Tu bot está funcionando.\n\n"
        f"📱 Tu Chat ID: {chat_id}\n"
        "✅ Configurado como PREMIUM\n\n"
        "Ahora ejecuta:\n"
        "`python main.py`\n\n"
        "Para recibir value bets automáticamente cada hora.",
        parse_mode='Markdown'
    )
    
    # Guardar chat ID en archivo
    with open('data/detected_chat_id.txt', 'w') as f:
        f.write(str(chat_id))
    
    print(f"\n💾 Chat ID guardado en data/detected_chat_id.txt")
    print(f"✅ Mensaje enviado exitosamente!")
    print(f"\n🚀 Ahora puedes ejecutar: python main.py\n")
    
    # Detener el bot después de responder
    await asyncio.sleep(2)
    context.application.stop_running()

async def main():
    print("\nBot temporal iniciado...")
    print("Envia CUALQUIER mensaje al bot en Telegram")
    print("   (por ejemplo: 'hola', '/start', '/stats', etc.)\n")
    
    app = Application.builder().token(os.getenv('BOT_TOKEN')).build()
    
    # Capturar CUALQUIER mensaje
    app.add_handler(MessageHandler(filters.ALL, handle_any_message))
    
    # Iniciar
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    # Esperar hasta que se detenga
    await app.updater.stop()
    await app.stop()
    await app.shutdown()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Bot detenido por usuario")
