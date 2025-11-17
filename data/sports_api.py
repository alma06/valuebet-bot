"""
data/sports_api.py - Consulta APIs confiables para obtener información actualizada de deportes

Integra múltiples fuentes para obtener:
- Alineaciones confirmadas
- Lesiones y ausencias
- Noticias de última hora
- Estados de jugadores
"""

import aiohttp
import asyncio
import os
import json
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Claves de API (agregar al .env)
ESPN_API_BASE = "https://site.api.espn.com/apis/site/v2/sports"
NBA_API_BASE = "https://stats.nba.com/stats"
MLB_API_BASE = "https://statsapi.mlb.com/api/v1"

# Headers para evitar bloqueos
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}


class SportsAPIClient:
    def __init__(self):
        self.session = None
        self.cache = {}  # Cache para evitar demasiadas requests
        self.cache_duration = 300  # 5 minutos
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=HEADERS, timeout=aiohttp.ClientTimeout(total=10))
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Verifica si el cache es válido"""
        if cache_key not in self.cache:
            return False
        
        cached_time = self.cache[cache_key].get('timestamp', 0)
        return (datetime.now().timestamp() - cached_time) < self.cache_duration
    
    def _set_cache(self, cache_key: str, data: dict):
        """Guarda datos en cache"""
        self.cache[cache_key] = {
            'data': data,
            'timestamp': datetime.now().timestamp()
        }
    
    def _get_cache(self, cache_key: str) -> Optional[dict]:
        """Obtiene datos del cache"""
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        return None

    async def get_nba_injury_report(self, team_abbreviation: str = None) -> Dict:
        """
        Obtiene el injury report oficial de la NBA
        """
        cache_key = f"nba_injuries_{team_abbreviation or 'all'}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        try:
            # Usar ESPN para injury report (más confiable que NBA.com directamente)
            url = f"{ESPN_API_BASE}/basketball/nba/news"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Filtrar noticias de lesiones
                    injury_info = {
                        'injuries': [],
                        'last_updated': datetime.now().isoformat()
                    }
                    
                    if 'articles' in data:
                        for article in data['articles'][:20]:  # Solo las 20 más recientes
                            headline = article.get('headline', '').lower()
                            description = article.get('description', '').lower()
                            
                            # Detectar palabras clave de lesiones
                            injury_keywords = ['injury', 'injured', 'out', 'doubtful', 'questionable', 'probable', 'ruled out', 'sidelined']
                            
                            if any(keyword in headline or keyword in description for keyword in injury_keywords):
                                injury_info['injuries'].append({
                                    'headline': article.get('headline', ''),
                                    'description': article.get('description', ''),
                                    'published': article.get('published', ''),
                                    'source': 'ESPN'
                                })
                    
                    self._set_cache(cache_key, injury_info)
                    return injury_info
                
        except Exception as e:
            logger.warning(f"Error fetching NBA injuries: {e}")
        
        return {'injuries': [], 'last_updated': datetime.now().isoformat()}

    async def get_mlb_lineups(self, team_id: str = None) -> Dict:
        """
        Obtiene las alineaciones confirmadas de MLB
        """
        cache_key = f"mlb_lineups_{team_id or 'all'}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        try:
            # Obtener juegos del día
            today = datetime.now().strftime('%Y-%m-%d')
            url = f"{MLB_API_BASE}/schedule/games?sportId=1&date={today}&hydrate=lineups,probablePitcher"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    lineups_info = {
                        'games': [],
                        'last_updated': datetime.now().isoformat()
                    }
                    
                    if 'dates' in data and data['dates']:
                        for date_data in data['dates']:
                            for game in date_data.get('games', []):
                                game_info = {
                                    'game_id': game.get('gamePk'),
                                    'home_team': game.get('teams', {}).get('home', {}).get('team', {}).get('name'),
                                    'away_team': game.get('teams', {}).get('away', {}).get('team', {}).get('name'),
                                    'status': game.get('status', {}).get('abstractGameState'),
                                    'lineups_posted': False,
                                    'probable_pitchers': {}
                                }
                                
                                # Probable pitchers
                                if 'probablePitcher' in game.get('teams', {}).get('home', {}):
                                    game_info['probable_pitchers']['home'] = game['teams']['home']['probablePitcher'].get('fullName')
                                
                                if 'probablePitcher' in game.get('teams', {}).get('away', {}):
                                    game_info['probable_pitchers']['away'] = game['teams']['away']['probablePitcher'].get('fullName')
                                
                                lineups_info['games'].append(game_info)
                    
                    self._set_cache(cache_key, lineups_info)
                    return lineups_info
                
        except Exception as e:
            logger.warning(f"Error fetching MLB lineups: {e}")
        
        return {'games': [], 'last_updated': datetime.now().isoformat()}

    async def get_soccer_lineups(self, league: str = 'premier-league') -> Dict:
        """
        Obtiene información de alineaciones de fútbol
        """
        cache_key = f"soccer_lineups_{league}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        try:
            # Usar ESPN Soccer API
            url = f"{ESPN_API_BASE}/soccer/{league}/scoreboard"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    soccer_info = {
                        'matches': [],
                        'last_updated': datetime.now().isoformat()
                    }
                    
                    if 'events' in data:
                        for match in data['events']:
                            match_info = {
                                'match_id': match.get('id'),
                                'home_team': match.get('competitions', [{}])[0].get('competitors', [{}])[0].get('team', {}).get('displayName'),
                                'away_team': match.get('competitions', [{}])[0].get('competitors', [{}])[1].get('team', {}).get('displayName'),
                                'status': match.get('status', {}).get('type', {}).get('description'),
                                'date': match.get('date'),
                                'lineups_available': False,
                                'key_players': []
                            }
                            
                            # Intentar obtener información de jugadores clave
                            if 'competitions' in match and match['competitions']:
                                comp = match['competitions'][0]
                                if 'competitors' in comp:
                                    for team in comp['competitors']:
                                        if 'roster' in team:
                                            for player in team.get('roster', []):
                                                if player.get('starter', False):
                                                    match_info['key_players'].append({
                                                        'name': player.get('athlete', {}).get('displayName'),
                                                        'position': player.get('position', {}).get('abbreviation'),
                                                        'team': team.get('team', {}).get('displayName')
                                                    })
                            
                            soccer_info['matches'].append(match_info)
                    
                    self._set_cache(cache_key, soccer_info)
                    return soccer_info
                
        except Exception as e:
            logger.warning(f"Error fetching soccer lineups: {e}")
        
        return {'matches': [], 'last_updated': datetime.now().isoformat()}

    async def get_team_news(self, sport: str, team_name: str) -> Dict:
        """
        Obtiene noticias recientes del equipo para detectar cambios importantes
        """
        cache_key = f"team_news_{sport}_{team_name}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        try:
            # Normalizar sport para ESPN
            sport_map = {
                'basketball': 'basketball/nba',
                'baseball': 'baseball/mlb',
                'soccer': 'soccer',
                'football': 'football/nfl',
                'tennis': 'tennis'
            }
            
            espn_sport = sport_map.get(sport, sport)
            url = f"{ESPN_API_BASE}/{espn_sport}/news"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    news_info = {
                        'articles': [],
                        'last_updated': datetime.now().isoformat()
                    }
                    
                    if 'articles' in data:
                        team_keywords = team_name.lower().split()
                        
                        for article in data['articles'][:10]:  # Solo 10 más recientes
                            headline = article.get('headline', '').lower()
                            description = article.get('description', '').lower()
                            
                            # Verificar si la noticia es relevante al equipo
                            if any(keyword in headline or keyword in description for keyword in team_keywords):
                                news_info['articles'].append({
                                    'headline': article.get('headline'),
                                    'description': article.get('description'),
                                    'published': article.get('published'),
                                    'impact_level': self._assess_news_impact(headline, description),
                                    'source': 'ESPN'
                                })
                    
                    self._set_cache(cache_key, news_info)
                    return news_info
                
        except Exception as e:
            logger.warning(f"Error fetching team news: {e}")
        
        return {'articles': [], 'last_updated': datetime.now().isoformat()}

    def _assess_news_impact(self, headline: str, description: str) -> str:
        """
        Evalúa el impacto potencial de una noticia
        """
        text = f"{headline} {description}".lower()
        
        # Palabras clave de alto impacto
        high_impact = ['injured', 'out', 'suspended', 'traded', 'released', 'benched', 'ejected', 'ruled out']
        medium_impact = ['questionable', 'doubtful', 'probable', 'limited', 'minutes restriction']
        low_impact = ['practice', 'interview', 'comment', 'statement']
        
        if any(keyword in text for keyword in high_impact):
            return 'HIGH'
        elif any(keyword in text for keyword in medium_impact):
            return 'MEDIUM'
        elif any(keyword in text for keyword in low_impact):
            return 'LOW'
        
        return 'UNKNOWN'

    async def get_comprehensive_team_info(self, sport: str, home_team: str, away_team: str) -> Dict:
        """
        Obtiene información completa de ambos equipos para un partido
        """
        try:
            # Ejecutar consultas en paralelo
            tasks = []
            
            if 'basketball' in sport or 'nba' in sport:
                tasks.extend([
                    self.get_nba_injury_report(),
                    self.get_team_news('basketball', home_team),
                    self.get_team_news('basketball', away_team)
                ])
            elif 'baseball' in sport or 'mlb' in sport:
                tasks.extend([
                    self.get_mlb_lineups(),
                    self.get_team_news('baseball', home_team),
                    self.get_team_news('baseball', away_team)
                ])
            elif 'soccer' in sport or 'football' in sport:
                tasks.extend([
                    self.get_soccer_lineups(),
                    self.get_team_news('soccer', home_team),
                    self.get_team_news('soccer', away_team)
                ])
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Procesar resultados
            comprehensive_info = {
                'home_team': home_team,
                'away_team': away_team,
                'sport': sport,
                'injury_report': {},
                'lineups': {},
                'home_news': {},
                'away_news': {},
                'overall_impact': 'MEDIUM',
                'confidence_adjustment': 0.0,  # -0.2 a +0.2 para ajustar probabilidades
                'last_updated': datetime.now().isoformat()
            }
            
            # Asignar resultados según el deporte
            if len(results) >= 3:
                if 'basketball' in sport or 'nba' in sport:
                    comprehensive_info['injury_report'] = results[0] if not isinstance(results[0], Exception) else {}
                    comprehensive_info['home_news'] = results[1] if not isinstance(results[1], Exception) else {}
                    comprehensive_info['away_news'] = results[2] if not isinstance(results[2], Exception) else {}
                elif 'baseball' in sport or 'mlb' in sport:
                    comprehensive_info['lineups'] = results[0] if not isinstance(results[0], Exception) else {}
                    comprehensive_info['home_news'] = results[1] if not isinstance(results[1], Exception) else {}
                    comprehensive_info['away_news'] = results[2] if not isinstance(results[2], Exception) else {}
                elif 'soccer' in sport or 'football' in sport:
                    comprehensive_info['lineups'] = results[0] if not isinstance(results[0], Exception) else {}
                    comprehensive_info['home_news'] = results[1] if not isinstance(results[1], Exception) else {}
                    comprehensive_info['away_news'] = results[2] if not isinstance(results[2], Exception) else {}
            
            # Calcular ajuste de confianza basado en la información disponible
            comprehensive_info['confidence_adjustment'] = self._calculate_confidence_adjustment(comprehensive_info)
            comprehensive_info['overall_impact'] = self._calculate_overall_impact(comprehensive_info)
            
            return comprehensive_info
            
        except Exception as e:
            logger.error(f"Error getting comprehensive team info: {e}")
            return {
                'home_team': home_team,
                'away_team': away_team,
                'sport': sport,
                'confidence_adjustment': 0.0,
                'overall_impact': 'MEDIUM',
                'last_updated': datetime.now().isoformat()
            }

    def _calculate_confidence_adjustment(self, info: Dict) -> float:
        """
        Calcula un ajuste de confianza basado en la información disponible
        Retorna un valor entre -0.2 (reducir confianza) y +0.2 (aumentar confianza)
        """
        adjustment = 0.0
        
        # Evaluar lesiones (NBA)
        injuries = info.get('injury_report', {}).get('injuries', [])
        for injury in injuries:
            impact = injury.get('impact_level', 'MEDIUM')
            if impact == 'HIGH':
                adjustment -= 0.05  # Reducir confianza por lesiones importantes
            elif impact == 'MEDIUM':
                adjustment -= 0.02
        
        # Evaluar noticias de ambos equipos
        for team_type in ['home_news', 'away_news']:
            articles = info.get(team_type, {}).get('articles', [])
            for article in articles:
                impact = article.get('impact_level', 'MEDIUM')
                if impact == 'HIGH':
                    adjustment -= 0.03  # Noticias negativas reducen confianza
                elif impact == 'LOW':
                    adjustment += 0.01  # Noticias neutrales/positivas aumentan ligeramente
        
        # Evaluar disponibilidad de alineaciones
        lineups = info.get('lineups', {})
        if lineups.get('games') or lineups.get('matches'):
            adjustment += 0.02  # Tener información de alineaciones aumenta confianza
        
        # Limitar el ajuste entre -0.2 y +0.2
        return max(-0.2, min(0.2, adjustment))

    def _calculate_overall_impact(self, info: Dict) -> str:
        """
        Calcula el impacto general basado en toda la información
        """
        high_impact_count = 0
        medium_impact_count = 0
        
        # Contar impactos de lesiones
        injuries = info.get('injury_report', {}).get('injuries', [])
        for injury in injuries:
            impact = injury.get('impact_level', 'MEDIUM')
            if impact == 'HIGH':
                high_impact_count += 1
            elif impact == 'MEDIUM':
                medium_impact_count += 1
        
        # Contar impactos de noticias
        for team_type in ['home_news', 'away_news']:
            articles = info.get(team_type, {}).get('articles', [])
            for article in articles:
                impact = article.get('impact_level', 'MEDIUM')
                if impact == 'HIGH':
                    high_impact_count += 1
                elif impact == 'MEDIUM':
                    medium_impact_count += 1
        
        # Determinar impacto general
        if high_impact_count >= 2:
            return 'HIGH'
        elif high_impact_count >= 1 or medium_impact_count >= 3:
            return 'MEDIUM'
        else:
            return 'LOW'


# Función helper para uso fácil
async def get_sports_info(sport: str, home_team: str, away_team: str) -> Dict:
    """
    Función de conveniencia para obtener información deportiva
    """
    async with SportsAPIClient() as client:
        return await client.get_comprehensive_team_info(sport, home_team, away_team)


# Ejemplo de uso
if __name__ == "__main__":
    async def test():
        async with SportsAPIClient() as client:
            # Probar con un partido de NBA
            info = await client.get_comprehensive_team_info(
                'basketball_nba', 
                'Philadelphia 76ers', 
                'Boston Celtics'
            )
            print(json.dumps(info, indent=2))
    
    asyncio.run(test())