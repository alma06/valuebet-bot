"""
utils/sport_translator.py - Traduce nombres de deportes al español.
"""

SPORT_TRANSLATIONS = {
    # Basketball
    'basketball_nba': 'Baloncesto (NBA)',
    'basketball_euroleague': 'Baloncesto (Euroliga)',
    'basketball_ncaab': 'Baloncesto (NCAA)',
    'basketball': 'Baloncesto',
    
    # American Football
    'americanfootball_nfl': 'Fútbol Americano (NFL)',
    'americanfootball_ncaaf': 'Fútbol Americano (NCAA)',
    'americanfootball': 'Fútbol Americano',
    
    # Baseball
    'baseball_mlb': 'Béisbol (MLB)',
    'baseball': 'Béisbol',
    
    # Soccer
    'soccer_epl': 'Fútbol (Premier League)',
    'soccer_spain_la_liga': 'Fútbol (La Liga)',
    'soccer_uefa_champs_league': 'Fútbol (Champions)',
    'soccer_uefa_europa_league': 'Fútbol (Europa League)',
    'soccer': 'Fútbol',
    
    # Tennis
    'tennis_atp': 'Tenis (ATP)',
    'tennis_wta': 'Tenis (WTA)',
    'tennis': 'Tenis',
}


def translate_sport(sport_key: str, sport_nice: str = None) -> str:
    """
    Traduce el nombre del deporte al español.
    
    Args:
        sport_key: Clave del deporte (ej: 'basketball_nba')
        sport_nice: Nombre legible opcional de la API
    
    Returns:
        Nombre del deporte en español
    """
    # Intentar traducción exacta primero
    if sport_key in SPORT_TRANSLATIONS:
        return SPORT_TRANSLATIONS[sport_key]
    
    # Intentar por prefijo
    for key, translation in SPORT_TRANSLATIONS.items():
        if sport_key.startswith(key):
            return translation
    
    # Fallback a sport_nice si existe
    if sport_nice:
        return sport_nice
    
    # Último fallback: capitalizar sport_key
    return sport_key.replace('_', ' ').title()
