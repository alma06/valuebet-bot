"""
Advanced Predictor - Modelo predictivo avanzado con estadísticas contextuales

Características:
- Análisis ofensivo/defensivo por equipo
- Factor local/visitante
- Impacto de lesiones y suspensiones
- Factores climáticos para deportes al aire libre
- Racha reciente y head-to-head
- Rest days y back-to-back games
- Ajuste dinámico de probabilidades
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
import logging
import math

logger = logging.getLogger(__name__)


class AdvancedPredictor:
    """
    Modelo predictivo avanzado que ajusta probabilidades base con factores contextuales
    """
    
    # Pesos de factores para diferentes deportes
    SPORT_WEIGHTS = {
        'basketball_nba': {
            'home_advantage': 0.035,  # 3.5% boost para local
            'rest_days': 0.02,
            'back_to_back': -0.04,
            'injuries': 0.10,
            'recent_form': 0.06,
            'head_to_head': 0.04
        },
        'baseball_mlb': {
            'home_advantage': 0.025,
            'pitcher_matchup': 0.15,
            'weather': 0.05,
            'injuries': 0.08,
            'recent_form': 0.05,
            'head_to_head': 0.04
        },
        'soccer': {
            'home_advantage': 0.045,
            'injuries': 0.12,
            'recent_form': 0.08,
            'head_to_head': 0.05,
            'rest_days': 0.03
        },
        'americanfootball_nfl': {
            'home_advantage': 0.03,
            'injuries': 0.15,
            'weather': 0.06,
            'rest_days': 0.04,
            'recent_form': 0.07
        }
    }
    
    def __init__(self):
        logger.info("AdvancedPredictor inicializado")
    
    def _get_sport_key(self, sport: str) -> str:
        """Normaliza el sport_key"""
        if 'basketball' in sport or 'nba' in sport:
            return 'basketball_nba'
        elif 'baseball' in sport or 'mlb' in sport:
            return 'baseball_mlb'
        elif 'soccer' in sport or 'football' in sport.lower():
            return 'soccer'
        elif 'americanfootball' in sport or 'nfl' in sport:
            return 'americanfootball_nfl'
        else:
            return 'default'
    
    def adjust_probability(
        self,
        base_probability: float,
        sport: str,
        is_home: bool = True,
        context: Optional[Dict] = None
    ) -> Tuple[float, Dict]:
        """
        Ajusta la probabilidad base con factores contextuales
        
        Args:
            base_probability: Probabilidad base (0-1)
            sport: Deporte del evento
            is_home: True si es equipo local
            context: Dict con información contextual
            
        Returns:
            Tuple[float, Dict]: (probabilidad ajustada, factores aplicados)
        """
        if context is None:
            context = {}
        
        sport_key = self._get_sport_key(sport)
        weights = self.SPORT_WEIGHTS.get(sport_key, self.SPORT_WEIGHTS.get('default', {}))
        
        adjustments = {}
        total_adjustment = 0.0
        
        # 1. Home Advantage
        if is_home and 'home_advantage' in weights:
            home_adj = weights['home_advantage']
            adjustments['home_advantage'] = home_adj
            total_adjustment += home_adj
        
        # 2. Rest Days
        rest_days = context.get('rest_days', 0)
        if rest_days is not None and 'rest_days' in weights:
            if rest_days >= 3:
                rest_adj = weights['rest_days'] * 1.0  # Bien descansado
            elif rest_days == 2:
                rest_adj = weights['rest_days'] * 0.5
            elif rest_days == 1:
                rest_adj = 0.0  # Normal
            else:  # 0 días (back-to-back)
                rest_adj = weights.get('back_to_back', -0.04)
            
            adjustments['rest_days'] = rest_adj
            total_adjustment += rest_adj
        
        # 3. Injuries Impact
        injury_impact = context.get('injury_impact', 0.0)  # 0 a 1 (1 = máximo impacto)
        if injury_impact > 0 and 'injuries' in weights:
            # Impacto negativo proporcional
            injury_adj = -weights['injuries'] * injury_impact
            adjustments['injuries'] = injury_adj
            total_adjustment += injury_adj
        
        # 4. Recent Form
        recent_form = context.get('recent_form', 0.0)  # -1 a +1 (mala a buena racha)
        if recent_form != 0 and 'recent_form' in weights:
            form_adj = weights['recent_form'] * recent_form
            adjustments['recent_form'] = form_adj
            total_adjustment += form_adj
        
        # 5. Head-to-Head
        h2h_advantage = context.get('h2h_advantage', 0.0)  # -1 a +1
        if h2h_advantage != 0 and 'head_to_head' in weights:
            h2h_adj = weights['head_to_head'] * h2h_advantage
            adjustments['head_to_head'] = h2h_adj
            total_adjustment += h2h_adj
        
        # 6. Weather (para deportes al aire libre)
        weather_impact = context.get('weather_impact', 0.0)  # -1 a +1
        if weather_impact != 0 and 'weather' in weights:
            weather_adj = weights['weather'] * weather_impact
            adjustments['weather'] = weather_adj
            total_adjustment += weather_adj
        
        # 7. Pitcher Matchup (baseball)
        pitcher_advantage = context.get('pitcher_advantage', 0.0)  # -1 a +1
        if pitcher_advantage != 0 and 'pitcher_matchup' in weights:
            pitcher_adj = weights['pitcher_matchup'] * pitcher_advantage
            adjustments['pitcher_matchup'] = pitcher_adj
            total_adjustment += pitcher_adj
        
        # Aplicar ajuste total con límites
        adjusted_probability = base_probability + total_adjustment
        
        # Mantener en rango válido [0.05, 0.95]
        adjusted_probability = max(0.05, min(0.95, adjusted_probability))
        
        adjustments['total_adjustment'] = total_adjustment
        adjustments['final_probability'] = adjusted_probability
        
        logger.debug(
            f"Probability adjusted: {base_probability:.3f} -> {adjusted_probability:.3f} "
            f"(adj: {total_adjustment:+.3f})"
        )
        
        return (adjusted_probability, adjustments)
    
    def calculate_injury_impact(self, injuries: List[Dict]) -> float:
        """
        Calcula el impacto agregado de lesiones
        
        Args:
            injuries: Lista de lesiones con {player_importance: float, status: str}
            
        Returns:
            float: Impacto total (0-1)
        """
        if not injuries:
            return 0.0
        
        total_impact = 0.0
        
        for injury in injuries:
            importance = injury.get('player_importance', 0.5)  # 0-1
            status = injury.get('status', 'day_to_day').lower()
            
            # Multiplicador según status
            if status in ['out', 'doubtful']:
                status_mult = 1.0
            elif status in ['questionable']:
                status_mult = 0.5
            elif status in ['day_to_day', 'probable']:
                status_mult = 0.2
            else:
                status_mult = 0.1
            
            total_impact += importance * status_mult
        
        # Normalizar (máximo 1.0)
        return min(1.0, total_impact)
    
    def calculate_recent_form(self, recent_results: List[str]) -> float:
        """
        Calcula la racha reciente del equipo
        
        Args:
            recent_results: Lista de últimos resultados ['W', 'L', 'W', ...]
            
        Returns:
            float: Score de racha (-1 a +1)
        """
        if not recent_results:
            return 0.0
        
        # Dar más peso a partidos más recientes
        weighted_sum = 0.0
        weight_total = 0.0
        
        for i, result in enumerate(recent_results):
            weight = 1.0 / (i + 1)  # Más reciente = más peso
            
            if result == 'W':
                weighted_sum += weight
            elif result == 'L':
                weighted_sum -= weight
            # 'D' (draw) no suma ni resta
            
            weight_total += weight
        
        if weight_total == 0:
            return 0.0
        
        form_score = weighted_sum / weight_total
        
        # Normalizar a [-1, 1]
        return max(-1.0, min(1.0, form_score))
    
    def calculate_h2h_advantage(self, h2h_results: List[str]) -> float:
        """
        Calcula ventaja en enfrentamientos directos
        
        Args:
            h2h_results: Lista de resultados h2h desde perspectiva del equipo ['W', 'L', 'D', ...]
            
        Returns:
            float: Ventaja h2h (-1 a +1)
        """
        if not h2h_results or len(h2h_results) < 3:
            return 0.0  # Muestra insuficiente
        
        wins = h2h_results.count('W')
        losses = h2h_results.count('L')
        total = wins + losses
        
        if total == 0:
            return 0.0
        
        win_rate = wins / total
        
        # Convertir win_rate [0,1] a advantage [-1,1]
        advantage = (win_rate - 0.5) * 2
        
        return advantage
    
    def calculate_weather_impact(
        self,
        weather: Dict,
        sport: str,
        team_style: Optional[str] = None
    ) -> float:
        """
        Calcula impacto del clima
        
        Args:
            weather: Dict con {temp, wind, precipitation, conditions}
            sport: Deporte
            team_style: Estilo de juego del equipo (opcional)
            
        Returns:
            float: Impacto del clima (-1 a +1)
        """
        if not weather or sport not in ['baseball_mlb', 'americanfootball_nfl', 'soccer']:
            return 0.0
        
        impact = 0.0
        
        temp = weather.get('temp')
        wind = weather.get('wind')
        precip = weather.get('precipitation', 0)
        
        # Baseball: viento afecta mucho
        if sport == 'baseball_mlb':
            if wind and wind > 15:
                impact -= 0.3  # Viento fuerte = más difícil
            if precip and precip > 0.5:
                impact -= 0.4  # Lluvia = peor condiciones
        
        # Football: clima extremo favorece defensa
        elif sport == 'americanfootball_nfl':
            if temp and temp < 32:  # Frío extremo
                if team_style == 'offensive':
                    impact -= 0.3
                elif team_style == 'defensive':
                    impact += 0.2
            
            if wind and wind > 20:
                impact -= 0.2
            
            if precip and precip > 0.5:
                impact -= 0.3
        
        # Soccer: lluvia afecta juego técnico
        elif sport == 'soccer':
            if precip and precip > 0.5:
                if team_style == 'technical':
                    impact -= 0.3
                elif team_style == 'physical':
                    impact += 0.2
        
        return max(-1.0, min(1.0, impact))
    
    def enhance_prediction(
        self,
        event: Dict,
        base_prob_home: float,
        base_prob_away: float,
        additional_data: Optional[Dict] = None
    ) -> Dict:
        """
        Genera predicción mejorada con análisis contextual completo
        
        Args:
            event: Dict con info del evento
            base_prob_home: Probabilidad base del local
            base_prob_away: Probabilidad base del visitante
            additional_data: Datos adicionales de contexto
            
        Returns:
            Dict con probabilidades ajustadas y análisis
        """
        sport = event.get('sport_key', '')
        
        if additional_data is None:
            additional_data = {}
        
        # Contexto para local
        home_context = {
            'rest_days': additional_data.get('home_rest_days'),
            'injury_impact': additional_data.get('home_injury_impact', 0.0),
            'recent_form': additional_data.get('home_recent_form', 0.0),
            'h2h_advantage': additional_data.get('home_h2h_advantage', 0.0),
            'weather_impact': additional_data.get('home_weather_impact', 0.0),
            'pitcher_advantage': additional_data.get('home_pitcher_advantage', 0.0)
        }
        
        # Contexto para visitante
        away_context = {
            'rest_days': additional_data.get('away_rest_days'),
            'injury_impact': additional_data.get('away_injury_impact', 0.0),
            'recent_form': additional_data.get('away_recent_form', 0.0),
            'h2h_advantage': additional_data.get('away_h2h_advantage', 0.0),
            'weather_impact': additional_data.get('away_weather_impact', 0.0),
            'pitcher_advantage': additional_data.get('away_pitcher_advantage', 0.0)
        }
        
        # Ajustar probabilidades
        adjusted_home, home_factors = self.adjust_probability(
            base_prob_home, sport, is_home=True, context=home_context
        )
        
        adjusted_away, away_factors = self.adjust_probability(
            base_prob_away, sport, is_home=False, context=away_context
        )
        
        # Normalizar para que sumen 1 (si es h2h sin empate)
        if 'draw' not in additional_data:
            total = adjusted_home + adjusted_away
            if total > 0:
                adjusted_home = adjusted_home / total
                adjusted_away = adjusted_away / total
        
        # Calcular confidence score
        confidence = self._calculate_confidence(home_factors, away_factors)
        
        return {
            'home_prob_base': base_prob_home,
            'away_prob_base': base_prob_away,
            'home_prob_adjusted': round(adjusted_home, 4),
            'away_prob_adjusted': round(adjusted_away, 4),
            'home_factors': home_factors,
            'away_factors': away_factors,
            'confidence_score': round(confidence, 3),
            'analysis': self._generate_analysis_text(
                event.get('home_team', 'Home'),
                event.get('away_team', 'Away'),
                home_factors,
                away_factors
            )
        }
    
    def _calculate_confidence(self, home_factors: Dict, away_factors: Dict) -> float:
        """
        Calcula score de confianza basado en cantidad y calidad de datos
        
        Returns:
            float: Confidence score (0-1)
        """
        # Contar factores usados
        home_count = len([v for k, v in home_factors.items() if k not in ['total_adjustment', 'final_probability']])
        away_count = len([v for k, v in away_factors.items() if k not in ['total_adjustment', 'final_probability']])
        
        avg_factors = (home_count + away_count) / 2
        
        # Más factores = más confianza
        factor_score = min(1.0, avg_factors / 5.0)  # Máximo con 5 factores
        
        # Magnitud de ajustes (ajustes moderados = más confianza)
        home_adj = abs(home_factors.get('total_adjustment', 0))
        away_adj = abs(away_factors.get('total_adjustment', 0))
        avg_adj = (home_adj + away_adj) / 2
        
        # Ajustes entre 0.05 y 0.15 son óptimos
        if 0.05 <= avg_adj <= 0.15:
            adj_score = 1.0
        elif avg_adj < 0.05:
            adj_score = 0.7  # Pocos datos
        else:
            adj_score = max(0.5, 1.0 - (avg_adj - 0.15))  # Ajustes muy grandes = menos confianza
        
        # Combinar scores
        confidence = (factor_score * 0.6 + adj_score * 0.4)
        
        return confidence
    
    def _generate_analysis_text(
        self,
        home_team: str,
        away_team: str,
        home_factors: Dict,
        away_factors: Dict
    ) -> str:
        """Genera texto de análisis contextual"""
        lines = []
        
        # Analizar factores principales
        home_adj = home_factors.get('total_adjustment', 0)
        away_adj = away_factors.get('total_adjustment', 0)
        
        if home_adj > 0.05:
            lines.append(f"{home_team} tiene ventajas significativas")
        elif away_adj > 0.05:
            lines.append(f"{away_team} tiene ventajas significativas")
        else:
            lines.append("Partido equilibrado segun analisis contextual")
        
        # Destacar factores clave
        if home_factors.get('injuries', 0) < -0.05:
            lines.append(f"- {home_team} afectado por lesiones importantes")
        if away_factors.get('injuries', 0) < -0.05:
            lines.append(f"- {away_team} afectado por lesiones importantes")
        
        if home_factors.get('recent_form', 0) > 0.03:
            lines.append(f"- {home_team} en buena racha reciente")
        elif home_factors.get('recent_form', 0) < -0.03:
            lines.append(f"- {home_team} en mala racha")
        
        if away_factors.get('recent_form', 0) > 0.03:
            lines.append(f"- {away_team} en buena racha reciente")
        elif away_factors.get('recent_form', 0) < -0.03:
            lines.append(f"- {away_team} en mala racha")
        
        return " ".join(lines) if lines else "Analisis contextual disponible"


# Ejemplo de uso
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    predictor = AdvancedPredictor()
    
    # Ejemplo de predicción mejorada
    event = {
        'sport_key': 'basketball_nba',
        'home_team': 'Lakers',
        'away_team': 'Warriors'
    }
    
    additional_data = {
        'home_rest_days': 2,
        'home_injury_impact': 0.2,  # Una lesión menor
        'home_recent_form': 0.6,  # Buena racha
        'home_h2h_advantage': -0.3,  # Malo historial vs Warriors
        'away_rest_days': 1,
        'away_injury_impact': 0.0,
        'away_recent_form': 0.3,
        'away_h2h_advantage': 0.3
    }
    
    result = predictor.enhance_prediction(
        event,
        base_prob_home=0.52,
        base_prob_away=0.48,
        additional_data=additional_data
    )
    
    print("="*70)
    print("PREDICCION MEJORADA")
    print("="*70)
    print(f"\nProbabilidades base:")
    print(f"  Lakers: {result['home_prob_base']:.1%}")
    print(f"  Warriors: {result['away_prob_base']:.1%}")
    print(f"\nProbabilidades ajustadas:")
    print(f"  Lakers: {result['home_prob_adjusted']:.1%}")
    print(f"  Warriors: {result['away_prob_adjusted']:.1%}")
    print(f"\nConfidence Score: {result['confidence_score']:.1%}")
    print(f"\nAnalisis: {result['analysis']}")
