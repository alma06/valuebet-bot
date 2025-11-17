"""Model functions: Poisson for football, simple estimators for tennis/NBA/MLB.

These are intentionally simple, modular functions. Improve with real data sources
(xG feeds, player rankings, injury APIs) for production accuracy.
"""
import math
from typing import Tuple
import statistics

# ---------- Football (Poisson model) ----------

def poisson_pmf(k: int, lam: float) -> float:
    return (lam ** k) * math.exp(-lam) / math.factorial(k)


def football_1x2_from_xg(home_xg: float, away_xg: float, max_goals: int = 10) -> Tuple[float, float, float]:
    """Estimate 1X2 probabilities using independent Poisson for goals.

    Returns (p_home_win, p_draw, p_away_win)
    """
    # Build distribution of goal counts
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
    # Normalize (small tail error possible)
    total = p_home + p_draw + p_away
    if total == 0:
        return 0.0, 0.0, 0.0
    return p_home / total, p_draw / total, p_away / total


# ---------- Tennis (ranking + recent form) ----------

def tennis_win_prob(ranking_a: int, ranking_b: int, recent_a: list = None, recent_b: list = None) -> float:
    """Simple tennis win probability based on rankings and recent form.

    ranking: lower is better. We transform ranking into strength.
    recent: list of last N results as 1/0.
    Returns probability of A winning.
    """
    if recent_a is None:
        recent_a = []
    if recent_b is None:
        recent_b = []
    # ranking strength (simple): inverse ranking
    s_a = 1.0 / max(1, ranking_a)
    s_b = 1.0 / max(1, ranking_b)
    # recent form factor
    fa = (sum(recent_a) / len(recent_a)) if recent_a else 0.5
    fb = (sum(recent_b) / len(recent_b)) if recent_b else 0.5
    # Combine
    strength_a = 0.7 * s_a + 0.3 * fa
    strength_b = 0.7 * s_b + 0.3 * fb
    prob_a = strength_a / (strength_a + strength_b)
    return prob_a


# ---------- NBA/MLB (simple team form + injuries) ----------

def team_win_prob_simple(winrate_a: float, winrate_b: float, injury_factor_a: float = 1.0, injury_factor_b: float = 1.0) -> float:
    """Estimate probability of team A beating B using winrates and injury multipliers.

    winrate in [0,1]; injury_factor multiplicative (e.g., 0.95 reduces strength).
    """
    a = max(0.001, winrate_a) * injury_factor_a
    b = max(0.001, winrate_b) * injury_factor_b
    prob_a = a / (a + b)
    return prob_a


# Helper to combine market analysis into 1X2 probabilities depending on sport

def estimate_probabilities(event: dict) -> dict:
    """Given a standardized event dict, estimate probabilities for the primary outcomes.

    Returns structure with keys depending on sport:
    - football: {'home': p_home, 'draw': p_draw, 'away': p_away}
    - tennis: {'home': p_home, 'away': p_away}
    - nba/mlb: {'home': p_home, 'away': p_away}
    """
    sport = event.get('sport_key', '')
    # Football
    if sport.startswith('soccer'):
        # Expect optional xg in event['extra'] e.g., {'home_xg': 1.2, 'away_xg': 0.9}
        extra = event.get('extra', {})
        hxg = float(extra.get('home_xg', 1.2))
        axg = float(extra.get('away_xg', 1.0))
        p_home, p_draw, p_away = football_1x2_from_xg(hxg, axg)
        return {'home': p_home, 'draw': p_draw, 'away': p_away}
    # Tennis
    if sport.startswith('tennis'):
        extra = event.get('extra', {})
        r_home = int(extra.get('ranking_home', 1000))
        r_away = int(extra.get('ranking_away', 1000))
        recent_home = extra.get('recent_home', [])
        recent_away = extra.get('recent_away', [])
        p_home = tennis_win_prob(r_home, r_away, recent_home, recent_away)
        return {'home': p_home, 'away': 1.0 - p_home}
    # NBA/MLB (basketball_nba, baseball_mlb)
    if sport.startswith('basketball') or sport.startswith('baseball'):
        extra = event.get('extra', {})
        wr_home = float(extra.get('winrate_home', 0.55))
        wr_away = float(extra.get('winrate_away', 0.45))
        inj_factor_h = float(extra.get('injury_factor_home', 1.0))
        inj_factor_a = float(extra.get('injury_factor_away', 1.0))
        p_home = team_win_prob_simple(wr_home, wr_away, inj_factor_h, inj_factor_a)
        return {'home': p_home, 'away': 1.0 - p_home}
    # Default fallback: equal
    return {'home': 0.5, 'away': 0.5, 'draw': 0.0}
