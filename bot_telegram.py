"""
bot_telegram.py - Bot de comandos de Telegram con sistema de referidos

Este archivo maneja todos los comandos interactivos del bot usando python-telegram-bot.
Se ejecuta en paralelo con main.py para el monitoreo de value bets.
"""

import os
import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# Cargar variables de entorno
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# Importar sistemas
from referrals import ReferralSystem, format_referral_stats
from data.users import UsersManager
from payments import PremiumPaymentProcessor
from analytics.performance_tracker import performance_tracker

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuración
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_CHAT_ID = os.getenv('CHAT_ID', '5901833301')
BOT_USERNAME = "Valueapuestasbot"

# Inicializar sistemas
referral_system = ReferralSystem("data/referrals.json")
users_manager = UsersManager("data/users.json")
payment_processor = PremiumPaymentProcessor(referral_system, users_manager)


# ============================================================================
# COMANDOS PARA USUARIOS
# ============================================================================

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /stats - Muestra estadísticas de performance del bot
    """
    try:
        # Importar base de datos
        try:
            from data.historical_db import historical_db
            
            # Obtener performance
            perf_7d = historical_db.get_bot_performance(days=7)
            perf_30d = historical_db.get_bot_performance(days=30)
            
            if perf_7d['total_predictions'] == 0 and perf_30d['total_predictions'] == 0:
                await update.message.reply_text(
                    "📊 **ESTADÍSTICAS DEL BOT**\n\n"
                    "⏳ Aún no hay predicciones verificadas.\n"
                    "El bot está recopilando datos...\n\n"
                    "Vuelve en 24-48 horas para ver estadísticas reales."
                )
                return
            
            # Formatear mensaje
            message = "📊 **PERFORMANCE DEL BOT**\n\n"
            
            if perf_7d['total_predictions'] > 0:
                message += f"**📅 Últimos 7 días:**\n"
                message += f"• Predicciones: {perf_7d['total_predictions']}\n"
                message += f"• Correctas: {perf_7d['correct']}\n"
                message += f"• Accuracy: {perf_7d['accuracy']*100:.1f}%\n"
                message += f"• ROI: {perf_7d['roi']*100:+.1f}%\n"
                message += f"• Profit: ${perf_7d['total_profit']:+.2f}\n\n"
            
            if perf_30d['total_predictions'] > 0:
                message += f"**📅 Últimos 30 días:**\n"
                message += f"• Predicciones: {perf_30d['total_predictions']}\n"
                message += f"• Correctas: {perf_30d['correct']}\n"
                message += f"• Accuracy: {perf_30d['accuracy']*100:.1f}%\n"
                message += f"• ROI: {perf_30d['roi']*100:+.1f}%\n"
                message += f"• Profit: ${perf_30d['total_profit']:+.2f}\n\n"
            
            # Obtener últimas predicciones
            import sqlite3
            conn = sqlite3.connect('data/historical.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT selection, odds, was_correct, profit_loss
                FROM predictions
                WHERE actual_result IS NOT NULL
                ORDER BY predicted_at DESC
                LIMIT 5
            """)
            
            recent = cursor.fetchall()
            conn.close()
            
            if recent:
                message += "**📋 Últimas 5 apuestas:**\n"
                for sel, odds, correct, profit in recent:
                    emoji = "✅" if correct else "❌"
                    message += f"{emoji} {sel} ({odds:.2f}) - ${profit:+.2f}\n"
            
            message += "\n💡 Stats actualizadas diariamente a las 2 AM"
            
            await update.message.reply_text(message)
            
        except ImportError:
            await update.message.reply_text(
                "⚠️ Sistema de estadísticas no disponible.\n"
                "Contacta al administrador."
            )
            
    except Exception as e:
        logger.error(f"Error en comando /stats: {e}")
        await update.message.reply_text(
            "❌ Error al obtener estadísticas. Intenta de nuevo."
        )

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /start [CODIGO_REFERIDO]
    Registra al usuario y muestra su código de referido
    """
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or update.effective_user.first_name or "Usuario"
    
    # Extraer código de referido si existe
    referrer_code = None
    if context.args and len(context.args) > 0:
        referrer_code = context.args[0].upper()
        logger.info(f"Usuario {user_id} inicio con codigo de referido: {referrer_code}")
    
    # Registrar en sistema de referidos
    result = referral_system.register_user(user_id, referrer_code)
    
    # Registrar en sistema de usuarios si no existe
    if not users_manager.get_user(user_id):
        users_manager.add_user(user_id)
    
    # Construir mensaje de bienvenida
    welcome_text = f"*Bienvenido al Bot de Value Bets, {username}!*\n\n"
    welcome_text += (
        "🤖 *QUE HACE ESTE BOT:*\n"
        "• Analiza odds de +30 casas de apuestas en tiempo real\n"
        "• Calcula probabilidades reales con IA avanzada\n"
        "• Detecta value bets (disparidades de mercado)\n"
        "• Optimiza stakes con Kelly Criterion\n"
        "• Cubre 33 deportes (NBA, Champions, NFL, etc)\n"
        "• Solo usuarios Premium reciben alertas\n\n"
    )
    
    # Obtener código y enlace
    referral_code = result.get('referral_code')
    referral_link = result.get('referral_link')
    
    if result['success']:
        if result.get('referred_by'):
            welcome_text += (
                "✅ Te has registrado usando un codigo de referido!\n"
                "Tu amigo recibira una recompensa cuando te suscribas a Premium.\n\n"
            )
        
        welcome_text += (
            f"*TU CODIGO DE REFERIDO:* `{referral_code}`\n"
            f"*Tu enlace:*\n"
            f"`{referral_link}`\n\n"
            "💰 *SISTEMA DE REFERIDOS:*\n"
            "• Ganas el *10% de comision* ($5) por cada amigo que pague Premium ($50)\n"
            "• Ganas *1 semana gratis* por cada 3 amigos que paguen\n"
            "• Retiros desde $5 USD\n"
            "• Sin limite de ganancias\n\n"
        )
    else:
        # Ya estaba registrado, obtener stats
        stats = referral_system.get_user_stats(user_id)
        if stats:
            referral_code = stats['referral_code']
            referral_link = stats['referral_link']
            welcome_text += (
                f"*Tu codigo de referido:* `{referral_code}`\n"
                f"*Tu enlace:*\n"
                f"`{referral_link}`\n\n"
                "💰 *Comparte y gana:* 10% comision + 1 semana gratis cada 3 referidos\n\n"
            )
    
    welcome_text += (
        "*COMANDOS DISPONIBLES:*\n"
        "/referidos - Ver tus estadisticas\n"
        "/estadisticas - Ver rendimiento del bot\n"
        "/canjear - Canjear semana gratis\n"
        "/retirar [monto] - Solicitar retiro\n"
        "/premium - Info de suscripcion Premium\n"
    )

    # Botones
    keyboard = [
        [
            InlineKeyboardButton("📊 Mis Referidos", callback_data="ver_referidos"),
            InlineKeyboardButton("⭐ Premium", callback_data="info_premium")
        ],
        [
            InlineKeyboardButton("📈 Estadísticas Bot", callback_data="ver_estadisticas"),
            InlineKeyboardButton("🔗 Compartir enlace", url=referral_link)
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    # Si fue referido, notificar al referrer
    if result.get('referred_by'):
        await notify_new_referral(context, result['referred_by'], username)


async def cmd_referidos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /referidos
    Muestra estadísticas completas de referidos
    """
    user_id = str(update.effective_user.id)
    
    stats = referral_system.get_user_stats(user_id)
    
    if not stats:
        await update.message.reply_text(
            "No estas registrado en el sistema de referidos.\n"
            "Usa /start para registrarte."
        )
        return
    
    # Formatear estadísticas con Markdown
    stats_text = (
        "*TUS ESTADISTICAS DE REFERIDOS*\n"
        "="*40 + "\n\n"
        f"*Tu codigo:* `{stats['referral_code']}`\n"
        f"*Tu enlace:*\n`{stats['referral_link']}`\n\n"
        "*REFERIDOS:*\n"
        f"  Total invitados: {stats['total_referrals']}\n"
        f"  Pagaron Premium: {stats['paid_referrals']}\n"
        f"  Pendientes: {stats['pending_referrals']}\n\n"
        "*GANANCIAS:*\n"
        f"  Saldo actual: ${stats['balance_usd']:.2f}\n"
        f"  Total ganado: ${stats['total_earned']:.2f}\n\n"
        "*SEMANAS GRATIS:*\n"
        f"  Ganadas: {stats['free_weeks_earned']}\n"
        f"  Disponibles: {stats['free_weeks_pending']}\n"
        f"  Proxima en: {stats['next_free_week_in']} referidos mas\n\n"
        "*RECOMPENSAS:*\n"
        f"  Por cada referido: $5.00 USD\n"
        f"  Cada 3 pagos: 1 semana Premium gratis\n"
    )
    
    # Botones
    keyboard = [
        [InlineKeyboardButton("🔗 Compartir enlace", url=stats['referral_link'])],
        [
            InlineKeyboardButton("🎁 Canjear semana", callback_data="canjear_semana"),
            InlineKeyboardButton("💵 Solicitar retiro", callback_data="solicitar_retiro")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        stats_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def cmd_canjear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /canjear
    Canjea una semana Premium gratis
    """
    user_id = str(update.effective_user.id)
    
    # Intentar canjear
    success, message = referral_system.redeem_free_week(user_id)
    
    if success:
        # Activar Premium por 1 semana en el sistema de usuarios
        user = users_manager.get_user(user_id)
        if user:
            user.add_free_premium_week()
            users_manager.update_user(user)
            
            message += "\n\n✅ Tu suscripcion Premium ha sido extendida por 7 dias!"
            
            logger.info(f"Usuario {user_id} canjeo semana Premium gratis")
        else:
            message += "\n\n⚠️ Error activando Premium. Contacta al administrador."
    
    await update.message.reply_text(message)


async def cmd_retirar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /retirar [monto]
    Solicita retiro de saldo
    """
    user_id = str(update.effective_user.id)
    
    # Validar argumentos
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "*Uso:* `/retirar [monto]`\n\n"
            "*Ejemplo:* `/retirar 25.50`\n\n"
            "Tu saldo sera verificado y el retiro procesado por el administrador.\n"
            "*Monto minimo:* $5.00 USD",
            parse_mode='Markdown'
        )
        return
    
    # Parsear monto
    try:
        amount = float(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Monto invalido. Usa numeros con punto decimal.\n"
            "Ejemplo: `/retirar 25.50`",
            parse_mode='Markdown'
        )
        return
    
    # Verificar monto mínimo
    if amount < 5.0:
        await update.message.reply_text(
            "❌ El monto minimo de retiro es *$5.00 USD*",
            parse_mode='Markdown'
        )
        return
    
    # Solicitar retiro
    success, message = referral_system.withdraw_balance(user_id, amount)
    
    if success:
        # Notificar al admin
        await notify_admin_withdrawal(context, user_id, amount)
        
        message += (
            "\n\n⏳ El administrador procesara tu solicitud en las proximas 24-48 horas.\n"
            "*Metodos de pago:* PayPal, Transferencia, Criptomonedas."
        )
    
    await update.message.reply_text(message, parse_mode='Markdown')


async def cmd_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /premium
    Muestra información de la suscripción Premium
    """
    premium_text = (
        "*SUSCRIPCION PREMIUM* ⭐\n\n"
        "*Precio:* $50 USD por semana\n\n"
        "*QUE HACE EL BOT:*\n\n"
        "🔍 *Analisis de Mercado:*\n"
        "• Escanea odds de multiples casas de apuestas\n"
        "• Detecta disparidades y oportunidades de valor\n"
        "• Compara precios en tiempo real (arbitraje)\n\n"
        "🧠 *Sistema de Prediccion:*\n"
        "• Calcula probabilidades reales con IA\n"
        "• Analiza alineaciones y lesiones en vivo\n"
        "• Considera descanso, racha y H2H\n"
        "• Ajusta por clima y condiciones del juego\n\n"
        "💰 *Gestion de Bankroll:*\n"
        "• Calcula stakes optimos con Kelly Criterion\n"
        "• Analiza EV (Expected Value) y edge\n"
        "• Categoriza riesgo (BAJO/MEDIO/ALTO)\n"
        "• Limita apuestas al 0.5%-5% del bankroll\n\n"
        "📊 *Tracking y Validacion:*\n"
        "• Registra todas las predicciones\n"
        "• Calcula accuracy y ROI real\n"
        "• Compara EV esperado vs resultados\n"
        "• Genera reportes de rendimiento\n\n"
        "⚡ *Sistema de Alertas:*\n"
        "• Monitoreo continuo 24/7\n"
        "• Actualizaciones cada hora\n"
        "• Alertas 4h antes del evento\n"
        "• Solo las 5 mejores del dia (70%+ prob, odds 1.5-2.1)\n\n"
        "*Incluye:*\n"
        "✅ 5 alertas diarias de maxima calidad\n"
        "✅ Analisis completo de cada pronostico\n"
        "✅ Stake recomendado y nivel de riesgo\n"
        "✅ Seguimiento de resultados\n"
        "✅ Soporte prioritario\n\n"
        "*Como suscribirte:*\n"
        "Contacta al administrador\n\n"
        "*Gana Premium gratis:*\n"
        "Invita 3 amigos que paguen = 1 semana gratis!\n"
        "Usa /referidos para ver tu enlace."
    )
    
    keyboard = [[InlineKeyboardButton("📊 Ver mis referidos", callback_data="ver_referidos")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        premium_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def cmd_estadisticas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /estadisticas
    Muestra estadísticas globales del bot
    """
    try:
        # Obtener estadísticas globales
        stats = performance_tracker.get_global_stats(days=30)
        
        # Formatear mensaje
        stats_text = (
            "📊 *ESTADÍSTICAS DEL BOT* (Últimos 30 días)\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📈 *RENDIMIENTO GLOBAL:*\n"
            f"  Total pronósticos: {stats['total_predictions']}\n"
            f"  ✅ Aciertos: {stats['won']}\n"
            f"  ❌ Fallos: {stats['lost']}\n"
            f"  ⏳ Pendientes: {stats['pending']}\n\n"
            f"🎯 *EFECTIVIDAD:*\n"
            f"  Win Rate: {stats['win_rate']}%\n"
            f"  ROI: {stats['roi']:+.1f}%\n\n"
            f"💰 *FINANCIERO:*\n"
            f"  Stake total: ${stats['total_stake']:.2f}\n"
            f"  Ganancia/Pérdida: ${stats['total_profit']:+.2f}\n\n"
            f"📊 *ANÁLISIS:*\n"
            f"  Cuota promedio: {stats['avg_odd']:.2f}\n"
            f"  Mejor deporte: {stats['best_sport']}\n\n"
        )
        
        # Agregar interpretación
        if stats['win_rate'] >= 55:
            stats_text += "✅ *Rendimiento EXCELENTE* - Por encima del umbral de rentabilidad\n"
        elif stats['win_rate'] >= 50:
            stats_text += "📊 *Rendimiento BUENO* - En zona de rentabilidad\n"
        else:
            stats_text += "⚠️ *Rendimiento en desarrollo* - Se optimiza continuamente\n"
        
        stats_text += "\n💡 *Nota:* Los resultados se verifican automáticamente tras finalizar cada evento."
        
        # Botón para actualizar
        keyboard = [[InlineKeyboardButton("🔄 Actualizar", callback_data="ver_estadisticas")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            stats_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error en cmd_estadisticas: {e}")
        await update.message.reply_text(
            "❌ Error al cargar estadísticas. Intenta de nuevo más tarde."
        )


# ============================================================================
# COMANDOS DE ADMINISTRADOR
# ============================================================================

def is_admin(user_id: str) -> bool:
    """Verifica si el usuario es administrador"""
    return user_id == ADMIN_CHAT_ID


async def cmd_aprobar_retiro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /aprobar_retiro USER_ID MONTO
    Aprueba un retiro de saldo (solo admin)
    """
    admin_id = str(update.effective_user.id)
    
    if not is_admin(admin_id):
        await update.message.reply_text("❌ Acceso denegado. Solo administradores.")
        return
    
    # Validar argumentos
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "*Uso:* `/aprobar_retiro [user_id] [monto]`\n\n"
            "*Ejemplo:* `/aprobar_retiro 123456789 25.50`",
            parse_mode='Markdown'
        )
        return
    
    user_id = context.args[0]
    
    try:
        amount = float(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Monto invalido")
        return
    
    # Aprobar retiro
    success, message = referral_system.approve_withdrawal(user_id, amount, admin_id)
    
    await update.message.reply_text(
        f"*{'✅ RETIRO APROBADO' if success else '❌ ERROR'}*\n\n{message}",
        parse_mode='Markdown'
    )
    
    # Notificar al usuario
    if success:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"✅ Tu retiro de *${amount:.2f}* ha sido aprobado y procesado!",
                parse_mode='Markdown'
            )
            logger.info(f"Retiro aprobado: {user_id} - ${amount:.2f}")
        except Exception as e:
            logger.error(f"Error notificando al usuario {user_id}: {e}")


async def cmd_reporte_referidos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /reporte_referidos
    Genera reporte completo del sistema (solo admin)
    """
    admin_id = str(update.effective_user.id)
    
    if not is_admin(admin_id):
        await update.message.reply_text("❌ Acceso denegado. Solo administradores.")
        return
    
    # Generar reporte
    report = referral_system.generate_report()
    
    await update.message.reply_text(
        f"```\n{report}\n```",
        parse_mode='Markdown'
    )


async def cmd_detectar_fraude(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /detectar_fraude USER_ID
    Analiza un usuario para detectar fraude (solo admin)
    """
    admin_id = str(update.effective_user.id)
    
    if not is_admin(admin_id):
        await update.message.reply_text("❌ Acceso denegado. Solo administradores.")
        return
    
    # Validar argumentos
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "*Uso:* `/detectar_fraude [user_id]`\n\n"
            "*Ejemplo:* `/detectar_fraude 123456789`",
            parse_mode='Markdown'
        )
        return
    
    user_id = context.args[0]
    
    # Analizar fraude
    analysis = referral_system.detect_fraud(user_id)
    
    message = (
        "*ANALISIS DE FRAUDE* 🔍\n\n"
        f"*Usuario:* `{user_id}`\n"
        f"*Nivel de riesgo:* {analysis['risk_level']}\n"
        f"*Score:* {analysis['risk_score']}/10\n\n"
        f"*Total referidos:* {analysis['total_referrals']}\n"
        f"*Referidos pagos:* {analysis['paid_referrals']}\n"
        f"*Total ganado:* ${analysis['total_earned']:.2f}\n\n"
    )
    
    if analysis['risk_factors']:
        message += "*FACTORES DE RIESGO:*\n"
        for factor in analysis['risk_factors']:
            message += f"⚠️ {factor}\n"
    else:
        message += "✅ No se detectaron factores de riesgo."
    
    await update.message.reply_text(message, parse_mode='Markdown')


# ============================================================================
# CALLBACK QUERIES (BOTONES)
# ============================================================================

async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja los callback queries de los botones inline
    """
    query = update.callback_query
    await query.answer()
    
    user_id = str(update.effective_user.id)
    data = query.data
    
    if data == "ver_referidos":
        # Mostrar estadísticas
        stats = referral_system.get_user_stats(user_id)
        if stats:
            stats_text = (
                "*TUS ESTADISTICAS DE REFERIDOS*\n\n"
                f"*Codigo:* `{stats['referral_code']}`\n"
                f"*Total referidos:* {stats['total_referrals']}\n"
                f"*Referidos pagos:* {stats['paid_referrals']}\n"
                f"*Saldo:* ${stats['balance_usd']:.2f}\n"
                f"*Semanas gratis:* {stats['free_weeks_pending']}\n\n"
                "Usa /referidos para ver detalles completos"
            )
            await query.edit_message_text(stats_text, parse_mode='Markdown')
    
    elif data == "canjear_semana":
        # Canjear semana gratis
        success, message = referral_system.redeem_free_week(user_id)
        
        if success:
            user = users_manager.get_user(user_id)
            if user:
                user.add_free_premium_week()
                users_manager.update_user(user)
                message += "\n\n✅ Premium extendido por 7 dias!"
        
        await query.edit_message_text(message)
    
    elif data == "solicitar_retiro":
        # Mostrar instrucciones
        await query.edit_message_text(
            "*Para solicitar un retiro:*\n\n"
            "`/retirar [monto]`\n\n"
            "*Ejemplo:* `/retirar 25.50`\n\n"
            "*Monto minimo:* $5.00 USD\n"
            "*Tiempo de proceso:* 24-48 horas",
            parse_mode='Markdown'
        )
    
    elif data == "info_premium":
        # Mostrar info de Premium
        await query.edit_message_text(
            "*SUSCRIPCION PREMIUM* ⭐\n\n"
            "*Precio:* $50 USD/semana\n\n"
            "*Incluye:*\n"
            "✅ 5 alertas diarias de calidad\n"
            "✅ Analisis con Kelly Criterion\n"
            "✅ Pronosticos con IA\n"
            "✅ Tracking de ROI\n\n"
            "Contacta al administrador para suscribirte.\n\n"
            "O invita 3 amigos y gana 1 semana gratis!",
            parse_mode='Markdown'
        )

    elif data == "ver_estadisticas":
        # Mostrar estadísticas globales
        try:
            stats = performance_tracker.get_global_stats(days=30)
            
            stats_text = (
                "📊 *ESTADÍSTICAS DEL BOT* (Últimos 30 días)\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📈 *RENDIMIENTO GLOBAL:*\n"
                f"  Total pronósticos: {stats['total_predictions']}\n"
                f"  ✅ Aciertos: {stats['won']}\n"
                f"  ❌ Fallos: {stats['lost']}\n"
                f"  ⏳ Pendientes: {stats['pending']}\n\n"
                f"🎯 *EFECTIVIDAD:*\n"
                f"  Win Rate: {stats['win_rate']}%\n"
                f"  ROI: {stats['roi']:+.1f}%\n\n"
                f"💰 *FINANCIERO:*\n"
                f"  Stake total: ${stats['total_stake']:.2f}\n"
                f"  Ganancia/Pérdida: ${stats['total_profit']:+.2f}\n\n"
                f"📊 *ANÁLISIS:*\n"
                f"  Cuota promedio: {stats['avg_odd']:.2f}\n"
                f"  Mejor deporte: {stats['best_sport']}\n\n"
            )
            
            if stats['win_rate'] >= 55:
                stats_text += "✅ *Rendimiento EXCELENTE*\n"
            elif stats['win_rate'] >= 50:
                stats_text += "📊 *Rendimiento BUENO*\n"
            else:
                stats_text += "⚠️ *Optimizando modelo*\n"
            
            stats_text += "\n💡 Resultados verificados automáticamente"
            
            await query.edit_message_text(stats_text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error mostrando estadísticas: {e}")
            await query.edit_message_text(
                "❌ Error al cargar estadísticas. Intenta de nuevo."
            )


# ============================================================================
# FUNCIONES DE NOTIFICACION
# ============================================================================

async def notify_new_referral(context: ContextTypes.DEFAULT_TYPE, referrer_id: str, new_user_name: str):
    """Notifica al referrer que un nuevo usuario usó su código"""
    try:
        stats = referral_system.get_user_stats(referrer_id)
        if stats:
            message = (
                "🎉 *NUEVO REFERIDO!*\n\n"
                f"{new_user_name} se registro usando tu codigo.\n"
                "Cuando se suscriba a Premium, ganaras $5 USD!\n\n"
                f"*Total referidos:* {stats['total_referrals']}\n"
                f"*Han pagado:* {stats['paid_referrals']}"
            )
            
            await context.bot.send_message(
                chat_id=referrer_id,
                text=message,
                parse_mode='Markdown'
            )
            
            logger.info(f"Notificacion de referido enviada a {referrer_id}")
    except Exception as e:
        logger.error(f"Error notificando a referrer {referrer_id}: {e}")


async def notify_admin_withdrawal(context: ContextTypes.DEFAULT_TYPE, user_id: str, amount: float):
    """Notifica al admin sobre una solicitud de retiro"""
    try:
        admin_message = (
            "💵 *SOLICITUD DE RETIRO*\n\n"
            f"*Usuario:* `{user_id}`\n"
            f"*Monto:* ${amount:.2f} USD\n"
            f"*Fecha:* {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"Usa `/aprobar_retiro {user_id} {amount}` para aprobar"
        )
        
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=admin_message,
            parse_mode='Markdown'
        )
        
        logger.info(f"Solicitud de retiro notificada: {user_id} - ${amount:.2f}")
    except Exception as e:
        logger.error(f"Error notificando retiro al admin: {e}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Inicia el bot de comandos"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN no configurado en .env")
        return
    
    logger.info("Iniciando Bot de Comandos de Telegram...")
    logger.info(f"Admin: {ADMIN_CHAT_ID}")
    
    # Crear aplicación
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Registrar comandos de usuario
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("referidos", cmd_referidos))
    application.add_handler(CommandHandler("canjear", cmd_canjear))
    application.add_handler(CommandHandler("retirar", cmd_retirar))
    application.add_handler(CommandHandler("premium", cmd_premium))
    application.add_handler(CommandHandler("estadisticas", cmd_estadisticas))
    application.add_handler(CommandHandler("stats", stats_command))
    
    # Registrar comandos de admin
    application.add_handler(CommandHandler("aprobar_retiro", cmd_aprobar_retiro))
    application.add_handler(CommandHandler("reporte_referidos", cmd_reporte_referidos))
    application.add_handler(CommandHandler("detectar_fraude", cmd_detectar_fraude))
    
    # Registrar callback query handler (botones)
    application.add_handler(CallbackQueryHandler(callback_query_handler))
    
    logger.info("Bot de comandos iniciado correctamente!")
    logger.info("Comandos disponibles: /start, /referidos, /canjear, /retirar, /premium, /stats")
    logger.info("Comandos admin: /aprobar_retiro, /reporte_referidos, /detectar_fraude")
    
    # Iniciar bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
