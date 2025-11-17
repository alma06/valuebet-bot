"""
admin_commands.py - Comandos administrativos para gestión de Premium y comisiones
"""

from typing import Dict, Optional
from data.users import get_users_manager
from notifier.premium_messages import format_commission_paid_confirmation


async def admin_activar_premium(admin_id: str, user_id: str, weeks: int = 1) -> str:
    """
    Comando admin para activar Premium manualmente tras recibir comprobante
    
    Args:
        admin_id: ID del administrador 
        user_id: ID del usuario a activar
        weeks: Semanas de Premium a activar
    
    Returns:
        Mensaje de confirmación
    """
    try:
        # Verificar que es admin (lista de IDs autorizados)
        ADMIN_IDS = ["ADMIN_USER_ID_1", "ADMIN_USER_ID_2"]  # Configurar IDs reales
        
        if admin_id not in ADMIN_IDS:
            return "❌ No tienes permisos de administrador"
        
        users_manager = get_users_manager()
        user = users_manager.get_user(user_id)
        
        # Añadir semanas de Premium
        user.add_free_premium_week(weeks)
        
        # Guardar cambios
        users_manager.save()
        
        return (f"✅ **PREMIUM ACTIVADO**\n\n"
               f"👤 **Usuario:** {user_id}\n"
               f"⏰ **Duración:** {weeks} semana(s)\n"
               f"📅 **Expira:** {user.suscripcion_fin}\n\n"
               f"El usuario ha sido notificado automáticamente.")
        
    except Exception as e:
        return f"❌ Error al activar Premium: {str(e)}"


async def admin_pagar_comision(admin_id: str, user_id: str, payment_method: str) -> str:
    """
    Comando admin para marcar comisión como pagada
    
    Args:
        admin_id: ID del administrador
        user_id: ID del usuario 
        payment_method: Método usado (PayPal, USDT, etc.)
    
    Returns:
        Mensaje de confirmación
    """
    try:
        # Verificar que es admin
        ADMIN_IDS = ["ADMIN_USER_ID_1", "ADMIN_USER_ID_2"]  # Configurar IDs reales
        
        if admin_id not in ADMIN_IDS:
            return "❌ No tienes permisos de administrador"
        
        users_manager = get_users_manager()
        user = users_manager.get_user(user_id)
        
        if user.saldo_comision <= 0:
            return f"❌ El usuario {user_id} no tiene saldo disponible"
        
        # Obtener saldo actual
        amount_to_pay = user.saldo_comision
        
        # Marcar como pagado (reinicia saldo)
        payment_info = user.pagar_comision()
        
        # Guardar cambios
        users_manager.save()
        
        # Mensaje para el admin
        admin_msg = (f"✅ **COMISIÓN PAGADA**\n\n"
                    f"👤 **Usuario:** {user_id}\n"
                    f"💰 **Monto:** ${amount_to_pay:.0f} USD\n"
                    f"💳 **Método:** {payment_method}\n"
                    f"📅 **Fecha:** {payment_info['payment_date']}\n\n"
                    f"El usuario ha sido notificado automáticamente.")
        
        return admin_msg
        
    except Exception as e:
        return f"❌ Error al procesar pago: {str(e)}"


async def admin_stats_user(admin_id: str, user_id: str) -> str:
    """
    Comando admin para ver estadísticas detalladas de un usuario
    
    Args:
        admin_id: ID del administrador
        user_id: ID del usuario a consultar
    
    Returns:
        Estadísticas del usuario
    """
    try:
        # Verificar que es admin
        ADMIN_IDS = ["ADMIN_USER_ID_1", "ADMIN_USER_ID_2"]  # Configurar IDs reales
        
        if admin_id not in ADMIN_IDS:
            return "❌ No tienes permisos de administrador"
        
        users_manager = get_users_manager()
        user = users_manager.get_user(user_id)
        
        # Calcular estadísticas
        is_premium = user.is_subscription_active()
        premium_status = "✅ ACTIVO" if is_premium else "❌ INACTIVO"
        premium_expiry = user.suscripcion_fin if user.suscripcion_fin else "N/A"
        
        return (f"📊 **ESTADÍSTICAS DE USUARIO**\n"
               f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
               f"👤 **ID:** {user_id}\n"
               f"📱 **Chat ID:** {user.chat_id}\n"
               f"💎 **Premium:** {premium_status}\n"
               f"📅 **Expira:** {premium_expiry}\n\n"
               f"💰 **COMISIONES:**\n"
               f"• Saldo actual: ${user.saldo_comision:.2f} USD\n"
               f"• Total ganado: ${user.total_commission_earned:.2f} USD\n"
               f"• Referidos pagos: {user.referrals_paid}\n"
               f"• Semanas gratis ganadas: {user.free_weeks_earned}\n\n"
               f"🔗 **REFERIDOS (Sistema anterior):**\n"
               f"• Código: {user.referral_code}\n"
               f"• Referidos totales: {len(user.referred_users)}\n"
               f"• Semanas ganadas: {user.premium_weeks_earned}\n"
               f"• Referido por: {user.referrer_id if user.referrer_id else 'Ninguno'}")
        
    except Exception as e:
        return f"❌ Error al obtener estadísticas: {str(e)}"


async def admin_list_pending_withdrawals(admin_id: str) -> str:
    """
    Lista usuarios con saldo de comisión pendiente de pago
    
    Args:
        admin_id: ID del administrador
    
    Returns:
        Lista de usuarios con saldo pendiente
    """
    try:
        # Verificar que es admin
        ADMIN_IDS = ["ADMIN_USER_ID_1", "ADMIN_USER_ID_2"]  # Configurar IDs reales
        
        if admin_id not in ADMIN_IDS:
            return "❌ No tienes permisos de administrador"
        
        users_manager = get_users_manager()
        pending_users = []
        
        for user in users_manager.users.values():
            if user.saldo_comision > 0:
                pending_users.append({
                    'user_id': user.chat_id,
                    'balance': user.saldo_comision,
                    'total_earned': user.total_commission_earned,
                    'referrals': user.referrals_paid
                })
        
        if not pending_users:
            return "✅ No hay comisiones pendientes de pago"
        
        # Ordenar por saldo descendente
        pending_users.sort(key=lambda x: x['balance'], reverse=True)
        
        msg = "💰 **COMISIONES PENDIENTES**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        total_pending = 0
        for i, user_data in enumerate(pending_users[:10]):  # Máximo 10
            user_id = user_data['user_id']
            balance = user_data['balance']
            total_pending += balance
            
            msg += (f"{i+1}. **Usuario:** {user_id}\n"
                   f"   💵 Saldo: ${balance:.2f} USD\n"
                   f"   👥 Referidos: {user_data['referrals']}\n\n")
        
        if len(pending_users) > 10:
            msg += f"... y {len(pending_users) - 10} usuarios más\n\n"
        
        msg += f"🎯 **TOTAL PENDIENTE:** ${total_pending:.2f} USD"
        
        return msg
        
    except Exception as e:
        return f"❌ Error al obtener pendientes: {str(e)}"


# Mapeo de comandos administrativos
ADMIN_COMMAND_HANDLERS = {
    "/admin_activar": admin_activar_premium,
    "/admin_pagar": admin_pagar_comision, 
    "/admin_stats": admin_stats_user,
    "/admin_pendientes": admin_list_pending_withdrawals
}


async def process_admin_command(admin_id: str, command: str, args: str = "") -> str:
    """
    Procesa comandos administrativos
    
    Args:
        admin_id: ID del administrador
        command: Comando a ejecutar
        args: Argumentos del comando
    
    Returns:
        Respuesta del comando
    """
    handler = ADMIN_COMMAND_HANDLERS.get(command)
    
    if not handler:
        return f"❌ Comando administrativo desconocido: {command}"
    
    # Parsear argumentos según el comando
    if command == "/admin_activar":
        # Formato: /admin_activar user_id [weeks]
        parts = args.split()
        if len(parts) < 1:
            return "❌ Uso: /admin_activar <user_id> [weeks]"
        
        user_id = parts[0]
        weeks = int(parts[1]) if len(parts) > 1 else 1
        return await handler(admin_id, user_id, weeks)
        
    elif command == "/admin_pagar":
        # Formato: /admin_pagar user_id payment_method
        parts = args.split(' ', 1)
        if len(parts) < 2:
            return "❌ Uso: /admin_pagar <user_id> <payment_method>"
        
        user_id = parts[0]
        payment_method = parts[1]
        return await handler(admin_id, user_id, payment_method)
        
    elif command == "/admin_stats":
        # Formato: /admin_stats user_id
        if not args.strip():
            return "❌ Uso: /admin_stats <user_id>"
        
        return await handler(admin_id, args.strip())
        
    elif command == "/admin_pendientes":
        # Sin argumentos
        return await handler(admin_id)
    
    return f"❌ Error procesando comando {command}"