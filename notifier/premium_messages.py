"""
Sistema de mensajes para promoción y gestión de Premium
Incluye botones de pago, confirmaciones y mensajes promocionales
"""

from typing import Dict, Any, Optional

def format_free_vs_premium_message() -> str:
    """
    Mensaje principal que diferencia usuarios Free vs Premium
    """
    return """🆓 **USUARIO GRATUITO**
• 1 alerta de value bet diaria
• Análisis básico de apuestas
• Acceso limitado a estadísticas

🔥 **VALUE BETS PREMIUM** 🔥
• 🚀 **Alertas ILIMITADAS** de value bets
• 📊 **Análisis completo** de cada apuesta
• 💰 **Gestión avanzada de bankroll**
• 📈 **Estadísticas detalladas** de rendimiento
• ⚡ **Alertas en tiempo real**
• 🎯 **Filtros personalizados** por deporte

💰 **Precio: 50 USD semanales**

🎁 **¡GANA DINERO REFIRIENDO AMIGOS!**
• 10% de comisión por cada referido que pague
• Cada 3 referidos pagos = 1 semana gratis

Elige tu método de pago:"""


def get_payment_keyboard():
    """
    Genera teclado inline con botones de pago
    """
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [
        [
            InlineKeyboardButton(
                "💳 PayPal", 
                url="https://paypal.me/valueapuestasbot/50"  # Reemplazar con tu enlace real
            )
        ],
        [
            InlineKeyboardButton(
                "💎 Tarjeta (Stripe)", 
                url="https://checkout.stripe.com/pay/cs_test_valueapuestas"  # Reemplazar con tu enlace real
            )
        ],
        [
            InlineKeyboardButton(
                "₿ USDT BEP20", 
                callback_data="show_usdt_wallet"
            )
        ],
        [
            InlineKeyboardButton(
                "📞 Soporte/Admin", 
                url="https://t.me/ADMIN_USERNAME"  # Reemplazar con tu usuario admin
            )
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def format_usdt_payment_message() -> str:
    """
    Mensaje con información de pago USDT
    """
    return """💰 **PAGO CON USDT (BEP20)**

📍 **Dirección de billetera:**
`0x1234567890abcdef1234567890abcdef12345678`

💵 **Monto:** 50 USDT
🌐 **Red:** BEP20 (Binance Smart Chain)

⚠️ **IMPORTANTE:**
• Usa solo la red BEP20
• Envía exactamente 50 USDT
• Guarda el hash de transacción

📤 **Después del pago:**
1. Toma captura del comprobante
2. Envía el hash de transacción al soporte
3. Tu Premium se activará en máximo 24 horas

📞 **Soporte:** @ADMIN_USERNAME"""


def format_payment_confirmation_message(payment_method: str) -> str:
    """
    Mensaje de confirmación después de seleccionar método de pago
    
    Args:
        payment_method: Método seleccionado (paypal, stripe, usdt)
    """
    if payment_method.lower() == "usdt":
        return format_usdt_payment_message()
    
    return f"""✅ **PAGO SELECCIONADO: {payment_method.upper()}**

📝 **Instrucciones:**
1. Completa el pago de 50 USD
2. Toma captura del comprobante
3. Envía el comprobante al soporte/admin
4. Tu Premium se activará en máximo 24 horas

📞 **Soporte/Admin:** @ADMIN_USERNAME

⚡ **Tu suscripción Premium incluye:**
• Alertas ILIMITADAS de value bets
• Análisis completo y gestión de bankroll
• Acceso a estadísticas avanzadas
• Soporte prioritario"""


def format_premium_activated_message(user_id: str, weeks: int = 1) -> str:
    """
    Mensaje cuando se activa Premium para un usuario
    
    Args:
        user_id: ID del usuario
        weeks: Semanas de Premium activadas
    """
    return f"""🎉 **¡PREMIUM ACTIVADO!**

✅ Tu suscripción Premium está activa
⏱️ **Duración:** {weeks} semana{'s' if weeks != 1 else ''}
🚀 **Beneficios desbloqueados:**

• 🎯 ALERTAS ILIMITADAS de value bets
• 📊 Análisis completo de apuestas
• 💰 Gestión avanzada de bankroll
• 📈 Estadísticas detalladas
• ⚡ Alertas en tiempo real

💡 **¡No olvides compartir tu link de referidos!**
Usa /mi_link para generar tu enlace y ganar comisiones

¡Disfruta de tu experiencia Premium! 🔥"""


def format_premium_expiry_warning(user_id: str, days_left: int) -> str:
    """
    Mensaje de advertencia de expiración de Premium
    
    Args:
        user_id: ID del usuario
        days_left: Días restantes
    """
    return f"""⚠️ **ADVERTENCIA DE EXPIRACIÓN**

Tu suscripción Premium expira en **{days_left} día{'s' if days_left != 1 else ''}**

🔄 **Para renovar:**
• Usa /premium para ver opciones de pago
• O contacta al soporte/admin

💰 **¿Quieres ganar dinero?**
• Comparte tu link de referidos: /mi_link
• 10% de comisión por cada referido que pague
• Cada 3 referidos = 1 semana gratis

📞 **Soporte:** @ADMIN_USERNAME"""


def format_free_limit_message() -> str:
    """
    Mensaje cuando usuario gratuito alcanza su límite diario
    """
    return """🚫 **LÍMITE ALCANZADO**

Has recibido tu 1 alerta diaria gratuita de hoy.

🔥 **¿Quieres más alertas?**
Upgradea a Premium y recibe:

• 🎯 **ALERTAS ILIMITADAS** (en lugar de 1)
• 📊 **Análisis completo** de cada apuesta
• 💰 **Gestión de bankroll** profesional
• 📈 **Estadísticas avanzadas**

💰 **Solo 50 USD semanales**

🎁 **Bonus:** Gana dinero refiriendo amigos
• 10% comisión por referido que pague
• Cada 3 referidos = 1 semana gratis

Usa /premium para activar tu suscripción 🚀"""


def format_referral_commission_earned(user_id: str, commission_amount: float, total_balance: float, referral_user_id: str) -> str:
    """
    Mensaje cuando usuario gana comisión por referido
    
    Args:
        user_id: ID del usuario que refirió
        commission_amount: Monto de comisión ganada
        total_balance: Saldo total acumulado
        referral_user_id: ID del usuario que fue referido
    """
    return f"""🎉 **¡TU REFERIDO HA PAGADO LA SUSCRIPCIÓN PREMIUM!**

👤 **Referido:** Usuario {referral_user_id[:8]}...
💰 **Comisión ganada:** {commission_amount} USD
💵 **Saldo total acumulado:** {total_balance} USD

💡 **Para retirar tu saldo:**
Escribe al soporte/admin: @ADMIN_USERNAME

🎯 **Sigue refiriendo y gana más:**
• Usa /mi_link para obtener tu enlace único
• 10% de comisión por cada referido que pague
• Cada 3 referidos = 1 semana gratis

¡Felicidades! 🔥"""


def format_free_week_earned(user_id: str, total_paid_referrals: int) -> str:
    """
    Mensaje cuando usuario gana semana gratis por 3 referidos
    
    Args:
        user_id: ID del usuario
        total_paid_referrals: Total de referidos pagos
    """
    return f"""🎉 **¡FELICIDADES! HAS ALCANZADO 3 REFERIDOS PAGOS**

⭐ **Logro desbloqueado:** 3 referidos con suscripción Premium
🎁 **Recompensa:** 1 semana gratis de Premium
📊 **Total de referidos pagos:** {total_paid_referrals}

✅ **Tu semana gratis se ha añadido automáticamente**
⏱️ **Disfruta todos los beneficios Premium sin costo**

🚀 **Sigue refiriendo para más recompensas:**
• Cada 3 referidos adicionales = otra semana gratis
• 10% de comisión en efectivo por cada referido

Usa /mi_link para seguir compartiendo 💰"""


def format_commission_withdrawal_request(user_id: str, current_balance: float) -> str:
    """
    Mensaje de solicitud de retiro de comisiones
    
    Args:
        user_id: ID del usuario
        current_balance: Saldo actual disponible
    """
    from datetime import datetime
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    return f"""💰 **SOLICITUD DE RETIRO**

**Usuario:** {user_id}
**Saldo disponible:** {current_balance} USD
**Fecha:** {current_date}

Para procesar el retiro, contacta al admin con:
• Tu ID de usuario
• Método de pago preferido
• Confirmación del monto

📞 **Admin/Soporte:** @ADMIN_USERNAME

⚠️ **Importante:** Solo se procesan retiros de mínimo 10 USD"""


def format_commission_paid_confirmation(user_id: str, amount_paid: float, payment_method: str) -> str:
    """
    Confirmación de comisión pagada (para enviar al usuario)
    
    Args:
        user_id: ID del usuario
        amount_paid: Monto pagado
        payment_method: Método usado para el pago
    """
    from datetime import datetime
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    return f"""✅ **COMISIÓN PAGADA**

💰 **Monto:** {amount_paid} USD
📤 **Método:** {payment_method}
📅 **Fecha:** {current_date}

Tu saldo de comisiones se ha reiniciado a 0 USD.

🎯 **Sigue refiriendo amigos:**
• Usa /mi_link para generar nuevo enlace
• 10% comisión por cada referido que pague
• Cada 3 referidos = 1 semana gratis

¡Gracias por ser parte de Value Apuestas! 🔥"""