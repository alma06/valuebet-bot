"""
Results Tracker - Sistema de seguimiento y validación de precisión del bot

Características:
- Registro de todas las predicciones enviadas
- Tracking automático de resultados
- Cálculo de precisión, ROI, y métricas de performance
- Análisis por deporte, mercado, y rangos de cuota
- Generación de reportes detallados
"""
import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ResultsTracker:
    """
    Rastrea y analiza el performance del bot a lo largo del tiempo
    """
    
    def __init__(self, tracking_file: str = "data/results_history.json"):
        """
        Args:
            tracking_file: Ruta al archivo JSON de historial
        """
        self.tracking_file = tracking_file
        self.predictions = []
        self._load_history()
        
        logger.info(f"ResultsTracker inicializado con {len(self.predictions)} predicciones históricas")
    
    def _load_history(self):
        """Carga el historial de predicciones desde el archivo"""
        path = Path(self.tracking_file)
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.predictions = data.get('predictions', [])
                logger.info(f"Historial cargado: {len(self.predictions)} predicciones")
            except Exception as e:
                logger.error(f"Error cargando historial: {e}")
                self.predictions = []
        else:
            self.predictions = []
            # Crear directorio si no existe
            path.parent.mkdir(parents=True, exist_ok=True)
    
    def _save_history(self):
        """Guarda el historial al archivo"""
        try:
            path = Path(self.tracking_file)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({
                    'last_updated': datetime.now(timezone.utc).isoformat(),
                    'total_predictions': len(self.predictions),
                    'predictions': self.predictions
                }, f, indent=2, ensure_ascii=False)
                
            logger.debug(f"Historial guardado: {len(self.predictions)} predicciones")
        except Exception as e:
            logger.error(f"Error guardando historial: {e}")
    
    def add_prediction(
        self,
        event_id: str,
        sport: str,
        home: str,
        away: str,
        market: str,
        selection: str,
        odds: float,
        probability: float,
        stake: float,
        confidence: float = 1.0,
        commence_time: Optional[str] = None
    ) -> str:
        """
        Registra una nueva predicción enviada
        
        Args:
            event_id: ID del evento
            sport: Deporte
            home: Equipo local
            away: Equipo visitante
            market: Tipo de mercado (h2h, totals, spreads)
            selection: Selección apostada
            odds: Cuota
            probability: Probabilidad estimada
            stake: Stake apostado
            confidence: Score de confianza
            commence_time: Hora de inicio del evento
            
        Returns:
            str: ID de la predicción
        """
        prediction_id = f"{event_id}_{market}_{selection}_{datetime.now(timezone.utc).timestamp()}"
        
        prediction = {
            'id': prediction_id,
            'event_id': event_id,
            'sport': sport,
            'home': home,
            'away': away,
            'market': market,
            'selection': selection,
            'odds': odds,
            'probability': probability,
            'stake': stake,
            'confidence': confidence,
            'commence_time': commence_time,
            'prediction_date': datetime.now(timezone.utc).isoformat(),
            'result': None,  # 'win', 'loss', 'void'
            'result_date': None,
            'profit': None,
            'roi': None
        }
        
        self.predictions.append(prediction)
        self._save_history()
        
        logger.info(f"Predicción registrada: {sport} - {selection} @ {odds} (Stake: ${stake})")
        
        return prediction_id
    
    def update_result(
        self,
        prediction_id: str,
        result: str,
        actual_odds: Optional[float] = None
    ) -> bool:
        """
        Actualiza el resultado de una predicción
        
        Args:
            prediction_id: ID de la predicción
            result: 'win', 'loss', o 'void'
            actual_odds: Cuota final si cambió
            
        Returns:
            bool: True si se actualizó correctamente
        """
        for pred in self.predictions:
            if pred['id'] == prediction_id:
                pred['result'] = result
                pred['result_date'] = datetime.now(timezone.utc).isoformat()
                
                # Calcular profit y ROI
                stake = pred['stake']
                odds = actual_odds if actual_odds else pred['odds']
                
                if result == 'win':
                    pred['profit'] = stake * (odds - 1)
                    pred['roi'] = ((odds - 1) * 100)
                elif result == 'loss':
                    pred['profit'] = -stake
                    pred['roi'] = -100.0
                else:  # void
                    pred['profit'] = 0.0
                    pred['roi'] = 0.0
                
                self._save_history()
                logger.info(f"Resultado actualizado: {prediction_id} -> {result} (Profit: ${pred['profit']})")
                return True
        
        logger.warning(f"Predicción no encontrada: {prediction_id}")
        return False
    
    def get_pending_predictions(self) -> List[Dict]:
        """
        Obtiene predicciones pendientes de resultado
        
        Returns:
            List de predicciones sin resultado
        """
        return [p for p in self.predictions if p['result'] is None]
    
    def get_settled_predictions(self) -> List[Dict]:
        """
        Obtiene predicciones con resultado
        
        Returns:
            List de predicciones con resultado
        """
        return [p for p in self.predictions if p['result'] is not None]
    
    def calculate_accuracy(self, sport: Optional[str] = None, market: Optional[str] = None) -> float:
        """
        Calcula el porcentaje de acierto
        
        Args:
            sport: Filtrar por deporte (opcional)
            market: Filtrar por mercado (opcional)
            
        Returns:
            float: Porcentaje de acierto (0-100)
        """
        settled = self.get_settled_predictions()
        
        # Filtrar
        if sport:
            settled = [p for p in settled if p['sport'] == sport]
        if market:
            settled = [p for p in settled if p['market'] == market]
        
        if not settled:
            return 0.0
        
        wins = len([p for p in settled if p['result'] == 'win'])
        total = len([p for p in settled if p['result'] in ['win', 'loss']])
        
        if total == 0:
            return 0.0
        
        return (wins / total) * 100
    
    def calculate_roi(self, sport: Optional[str] = None, market: Optional[str] = None) -> float:
        """
        Calcula el ROI total
        
        Args:
            sport: Filtrar por deporte (opcional)
            market: Filtrar por mercado (opcional)
            
        Returns:
            float: ROI en porcentaje
        """
        settled = self.get_settled_predictions()
        
        # Filtrar
        if sport:
            settled = [p for p in settled if p['sport'] == sport]
        if market:
            settled = [p for p in settled if p['market'] == market]
        
        if not settled:
            return 0.0
        
        total_staked = sum(p['stake'] for p in settled)
        total_profit = sum(p['profit'] for p in settled if p['profit'] is not None)
        
        if total_staked == 0:
            return 0.0
        
        return (total_profit / total_staked) * 100
    
    def calculate_ev_accuracy(self) -> Tuple[float, float]:
        """
        Compara EV esperado vs EV real (calibración del modelo)
        
        Returns:
            Tuple[float, float]: (EV esperado promedio, EV real promedio)
        """
        settled = self.get_settled_predictions()
        
        if not settled:
            return (0.0, 0.0)
        
        expected_evs = []
        actual_evs = []
        
        for pred in settled:
            if pred['result'] in ['win', 'loss']:
                # EV esperado = (prob * profit_if_win) - ((1-prob) * stake)
                prob = pred['probability']
                odds = pred['odds']
                stake = pred['stake']
                
                expected_profit = stake * (odds - 1)
                expected_ev = (prob * expected_profit) - ((1 - prob) * stake)
                
                # EV real es el profit real
                actual_ev = pred['profit']
                
                expected_evs.append(expected_ev)
                actual_evs.append(actual_ev)
        
        if not expected_evs:
            return (0.0, 0.0)
        
        avg_expected = sum(expected_evs) / len(expected_evs)
        avg_actual = sum(actual_evs) / len(actual_evs)
        
        return (avg_expected, avg_actual)
    
    def get_stats_by_sport(self) -> Dict[str, Dict]:
        """
        Genera estadísticas detalladas por deporte
        
        Returns:
            Dict con stats por deporte
        """
        settled = self.get_settled_predictions()
        sports = set(p['sport'] for p in settled)
        
        stats = {}
        for sport in sports:
            sport_preds = [p for p in settled if p['sport'] == sport]
            
            wins = len([p for p in sport_preds if p['result'] == 'win'])
            total = len([p for p in sport_preds if p['result'] in ['win', 'loss']])
            
            total_staked = sum(p['stake'] for p in sport_preds)
            total_profit = sum(p['profit'] for p in sport_preds if p['profit'] is not None)
            
            stats[sport] = {
                'total_predictions': len(sport_preds),
                'wins': wins,
                'losses': total - wins,
                'accuracy': (wins / total * 100) if total > 0 else 0,
                'total_staked': round(total_staked, 2),
                'total_profit': round(total_profit, 2),
                'roi': round((total_profit / total_staked * 100), 2) if total_staked > 0 else 0
            }
        
        return stats
    
    def get_stats_by_odds_range(self) -> Dict[str, Dict]:
        """
        Genera estadísticas por rangos de cuota
        
        Returns:
            Dict con stats por rango de odds
        """
        settled = self.get_settled_predictions()
        
        ranges = {
            '1.50-1.80': (1.50, 1.80),
            '1.81-2.00': (1.81, 2.00),
            '2.01-2.25': (2.01, 2.25),
            '2.26-2.50': (2.26, 2.50),
            '2.51+': (2.51, float('inf'))
        }
        
        stats = {}
        for range_name, (min_odd, max_odd) in ranges.items():
            range_preds = [p for p in settled if min_odd <= p['odds'] < max_odd and p['result'] in ['win', 'loss']]
            
            if range_preds:
                wins = len([p for p in range_preds if p['result'] == 'win'])
                total = len(range_preds)
                
                total_staked = sum(p['stake'] for p in range_preds)
                total_profit = sum(p['profit'] for p in range_preds if p['profit'] is not None)
                
                stats[range_name] = {
                    'total_predictions': total,
                    'wins': wins,
                    'losses': total - wins,
                    'accuracy': round((wins / total * 100), 2),
                    'roi': round((total_profit / total_staked * 100), 2) if total_staked > 0 else 0
                }
        
        return stats
    
    def generate_report(self) -> str:
        """
        Genera un reporte completo de performance
        
        Returns:
            str: Reporte formateado
        """
        settled = self.get_settled_predictions()
        pending = self.get_pending_predictions()
        
        if not settled:
            return "No hay predicciones con resultado todavia"
        
        overall_accuracy = self.calculate_accuracy()
        overall_roi = self.calculate_roi()
        expected_ev, actual_ev = self.calculate_ev_accuracy()
        
        wins = len([p for p in settled if p['result'] == 'win'])
        losses = len([p for p in settled if p['result'] == 'loss'])
        voids = len([p for p in settled if p['result'] == 'void'])
        
        total_staked = sum(p['stake'] for p in settled)
        total_profit = sum(p['profit'] for p in settled if p['profit'] is not None)
        
        lines = [
            "="*70,
            "REPORTE DE PERFORMANCE DEL BOT",
            "="*70,
            "",
            "RESUMEN GENERAL:",
            f"  Total predicciones: {len(self.predictions)}",
            f"  Resueltas: {len(settled)} | Pendientes: {len(pending)}",
            f"  Ganadas: {wins} | Perdidas: {losses} | Anuladas: {voids}",
            "",
            "METRICAS CLAVE:",
            f"  Precision: {overall_accuracy:.2f}%",
            f"  ROI: {overall_roi:+.2f}%",
            f"  Total apostado: ${total_staked:.2f}",
            f"  Profit total: ${total_profit:+.2f}",
            "",
            "CALIBRACION DEL MODELO:",
            f"  EV esperado promedio: ${expected_ev:.2f}",
            f"  EV real promedio: ${actual_ev:.2f}",
            f"  Diferencia: ${(actual_ev - expected_ev):+.2f}",
            "",
            "-"*70,
            "STATS POR DEPORTE:",
            "-"*70,
        ]
        
        stats_by_sport = self.get_stats_by_sport()
        for sport, stats in sorted(stats_by_sport.items()):
            lines.append(f"\n{sport}:")
            lines.append(f"  Predicciones: {stats['total_predictions']} | W: {stats['wins']} | L: {stats['losses']}")
            lines.append(f"  Precision: {stats['accuracy']:.2f}% | ROI: {stats['roi']:+.2f}%")
            lines.append(f"  Apostado: ${stats['total_staked']:.2f} | Profit: ${stats['total_profit']:+.2f}")
        
        lines.append("")
        lines.append("-"*70)
        lines.append("STATS POR RANGO DE CUOTA:")
        lines.append("-"*70)
        
        stats_by_odds = self.get_stats_by_odds_range()
        for range_name, stats in sorted(stats_by_odds.items()):
            lines.append(f"\n{range_name}:")
            lines.append(f"  Predicciones: {stats['total_predictions']} | W: {stats['wins']} | L: {stats['losses']}")
            lines.append(f"  Precision: {stats['accuracy']:.2f}% | ROI: {stats['roi']:+.2f}%")
        
        lines.append("")
        lines.append("="*70)
        
        return "\n".join(lines)


# Ejemplo de uso
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Crear tracker
    tracker = ResultsTracker("data/results_history.json")
    
    # Registrar algunas predicciones de ejemplo
    pred1_id = tracker.add_prediction(
        event_id="evt_123",
        sport="basketball_nba",
        home="Lakers",
        away="Warriors",
        market="h2h",
        selection="Lakers",
        odds=1.85,
        probability=0.60,
        stake=25.0,
        confidence=0.85
    )
    
    pred2_id = tracker.add_prediction(
        event_id="evt_124",
        sport="baseball_mlb",
        home="Yankees",
        away="Red Sox",
        market="totals",
        selection="Over 8.5",
        odds=1.95,
        probability=0.58,
        stake=20.0,
        confidence=0.75
    )
    
    # Simular resultados
    tracker.update_result(pred1_id, 'win')
    tracker.update_result(pred2_id, 'loss')
    
    # Generar reporte
    print(tracker.generate_report())
