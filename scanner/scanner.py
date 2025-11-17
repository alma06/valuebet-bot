"""Scanner: identify value bets using model.probabilities and per-sport thresholds.

Rules implemented per your spec:
- Value = odd * prob_est
- Thresholds by sport:
    NBA: 1.09
    MLB: 1.10
    Fútbol: 1.08
    Tenis: 1.07
- Only odds in range 1.5 - 2.5
- Probabilidad mínima: 55%
- Max 5 alerts per day (state stored in data/alerts_state.json)
- Reinicio diario a las 6 AM hora de América (Eastern Time)
- Excluir partidos en vivo (commence_time ya pasó)
- Solo partidos en las próximas 24 horas
- Incluir mercados: h2h, totals, spreads (hándicap)
"""
from typing import List, Dict
from statistics import mean
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

# Intentar usar modelo mejorado, fallback al básico
try:
    from model.enhanced_probabilities import estimate_probabilities_enhanced as estimate_probabilities
    USING_ENHANCED_MODEL = True
except ImportError:
    from model.probabilities import estimate_probabilities
    USING_ENHANCED_MODEL = False

from data.state import AlertsState
from analyzer import generate_analysis

# thresholds per sport key prefix
THRESHOLDS = {
    'basketball': 1.09,
    'americanfootball': 1.09,
    'baseball': 1.10,
    'soccer': 1.08,
    'tennis': 1.07,
}


def implied_prob_from_odd(odd: float) -> float:
    return 1.0 / odd if odd and odd > 0 else 0.0


class ValueScanner:
    def __init__(self, min_odd: float = 1.5, max_odd: float = 2.5, min_prob: float = 0.55):
        self.min_odd = min_odd
        self.max_odd = max_odd
        self.min_prob = min_prob

    def sport_prefix(self, sport_key: str) -> str:
        for k in THRESHOLDS.keys():
            if sport_key.startswith(k):
                return k
        # fallback: try substrings
        if 'soccer' in sport_key or 'football' in sport_key:
            return 'soccer'
        if 'tennis' in sport_key:
            return 'tennis'
        if 'nba' in sport_key or 'basketball' in sport_key:
            return 'basketball'
        if 'mlb' in sport_key or 'baseball' in sport_key:
            return 'baseball'
        return 'other'

    def find_value_bets(self, events: List[Dict]) -> List[Dict]:
        results = []
        now_utc = datetime.now(timezone.utc)
        
        # Límite: 24 horas desde ahora
        max_time = now_utc + timedelta(hours=24)
        
        for ev in events:
            # Filtrar partidos: solo en las próximas 24 horas
            commence_str = ev.get('commence_time')
            if commence_str:
                try:
                    commence_time = datetime.fromisoformat(commence_str.replace('Z', '+00:00'))
                    
                    if commence_time <= now_utc:
                        # Partido ya comenzó o está en vivo
                        continue
                    
                    if commence_time > max_time:
                        # Partido es en más de 24 horas
                        continue
                        
                except Exception:
                    pass  # Si no se puede parsear, continuar con el evento
            
            sport_key = ev.get('sport_key', ev.get('_sport_key', ''))
            prefix = self.sport_prefix(sport_key)
            threshold = THRESHOLDS.get(prefix)
            if not threshold:
                continue
            probs = estimate_probabilities(ev)
            # Incluir mercados: h2h, totals (over/under), spreads (hándicap)
            for bm in ev.get('bookmakers', []):
                for m in bm.get('markets', []):
                    market_key = m.get('key')
                    # Aceptar h2h, totals, spreads
                    if market_key not in ['h2h', 'totals', 'spreads']:
                        continue
                    
                    for out in m.get('outcomes', []):
                        sel = out.get('name')
                        odd = float(out.get('price'))
                        if odd < self.min_odd or odd > self.max_odd:
                            continue
                        
                        # Determinar probabilidad según el mercado
                        prob_est = None
                        
                        if market_key == 'h2h':
                            # Mercado head-to-head (ganador)
                            home = ev.get('home_team') or ev.get('home') or ev.get('competitor_home')
                            away = ev.get('away_team') or ev.get('away') or ev.get('competitor_away')
                            name_lower = sel.lower()
                            if 'draw' in name_lower or name_lower in ['x','empate']:
                                prob_est = probs.get('draw')
                            elif (home and home.lower() in name_lower) or name_lower in ['home','local']:
                                prob_est = probs.get('home')
                            elif (away and away.lower() in name_lower) or name_lower in ['away','visitante']:
                                prob_est = probs.get('away')
                            else:
                                if 'home' in probs:
                                    prob_est = probs.get('home')
                                else:
                                    prob_est = list(probs.values())[0]
                        
                        elif market_key == 'totals':
                            # Totales: Over/Under - usar 50% como estimación base
                            # (simplificación, idealmente analizar histórico de puntos)
                            prob_est = 0.52 if 'over' in sel.lower() else 0.48
                        
                        elif market_key == 'spreads':
                            # Hándicap: usar probabilidad home/away ajustada
                            home = ev.get('home_team') or ev.get('home') or ev.get('competitor_home')
                            name_lower = sel.lower()
                            if home and home.lower() in name_lower:
                                prob_est = probs.get('home', 0.5)
                            else:
                                prob_est = probs.get('away', 0.5)
                        
                        if not prob_est or prob_est < self.min_prob:
                            continue  # Filtrar si prob < 55%
                        
                        value = odd * prob_est
                        if value >= threshold:
                            home = ev.get('home_team') or ev.get('home') or ev.get('competitor_home')
                            away = ev.get('away_team') or ev.get('away') or ev.get('competitor_away')
                            analysis = generate_analysis(ev, sel, odd, prob_est)
                            
                            # Formatear fecha y hora del evento
                            commence_time_str = ""
                            if commence_str:
                                try:
                                    dt = datetime.fromisoformat(commence_str.replace('Z', '+00:00'))
                                    commence_time_str = dt.strftime("%Y-%m-%d %H:%M UTC")
                                except:
                                    commence_time_str = commence_str
                            
                            results.append({
                                'id': ev.get('id'),
                                'sport': ev.get('sport_nice', sport_key),
                                'sport_key': sport_key,
                                'home': home,
                                'away': away,
                                'commence_time': commence_time_str,
                                'market': market_key,
                                'selection': sel,
                                'odds': odd,
                                'prob': prob_est,
                                'value': value,
                                'book': bm.get('title'),
                                'url': bm.get('url',''),
                                'analysis': analysis,
                            })
        # De-duplicate by id+selection keeping highest
        unique = {}
        for r in results:
            key = (r['id'], r['selection'])
            if key not in unique or r['value'] > unique[key]['value']:
                unique[key] = r
        return list(unique.values())
