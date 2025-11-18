"""
analytics/performance_tracker.py - Sistema de seguimiento de rendimiento del bot

Consulta tabla 'predictions' en Supabase y calcula estadísticas globales:
- Total de pronósticos enviados
- Aciertos y fallos
- % de efectividad
- ROI acumulado
"""
import logging
from typing import Dict, Optional
from datetime import datetime, timezone, timedelta
from data.historical_db import historical_db

logger = logging.getLogger(__name__)


class PerformanceTracker:
    """Rastrea el rendimiento global del bot"""

    def __init__(self):
        self.db = historical_db

    def get_global_stats(self, days: int = 30) -> Dict:
        """
        Obtener estadísticas globales del bot
        
        Args:
            days: Número de días hacia atrás a considerar (default: 30)
            
        Returns:
            Dict con estadísticas:
            {
                'total_predictions': int,
                'won': int,
                'lost': int,
                'pending': int,
                'win_rate': float,
                'roi': float,
                'total_stake': float,
                'total_profit': float,
                'avg_odd': float,
                'best_sport': str
            }
        """
        try:
            # Calcular fecha límite
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            cutoff_str = cutoff_date.isoformat()

            # Consultar todas las predicciones
            response = self.db.supabase.table('predictions') \
                .select('*') \
                .gte('created_at', cutoff_str) \
                .execute()

            predictions = response.data

            if not predictions:
                return self._empty_stats()

            # Calcular estadísticas
            total = len(predictions)
            won = sum(1 for p in predictions if p.get('result') == 'won')
            lost = sum(1 for p in predictions if p.get('result') == 'lost')
            pending = sum(1 for p in predictions if p.get('result') in [None, 'pending'])

            # Win rate
            settled = won + lost
            win_rate = (won / settled * 100) if settled > 0 else 0

            # ROI y ganancias
            total_stake = 0
            total_profit = 0
            
            for p in predictions:
                if p.get('result') in ['won', 'lost']:
                    stake = float(p.get('stake', 20))
                    odd = float(p.get('odds', 1.0))
                    
                    total_stake += stake
                    
                    if p.get('result') == 'won':
                        total_profit += (stake * odd) - stake
                    else:
                        total_profit -= stake

            roi = (total_profit / total_stake * 100) if total_stake > 0 else 0

            # Cuota promedio
            avg_odd = sum(float(p.get('odds', 0)) for p in predictions) / total if total > 0 else 0

            # Mejor deporte por win rate
            sports_stats = {}
            for p in predictions:
                sport = p.get('sport_key', 'unknown')
                if sport not in sports_stats:
                    sports_stats[sport] = {'won': 0, 'total': 0}
                
                sports_stats[sport]['total'] += 1
                if p.get('result') == 'won':
                    sports_stats[sport]['won'] += 1

            best_sport = 'N/A'
            best_rate = 0
            for sport, stats in sports_stats.items():
                if stats['total'] >= 5:  # Mínimo 5 picks
                    rate = stats['won'] / stats['total']
                    if rate > best_rate:
                        best_rate = rate
                        best_sport = sport

            return {
                'total_predictions': total,
                'won': won,
                'lost': lost,
                'pending': pending,
                'win_rate': round(win_rate, 1),
                'roi': round(roi, 1),
                'total_stake': round(total_stake, 2),
                'total_profit': round(total_profit, 2),
                'avg_odd': round(avg_odd, 2),
                'best_sport': best_sport,
                'days': days
            }

        except Exception as e:
            logger.error(f"Error calculando estadísticas globales: {e}")
            return self._empty_stats()

    def get_recent_results(self, limit: int = 10) -> list:
        """
        Obtener últimos resultados del bot
        
        Args:
            limit: Número de resultados a retornar
            
        Returns:
            Lista de predicciones con resultado
        """
        try:
            response = self.db.supabase.table('predictions') \
                .select('*') \
                .not_.is_('result', 'null') \
                .order('event_start_time', desc=True) \
                .limit(limit) \
                .execute()

            return response.data

        except Exception as e:
            logger.error(f"Error obteniendo resultados recientes: {e}")
            return []

    def get_sport_breakdown(self) -> Dict:
        """
        Obtener desglose de estadísticas por deporte
        
        Returns:
            Dict con stats por deporte:
            {
                'basketball_nba': {'total': 50, 'won': 30, 'win_rate': 60.0, 'roi': 15.5},
                ...
            }
        """
        try:
            response = self.db.supabase.table('predictions') \
                .select('sport_key, result, odds, stake') \
                .execute()

            predictions = response.data
            sports = {}

            for p in predictions:
                sport = p.get('sport_key', 'unknown')
                if sport not in sports:
                    sports[sport] = {
                        'total': 0,
                        'won': 0,
                        'lost': 0,
                        'stake': 0,
                        'profit': 0
                    }

                sports[sport]['total'] += 1
                
                if p.get('result') == 'won':
                    sports[sport]['won'] += 1
                    stake = float(p.get('stake', 20))
                    odd = float(p.get('odds', 1.0))
                    sports[sport]['stake'] += stake
                    sports[sport]['profit'] += (stake * odd) - stake
                elif p.get('result') == 'lost':
                    sports[sport]['lost'] += 1
                    stake = float(p.get('stake', 20))
                    sports[sport]['stake'] += stake
                    sports[sport]['profit'] -= stake

            # Calcular win_rate y ROI
            for sport, stats in sports.items():
                settled = stats['won'] + stats['lost']
                stats['win_rate'] = round(stats['won'] / settled * 100, 1) if settled > 0 else 0
                stats['roi'] = round(stats['profit'] / stats['stake'] * 100, 1) if stats['stake'] > 0 else 0

            return sports

        except Exception as e:
            logger.error(f"Error calculando desglose por deporte: {e}")
            return {}

    def _empty_stats(self) -> Dict:
        """Estadísticas vacías por defecto"""
        return {
            'total_predictions': 0,
            'won': 0,
            'lost': 0,
            'pending': 0,
            'win_rate': 0,
            'roi': 0,
            'total_stake': 0,
            'total_profit': 0,
            'avg_odd': 0,
            'best_sport': 'N/A',
            'days': 30
        }


# Instancia global
performance_tracker = PerformanceTracker()
