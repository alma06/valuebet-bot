"""Test directo con la librería de telegram"""
import asyncio
from telegram import Bot
import os
from dotenv import load_dotenv

load_dotenv()

async def test():
    bot = Bot(token=os.getenv('BOT_TOKEN'))
    
    # Primero obtener info del bot
    me = await bot.get_me()
    print(f"Bot activo: @{me.username}")
    
    # Obtener updates recientes para ver tu chat_id real
    updates = await bot.get_updates()
    
    if updates:
        print(f"\n✅ {len(updates)} mensajes recientes:")
        for u in updates[-5:]:  # últimos 5
            if u.message:
                chat_id = u.message.chat.id
                username = u.message.chat.username
                text = u.message.text[:50] if u.message.text else "N/A"
                print(f"   Chat ID: {chat_id} (@{username}): {text}")
        
        # Usar el chat_id más reciente
        last_chat_id = updates[-1].message.chat.id
        print(f"\n📤 Enviando mensaje a: {last_chat_id}")
        
        await bot.send_message(
            chat_id=last_chat_id,
            text="🎉 ¡Alerta de prueba exitosa!\n\nTu bot está funcionando correctamente.\n\n✅ Ahora recibirás value bets automáticamente."
        )
        print("✅ Mensaje enviado! Revisa tu Telegram")
    else:
        print("❌ No hay updates. ¿Enviaste /start al bot?")

asyncio.run(test())
