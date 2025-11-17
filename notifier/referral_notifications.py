"""
notifier/referral_notifications.py - Notificaciones del sistema de referidos.
"""
from typing import Dict, Optional
from data.users import get_users_manager


def format_referral_reward_notification(referrer_chat_id: str, new_referral_chat_id: str) -> str:
    """
    Genera notificación cuando un usuario gana semana premium por referido.
    
    Args:
        referrer_chat_id: ID del usuario que refirió
        new_referral_chat_id: ID del nuevo usuario referido
    
    Returns:
        Mensaje de notificación
    """
    users_manager = get_users_manager()
    referrer = users_manager.get_user(referrer_chat_id)
    
    total_referidos = len(referrer.referred_users)
    
    return (
        f"🎉 ¡FELICIDADES! 🎉\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 ¡Nuevo referido registrado!\n"
        f"🏆 Has alcanzado {total_referidos} referidos totales\n\n"
        f"🎁 RECOMPENSA DESBLOQUEADA:\n"
        f"⭐ +1 SEMANA PREMIUM GRATIS\n"
        f"📅 Semana #{referrer.premium_weeks_earned}\n\n"
        f"🌟 BENEFICIOS ACTIVADOS:\n"
        f"✅ Alertas ILIMITADAS (vs 1 gratis)\n"
        f"✅ Análisis completo de valor\n"
        f"✅ Stakes recomendados\n"
        f"✅ Gestión de bankroll\n"
        f"✅ Tracking de ROI\n\n"
        f"♾️  ¡Sigue invitando para más semanas!\n"
        f"👥 Cada 5 referidos = 1 semana premium\n\n"
        f"📲 Usa /mis_referidos para ver estadísticas"
    )


def format_premium_expiry_warning(chat_id: str, days_left: int) -> str:
    """
    Genera notificación de advertencia cuando el premium está por expirar.
    
    Args:
        chat_id: ID del usuario
        days_left: Días restantes de premium
    
    Returns:
        Mensaje de advertencia
    """
    if days_left == 1:
        urgency = "⚠️ ¡ÚLTIMO DÍA!"
        message = "Tu premium expira MAÑANA"
    elif days_left <= 3:
        urgency = "⏰ ¡POCOS DÍAS!"
        message = f"Tu premium expira en {days_left} días"
    else:
        urgency = "📅 Recordatorio"
        message = f"Tu premium expira en {days_left} días"
    
    return (
        f"{urgency}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💎 {message}\n\n"
        f"🔄 RENUEVA GRATIS:\n"
        f"👥 Invita más amigos para extender\n"
        f"🎁 5 referidos = 1 semana premium\n\n"
        f"💳 O UPGRADE PERMANENTE:\n"
        f"💬 Usa /upgrade para más información\n\n"
        f"📲 Usa /referir para tu link de referido\n"
        f"📊 Usa /mis_referidos para ver progreso"
    )


def format_welcome_referral_notification(referrer_chat_id: str) -> str:
    """
    Genera notificación para el referidor cuando alguien usa su código.
    
    Args:
        referrer_chat_id: ID del usuario que refirió
    
    Returns:
        Mensaje de notificación
    """
    users_manager = get_users_manager()
    referrer = users_manager.get_user(referrer_chat_id)
    
    total_referidos = len(referrer.referred_users)
    referidos_faltantes = 5 - (total_referidos % 5)
    
    return (
        f"👥 ¡NUEVO REFERIDO!\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎉 ¡Alguien usó tu código de referido!\n"
        f"📈 Total referidos: {total_referidos}\n\n"
        f"🎯 PROGRESO:\n"
        f"⏳ Faltan {referidos_faltantes} para próxima semana premium\n"
        f"🎁 Cada 5 referidos = 1 semana gratis\n\n"
        f"📲 Sigue compartiendo tu link:\n"
        f"💬 Usa /referir para obtenerlo\n"
        f"📊 Usa /mis_referidos para estadísticas"
    )


def check_and_format_premium_expiry_notifications(days_to_warn: int = 3) -> Dict[str, str]:
    """
    Verifica usuarios con premium por expirar y genera notificaciones.
    
    Args:
        days_to_warn: Días de antelación para avisar
    
    Returns:
        Dict con chat_id como clave y mensaje como valor
    """
    from datetime import datetime, timezone, timedelta
    
    users_manager = get_users_manager()
    notifications = {}
    
    current_time = datetime.now(timezone.utc)
    warning_threshold = current_time + timedelta(days=days_to_warn)
    
    for user in users_manager.users.values():
        if user.premium_expires_at and not user.is_permanent_premium:
            expiry_time = datetime.fromisoformat(user.premium_expires_at)
            
            # Solo notificar si expira dentro del umbral y aún no ha expirado
            if current_time <= expiry_time <= warning_threshold:
                days_left = (expiry_time - current_time).days
                message = format_premium_expiry_warning(user.chat_id, days_left)
                notifications[user.chat_id] = message
    
    return notifications