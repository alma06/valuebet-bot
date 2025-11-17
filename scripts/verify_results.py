"""
verify_results.py - Verificación automática de resultados de predicciones

Este script:
1. Obtiene predicciones pendientes de verificación
2. Consulta resultados en The Odds API
3. Actualiza la base de datos con ganancias/pérdidas reales
4. Calcula ROI real del bot

Ejecutar diariamente a las 2 AM (después de que terminen partidos)
"""

import sys
import pathlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

# Agregar proyecto al path
PROJECT_ROOT = pathlib.Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from data.odds_api import OddsFetcher
from data.historical_db import historical_db
from dotenv import load_dotenv
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()


class ResultsVerifier:
    """Verifica resultados de predicciones contra datos reales"""
    
    def __init__(self):
        self.odds_api = OddsFetcher(api_key=os.getenv('API_KEY'))
        self.db = historical_db
        
    def get_match_result(self, match_id: str, sport_key: str) -> Optional[Dict]:
        """
        Obtiene el resultado de un partido desde The Odds API
        
        Returns:
            Dict con 'home_score', 'away_score', 'winner' ('home', 'away', 'draw')
            None si no hay resultado disponible
        """
        try:
            # The Odds API tiene endpoint de scores (requiere plan pago)
            # Como fallback, usamos el estado del evento
            
            # Intentar obtener scores
            url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/scores/"
            params = {
                'apiKey': self.odds_api.api_key,
                'daysFrom': 3  # Últimos 3 días
            }
            
            response = self.odds_api.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                events = response.json()
                
                # Buscar el partido
                for event in events:
                    if event.get('id') == match_id:
                        scores = event.get('scores')
                        if scores and len(scores) >= 2:
                            home_score = scores[0].get('score')
                            away_score = scores[1].get('score')
                            
                            if home_score is not None and away_score is not None:
                                # Determinar ganador
                                if home_score > away_score:
                                    winner = 'home'
                                elif away_score > home_score:
                                    winner = 'away'
                                else:
                                    winner = 'draw'
                                
                                return {
                                    'home_score': home_score,
                                    'away_score': away_score,
                                    'winner': winner,
                                    'completed': event.get('completed', False)
                                }
                
                logger.warning(f"No se encontró resultado para {match_id}")
                return None
            
            elif response.status_code == 401:
                logger.error("API Key inválida o plan sin acceso a scores")
                return None
            
            elif response.status_code == 422:
                logger.warning(f"Sport {sport_key} no soporta scores en API")
                return None
            
            else:
                logger.error(f"Error API: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error obteniendo resultado: {e}")
            return None
    
    def calculate_profit_loss(self, prediction: Dict, result: Dict) -> float:
        """
        Calcula ganancia o pérdida de una predicción
        
        Args:
            prediction: Dict con 'selection', 'odds', 'stake'
            result: Dict con 'winner'
        
        Returns:
            float: Ganancia (positivo) o pérdida (negativo)
        """
        stake = prediction.get('stake', 0)
        odds = prediction.get('odds', 0)
        selection = prediction.get('selection', '').lower()
        winner = result.get('winner', '').lower()
        
        # Mapear selección a resultado
        selection_map = {
            'home': 'home',
            'away': 'away',
            'draw': 'draw',
            'over': 'over',
            'under': 'under'
        }
        
        # Verificar si ganó
        was_correct = False
        
        if selection in selection_map:
            was_correct = (selection_map[selection] == winner)
        else:
            # Para spreads, totals, etc.
            # Simplificado: si el winner coincide con parte del selection
            was_correct = (winner in selection)
        
        if was_correct:
            # Ganó: retorna stake * (odds - 1)
            profit = stake * (odds - 1.0)
        else:
            # Perdió: pierde el stake
            profit = -stake
        
        return profit
    
    def verify_pending_predictions(self, days: int = 1) -> Dict:
        """
        Verifica todas las predicciones pendientes de los últimos N días
        
        Args:
            days: Días hacia atrás a verificar
        
        Returns:
            Dict con estadísticas de verificación
        """
        logger.info(f"🔍 Verificando predicciones de los últimos {days} días...")
        
        # Obtener predicciones sin resultado
        import sqlite3
        conn = sqlite3.connect('data/historical.db')
        cursor = conn.cursor()
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        cursor.execute("""
            SELECT id, match_id, sport_key, selection, odds, predicted_prob, 
                   value_score, stake, predicted_at
            FROM predictions 
            WHERE actual_result IS NULL 
            AND predicted_at >= ?
            ORDER BY predicted_at ASC
        """, (cutoff_date.isoformat(),))
        
        pending = cursor.fetchall()
        conn.close()
        
        logger.info(f"📊 Encontradas {len(pending)} predicciones pendientes")
        
        stats = {
            'total_checked': 0,
            'verified': 0,
            'still_pending': 0,
            'correct': 0,
            'incorrect': 0,
            'total_profit': 0.0
        }
        
        for pred in pending:
            pred_id, match_id, sport_key, selection, odds, pred_prob, value, stake, pred_time = pred
            
            stats['total_checked'] += 1
            
            logger.info(f"Verificando predicción #{pred_id}: {match_id}")
            
            # Obtener resultado
            result = self.get_match_result(match_id, sport_key)
            
            if result is None:
                stats['still_pending'] += 1
                logger.info(f"  ⏳ Sin resultado aún")
                continue
            
            if not result.get('completed', False):
                stats['still_pending'] += 1
                logger.info(f"  ⏳ Partido no completado")
                continue
            
            # Calcular ganancia/pérdida
            profit_loss = self.calculate_profit_loss(
                {
                    'selection': selection,
                    'odds': odds,
                    'stake': stake
                },
                result
            )
            
            was_correct = (profit_loss > 0)
            
            # Actualizar en BD
            self.db.update_prediction_result(
                prediction_id=pred_id,
                actual_result=result['winner'],
                was_correct=was_correct,
                profit_loss=profit_loss
            )
            
            stats['verified'] += 1
            stats['total_profit'] += profit_loss
            
            if was_correct:
                stats['correct'] += 1
                logger.info(f"  ✅ CORRECTO - Ganancia: ${profit_loss:.2f}")
            else:
                stats['incorrect'] += 1
                logger.info(f"  ❌ INCORRECTO - Pérdida: ${profit_loss:.2f}")
        
        return stats
    
    def generate_report(self, stats: Dict) -> str:
        """Genera reporte legible de verificación"""
        
        accuracy = (stats['correct'] / stats['verified'] * 100) if stats['verified'] > 0 else 0
        
        report = f"""
╔═══════════════════════════════════════════════════╗
║     REPORTE DE VERIFICACIÓN DE RESULTADOS        ║
╚═══════════════════════════════════════════════════╝

📊 PREDICCIONES REVISADAS:
   • Total chequeadas: {stats['total_checked']}
   • Verificadas: {stats['verified']}
   • Pendientes: {stats['still_pending']}

✅ RESULTADOS:
   • Correctas: {stats['correct']}
   • Incorrectas: {stats['incorrect']}
   • Accuracy: {accuracy:.1f}%

💰 GANANCIAS/PÉRDIDAS:
   • Total: ${stats['total_profit']:+.2f}
   • Promedio por apuesta: ${stats['total_profit'] / stats['verified']:.2f} (si verified > 0)

🎯 ROI: {(stats['total_profit'] / (stats['verified'] * 25) * 100):+.1f}% (asumiendo $25 stake promedio)

Fecha: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
        return report


def main():
    """Función principal"""
    logger.info("="*60)
    logger.info("🤖 VERIFICADOR AUTOMÁTICO DE RESULTADOS")
    logger.info("="*60)
    
    verifier = ResultsVerifier()
    
    # Verificar últimos 2 días (para capturar partidos de ayer que terminaron tarde)
    stats = verifier.verify_pending_predictions(days=2)
    
    # Generar reporte
    report = verifier.generate_report(stats)
    print(report)
    
    # Guardar reporte en archivo
    reports_dir = PROJECT_ROOT / 'data' / 'reports'
    reports_dir.mkdir(exist_ok=True)
    
    report_file = reports_dir / f"verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"📄 Reporte guardado en: {report_file}")
    
    # Obtener performance general del bot
    logger.info("\n📈 PERFORMANCE GENERAL DEL BOT:")
    performance = historical_db.get_bot_performance(days=30)
    
    if performance['total_predictions'] > 0:
        print(f"""
🎯 Últimos 30 días:
   • Total predicciones: {performance['total_predictions']}
   • Correctas: {performance['correct']}
   • Accuracy: {performance['accuracy']*100:.1f}%
   • ROI: {performance['roi']*100:+.1f}%
   • Profit total: ${performance['total_profit']:+.2f}
""")
    else:
        print("\n⚠️  Sin predicciones verificadas en los últimos 30 días")
    
    logger.info("✅ Verificación completada")


if __name__ == "__main__":
    main()
