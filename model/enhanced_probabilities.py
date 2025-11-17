"""
model/enhanced_probabilities.py - Modelo mejorado con datos reales

Mejoras sobre probabilities.py:
- Usa datos históricos de la base de datos
- Calcula xG real basado en estadísticas
- Considera lesiones
- Ajusta por forma reciente
- Factor de localía con datos reales
"""
import math
from typing import Dict, Optional, List
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)

try:
    from data.historical_db import historical_db
    from data.stats_api import nba_api, football_api
except ImportError:
    logger.warning("Could not import historical_db or stats_api")
    historical_db = None
    nba_api = None
    football_api = None


def poisson_pmf(k: int, lam: float) -> float:
    """Probabilidad de Poisson"""
    if lam <= 0:
        return 0.0
    return (lam ** k) * math.exp(-lam) / math.factorial(k)


def calculate_xg_from_stats(team_stats: Dict, is_home: bool = True) -> float:
    """
    Calcula xG basado en estadísticas reales del equipo
    
    Args:
        team_stats: Estadísticas del equipo
        is_home: Si juega de local
    
    Returns:
        Expected goals estimado
    """
    try:
        # Obtener goles por partido
        total_goals = team_stats.get('goals_for', 0)
        matches_played = (team_stats.get('wins', 0) + 
                         team_stats.get('losses', 0) + 
                         team_stats.get('draws', 0))
        
        if matches_played == 0:
            return 1.2  # Default
        
        goals_per_game = total_goals / matches_played
        
        # Ajustar por localía (equipos locales suelen meter ~15% más goles)
        if is_home:
            home_factor = 1.15
            home_wins = team_stats.get('home_wins', 0)
            home_matches = matches_played / 2  # Aproximadamente mitad local/visitante
            if home_matches > 0:
                home_win_rate = home_wins / home_matches
                home_factor = 1.0 + (home_win_rate * 0.3)  # Factor dinámico
            
            goals_per_game *= home_factor
        else:
            # Factor visitante (suelen meter ~10% menos)
            away_factor = 0.90
            away_wins = team_stats.get('away_wins', 0)
            away_matches = matches_played / 2
            if away_matches > 0:
                away_win_rate = away_wins / away_matches
                away_factor = 1.0 - ((1 - away_win_rate) * 0.2)
            
            goals_per_game *= away_factor
        
        return max(0.5, min(3.5, goals_per_game))  # Limitar entre 0.5 y 3.5
        
    except Exception as e:
        logger.error(f"Error calculating xG: {e}")
        return 1.2


def adjust_for_recent_form(base_prob: float, recent_matches: List[Dict], team_name: str) -> float:
    """
    Ajusta probabilidad según forma reciente
    
    Args:
        base_prob: Probabilidad base
        recent_matches: Últimos 5-10 partidos
        team_name: Nombre del equipo
    
    Returns:
        Probabilidad ajustada
    """
    if not recent_matches or len(recent_matches) < 3:
        return base_prob
    
    try:
        # Calcular winrate reciente
        recent_wins = 0
        for match in recent_matches[:5]:  # Últimos 5 partidos
            is_home = match.get('home_team') == team_name
            home_score = match.get('home_score', 0)
            away_score = match.get('away_score', 0)
            
            if is_home and home_score > away_score:
                recent_wins += 1
            elif not is_home and away_score > home_score:
                recent_wins += 1
        
        recent_form = recent_wins / min(5, len(recent_matches))
        
        # Ajustar probabilidad
        # Si racha buena (>60%) → aumentar hasta +15%
        # Si racha mala (<40%) → reducir hasta -15%
        if recent_form > 0.6:
            adjustment = (recent_form - 0.6) * 0.375  # Max +15%
            return min(0.95, base_prob * (1 + adjustment))
        elif recent_form < 0.4:
            adjustment = (0.4 - recent_form) * 0.375  # Max -15%
            return max(0.05, base_prob * (1 - adjustment))
        
        return base_prob
        
    except Exception as e:
        logger.error(f"Error adjusting for form: {e}")
        return base_prob


def adjust_for_injuries(base_prob: float, injuries: List[Dict], team_name: str) -> float:
    """
    Ajusta probabilidad según lesiones
    
    Args:
        base_prob: Probabilidad base
        injuries: Lista de lesiones del equipo
        team_name: Nombre del equipo
    
    Returns:
        Probabilidad ajustada
    """
    if not injuries:
        return base_prob
    
    try:
        # Contar lesiones por severidad
        out_count = sum(1 for inj in injuries if 'out' in inj.get('status', '').lower())
        doubtful_count = sum(1 for inj in injuries if 'doubtful' in inj.get('status', '').lower())
        
        # Reducir probabilidad según lesiones
        # Cada jugador "out" reduce ~5%, doubtful ~2%
        injury_penalty = (out_count * 0.05) + (doubtful_count * 0.02)
        injury_penalty = min(0.25, injury_penalty)  # Máximo -25%
        
        adjusted_prob = base_prob * (1 - injury_penalty)
        return max(0.05, adjusted_prob)
        
    except Exception as e:
        logger.error(f"Error adjusting for injuries: {e}")
        return base_prob


def adjust_for_h2h(base_prob: float, h2h_matches: List[Dict], team_name: str) -> float:
    """
    Ajusta según historial H2H
    
    Args:
        base_prob: Probabilidad base
        h2h_matches: Partidos previos entre equipos
        team_name: Nombre del equipo
    
    Returns:
        Probabilidad ajustada
    """
    if not h2h_matches or len(h2h_matches) < 2:
        return base_prob
    
    try:
        # Calcular winrate en H2H
        h2h_wins = 0
        for match in h2h_matches[:5]:  # Últimos 5 H2H
            is_home = match.get('home_team') == team_name
            home_score = match.get('home_score', 0)
            away_score = match.get('away_score', 0)
            
            if is_home and home_score > away_score:
                h2h_wins += 1
            elif not is_home and away_score > home_score:
                h2h_wins += 1
        
        h2h_rate = h2h_wins / min(5, len(h2h_matches))
        
        # Ajustar probabilidad (peso menor que forma reciente)
        # Si domina H2H (>70%) → +10% max
        # Si pierde H2H (<30%) → -10% max
        if h2h_rate > 0.7:
            adjustment = (h2h_rate - 0.7) * 0.33  # Max +10%
            return min(0.95, base_prob * (1 + adjustment))
        elif h2h_rate < 0.3:
            adjustment = (0.3 - h2h_rate) * 0.33  # Max -10%
            return max(0.05, base_prob * (1 - adjustment))
        
        return base_prob
        
    except Exception as e:
        logger.error(f"Error adjusting for H2H: {e}")
        return base_prob


def estimate_probabilities_enhanced(event: Dict) -> Dict:
    """
    Versión mejorada de estimate_probabilities con datos reales
    
    Args:
        event: Evento con información del partido
    
    Returns:
        Diccionario con probabilidades:
        {'home': float, 'away': float, 'draw': float (si aplica)}
    """
    sport = event.get('sport_key', '')
    home_team = event.get('home_team') or event.get('home')
    away_team = event.get('away_team') or event.get('away')
    
    # Si no hay datos históricos, usar modelo básico
    if not historical_db:
        return _fallback_probabilities(event)
    
    try:
        # FÚTBOL
        if sport.startswith('soccer'):
            return _estimate_football_enhanced(event, home_team, away_team, sport)
        
        # BALONCESTO
        elif sport.startswith('basketball'):
            return _estimate_basketball_enhanced(event, home_team, away_team, sport)
        
        # BASEBALL
        elif sport.startswith('baseball'):
            return _estimate_baseball_enhanced(event, home_team, away_team, sport)
        
        # TENIS
        elif sport.startswith('tennis'):
            return _estimate_tennis_enhanced(event, home_team, away_team)
        
        # FALLBACK
        else:
            return _fallback_probabilities(event)
            
    except Exception as e:
        logger.error(f"Error in enhanced probabilities: {e}")
        return _fallback_probabilities(event)


def _estimate_football_enhanced(event: Dict, home_team: str, away_team: str, sport: str) -> Dict:
    """Estimación mejorada para fútbol"""
    
    # 1. Obtener estadísticas de equipos
    home_stats = historical_db.get_team_stats(home_team, sport)
    away_stats = historical_db.get_team_stats(away_team, sport)
    
    # 2. Calcular xG basado en stats reales
    if home_stats and away_stats:
        home_xg = calculate_xg_from_stats(home_stats, is_home=True)
        away_xg = calculate_xg_from_stats(away_stats, is_home=False)
    else:
        # Fallback a valores por defecto
        home_xg = 1.3
        away_xg = 1.0
    
    # 3. Calcular probabilidades base con Poisson
    p_home, p_draw, p_away = _football_1x2_from_xg(home_xg, away_xg)
    
    # 4. Ajustar por forma reciente
    recent_home = historical_db.get_recent_matches(home_team, sport, limit=10)
    if recent_home:
        p_home = adjust_for_recent_form(p_home, recent_home, home_team)
    
    recent_away = historical_db.get_recent_matches(away_team, sport, limit=10)
    if recent_away:
        p_away = adjust_for_recent_form(p_away, recent_away, away_team)
    
    # 5. Ajustar por H2H
    h2h_matches = historical_db.get_h2h(home_team, away_team, sport, limit=5)
    if h2h_matches:
        p_home = adjust_for_h2h(p_home, h2h_matches, home_team)
        p_away = adjust_for_h2h(p_away, h2h_matches, away_team)
    
    # 6. Ajustar por lesiones
    home_injuries = historical_db.get_team_injuries(home_team, sport)
    if home_injuries:
        p_home = adjust_for_injuries(p_home, home_injuries, home_team)
    
    away_injuries = historical_db.get_team_injuries(away_team, sport)
    if away_injuries:
        p_away = adjust_for_injuries(p_away, away_injuries, away_team)
    
    # 7. Normalizar probabilidades
    total = p_home + p_draw + p_away
    if total > 0:
        p_home /= total
        p_draw /= total
        p_away /= total
    
    return {'home': p_home, 'draw': p_draw, 'away': p_away}


def _estimate_basketball_enhanced(event: Dict, home_team: str, away_team: str, sport: str) -> Dict:
    """Estimación mejorada para baloncesto"""
    
    # 1. Obtener estadísticas
    home_stats = historical_db.get_team_stats(home_team, sport)
    away_stats = historical_db.get_team_stats(away_team, sport)
    
    # 2. Calcular winrate base
    if home_stats and away_stats:
        home_wins = home_stats.get('wins', 0)
        home_losses = home_stats.get('losses', 0)
        home_total = home_wins + home_losses
        home_winrate = home_wins / home_total if home_total > 0 else 0.5
        
        away_wins = away_stats.get('wins', 0)
        away_losses = away_stats.get('losses', 0)
        away_total = away_wins + away_losses
        away_winrate = away_wins / away_total if away_total > 0 else 0.5
        
        # Factor de localía NBA (~60% de victorias locales)
        home_winrate *= 1.15
    else:
        home_winrate = 0.55
        away_winrate = 0.45
    
    # 3. Calcular probabilidad base
    p_home = home_winrate / (home_winrate + away_winrate)
    p_away = 1 - p_home
    
    # 4. Ajustar por forma reciente
    recent_home = historical_db.get_recent_matches(home_team, sport, limit=10)
    if recent_home:
        p_home = adjust_for_recent_form(p_home, recent_home, home_team)
        p_away = 1 - p_home
    
    # 5. Ajustar por lesiones
    home_injuries = historical_db.get_team_injuries(home_team, sport)
    if home_injuries:
        p_home = adjust_for_injuries(p_home, home_injuries, home_team)
        p_away = 1 - p_home
    
    return {'home': p_home, 'away': p_away}


def _estimate_baseball_enhanced(event: Dict, home_team: str, away_team: str, sport: str) -> Dict:
    """Estimación mejorada para baseball"""
    # Similar a basketball pero con ajustes específicos de MLB
    return _estimate_basketball_enhanced(event, home_team, away_team, sport)


def _estimate_tennis_enhanced(event: Dict, player1: str, player2: str) -> Dict:
    """Estimación mejorada para tenis"""
    # Usar forma reciente de ambos jugadores
    sport = event.get('sport_key', 'tennis')
    
    recent_p1 = historical_db.get_recent_matches(player1, sport, limit=10)
    recent_p2 = historical_db.get_recent_matches(player2, sport, limit=10)
    
    # Calcular winrate reciente
    p1_wins = sum(1 for m in recent_p1 if (m.get('home_team') == player1 and m.get('home_score', 0) > m.get('away_score', 0)) or 
                                          (m.get('away_team') == player1 and m.get('away_score', 0) > m.get('home_score', 0)))
    p1_rate = p1_wins / len(recent_p1) if recent_p1 else 0.5
    
    p2_wins = sum(1 for m in recent_p2 if (m.get('home_team') == player2 and m.get('home_score', 0) > m.get('away_score', 0)) or 
                                          (m.get('away_team') == player2 and m.get('away_score', 0) > m.get('home_score', 0)))
    p2_rate = p2_wins / len(recent_p2) if recent_p2 else 0.5
    
    # Probabilidad
    p_home = p1_rate / (p1_rate + p2_rate)
    return {'home': p_home, 'away': 1 - p_home}


def _football_1x2_from_xg(home_xg: float, away_xg: float, max_goals: int = 10) -> tuple:
    """Calcular probabilidades 1X2 con Poisson"""
    home_probs = [poisson_pmf(k, home_xg) for k in range(0, max_goals + 1)]
    away_probs = [poisson_pmf(k, away_xg) for k in range(0, max_goals + 1)]
    
    p_home = 0.0
    p_draw = 0.0
    p_away = 0.0
    
    for i, ph in enumerate(home_probs):
        for j, pa in enumerate(away_probs):
            prob = ph * pa
            if i > j:
                p_home += prob
            elif i == j:
                p_draw += prob
            else:
                p_away += prob
    
    total = p_home + p_draw + p_away
    if total > 0:
        return p_home / total, p_draw / total, p_away / total
    return 0.33, 0.33, 0.33


def _fallback_probabilities(event: Dict) -> Dict:
    """Probabilidades por defecto cuando no hay datos"""
    sport = event.get('sport_key', '')
    
    if 'soccer' in sport:
        return {'home': 0.45, 'draw': 0.27, 'away': 0.28}
    else:
        return {'home': 0.52, 'away': 0.48}
