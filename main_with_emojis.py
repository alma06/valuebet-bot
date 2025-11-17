"""
main.py - Bot de Value Bets con monitoreo continuo y alertas progresivas

Características principales:
- Monitoreo diario a las 6 AM (hora de América)
- Actualización cada hora de cuotas y probabilidades
- Alertas solo cuando el evento está a menos de 2 horas
- Máximo 3-5 alertas diarias por usuario
- Solo usuarios premium reciben alertas
- Filtros estrictos: cuotas 1.5-2.1, probabilidad 70%+
"""

import asyncio
import sys
import pathlib
import os
import logging
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from typing import List, Dict, Set, Optional
from dotenv import load_dotenv

# Asegurar que el proyecto esté en sys.path
PROJECT_ROOT = pathlib.Path(__file__).parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Imports del sistema existente
from data.odds_api import OddsFetcher
from scanner.scanner import ValueScanner
from notifier.telegram import TelegramNotifier
from data.users import get_users_manager, User
from data.state import AlertsState
from notifier.alert_formatter import format_premium_alert
from utils.sport_translator import translate_sport

# Configurar encoding UTF-8 para Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('value_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

# Configuración desde .env
API_KEY = os.getenv("API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN") 
CHAT_ID = os.getenv("CHAT_ID")

# Configuración de filtros
MIN_ODD = float(os.getenv("MIN_ODD", "1.5"))
MAX_ODD = float(os.getenv("MAX_ODD", "2.1"))  # Reducido según especificación
MIN_PROB = float(os.getenv("MIN_PROB", "0.70"))  # 70% mínimo según especificación
MAX_ALERTS_PER_DAY = int(os.getenv("MAX_ALERTS_PER_DAY", "5"))

# Deportes a monitorear
SPORTS = os.getenv("SPORTS", "basketball_nba,soccer_epl,soccer_spain_la_liga,tennis_atp,tennis_wta,baseball_mlb").split(",")

# Configuración de tiempo
AMERICA_TZ = ZoneInfo("America/New_York")  # Hora de América
DAILY_START_HOUR = 6  # 6 AM
UPDATE_INTERVAL_HOURS = 1  # Actualizar cada hora
ALERT_WINDOW_HOURS = 2  # Alertar cuando falten menos de 2 horas

# Configuración adicional
SAMPLE_PATH = os.getenv("SAMPLE_ODDS_PATH", "data/sample_odds.json")


class ValueBotMonitor:
    """
    Monitor principal del bot de value bets con alertas progresivas
    """
    
    def __init__(self):
        self.fetcher = OddsFetcher(api_key=API_KEY)
        self.scanner = ValueScanner(
            min_odd=MIN_ODD, 
            max_odd=MAX_ODD, 
            min_prob=MIN_PROB
        )
        self.notifier = TelegramNotifier(BOT_TOKEN)
        self.users_manager = get_users_manager()
        self.alerts_state = AlertsState("data/alerts_state.json", MAX_ALERTS_PER_DAY)
        
        # Tracking de eventos monitoreados
        self.monitored_events: Dict[str, Dict] = {}  # event_id -> event_data
        self.sent_alerts: Set[str] = set()  # Para evitar duplicados
        
        logger.info("ValueBotMonitor inicializado")
        logger.info(f"Deportes: {', '.join(SPORTS)}")
        logger.info(f"Filtros: odds {MIN_ODD}-{MAX_ODD}, prob {MIN_PROB:.0%}+")
        logger.info(f"Alertas: maximo {MAX_ALERTS_PER_DAY} diarias, <{ALERT_WINDOW_HOURS}h antes")

    def is_daily_start_time(self) -> bool:
        """
        Verifica si es hora de inicio diario (6 AM América)
        """
        now = datetime.now(AMERICA_TZ)
        return now.hour == DAILY_START_HOUR and now.minute < 5

    def get_events_starting_soon(self, max_hours: float = ALERT_WINDOW_HOURS) -> List[Dict]:
        """
        Filtra eventos que empiezan en menos de max_hours
        """
        now = datetime.now(timezone.utc)
        cutoff_time = now + timedelta(hours=max_hours)
        
        events_soon = []
        for event_id, event_data in self.monitored_events.items():
            commence_time = event_data.get('commence_time')
            if commence_time and isinstance(commence_time, datetime):
                if now <= commence_time <= cutoff_time:
                    events_soon.append(event_data)
        
        return events_soon

    def get_next_update_time(self) -> datetime:
        """
        Calcula la próxima hora de actualización (cada hora en punto)
        """
        now = datetime.now(AMERICA_TZ)
        next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        return next_hour

    def get_next_daily_start(self) -> datetime:
        """
        Calcula el próximo inicio diario (6 AM América)
        """
        now = datetime.now(AMERICA_TZ)
        next_start = now.replace(hour=DAILY_START_HOUR, minute=0, second=0, microsecond=0)
        
        if now >= next_start:
            next_start += timedelta(days=1)
        
        return next_start

    async def fetch_and_update_events(self) -> List[Dict]:
        """
        Obtiene eventos de las APIs y actualiza el monitoring
        """
        try:
            logger.info("Fetching odds from APIs...")
            events = await self.fetcher.fetch_odds(SPORTS)
            logger.info(f"Fetched {len(events)} events total")
            
            # Procesar y almacenar eventos
            processed_events = []
            current_time = datetime.now(timezone.utc)
            
            for event in events:
                try:
                    # Parsear tiempo de inicio
                    commence_str = event.get('commence_time')
                    if commence_str:
                        if isinstance(commence_str, str):
                            commence_time = datetime.fromisoformat(commence_str.replace('Z', '+00:00'))
                        else:
                            commence_time = commence_str
                    else:
                        continue  # Skip eventos sin tiempo
                    
                    # Solo eventos futuros (no en vivo)
                    if commence_time <= current_time:
                        continue
                    
                    # Agregar tiempo parseado al evento
                    event['commence_time'] = commence_time
                    event_id = event.get('id', f"{event.get('sport_key', 'unknown')}_{len(processed_events)}")
                    
                    # Actualizar en monitored_events
                    self.monitored_events[event_id] = event
                    processed_events.append(event)
                    
                except Exception as e:
                    logger.warning(f"Error processing event: {e}")
                    continue
            
            # Limpiar eventos pasados del monitoring
            current_time = datetime.now(timezone.utc)
            expired_events = [
                event_id for event_id, event in self.monitored_events.items()
                if event.get('commence_time') and event['commence_time'] <= current_time
            ]
            
            for event_id in expired_events:
                del self.monitored_events[event_id]
                logger.debug(f"🗑️ Removed expired event: {event_id}")
            
            logger.info(f"Events processed: {len(processed_events)}, total monitored: {len(self.monitored_events)}")
            return processed_events
            
        except Exception as e:
            logger.error(f"❌ Error fetching events: {e}")
            return []

    async def find_value_opportunities(self, events: List[Dict]) -> List[Dict]:
        """
        Encuentra oportunidades de value betting usando el scanner existente
        """
        try:
            # Usar el scanner de value existente
            candidates = self.scanner.find_candidates(events)
            
            logger.info(f"🔍 Found {len(candidates)} value candidates")
            
            # Log de candidatos encontrados
            for i, candidate in enumerate(candidates[:10], 1):  # Solo log primeros 10
                sport = candidate.get('sport', 'Unknown')
                selection = candidate.get('selection', 'Unknown')
                odds = candidate.get('odds', 0.0)
                prob = candidate.get('prob', 0.0) * 100
                value = candidate.get('value', 0.0)
                
                logger.info(
                    f"  [{i}] {sport}: {selection} @ {odds:.2f} "
                    f"(prob: {prob:.1f}%, value: {value:.3f})"
                )
            
            return candidates
            
        except Exception as e:
            logger.error(f"❌ Error finding value opportunities: {e}")
            return []

    async def send_alert_to_user(self, user: User, candidate: Dict) -> bool:
        """
        Envía alerta a un usuario específico
        """
        try:
            # Verificar si el usuario puede recibir más alertas
            if not user.can_send_alert():
                logger.debug(f"User {user.chat_id} has reached daily limit")
                return False
            
            # Verificar si es usuario premium
            if not user.is_premium_active():
                logger.debug(f"User {user.chat_id} is not premium")
                return False
            
            # Calcular stake recomendado
            odds = candidate.get('odds', 2.0)
            prob = candidate.get('prob', 0.5)
            stake = user.calculate_stake(odds, prob)
            
            # Formatear mensaje premium
            message = format_premium_alert(candidate, user, stake)
            
            # Enviar mensaje
            await self.notifier.send_message(user.chat_id, message)
            
            # Registrar alerta enviada
            user.record_alert_sent()
            self.users_manager.save_user(user)
            
            # Agregar a sent_alerts para evitar duplicados
            alert_key = f"{user.chat_id}_{candidate.get('id', '')}_{candidate.get('selection', '')}"
            self.sent_alerts.add(alert_key)
            
            logger.info(f"✅ Alert sent to {user.chat_id}: {candidate.get('selection', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending alert to {user.chat_id}: {e}")
            return False

    async def process_alerts_for_imminent_events(self) -> int:
        """
        Procesa alertas para eventos que empiezan pronto
        """
        # Obtener eventos que empiezan pronto
        imminent_events = self.get_events_starting_soon(ALERT_WINDOW_HOURS)
        
        if not imminent_events:
            logger.info("No imminent events found")
            return 0
        
        logger.info(f"⏰ {len(imminent_events)} events starting within {ALERT_WINDOW_HOURS} hours")
        
        # Encontrar value bets en estos eventos
        value_candidates = await self.find_value_opportunities(imminent_events)
        
        if not value_candidates:
            logger.info("No value opportunities in imminent events")
            return 0
        
        # Obtener usuarios premium
        users = self.users_manager.get_all_users()
        premium_users = [user for user in users if user.is_premium_active()]
        
        if not premium_users:
            logger.info("No premium users to send alerts")
            return 0
        
        logger.info(f"👥 {len(premium_users)} premium users available")
        
        total_alerts_sent = 0
        
        # Enviar alertas a usuarios premium
        for candidate in value_candidates:
            # Verificar si ya enviamos esta alerta
            candidate_key = f"{candidate.get('id', '')}_{candidate.get('selection', '')}"
            
            alerts_sent_for_candidate = 0
            
            for user in premium_users:
                # Verificar límites
                if not user.can_send_alert():
                    continue
                
                # Verificar duplicados
                alert_key = f"{user.chat_id}_{candidate_key}"
                if alert_key in self.sent_alerts:
                    continue
                
                # Enviar alerta
                success = await self.send_alert_to_user(user, candidate)
                if success:
                    alerts_sent_for_candidate += 1
                    total_alerts_sent += 1
                
                # Limitar alertas por candidato (evitar spam)
                if alerts_sent_for_candidate >= len(premium_users):
                    break
        
        logger.info(f"📨 Total alerts sent: {total_alerts_sent}")
        return total_alerts_sent

    async def daily_initialization(self):
        """
        Inicialización diaria a las 6 AM
        """
        logger.info("DAILY INITIALIZATION - 6 AM America")
        
        # Reset del estado de alertas diarias
        self.alerts_state.reset_if_needed()
        
        # Reset de usuarios (contadores diarios)
        users = self.users_manager.get_all_users()
        for user in users:
            user._check_reset()  # Reset contadores diarios
        
        # Limpiar sent_alerts del día anterior
        self.sent_alerts.clear()
        
        # Fetch inicial de eventos del día
        events = await self.fetch_and_update_events()
        
        # Log resumen de eventos por deporte
        sport_counts = {}
        for event in events:
            sport = event.get('sport_key', 'unknown')
            sport_counts[sport] = sport_counts.get(sport, 0) + 1
        
        logger.info("Events by sport:")
        for sport, count in sport_counts.items():
            sport_name = translate_sport(sport, sport)
            logger.info(f"  🏆 {sport_name}: {count} events")
        
        logger.info(f"✅ Daily initialization complete - monitoring {len(events)} events")

    async def hourly_update(self):
        """
        Actualización cada hora
        """
        logger.info("HOURLY UPDATE")
        
        # Actualizar eventos y cuotas
        events = await self.fetch_and_update_events()
        
        # Procesar alertas para eventos inminentes
        alerts_sent = await self.process_alerts_for_imminent_events()
        
        # Log resumen
        imminent_count = len(self.get_events_starting_soon(ALERT_WINDOW_HOURS))
        total_monitored = len(self.monitored_events)
        
        logger.info(
            f"📊 Update summary: {total_monitored} events monitored, "
            f"{imminent_count} imminent, {alerts_sent} alerts sent"
        )

    async def run_continuous_monitoring(self):
        """
        Loop principal de monitoreo continuo
        """
        logger.info("Starting continuous monitoring")
        logger.info(f"⏰ Daily start: {DAILY_START_HOUR}:00 AM America")
        logger.info(f"🔄 Updates: every {UPDATE_INTERVAL_HOURS} hour(s)")
        logger.info(f"🚨 Alert window: {ALERT_WINDOW_HOURS} hours before event")
        
        # Verificar configuración
        if not API_KEY or not BOT_TOKEN:
            logger.error("❌ Missing API_KEY or BOT_TOKEN in environment")
            return
        
        while True:
            try:
                now = datetime.now(AMERICA_TZ)
                
                # Verificar si es hora de inicialización diaria
                if self.is_daily_start_time():
                    await self.daily_initialization()
                
                # Realizar actualización cada hora
                await self.hourly_update()
                
                # Calcular tiempo hasta próxima actualización
                next_update = self.get_next_update_time()
                sleep_seconds = (next_update - now).total_seconds()
                
                # Asegurar que dormimos al menos 1 minuto
                sleep_seconds = max(60, sleep_seconds)
                
                logger.info(f"⏸️ Sleeping until next update: {next_update.strftime('%H:%M')} America ({sleep_seconds/60:.1f} min)")
                
                await asyncio.sleep(sleep_seconds)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                logger.exception("Full traceback:")
                # Esperar 5 minutos antes de reintentar
                await asyncio.sleep(300)

    async def run_immediate_check(self):
        """
        Ejecuta un chequeo inmediato (para testing)
        """
        logger.info("Running immediate check")
        
        # Fetch eventos
        await self.fetch_and_update_events()
        
        # Procesar alertas
        alerts_sent = await self.process_alerts_for_imminent_events()
        
        # Mostrar resumen
        total_events = len(self.monitored_events)
        imminent_events = len(self.get_events_starting_soon(ALERT_WINDOW_HOURS))
        
        logger.info("Immediate check results:")
        logger.info(f"  Total events: {total_events}")
        logger.info(f"  Imminent events: {imminent_events}")
        logger.info(f"  Alerts sent: {alerts_sent}")


async def main():
    """
    Función principal
    """
    monitor = ValueBotMonitor()
    
    # Verificar argumentos de línea de comandos
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        # Modo de prueba inmediata
        await monitor.run_immediate_check()
    else:
        # Modo de monitoreo continuo
        await monitor.run_continuous_monitoring()


if __name__ == "__main__":
    try:
        # Verificar que tenemos las variables necesarias
        if not API_KEY:
            print("Warning: API_KEY not found in .env - using sample data")
        
        if not BOT_TOKEN:
            print("Error: BOT_TOKEN not found in .env")
            sys.exit(1)
        
        print("Starting Value Bets Bot...")
        print(f"Monitoring: {', '.join(SPORTS)}")
        print(f"Filters: odds {MIN_ODD}-{MAX_ODD}, prob {MIN_PROB:.0%}+, max {MAX_ALERTS_PER_DAY} daily")
        print("Press Ctrl+C to stop")
        
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)