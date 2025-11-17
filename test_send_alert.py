"""
test_send_alert.py - Enviar alerta de prueba al usuario
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from notifier.telegram import TelegramNotifier
from dotenv import load_dotenv
import os

load_dotenv()

async def send_test_alert():
    """Envía una alerta de prueba"""
    
    bot_token = os.getenv('BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID', '5901833301')
    
    print(f"\n🔔 Enviando alerta de prueba...")
    print(f"   Bot Token: {bot_token[:20]}...")
    print(f"   Chat ID: {chat_id}")
    
    notifier = TelegramNotifier(bot_token)
    
    # Mensaje de prueba
    message = """
🎯 **ALERTA DE PRUEBA - VALUE BET**

⚽ **Real Madrid vs Barcelona**
🏆 LaLiga

📊 **Análisis:**
• Cuota: 2.05
• Prob. estimada: 55%
• Value: 12.8%
• Kelly: 4.2%

💰 **Apuesta recomendada:**
Stake: $42 (4.2% bankroll)
Ganancia potencial: $44.10

📈 Sistema mejorado activo ✅
🔥 Esta es una alerta de prueba

Para ver estadísticas reales: /stats
"""
    
    try:
        await notifier.send_message(chat_id, message)
        print("✅ Alerta enviada exitosamente!")
        print(f"\n💡 Revisa tu Telegram (@{chat_id})")
    except Exception as e:
        print(f"❌ Error enviando alerta: {e}")
        print("\nPosibles causas:")
        print("1. Bot token incorrecto")
        print("2. Chat ID incorrecto") 
        print("3. No has iniciado conversación con el bot (/start)")

if __name__ == "__main__":
    asyncio.run(send_test_alert())
