import asyncio
from notifier.telegram import TelegramNotifier
from dotenv import load_dotenv
import os

load_dotenv()

async def test_alert():
    bot_token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    
    notifier = TelegramNotifier(bot_token)
    
    message = """ **ALERTA DE PRUEBA - VALUE BET BOT**

 **Basketball NBA**
 Cleveland Cavaliers vs Milwaukee Bucks
 2025-11-17 22:00 UTC

 **ANÁLISIS:**
 Pronóstico: Cleveland Cavaliers
 Cuota: 2.10
 Probabilidad estimada: 65%
 Value: 1.365

**RAZONAMIENTO:**
 Cleveland tiene ventaja de local
 Mejor forma reciente (4-1 últimos 5)
 Milwaukee viene de 2 derrotas

 **Casa de apuestas:** DraftKings

**STAKE RECOMENDADO:** $50 (5% bankroll)

---
 Sistema profesional activo
 Análisis con modelo mejorado"""
    
    success = await notifier.send_message(chat_id, message)
    
    if success:
        print(" Alerta de prueba enviada correctamente a Telegram")
        print(f" Revisa tu Telegram (chat_id: {chat_id})")
    else:
        print(" Error al enviar alerta")

asyncio.run(test_alert())
