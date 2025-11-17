"""
main_v2.py - Sistema integrado con APIs deportivas y ajuste de probabilidades

Nuevo flujo:
1. Fetch odds como antes
2. Generar candidatos base  
3. Ajustar probabilidades con información deportiva en tiempo real
4. Filtrar solo los 5 mejores para usuarios premium
5. Enviar alertas premium exclusivas
"""
import sys
import pathlib
import os
import asyncio
from dotenv import load_dotenv
import logging
from typing import List, Dict

# Ensure project root is on sys.path
PROJECT_ROOT = pathlib.Path(__file__).parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Imports existentes
from data.odds_api import OddsFetcher
from scanner.advanced_scanner import find_value_bets_advanced
from notifier.telegram import TelegramNotifier
from data.users import get_users_manager, User

# Nuevos imports para el sistema mejorado
from model.probability_adjuster import adjust_candidate_probabilities
from utils.quality_filter import QualityFilter, get_quality_report
from notifier.premium_alert_formatter import (
    format_premium_exclusive_alert,
    format_free_user_upgrade_message,
    format_quality_summary_for_admin,
    should_send_alert
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Configuración
CHECK_INTERVAL_MIN = int(os.getenv("CHECK_INTERVAL_MIN", 5))
THEODDS_API_KEY = os.getenv("API_KEY") or os.getenv("THEODDS_API_KEY")
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID")
SPORTS = os.getenv("SPORTS", "basketball_nba,baseball_mlb,soccer_epl,tennis_atp").split(",")
SAMPLE_PATH = os.getenv("SAMPLE_ODDS_PATH", "data/sample_odds.json")

# Nuevos parámetros de calidad
MIN_QUALITY_THRESHOLD = float(os.getenv("MIN_QUALITY_THRESHOLD", "0.6"))  # Calidad mínima
MAX_DAILY_ALERTS = int(os.getenv("MAX_DAILY_ALERTS", "5"))  # Máximo 5 por día


async def send_premium_alert(user: User, candidate: Dict, notifier: TelegramNotifier, users_manager):
    """
    Envía alerta premium exclusiva con información ajustada
    """
    try:
        # Calcular stake recomendado
        odds = candidate.get('odds', 2.0)
        prob = candidate.get('prob_calculated', 0.55)
        if isinstance(prob, (int, float)) and prob > 1:
            prob = prob / 100  # Convertir a decimal si está en porcentaje
        
        stake = user.calculate_stake(odds, prob)
        
        # Formatear mensaje premium exclusivo
        message = format_premium_exclusive_alert(candidate, user, stake)
        
        # Enviar alerta
        await notifier.send_message(user.chat_id, message)
        
        # Registrar envío
        user.record_alert_sent()
        users_manager.save_user(user)
        
        # Log exitoso
        event = candidate.get('event', 'Unknown')
        quality_score = candidate.get('quality_score', 0.0)
        logger.info(f"✅ Premium alert sent to {user.chat_id}: {event} (Q:{quality_score:.3f})")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error sending premium alert to {user.chat_id}: {e}")
        return False


async def send_upgrade_message(user: User, notifier: TelegramNotifier):
    """
    Envía mensaje de upgrade a usuarios gratuitos
    """
    try:
        message = format_free_user_upgrade_message()
        await notifier.send_message(user.chat_id, message)
        logger.info(f"📨 Upgrade message sent to {user.chat_id}")
        return True
    except Exception as e:
        logger.error(f"❌ Error sending upgrade message to {user.chat_id}: {e}")
        return False


async def process_and_send_alerts(adjusted_candidates: List[Dict], users_manager, notifier: TelegramNotifier):
    """
    Procesa candidatos ajustados y envía alertas premium exclusivas
    """
    if not adjusted_candidates:
        logger.info("📭 No candidates to process")
        return
    
    # Filtrar mejores candidatos por calidad
    quality_filter = QualityFilter(max_daily_alerts=MAX_DAILY_ALERTS)
    best_candidates = quality_filter.select_best_candidates(adjusted_candidates)
    
    # Verificar si la calidad es suficiente para el día
    should_skip, reason = quality_filter.should_skip_low_quality_day(
        adjusted_candidates, 
        min_threshold=MIN_QUALITY_THRESHOLD
    )
    
    if should_skip:
        logger.warning(f"⏸️ Skipping day due to low quality: {reason}")
        
        # Enviar resumen al admin
        admin_message = f"⚠️ **CALIDAD INSUFICIENTE HOY**\n\n{reason}\n\nNo se enviarán alertas premium."
        try:
            await notifier.send_message(TELEGRAM_CHAT_ID, admin_message)
        except:
            pass
        return
    
    # Log reporte de calidad
    quality_report = get_quality_report(adjusted_candidates)
    logger.info(quality_report)
    
    # Obtener usuarios
    users = users_manager.get_all_users()
    
    premium_alerts_sent = 0
    upgrade_messages_sent = 0
    
    for user in users:
        try:
            if user.is_premium_active() and user.can_send_alert():
                # Usuario premium: enviar alertas de calidad
                
                for candidate in best_candidates:
                    if not user.can_send_alert():
                        break  # Ya alcanzó el límite diario
                    
                    # Verificar si el candidato cumple criterios mínimos
                    if should_send_alert(candidate, MIN_QUALITY_THRESHOLD):
                        success = await send_premium_alert(user, candidate, notifier, users_manager)
                        if success:
                            premium_alerts_sent += 1
                    
            elif not user.is_premium_active():
                # Usuario gratuito: enviar mensaje de upgrade (máximo 1 por día)
                if user.alerts_sent_today == 0:  # Solo si no ha recibido mensaje hoy
                    success = await send_upgrade_message(user, notifier)
                    if success:
                        user.record_alert_sent()  # Contar como "alerta" para evitar spam
                        users_manager.save_user(user)
                        upgrade_messages_sent += 1
                        
        except Exception as e:
            logger.error(f"Error processing user {user.chat_id}: {e}")
    
    # Enviar resumen al admin
    quality_summary = quality_filter.get_quality_summary(best_candidates)
    admin_summary = format_quality_summary_for_admin(quality_summary)
    
    admin_message = f"{admin_summary}\n\n📊 **RESUMEN DE ENVÍOS:**\n"
    admin_message += f"💎 Alertas premium: {premium_alerts_sent}\n"
    admin_message += f"📨 Mensajes upgrade: {upgrade_messages_sent}\n"
    admin_message += f"🎯 Candidatos totales: {len(adjusted_candidates)}\n"
    admin_message += f"⭐ Seleccionados: {len(best_candidates)}"
    
    try:
        await notifier.send_message(TELEGRAM_CHAT_ID, admin_message)
    except Exception as e:
        logger.error(f"Error sending admin summary: {e}")
    
    logger.info(f"✅ Alerts processed: {premium_alerts_sent} premium, {upgrade_messages_sent} upgrades")


async def periodic_run():
    """
    Ciclo principal mejorado con ajuste de probabilidades
    """
    print("🚀 Iniciando bot mejorado con análisis en tiempo real")
    print(f"⏰ Chequeando cada {CHECK_INTERVAL_MIN} minutos")
    print(f"🎯 Máximo {MAX_DAILY_ALERTS} alertas premium diarias")
    print(f"⭐ Calidad mínima requerida: {MIN_QUALITY_THRESHOLD:.1%}")
    
    # Inicializar componentes
    fetcher = OddsFetcher(api_key=THEODDS_API_KEY, sample_path=SAMPLE_PATH)
    users_manager = get_users_manager()
    notifier = TelegramNotifier(TELEGRAM_TOKEN)
    
    print(f"📊 Usuarios cargados: {len(users_manager.get_all_users())}")
    
    while True:
        try:
            print(f"\n🔄 Iniciando ciclo: {asyncio.get_event_loop().time()}")
            
            # 1. Fetch odds (como antes)
            print("📡 Fetching odds...")
            events = await fetcher.fetch_odds(SPORTS)
            print(f"📡 Fetched {len(events)} events")
            
            # 2. Generar candidatos base con análisis avanzado
            print("🔍 Finding value bets...")
            base_candidates = await find_value_bets_advanced(events)
            print(f"🔍 Base candidates found: {len(base_candidates)}")
            
            if not base_candidates:
                print("📭 No base candidates found, waiting for next cycle...")
                await asyncio.sleep(CHECK_INTERVAL_MIN * 60)
                continue
            
            # 3. NUEVO: Ajustar probabilidades con información deportiva
            print("🏥 Adjusting probabilities with sports data...")
            adjusted_candidates = await adjust_candidate_probabilities(base_candidates)
            print(f"🔄 Probabilities adjusted for {len(adjusted_candidates)} candidates")
            
            # Mostrar resumen de candidatos ajustados
            for i, candidate in enumerate(adjusted_candidates[:10], 1):  # Mostrar top 10
                event = candidate.get('event', 'N/A')
                selection = candidate.get('selection', 'N/A')
                odds = candidate.get('odds', 0)
                original_value = candidate.get('original_value', 0)
                adjusted_value = candidate.get('value', 0)
                quality_score = candidate.get('quality_score', 0)
                adjustment = candidate.get('probability_adjustment', 0)
                
                print(f"  [{i}] {event[:30]}...")
                print(f"      Selection: {selection}")
                print(f"      Odds: {odds:.2f} | Value: {original_value:.3f} → {adjusted_value:.3f}")
                print(f"      Quality: {quality_score:.3f} | Prob.Adj: {adjustment:+.3f}")
            
            # 4. NUEVO: Procesar y enviar solo alertas premium de calidad
            print("📨 Processing premium alerts...")
            await process_and_send_alerts(adjusted_candidates, users_manager, notifier)
            
            print(f"✅ Cycle completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Error en ciclo: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"⏰ Waiting {CHECK_INTERVAL_MIN} minutes until next cycle...")
        await asyncio.sleep(CHECK_INTERVAL_MIN * 60)


if __name__ == "__main__":
    try:
        asyncio.run(periodic_run())
    except KeyboardInterrupt:
        print("🛑 Interrumpido por usuario")
    except Exception as e:
        print(f"💥 Error fatal: {e}")
        import traceback
        traceback.print_exc()