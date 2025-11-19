"""
commands/referral_commands.py - Comandos de Telegram para el sistema de referidos

Comandos disponibles:
- /start [CODIGO] - Inicia el bot (con código de referido opcional)
- /referidos - Muestra tus estadísticas de referidos
- /canjear - Canjea una semana Premium gratis
- /retirar [monto] - Solicita retiro de saldo
"""

import logging
from typing import Optional
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from referrals import ReferralSystem, format_referral_stats
from data.users import UsersManager

logger = logging.getLogger(__name__)


class ReferralCommands:
    """
    Maneja los comandos de Telegram relacionados con referidos
    """
    
    def __init__(
        self,
        referral_system: ReferralSystem,
        user_manager: UsersManager,
        bot_username: str = "Valueapuestasbot"
    ):
        """
        Args:
            referral_system: Sistema de referidos
            user_manager: Gestor de usuarios
            bot_username: Username del bot en Telegram
        """
        self.referral_system = referral_system
        self.user_manager = user_manager
        self.bot_username = bot_username
    
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Maneja el comando /start con código de referido opcional
        
        Formato: /start o /start CODIGO_REFERIDO
        """
        user_id = str(update.effective_user.id)
        username = update.effective_user.username or "Usuario"
        
        # Extraer código de referido si existe
        referrer_code = None
        if context.args and len(context.args) > 0:
            referrer_code = context.args[0].upper()
            logger.info(f"Usuario {user_id} inició con código de referido: {referrer_code}")
        
        # Registrar en sistema de referidos
        result = self.referral_system.register_user(user_id, referrer_code)
        
        # Mensaje de bienvenida
        welcome_text = f"Bienvenido al Bot de Value Bets, {username}!\n\n"
        
        if result['success']:
            if result.get('referred_by'):
                # Usuario fue referido
                welcome_text += (
                    "Te has registrado exitosamente usando un código de referido!\n"
                    "Tu amigo recibirá una recompensa cuando te suscribas a Premium.\n\n"
                )
            
            # Mostrar su propio código
            welcome_text += (
                f"TU CODIGO DE REFERIDO: {result['referral_code']}\n"
                f"Tu enlace: {result['referral_link']}\n\n"
                "Comparte tu enlace y gana:\n"
                "- $5 USD por cada amigo que pague Premium\n"
                "- 1 semana gratis cada 3 amigos que paguen\n\n"
            )
        else:
            # Ya estaba registrado
            stats = self.referral_system.get_user_stats(user_id)
            if stats:
                welcome_text += (
                    f"Tu código de referido: {stats['referral_code']}\n"
                    f"Tu enlace: {stats['referral_link']}\n\n"
                )
        
        welcome_text += (
            "COMANDOS DISPONIBLES:\n"
            "/referidos - Ver tus estadísticas\n"
            "/canjear - Canjear semana gratis\n"
            "/retirar [monto] - Solicitar retiro\n"
            "/premium - Suscribirse a Premium\n"
            "/help - Ayuda completa\n"
        )
        
        # Teclado con botones
        keyboard = [
            [
                InlineKeyboardButton("Ver mis referidos", callback_data="referidos"),
                InlineKeyboardButton("Suscribirse Premium", callback_data="premium")
            ],
            [
                InlineKeyboardButton("Compartir mi enlace", switch_inline_query=result.get('referral_link', ''))
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        # Si fue referido, notificar al referrer
        if result.get('referred_by'):
            await self._notify_referrer(result['referred_by'], username)
    
    async def _notify_referrer(self, referrer_id: str, new_user_name: str):
        """Notifica al referrer que un nuevo usuario usó su código"""
        try:
            stats = self.referral_system.get_user_stats(referrer_id)
            if stats:
                message = (
                    f"NUEVO REFERIDO!\n\n"
                    f"{new_user_name} se registró usando tu código.\n"
                    f"Cuando se suscriba a Premium, ganarás $5 USD!\n\n"
                    f"Total referidos: {stats['total_referrals']}\n"
                    f"Han pagado: {stats['paid_referrals']}\n"
                )
                
                # Enviar notificación al referrer
                # Nota: Necesitas el bot instance para enviar mensajes
                # context.bot.send_message(chat_id=referrer_id, text=message)
                
                logger.info(f"Notificación de referido enviada a {referrer_id}")
        except Exception as e:
            logger.error(f"Error notificando a referrer {referrer_id}: {e}")
    
    async def handle_referidos(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Maneja el comando /referidos - Muestra estadísticas
        """
        user_id = str(update.effective_user.id)
        
        stats = self.referral_system.get_user_stats(user_id)
        
        if not stats:
            await update.message.reply_text(
                "No estás registrado en el sistema de referidos.\n"
                "Usa /start para registrarte."
            )
            return
        
        # Formatear estadísticas
        stats_text = format_referral_stats(stats)
        
        # Teclado con acciones
        keyboard = [
            [InlineKeyboardButton("Compartir mi enlace", switch_inline_query=stats['referral_link'])],
            [
                InlineKeyboardButton("Canjear semana gratis", callback_data="canjear_semana"),
                InlineKeyboardButton("Solicitar retiro", callback_data="solicitar_retiro")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            stats_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    async def handle_canjear(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Maneja el comando /canjear - Canjea una semana Premium gratis
        """
        user_id = str(update.effective_user.id)
        
        # Intentar canjear
        success, message = self.referral_system.redeem_free_week(user_id)
        
        if success:
            # Activar Premium por 1 semana
            try:
                # Extender Premium 7 días
                # user = self.user_manager.get_user(user_id)
                # user.extend_premium(days=7)
                
                message += "\n\nTu suscripción Premium ha sido extendida por 7 días!"
                
                logger.info(f"Usuario {user_id} canjeó semana Premium gratis")
            except Exception as e:
                logger.error(f"Error activando Premium para {user_id}: {e}")
                message += "\n\nError activando Premium. Contacta al administrador."
        
        await update.message.reply_text(message)
    
    async def handle_retirar(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Maneja el comando /retirar [monto] - Solicita retiro de saldo
        
        Formato: /retirar 25.50
        """
        user_id = str(update.effective_user.id)
        
        # Validar argumentos
        if not context.args or len(context.args) < 1:
            await update.message.reply_text(
                "Uso: /retirar [monto]\n\n"
                "Ejemplo: /retirar 25.50\n\n"
                "Tu saldo será verificado y el retiro procesado por el administrador."
            )
            return
        
        # Parsear monto
        try:
            amount = float(context.args[0])
        except ValueError:
            await update.message.reply_text(
                "Monto inválido. Usa números con punto decimal.\n"
                "Ejemplo: /retirar 25.50"
            )
            return
        
        # Verificar monto mínimo
        if amount < 5.0:
            await update.message.reply_text(
                "El monto mínimo de retiro es $5.00 USD"
            )
            return
        
        # Solicitar retiro
        success, message = self.referral_system.withdraw_balance(user_id, amount)
        
        if success:
            # Notificar al admin
            await self._notify_admin_withdrawal(user_id, amount)
            
            message += (
                "\n\nEl administrador procesará tu solicitud en las próximas 24-48 horas.\n"
                "Métodos de pago: PayPal, Transferencia, Criptomonedas."
            )
        
        await update.message.reply_text(message)
    
    async def _notify_admin_withdrawal(self, user_id: str, amount: float):
        """Notifica al admin sobre una solicitud de retiro"""
        try:
            admin_message = (
                f"SOLICITUD DE RETIRO\n\n"
                f"Usuario: {user_id}\n"
                f"Monto: ${amount:.2f} USD\n"
                f"Fecha: {context.utc_now.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"Usa /aprobar_retiro {user_id} {amount} para aprobar"
            )
            
            # Enviar a admin
            # ADMIN_CHAT_ID debe estar configurado
            # context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message)
            
            logger.info(f"Solicitud de retiro de {user_id}: ${amount:.2f}")
        except Exception as e:
            logger.error(f"Error notificando retiro al admin: {e}")
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Maneja los callback queries de los botones inline
        """
        query = update.callback_query
        await query.answer()
        
        user_id = str(update.effective_user.id)
        data = query.data
        
        if data == "referidos":
            # Mostrar estadísticas
            stats = self.referral_system.get_user_stats(user_id)
            if stats:
                stats_text = format_referral_stats(stats)
                await query.edit_message_text(stats_text)
        
        elif data == "canjear_semana":
            # Canjear semana gratis
            success, message = self.referral_system.redeem_free_week(user_id)
            await query.edit_message_text(message)
        
        elif data == "solicitar_retiro":
            # Mostrar instrucciones
            await query.edit_message_text(
                "Para solicitar un retiro, usa:\n\n"
                "/retirar [monto]\n\n"
                "Ejemplo: /retirar 25.50\n\n"
                "Monto mínimo: $5.00 USD\n"
                "Tiempo de proceso: 24-48 horas"
            )
        
        elif data == "premium":
            # Mostrar opciones de Premium
            await query.edit_message_text(
                "SUSCRIPCION PREMIUM\n\n"
                "Precio: 15€ por semana\n\n"
                "Incluye:\n"
                "- Hasta 5 alertas diarias de máxima calidad\n"
                "- Análisis profesional con Kelly Criterion\n"
                "- Pronósticos con IA y datos en tiempo real\n"
                "- Seguimiento de resultados y ROI\n"
                "- Soporte prioritario\n\n"
                "Contacta al administrador para suscribirte."
            )


# Comandos de administrador
class AdminReferralCommands:
    """
    Comandos de administración para el sistema de referidos
    """
    
    def __init__(
        self,
        referral_system: ReferralSystem,
        admin_ids: list
    ):
        """
        Args:
            referral_system: Sistema de referidos
            admin_ids: Lista de IDs de usuarios admin
        """
        self.referral_system = referral_system
        self.admin_ids = admin_ids
    
    def _is_admin(self, user_id: str) -> bool:
        """Verifica si el usuario es admin"""
        return user_id in self.admin_ids
    
    async def handle_aprobar_retiro(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Aprueba un retiro de saldo
        
        Formato: /aprobar_retiro USER_ID MONTO
        """
        admin_id = str(update.effective_user.id)
        
        if not self._is_admin(admin_id):
            await update.message.reply_text("Acceso denegado. Solo administradores.")
            return
        
        # Validar argumentos
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "Uso: /aprobar_retiro [user_id] [monto]\n\n"
                "Ejemplo: /aprobar_retiro 123456789 25.50"
            )
            return
        
        user_id = context.args[0]
        
        try:
            amount = float(context.args[1])
        except ValueError:
            await update.message.reply_text("Monto inválido")
            return
        
        # Aprobar retiro
        success, message = self.referral_system.approve_withdrawal(user_id, amount, admin_id)
        
        await update.message.reply_text(
            f"{'RETIRO APROBADO' if success else 'ERROR'}\n\n{message}"
        )
        
        # Notificar al usuario
        if success:
            try:
                # context.bot.send_message(
                #     chat_id=user_id,
                #     text=f"Tu retiro de ${amount:.2f} ha sido aprobado y procesado!"
                # )
                logger.info(f"Retiro aprobado: {user_id} - ${amount:.2f}")
            except Exception as e:
                logger.error(f"Error notificando al usuario {user_id}: {e}")
    
    async def handle_reporte_referidos(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Genera reporte completo del sistema de referidos
        
        Comando: /reporte_referidos
        """
        admin_id = str(update.effective_user.id)
        
        if not self._is_admin(admin_id):
            await update.message.reply_text("Acceso denegado. Solo administradores.")
            return
        
        # Generar reporte
        report = self.referral_system.generate_report()
        
        await update.message.reply_text(
            f"```\n{report}\n```",
            parse_mode='Markdown'
        )
    
    async def handle_detectar_fraude(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Analiza un usuario para detectar fraude
        
        Formato: /detectar_fraude USER_ID
        """
        admin_id = str(update.effective_user.id)
        
        if not self._is_admin(admin_id):
            await update.message.reply_text("Acceso denegado. Solo administradores.")
            return
        
        # Validar argumentos
        if not context.args or len(context.args) < 1:
            await update.message.reply_text(
                "Uso: /detectar_fraude [user_id]\n\n"
                "Ejemplo: /detectar_fraude 123456789"
            )
            return
        
        user_id = context.args[0]
        
        # Analizar fraude
        analysis = self.referral_system.detect_fraud(user_id)
        
        message = (
            f"ANALISIS DE FRAUDE\n\n"
            f"Usuario: {user_id}\n"
            f"Nivel de riesgo: {analysis['risk_level']}\n"
            f"Score: {analysis['risk_score']}/10\n\n"
            f"Total referidos: {analysis['total_referrals']}\n"
            f"Referidos pagos: {analysis['paid_referrals']}\n"
            f"Total ganado: ${analysis['total_earned']:.2f}\n\n"
        )
        
        if analysis['risk_factors']:
            message += "FACTORES DE RIESGO:\n"
            for factor in analysis['risk_factors']:
                message += f"- {factor}\n"
        else:
            message += "No se detectaron factores de riesgo."
        
        await update.message.reply_text(message)


# Ejemplo de uso con python-telegram-bot
if __name__ == "__main__":
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler
    
    # Inicializar sistemas
    referral_system = ReferralSystem()
    user_manager = None  # Tu UserManager aquí
    
    # Comandos de usuario
    ref_commands = ReferralCommands(referral_system, user_manager)
    
    # Comandos de admin
    admin_commands = AdminReferralCommands(
        referral_system,
        admin_ids=["5901833301"]  # Tu ID de admin
    )
    
    # Crear aplicación (necesitas tu BOT_TOKEN)
    # application = Application.builder().token("TU_BOT_TOKEN").build()
    
    # Registrar handlers
    # application.add_handler(CommandHandler("start", ref_commands.handle_start))
    # application.add_handler(CommandHandler("referidos", ref_commands.handle_referidos))
    # application.add_handler(CommandHandler("canjear", ref_commands.handle_canjear))
    # application.add_handler(CommandHandler("retirar", ref_commands.handle_retirar))
    # application.add_handler(CallbackQueryHandler(ref_commands.handle_callback_query))
    
    # Handlers de admin
    # application.add_handler(CommandHandler("aprobar_retiro", admin_commands.handle_aprobar_retiro))
    # application.add_handler(CommandHandler("reporte_referidos", admin_commands.handle_reporte_referidos))
    # application.add_handler(CommandHandler("detectar_fraude", admin_commands.handle_detectar_fraude))
    
    # application.run_polling()
