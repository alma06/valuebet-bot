"""
utils/lineup_analyzer.py - Análisis de alineaciones y factores críticos
"""

from typing import Dict, List, Optional
import re


def analyze_lineup_impact(candidate: Dict) -> Dict:
    """
    Analiza el impacto potencial de las alineaciones en el pronóstico.
    
    Args:
        candidate: Diccionario con información del candidato
        
    Returns:
        Dict con análisis de impacto de alineaciones
    """
    sport_key = candidate.get('sport_key', '').lower()
    event_name = candidate.get('event', '')
    market_type = candidate.get('market_key', '')
    
    # Extraer nombres de equipos
    teams = extract_team_names(event_name)
    home_team = teams.get('home', 'Equipo Local')
    away_team = teams.get('away', 'Equipo Visitante')
    
    analysis = {
        'sport': sport_key,
        'home_team': home_team,
        'away_team': away_team,
        'critical_factors': get_critical_factors(sport_key),
        'lineup_sources': get_lineup_sources(sport_key),
        'timing_advice': get_timing_advice(sport_key),
        'impact_level': assess_impact_level(market_type, sport_key)
    }
    
    return analysis


def extract_team_names(event_name: str) -> Dict[str, str]:
    """
    Extrae nombres de equipos del string del evento.
    """
    if ' vs ' in event_name:
        teams = event_name.split(' vs ')
        return {
            'home': teams[0].strip(),
            'away': teams[1].strip()
        }
    elif ' @ ' in event_name:
        teams = event_name.split(' @ ')
        return {
            'away': teams[0].strip(),
            'home': teams[1].strip()
        }
    else:
        return {
            'home': 'Equipo Local',
            'away': 'Equipo Visitante'
        }


def get_critical_factors(sport_key: str) -> List[str]:
    """
    Retorna factores críticos a monitorear según el deporte.
    """
    if 'basketball' in sport_key or 'nba' in sport_key:
        return [
            "Estrellas titulares (20+ puntos por juego)",
            "Lesiones de última hora en jugadores clave",
            "Descanso programado (load management)",
            "Jugadores en protocols de salud",
            "Rotaciones reducidas por el entrenador",
            "Back-to-back games (cansancio acumulado)"
        ]
    
    elif 'soccer' in sport_key or 'football' in sport_key:
        return [
            "Delanteros titulares y máximos goleadores",
            "Portero titular vs suplente",
            "Suspensiones por acumulación de tarjetas",
            "Rotaciones por competencias europeas",
            "Lesiones en defensa central",
            "Mediocampistas creativos (asistencias)"
        ]
    
    elif 'baseball' in sport_key or 'mlb' in sport_key:
        return [
            "Pitcher abridor confirmado y ERA",
            "Disponibilidad del bullpen principal",
            "Bateadores estrella en el lineup",
            "Condiciones climáticas (viento, lluvia)",
            "Matchup zurdo vs derecho",
            "Catcher titular vs suplente"
        ]
    
    elif 'tennis' in sport_key:
        return [
            "Lesiones o molestias físicas recientes",
            "Estado de forma actual (últimos 5 matches)",
            "Superficie preferida del jugador",
            "Historial head-to-head",
            "Fatiga por torneos consecutivos",
            "Condiciones climáticas y viento"
        ]
    
    elif 'american_football' in sport_key or 'nfl' in sport_key:
        return [
            "Quarterback titular confirmado",
            "Running backs principales disponibles",
            "Wide receivers estrella en el lineup",
            "Lesiones en línea ofensiva",
            "Defensive backs vs passing game",
            "Condiciones climáticas extremas"
        ]
    
    else:
        return [
            "Jugadores estrella confirmados en alineación",
            "Lesiones o ausencias de último momento",
            "Cambios tácticos del entrenador",
            "Motivación del equipo (objetivos de temporada)",
            "Condiciones ambientales",
            "Rivalidad o presión del partido"
        ]


def get_lineup_sources(sport_key: str) -> List[str]:
    """
    Retorna fuentes confiables para verificar alineaciones.
    """
    if 'basketball' in sport_key or 'nba' in sport_key:
        return [
            "NBA.com injury report (oficial)",
            "Cuentas oficiales de Twitter de equipos",
            "ESPN NBA reporters",
            "The Athletic NBA insiders",
            "Rotoworld NBA news",
            "FantasyLabs NBA lineups"
        ]
    
    elif 'soccer' in sport_key or 'football' in sport_key:
        return [
            "Cuentas oficiales de los clubes",
            "Conferencias de prensa pre-partido",
            "Sky Sports Football",
            "ESPN FC reporters",
            "Fabrizio Romano (transfers/news)",
            "BBC Sport Football"
        ]
    
    elif 'baseball' in sport_key or 'mlb' in sport_key:
        return [
            "MLB.com starting lineups",
            "Cuentas oficiales de equipos MLB",
            "ESPN MLB insiders",
            "Rotoworld MLB news",
            "The Athletic baseball reporters",
            "FantasyLabs MLB lineups"
        ]
    
    else:
        return [
            "Cuentas oficiales de equipos/organizaciones",
            "Sitios web oficiales de ligas",
            "Reporteros deportivos especializados",
            "Conferencias de prensa oficiales",
            "ESPN y otros medios deportivos",
            "Aplicaciones deportivas confiables"
        ]


def get_timing_advice(sport_key: str) -> Dict[str, str]:
    """
    Retorna consejos de timing para verificar alineaciones.
    """
    if 'basketball' in sport_key or 'nba' in sport_key:
        return {
            'optimal_time': '2-3 horas antes del juego',
            'latest_check': '30 minutos antes del tip-off',
            'injury_report': '5:00 PM ET día anterior + updates',
            'warning': 'Load management puede decidirse último momento'
        }
    
    elif 'soccer' in sport_key or 'football' in sport_key:
        return {
            'optimal_time': '1-2 horas antes del kickoff',
            'latest_check': '30 minutos antes del partido',
            'injury_report': 'Conferencia de prensa día anterior',
            'warning': 'Lesiones en calentamiento son comunes'
        }
    
    elif 'baseball' in sport_key or 'mlb' in sport_key:
        return {
            'optimal_time': '3-4 horas antes del primer pitch',
            'latest_check': '1 hora antes del juego',
            'injury_report': 'Daily lineup cards publicados',
            'warning': 'Clima puede cambiar pitcher y lineup'
        }
    
    else:
        return {
            'optimal_time': '1-3 horas antes del evento',
            'latest_check': '30 minutos antes del inicio',
            'injury_report': 'Reportes oficiales del día',
            'warning': 'Cambios de último momento posibles'
        }


def assess_impact_level(market_type: str, sport_key: str) -> Dict[str, str]:
    """
    Evalúa el nivel de impacto de las alineaciones según mercado y deporte.
    """
    impact_levels = {
        'h2h': 'ALTO - Las alineaciones pueden cambiar completamente el resultado',
        'spreads': 'MEDIO-ALTO - Jugadores clave afectan la diferencia de puntos',
        'totals': 'MEDIO - Jugadores ofensivos/defensivos impactan el total'
    }
    
    base_impact = impact_levels.get(market_type, 'MEDIO - Verificar siempre')
    
    sport_multipliers = {
        'basketball': 'CRÍTICO en NBA - Pocas substituciones, impacto individual alto',
        'soccer': 'ALTO en fútbol - 11 vs 11, cada posición es clave',
        'baseball': 'MEDIO-ALTO en MLB - Pitcher y bateadores estrella',
        'tennis': 'MÁXIMO en tenis - Solo 1 jugador, impacto 100%'
    }
    
    sport_context = ''
    for key, context in sport_multipliers.items():
        if key in sport_key.lower():
            sport_context = context
            break
    
    return {
        'market_impact': base_impact,
        'sport_context': sport_context or 'MEDIO - Verificar factores clave',
        'recommendation': 'SIEMPRE verificar antes de apostar'
    }


def format_lineup_warning(candidate: Dict) -> List[str]:
    """
    Genera advertencias específicas sobre alineaciones para incluir en alertas.
    """
    analysis = analyze_lineup_impact(candidate)
    
    warnings = [
        "🚨 **FACTOR CRÍTICO: ALINEACIONES**",
        f"⚠️ **Impacto:** {analysis['impact_level']['sport_context']}",
        f"⏰ **Verificar:** {analysis['timing_advice']['optimal_time']}",
        ""
    ]
    
    # Añadir factores críticos específicos
    warnings.append("🔍 **Monitorear especialmente:**")
    for factor in analysis['critical_factors'][:3]:  # Solo top 3 para no sobrecargar
        warnings.append(f"  • {factor}")
    
    warnings.extend([
        "",
        f"📱 **Fuentes confiables:** {', '.join(analysis['lineup_sources'][:2])}",
        f"⚡ **Último check:** {analysis['timing_advice']['latest_check']}",
        "🔄 **Si hay cambios importantes:** Evitar o ajustar apuesta"
    ])
    
    return warnings


# Función para integrar con el sistema de alertas
def get_lineup_section(candidate: Dict, is_premium: bool = False) -> List[str]:
    """
    Genera la sección de alineaciones para incluir en las alertas.
    
    Args:
        candidate: Información del candidato
        is_premium: Si es usuario premium (más detalle)
    
    Returns:
        Lista de líneas para incluir en la alerta
    """
    if is_premium:
        return format_lineup_warning(candidate)
    else:
        return [
            "👥 **FACTOR ALINEACIONES:**",
            "⚠️ **IMPORTANTE:** Verifica alineaciones antes de apostar",
            "🔍 Jugadores clave lesionados pueden cambiar el pronóstico",
            "📋 Consulta alineaciones oficiales 1-2 horas antes del juego",
            "🚨 Si hay cambios importantes, ajusta o evita la apuesta"
        ]