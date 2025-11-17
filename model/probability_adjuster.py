"""
model/probability_adjuster.py - Ajusta probabilidades basado en información en tiempo real

Este módulo toma las probabilidades estimadas base y las ajusta usando:
- Información de lesiones en tiempo real
- Estados de alineaciones confirmadas  
- Noticias de impacto
- Factores contextuales del partido
"""

import asyncio
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import re
import math

# Importar el cliente de APIs deportivas
from data.sports_api import get_sports_info

logger = logging.getLogger(__name__)


class ProbabilityAdjuster:
    def __init__(self):
        # Factores de ajuste por tipo de información
        self.injury_factors = {
            'star_player_out': -0.15,      # Estrella fuera: -15% probabilidad
            'starter_out': -0.08,          # Titular fuera: -8% probabilidad  
            'key_player_doubtful': -0.05,  # Jugador clave dudoso: -5%
            'role_player_out': -0.02,      # Jugador de rol fuera: -2%
            'minor_injury': -0.01          # Lesión menor: -1%
        }
        
        self.lineup_factors = {
            'confirmed_lineup': +0.03,      # Alineación confirmada: +3%
            'optimal_lineup': +0.05,        # Alineación óptima: +5%
            'rotational_changes': -0.02,    # Cambios de rotación: -2%
            'emergency_lineup': -0.08,      # Alineación de emergencia: -8%
            'untested_lineup': -0.05        # Alineación no probada: -5%
        }
        
        self.news_factors = {
            'positive_momentum': +0.02,     # Momentum positivo: +2%
            'team_chemistry_good': +0.03,   # Buena química: +3%
            'coaching_stability': +0.01,    # Estabilidad coaching: +1%
            'negative_news': -0.04,         # Noticias negativas: -4%
            'internal_conflict': -0.06,     # Conflicto interno: -6%
            'distraction': -0.03            # Distracciones: -3%
        }

    async def adjust_probabilities(self, candidates: List[Dict]) -> List[Dict]:
        """
        Ajusta las probabilidades de todos los candidatos usando información en tiempo real
        
        Args:
            candidates: Lista de candidatos con probabilidades base
            
        Returns:
            Lista de candidatos con probabilidades ajustadas
        """
        adjusted_candidates = []
        
        for candidate in candidates:
            try:
                adjusted_candidate = await self._adjust_single_candidate(candidate)
                adjusted_candidates.append(adjusted_candidate)
                
            except Exception as e:
                logger.warning(f"Error adjusting candidate {candidate.get('event', 'Unknown')}: {e}")
                # Si hay error, usar candidato original
                adjusted_candidates.append(candidate)
        
        return adjusted_candidates

    async def _adjust_single_candidate(self, candidate: Dict) -> Dict:
        """
        Ajusta las probabilidades de un candidato individual
        """
        # Extraer información del evento
        event = candidate.get('event', '')
        sport = candidate.get('sport_key', '')
        market = candidate.get('market_key', '')
        selection = candidate.get('selection', '')
        
        # Obtener equipos del evento
        home_team, away_team = self._extract_teams(event)
        
        # Obtener información deportiva en tiempo real
        sports_info = await get_sports_info(sport, home_team, away_team)
        
        # Calcular ajustes
        adjustments = await self._calculate_adjustments(
            candidate, sports_info, home_team, away_team
        )
        
        # Aplicar ajustes a la probabilidad
        original_prob = candidate.get('prob_calculated', candidate.get('real_probability', 0.55))
        if isinstance(original_prob, (int, float)):
            if original_prob > 1:  # Si está en porcentaje (55.0)
                original_prob = original_prob / 100
        else:
            original_prob = 0.55  # Fallback
        
        # Aplicar ajuste total
        total_adjustment = sum(adjustments['adjustments'].values())
        adjusted_prob = original_prob + total_adjustment
        
        # Limitar probabilidad entre 10% y 90%
        adjusted_prob = max(0.10, min(0.90, adjusted_prob))
        
        # Crear candidato ajustado
        adjusted_candidate = candidate.copy()
        
        # Actualizar probabilidades
        adjusted_candidate['prob_calculated'] = adjusted_prob
        adjusted_candidate['real_probability'] = adjusted_prob * 100  # Para compatibilidad
        adjusted_candidate['original_probability'] = original_prob
        adjusted_candidate['probability_adjustment'] = total_adjustment
        
        # Recalcular valor con nueva probabilidad
        odds = candidate.get('odds', candidate.get('odd', 2.0))
        new_value = odds * adjusted_prob
        adjusted_candidate['value'] = new_value
        adjusted_candidate['original_value'] = candidate.get('value', odds * original_prob)
        
        # Calcular nuevo score de confianza
        confidence_score = self._calculate_confidence_score(adjustments, sports_info)
        adjusted_candidate['confidence_score'] = confidence_score
        
        # Añadir información de ajustes para transparencia
        adjusted_candidate['adjustment_details'] = adjustments
        adjusted_candidate['sports_info_summary'] = {
            'data_quality': sports_info.get('overall_impact', 'MEDIUM'),
            'confidence_adjustment': sports_info.get('confidence_adjustment', 0.0),
            'last_updated': sports_info.get('last_updated', datetime.now().isoformat())
        }
        
        return adjusted_candidate

    def _extract_teams(self, event: str) -> Tuple[str, str]:
        """
        Extrae nombres de equipos del string del evento
        """
        if ' vs ' in event:
            teams = event.split(' vs ')
            return teams[0].strip(), teams[1].strip()
        elif ' @ ' in event:
            teams = event.split(' @ ')
            return teams[1].strip(), teams[0].strip()  # @ significa away @ home
        else:
            # Fallback: dividir por espacios y tomar primeras/últimas palabras
            words = event.split()
            if len(words) >= 2:
                mid = len(words) // 2
                home = ' '.join(words[:mid])
                away = ' '.join(words[mid:])
                return home, away
            return 'Team A', 'Team B'

    async def _calculate_adjustments(self, candidate: Dict, sports_info: Dict, 
                                   home_team: str, away_team: str) -> Dict:
        """
        Calcula todos los ajustes basado en la información deportiva
        """
        adjustments = {
            'injury_adjustment': 0.0,
            'lineup_adjustment': 0.0,
            'news_adjustment': 0.0,
            'contextual_adjustment': 0.0
        }
        
        selection = candidate.get('selection', '').lower()
        
        # Determinar qué equipo estamos apostando
        betting_team = self._determine_betting_team(selection, home_team, away_team)
        
        # Ajustes por lesiones
        adjustments['injury_adjustment'] = self._calculate_injury_adjustment(
            sports_info, betting_team, home_team, away_team
        )
        
        # Ajustes por alineaciones
        adjustments['lineup_adjustment'] = self._calculate_lineup_adjustment(
            sports_info, betting_team, home_team, away_team
        )
        
        # Ajustes por noticias
        adjustments['news_adjustment'] = self._calculate_news_adjustment(
            sports_info, betting_team, home_team, away_team
        )
        
        # Ajustes contextuales (mercado, sport, etc.)
        adjustments['contextual_adjustment'] = self._calculate_contextual_adjustment(
            candidate, sports_info
        )
        
        return {
            'adjustments': adjustments,
            'betting_team': betting_team,
            'total_adjustment': sum(adjustments.values()),
            'reasoning': self._generate_adjustment_reasoning(adjustments, sports_info)
        }

    def _determine_betting_team(self, selection: str, home_team: str, away_team: str) -> str:
        """
        Determina en qué equipo estamos apostando basado en la selección
        """
        selection_lower = selection.lower()
        home_lower = home_team.lower()
        away_lower = away_team.lower()
        
        # Buscar palabras clave del equipo en la selección
        home_keywords = home_lower.split()
        away_keywords = away_lower.split()
        
        home_matches = sum(1 for keyword in home_keywords if keyword in selection_lower)
        away_matches = sum(1 for keyword in away_keywords if keyword in selection_lower)
        
        if home_matches > away_matches:
            return home_team
        elif away_matches > home_matches:
            return away_team
        else:
            # Si no se puede determinar, usar el primer equipo mencionado
            if home_lower in selection_lower:
                return home_team
            elif away_lower in selection_lower:
                return away_team
            return home_team  # Fallback

    def _calculate_injury_adjustment(self, sports_info: Dict, betting_team: str, 
                                   home_team: str, away_team: str) -> float:
        """
        Calcula ajuste basado en lesiones
        """
        adjustment = 0.0
        
        injury_report = sports_info.get('injury_report', {})
        injuries = injury_report.get('injuries', [])
        
        for injury in injuries:
            headline = injury.get('headline', '').lower()
            description = injury.get('description', '').lower()
            
            # Verificar si afecta al equipo que estamos apostando
            team_affected = self._injury_affects_team(
                headline + ' ' + description, betting_team, home_team, away_team
            )
            
            if team_affected == betting_team:
                # La lesión afecta nuestro equipo (negativo)
                severity = self._assess_injury_severity(headline, description)
                adjustment += self.injury_factors.get(severity, -0.02)
                
            elif team_affected in [home_team, away_team]:
                # La lesión afecta al oponente (positivo para nosotros)
                severity = self._assess_injury_severity(headline, description)
                adjustment -= self.injury_factors.get(severity, -0.02)  # Invertir el signo
        
        return adjustment

    def _injury_affects_team(self, text: str, betting_team: str, 
                           home_team: str, away_team: str) -> Optional[str]:
        """
        Determina qué equipo se ve afectado por una lesión
        """
        betting_keywords = betting_team.lower().split()
        home_keywords = home_team.lower().split()
        away_keywords = away_team.lower().split()
        
        text_lower = text.lower()
        
        betting_matches = sum(1 for keyword in betting_keywords if keyword in text_lower)
        home_matches = sum(1 for keyword in home_keywords if keyword in text_lower)
        away_matches = sum(1 for keyword in away_keywords if keyword in text_lower)
        
        max_matches = max(betting_matches, home_matches, away_matches)
        
        if max_matches == 0:
            return None
        
        if betting_matches == max_matches:
            return betting_team
        elif home_matches == max_matches:
            return home_team
        elif away_matches == max_matches:
            return away_team
        
        return None

    def _assess_injury_severity(self, headline: str, description: str) -> str:
        """
        Evalúa la severidad de una lesión
        """
        text = f"{headline} {description}".lower()
        
        # Palabras clave de severidad
        star_indicators = ['star', 'all-star', 'mvp', 'leading scorer', 'key player', 'franchise']
        severe_indicators = ['out', 'ruled out', 'sidelined', 'surgery', 'torn', 'broken']
        moderate_indicators = ['doubtful', 'questionable', 'limited', 'day-to-day']
        
        is_star = any(indicator in text for indicator in star_indicators)
        is_severe = any(indicator in text for indicator in severe_indicators)
        is_moderate = any(indicator in text for indicator in moderate_indicators)
        
        if is_star and is_severe:
            return 'star_player_out'
        elif is_star and is_moderate:
            return 'key_player_doubtful'
        elif is_severe:
            return 'starter_out'
        elif is_moderate:
            return 'role_player_out'
        else:
            return 'minor_injury'

    def _calculate_lineup_adjustment(self, sports_info: Dict, betting_team: str,
                                   home_team: str, away_team: str) -> float:
        """
        Calcula ajuste basado en información de alineaciones
        """
        adjustment = 0.0
        
        lineups = sports_info.get('lineups', {})
        
        # Para MLB - verificar pitchers probables
        if 'games' in lineups:
            for game in lineups['games']:
                if (betting_team.lower() in game.get('home_team', '').lower() or 
                    betting_team.lower() in game.get('away_team', '').lower()):
                    
                    probable_pitchers = game.get('probable_pitchers', {})
                    if probable_pitchers:
                        adjustment += self.lineup_factors['confirmed_lineup']
                        
                        # Si tiene pitcher confirmado, es buena señal
                        team_side = 'home' if betting_team.lower() in game.get('home_team', '').lower() else 'away'
                        if team_side in probable_pitchers:
                            adjustment += self.lineup_factors['optimal_lineup'] / 2
        
        # Para fútbol - verificar alineaciones disponibles
        elif 'matches' in lineups:
            for match in lineups['matches']:
                if (betting_team.lower() in match.get('home_team', '').lower() or 
                    betting_team.lower() in match.get('away_team', '').lower()):
                    
                    if match.get('lineups_available'):
                        adjustment += self.lineup_factors['confirmed_lineup']
                    
                    key_players = match.get('key_players', [])
                    team_players = [p for p in key_players if betting_team.lower() in p.get('team', '').lower()]
                    
                    if len(team_players) >= 8:  # Alineación casi completa
                        adjustment += self.lineup_factors['optimal_lineup']
                    elif len(team_players) >= 5:  # Alineación parcial
                        adjustment += self.lineup_factors['confirmed_lineup']
        
        return adjustment

    def _calculate_news_adjustment(self, sports_info: Dict, betting_team: str,
                                 home_team: str, away_team: str) -> float:
        """
        Calcula ajuste basado en noticias del equipo
        """
        adjustment = 0.0
        
        # Evaluar noticias del equipo que estamos apostando
        team_news_key = 'home_news' if betting_team == home_team else 'away_news'
        team_news = sports_info.get(team_news_key, {})
        
        articles = team_news.get('articles', [])
        for article in articles:
            impact = article.get('impact_level', 'MEDIUM')
            headline = article.get('headline', '').lower()
            description = article.get('description', '').lower()
            
            text = f"{headline} {description}"
            
            # Evaluar tipo de noticia
            if self._is_positive_news(text):
                if impact == 'HIGH':
                    adjustment += self.news_factors['positive_momentum']
                elif impact == 'MEDIUM':
                    adjustment += self.news_factors['team_chemistry_good'] / 2
                    
            elif self._is_negative_news(text):
                if impact == 'HIGH':
                    adjustment += self.news_factors['negative_news']
                elif impact == 'MEDIUM':
                    adjustment += self.news_factors['distraction'] / 2
        
        return adjustment

    def _is_positive_news(self, text: str) -> bool:
        """
        Determina si una noticia es positiva
        """
        positive_keywords = [
            'win', 'victory', 'strong', 'healthy', 'returns', 'comeback',
            'confident', 'ready', 'motivated', 'improved', 'chemistry',
            'momentum', 'streak', 'dominant'
        ]
        return any(keyword in text for keyword in positive_keywords)

    def _is_negative_news(self, text: str) -> bool:
        """
        Determina si una noticia es negativa
        """
        negative_keywords = [
            'injured', 'suspension', 'conflict', 'problem', 'issue',
            'concern', 'worry', 'doubt', 'struggle', 'lose', 'loss',
            'argument', 'dispute', 'distraction', 'controversy'
        ]
        return any(keyword in text for keyword in negative_keywords)

    def _calculate_contextual_adjustment(self, candidate: Dict, sports_info: Dict) -> float:
        """
        Calcula ajustes contextuales basado en el tipo de apuesta y deporte
        """
        adjustment = 0.0
        
        market = candidate.get('market_key', '')
        sport = candidate.get('sport_key', '')
        
        # Usar el ajuste de confianza de sports_info
        confidence_adj = sports_info.get('confidence_adjustment', 0.0)
        adjustment += confidence_adj
        
        # Ajustes específicos por mercado
        if market == 'h2h':  # Mercado de ganador
            # Mayor impacto de lesiones de estrellas
            adjustment *= 1.2
        elif market == 'spreads':  # Hándicap
            # Moderado impacto
            adjustment *= 1.0
        elif market == 'totals':  # Totales
            # Menor impacto de lesiones individuales
            adjustment *= 0.8
        
        # Ajustes específicos por deporte
        if 'basketball' in sport or 'nba' in sport:
            # Basketball es muy susceptible a jugadores individuales
            adjustment *= 1.3
        elif 'baseball' in sport or 'mlb' in sport:
            # Baseball depende mucho del pitcher
            adjustment *= 1.1
        elif 'soccer' in sport or 'football' in sport:
            # Fútbol es más predecible con equipos completos
            adjustment *= 0.9
        
        return adjustment

    def _calculate_confidence_score(self, adjustments: Dict, sports_info: Dict) -> float:
        """
        Calcula un score de confianza basado en la calidad de la información
        """
        base_score = 0.7  # Score base
        
        # Factores que aumentan confianza
        data_quality = sports_info.get('overall_impact', 'MEDIUM')
        if data_quality == 'HIGH':
            base_score += 0.15
        elif data_quality == 'LOW':
            base_score += 0.05
        
        # Información de lesiones disponible
        injury_report = sports_info.get('injury_report', {})
        if injury_report.get('injuries'):
            base_score += 0.1
        
        # Información de alineaciones disponible
        lineups = sports_info.get('lineups', {})
        if lineups.get('games') or lineups.get('matches'):
            base_score += 0.1
        
        # Noticias recientes disponibles
        home_news = sports_info.get('home_news', {}).get('articles', [])
        away_news = sports_info.get('away_news', {}).get('articles', [])
        if home_news or away_news:
            base_score += 0.05
        
        # Penalizar si no hay información suficiente
        total_adjustment = abs(sum(adjustments['adjustments'].values()))
        if total_adjustment < 0.01:  # Muy poco ajuste podría indicar falta de información
            base_score -= 0.05
        
        return max(0.1, min(1.0, base_score))

    def _generate_adjustment_reasoning(self, adjustments: Dict, sports_info: Dict) -> str:
        """
        Genera una explicación de los ajustes realizados
        """
        reasoning_parts = []
        
        adj = adjustments['adjustments']
        
        if abs(adj['injury_adjustment']) > 0.01:
            direction = "positivo" if adj['injury_adjustment'] > 0 else "negativo"
            reasoning_parts.append(f"Ajuste por lesiones: {direction} ({adj['injury_adjustment']:+.3f})")
        
        if abs(adj['lineup_adjustment']) > 0.01:
            direction = "positivo" if adj['lineup_adjustment'] > 0 else "negativo"
            reasoning_parts.append(f"Ajuste por alineaciones: {direction} ({adj['lineup_adjustment']:+.3f})")
        
        if abs(adj['news_adjustment']) > 0.01:
            direction = "positivo" if adj['news_adjustment'] > 0 else "negativo"
            reasoning_parts.append(f"Ajuste por noticias: {direction} ({adj['news_adjustment']:+.3f})")
        
        if abs(adj['contextual_adjustment']) > 0.01:
            direction = "positivo" if adj['contextual_adjustment'] > 0 else "negativo"
            reasoning_parts.append(f"Ajuste contextual: {direction} ({adj['contextual_adjustment']:+.3f})")
        
        if not reasoning_parts:
            reasoning_parts.append("Sin ajustes significativos aplicados")
        
        total = sum(adj.values())
        reasoning_parts.append(f"Total: {total:+.3f}")
        
        return " | ".join(reasoning_parts)


# Función helper para uso directo
async def adjust_candidate_probabilities(candidates: List[Dict]) -> List[Dict]:
    """
    Función de conveniencia para ajustar probabilidades de candidatos
    """
    adjuster = ProbabilityAdjuster()
    return await adjuster.adjust_probabilities(candidates)


# Ejemplo de uso
if __name__ == "__main__":
    async def test():
        # Candidato de prueba
        test_candidates = [{
            'event': 'Philadelphia 76ers vs Boston Celtics',
            'sport_key': 'basketball_nba',
            'market_key': 'h2h',
            'selection': 'Philadelphia 76ers',
            'odds': 2.10,
            'prob_calculated': 0.55,
            'value': 1.155
        }]
        
        adjuster = ProbabilityAdjuster()
        adjusted = await adjuster.adjust_probabilities(test_candidates)
        
        for candidate in adjusted:
            print(f"Original prob: {candidate.get('original_probability', 'N/A'):.3f}")
            print(f"Adjusted prob: {candidate.get('prob_calculated', 'N/A'):.3f}")
            print(f"Adjustment: {candidate.get('probability_adjustment', 'N/A'):+.3f}")
            print(f"Reasoning: {candidate.get('adjustment_details', {}).get('reasoning', 'N/A')}")
    
    asyncio.run(test())