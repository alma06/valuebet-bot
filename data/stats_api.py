"""
data/stats_api.py - APIs gratuitas para estadísticas deportivas

Fuentes de datos:
- Football-Data.org (fútbol)
- NBA Stats API (baloncesto)
- ESPN (scraping de lesiones)
- Balldontlie.io (NBA alternativa)
"""
import requests
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class FootballDataAPI:
    """
    API gratuita de Football-Data.org
    Límite: 10 requests/minuto
    Datos: Premier League, La Liga, Bundesliga, Serie A, Ligue 1, Champions
    """
    
    BASE_URL = "https://api.football-data.org/v4"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: Token gratuito de football-data.org
                     Registrarse en: https://www.football-data.org/client/register
        """
        self.api_key = api_key or "YOUR_FREE_TOKEN_HERE"
        self.headers = {"X-Auth-Token": self.api_key}
        self.last_request_time = 0
        self.min_request_interval = 6  # 10 req/min = 6 segundos entre requests
    
    def _rate_limit(self):
        """Respetar límite de 10 req/min"""
        now = time.time()
        time_since_last = now - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def get_team_stats(self, team_id: int) -> Optional[Dict]:
        """
        Obtiene estadísticas de un equipo
        
        Returns:
            {
                'wins': int,
                'draws': int,
                'losses': int,
                'goals_for': int,
                'goals_against': int,
                'home_record': {...},
                'away_record': {...}
            }
        """
        try:
            self._rate_limit()
            url = f"{self.BASE_URL}/teams/{team_id}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Procesar datos
                return self._parse_team_stats(data)
            else:
                logger.warning(f"Football-Data API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching team stats: {e}")
            return None
    
    def get_h2h(self, team1_id: int, team2_id: int, limit: int = 10) -> List[Dict]:
        """
        Obtiene historial head-to-head entre dos equipos
        
        Returns:
            Lista de últimos partidos entre los equipos
        """
        try:
            self._rate_limit()
            url = f"{self.BASE_URL}/matches"
            params = {
                'team1': team1_id,
                'team2': team2_id,
                'limit': limit,
                'status': 'FINISHED'
            }
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('matches', [])
            return []
            
        except Exception as e:
            logger.error(f"Error fetching H2H: {e}")
            return []
    
    def get_recent_matches(self, team_id: int, limit: int = 10) -> List[Dict]:
        """
        Obtiene últimos partidos de un equipo
        
        Returns:
            Lista con forma reciente del equipo
        """
        try:
            self._rate_limit()
            url = f"{self.BASE_URL}/teams/{team_id}/matches"
            params = {
                'limit': limit,
                'status': 'FINISHED'
            }
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('matches', [])
            return []
            
        except Exception as e:
            logger.error(f"Error fetching recent matches: {e}")
            return []
    
    def _parse_team_stats(self, data: Dict) -> Dict:
        """Parsea respuesta de la API en formato estándar"""
        # Implementar parseo según estructura de football-data.org
        return {
            'team_name': data.get('name', ''),
            'team_id': data.get('id', 0),
            # Agregar más campos según necesidad
        }


class NBAStatsAPI:
    """
    API gratuita oficial de NBA Stats
    Límite: Sin límite oficial (usar con moderación)
    Datos: Todos los equipos y jugadores NBA
    """
    
    BASE_URL = "https://stats.nba.com/stats"
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://stats.nba.com/',
        }
        self.last_request_time = 0
        self.min_request_interval = 1  # 1 segundo entre requests (cortesía)
    
    def _rate_limit(self):
        """Rate limiting cortés"""
        now = time.time()
        time_since_last = now - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def get_team_stats(self, team_id: int, season: str = "2024-25") -> Optional[Dict]:
        """
        Obtiene estadísticas de un equipo NBA
        
        Args:
            team_id: ID del equipo (ej: 1610612747 para Lakers)
            season: Temporada (ej: "2024-25")
        
        Returns:
            {
                'wins': int,
                'losses': int,
                'win_pct': float,
                'ppg': float,  # Puntos por partido
                'oppg': float,  # Puntos rivales
                'home_record': str,
                'away_record': str
            }
        """
        try:
            self._rate_limit()
            endpoint = f"{self.BASE_URL}/teamdashboardbygeneralsplits"
            params = {
                'TeamID': team_id,
                'Season': season,
                'SeasonType': 'Regular Season',
                'MeasureType': 'Base',
                'PerMode': 'Totals'
            }
            
            response = requests.get(endpoint, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_nba_team_stats(data)
            else:
                logger.warning(f"NBA Stats API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching NBA team stats: {e}")
            return None
    
    def get_recent_games(self, team_id: int, last_n: int = 10) -> List[Dict]:
        """
        Obtiene últimos N partidos de un equipo
        
        Returns:
            Lista de resultados recientes
        """
        try:
            self._rate_limit()
            endpoint = f"{self.BASE_URL}/teamgamelog"
            params = {
                'TeamID': team_id,
                'Season': '2024-25',
                'SeasonType': 'Regular Season'
            }
            
            response = requests.get(endpoint, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                games = self._parse_nba_game_log(data)
                return games[:last_n]
            return []
            
        except Exception as e:
            logger.error(f"Error fetching NBA recent games: {e}")
            return []
    
    def get_injury_report(self) -> List[Dict]:
        """
        Obtiene reporte de lesiones NBA
        
        Returns:
            Lista de jugadores lesionados
        """
        try:
            self._rate_limit()
            # NBA no tiene endpoint público de lesiones, usar scraping alternativo
            logger.info("Injury report requires ESPN scraping")
            return []
            
        except Exception as e:
            logger.error(f"Error fetching injury report: {e}")
            return []
    
    def _parse_nba_team_stats(self, data: Dict) -> Dict:
        """Parsea respuesta de NBA Stats API"""
        try:
            result_sets = data.get('resultSets', [])
            if result_sets:
                headers = result_sets[0].get('headers', [])
                rows = result_sets[0].get('rowSet', [])
                
                if rows:
                    row = rows[0]
                    stats_dict = dict(zip(headers, row))
                    
                    return {
                        'wins': stats_dict.get('W', 0),
                        'losses': stats_dict.get('L', 0),
                        'win_pct': stats_dict.get('W_PCT', 0.5),
                        'ppg': stats_dict.get('PTS', 0) / max(stats_dict.get('GP', 1), 1),
                        'oppg': stats_dict.get('OPP_PTS', 0) / max(stats_dict.get('GP', 1), 1),
                    }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error parsing NBA stats: {e}")
            return {}
    
    def _parse_nba_game_log(self, data: Dict) -> List[Dict]:
        """Parsea game log de NBA"""
        try:
            result_sets = data.get('resultSets', [])
            if result_sets:
                headers = result_sets[0].get('headers', [])
                rows = result_sets[0].get('rowSet', [])
                
                games = []
                for row in rows:
                    game_dict = dict(zip(headers, row))
                    games.append({
                        'date': game_dict.get('GAME_DATE', ''),
                        'matchup': game_dict.get('MATCHUP', ''),
                        'result': game_dict.get('WL', ''),
                        'pts': game_dict.get('PTS', 0),
                        'opp_pts': game_dict.get('OPP_PTS', 0),
                    })
                
                return games
            
            return []
            
        except Exception as e:
            logger.error(f"Error parsing game log: {e}")
            return []


class ESPNInjuryScraper:
    """
    Scraper de ESPN para obtener lesiones
    Fuente: ESPN Injury Report (gratis, sin API key)
    """
    
    INJURY_URLS = {
        'nba': 'https://www.espn.com/nba/injuries',
        'nfl': 'https://www.espn.com/nfl/injuries',
        'mlb': 'https://www.espn.com/mlb/injuries',
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_injuries(self, sport: str = 'nba') -> List[Dict]:
        """
        Scraper de lesiones de ESPN
        
        Args:
            sport: 'nba', 'nfl', 'mlb'
        
        Returns:
            Lista de lesiones:
            [
                {
                    'player': 'LeBron James',
                    'team': 'Lakers',
                    'position': 'F',
                    'injury': 'Ankle',
                    'status': 'Out'
                },
                ...
            ]
        """
        try:
            url = self.INJURY_URLS.get(sport.lower())
            if not url:
                logger.warning(f"Sport {sport} not supported for injury scraping")
                return []
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.content, 'lxml')
                
                injuries = []
                # Parsear tabla de lesiones de ESPN
                # Estructura puede cambiar, implementar según HTML actual
                
                # Ejemplo simplificado (ajustar según estructura real):
                tables = soup.find_all('table', class_='Table')
                for table in tables:
                    rows = table.find_all('tr')[1:]  # Skip header
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) >= 4:
                            injuries.append({
                                'player': cells[0].get_text(strip=True),
                                'position': cells[1].get_text(strip=True),
                                'injury': cells[2].get_text(strip=True),
                                'status': cells[3].get_text(strip=True),
                            })
                
                logger.info(f"Scraped {len(injuries)} injuries from ESPN {sport}")
                return injuries
                
            else:
                logger.warning(f"ESPN scraping failed: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error scraping ESPN injuries: {e}")
            return []


# Instancia global
football_api = FootballDataAPI()
nba_api = NBAStatsAPI()
injury_scraper = ESPNInjuryScraper()


def get_football_stats(team_name: str) -> Optional[Dict]:
    """Helper para obtener stats de fútbol por nombre de equipo"""
    # Implementar búsqueda de team_id por nombre
    return None


def get_nba_stats(team_name: str) -> Optional[Dict]:
    """Helper para obtener stats NBA por nombre de equipo"""
    # Mapeo de nombres a IDs (implementar)
    team_ids = {
        'Lakers': 1610612747,
        'Celtics': 1610612738,
        # Agregar todos los equipos...
    }
    
    team_id = team_ids.get(team_name)
    if team_id:
        return nba_api.get_team_stats(team_id)
    return None


def get_injuries_by_sport(sport: str) -> List[Dict]:
    """Helper para obtener lesiones por deporte"""
    sport_map = {
        'basketball_nba': 'nba',
        'americanfootball_nfl': 'nfl',
        'baseball_mlb': 'mlb',
    }
    
    espn_sport = sport_map.get(sport, sport)
    return injury_scraper.get_injuries(espn_sport)
