"""
scanner/advanced_scanner.py - Scanner avanzado con análisis completo de odds-trader intelligence.

Integra todos los módulos analytics (vig, consensus, movement, sharp) para detectar
value bets reales y filtrar trampas de valor (value traps).
"""
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timezone, timedelta
import os
import sys

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from model.probabilities import estimate_probabilities
from analytics.vig import calculate_vig, is_vig_acceptable, market_efficiency_score
from analytics.consensus import consensus_score, find_best_value_book, market_agreement_score
from analytics.movement import detect_movement, store_initial_odd, get_movement_summary
from analytics.sharp_detector import detect_sharp_signals, get_sharp_summary


MIN_ODD = float(os.getenv("MIN_ODD", "1.5"))
MAX_ODD = float(os.getenv("MAX_ODD", "2.5"))
MIN_PROBABILITY = float(os.getenv("MIN_PROBABILITY", "55"))  # 55% de acierto mínimo

# Sport-specific value thresholds
VALUE_THRESHOLDS = {
    "NBA": 1.09,
    "MLB": 1.10,
    "Soccer": 1.08,
    "Tennis": 1.07
}


def sport_prefix(sport: str) -> str:
    """Mapea sport key a nombre normalizado."""
    lower = sport.lower()
    if "basketball" in lower or "nba" in lower:
        return "NBA"
    elif "baseball" in lower or "mlb" in lower:
        return "MLB"
    elif "soccer" in lower or "football" in lower:
        return "Soccer"
    elif "tennis" in lower:
        return "Tennis"
    return "Soccer"  # default


async def find_value_bets_advanced(odds_data: List[Dict]) -> List[Dict]:
    """
    Scanner avanzado con validación completa de odds-trader intelligence.
    
    Flow:
    1. Filters básicos (tiempo, cuotas, live games)
    2. Cálculo de probabilidades (modelo por deporte)
    3. Análisis de vig (margin bookmaker)
    4. Cálculo de valor (prob real vs implied)
    5. Análisis de consenso (comparar con otras casas)
    6. Análisis de movimiento (línea subió/bajó)
    7. Detección sharp (señales de dinero profesional)
    8. Score final y filtro de trampas
    
    Returns:
        Lista de candidatos con análisis completo
    """
    candidates = []
    now = datetime.now(timezone.utc)
    window_end = now + timedelta(hours=24)
    
    for event in odds_data:
        sport = event.get("sport_key", "")
        sport_name = sport_prefix(sport)
        threshold = VALUE_THRESHOLDS.get(sport_name, 1.08)
        
        # Filter: evento futuro en ventana de 24h
        commence_time_str = event.get("commence_time", "")
        if not commence_time_str:
            continue
        
        try:
            commence_time = datetime.fromisoformat(commence_time_str.replace("Z", "+00:00"))
        except:
            continue
        
        if commence_time <= now or commence_time > window_end:
            continue
        
        home_team = event.get("home_team", "")
        away_team = event.get("away_team", "")
        event_id = event.get("id", "")
        
        # Estimar probabilidades con modelo por deporte (una vez por evento)
        probabilities = estimate_probabilities(event)
        if not probabilities:
            continue
        
        # Iterar sobre bookmakers
        for bookmaker_data in event.get("bookmakers", []):
            bookmaker = bookmaker_data.get("key", "")
            
            # Iterar sobre markets (h2h, totals, spreads)
            for market in bookmaker_data.get("markets", []):
                market_key = market.get("key", "")
                
                # Recolectar cuotas de todos los books para este mercado (para consensus)
                all_books_odds = {}
                for bm in event.get("bookmakers", []):
                    for mk in bm.get("markets", []):
                        if mk.get("key") == market_key:
                            for outcome in mk.get("outcomes", []):
                                outcome_name = outcome.get("name", "")
                                odd_val = outcome.get("price", 0)
                                
                                if outcome_name not in all_books_odds:
                                    all_books_odds[outcome_name] = {}
                                all_books_odds[outcome_name][bm.get("key", "")] = odd_val
                
                # Analizar cada outcome del market actual
                for outcome in market.get("outcomes", []):
                    outcome_name = outcome.get("name", "")
                    odd = outcome.get("price", 0)
                    
                    # Filter: rango de cuotas
                    if not (MIN_ODD <= odd <= MAX_ODD):
                        continue
                    
                    # Determinar probabilidad según el mercado (igual que scanner.py)
                    real_prob = None
                    
                    if market_key == 'h2h':
                        # Mercado head-to-head (ganador)
                        name_lower = outcome_name.lower()
                        if 'draw' in name_lower or name_lower in ['x', 'empate']:
                            real_prob = probabilities.get('draw')
                        elif (home_team and home_team.lower() in name_lower) or name_lower in ['home', 'local']:
                            real_prob = probabilities.get('home')
                        elif (away_team and away_team.lower() in name_lower) or name_lower in ['away', 'visitante']:
                            real_prob = probabilities.get('away')
                        else:
                            # Fallback: usar primera probabilidad disponible
                            if 'home' in probabilities:
                                real_prob = probabilities.get('home')
                            elif probabilities:
                                real_prob = list(probabilities.values())[0]
                    
                    elif market_key == 'totals':
                        # Totales: Over/Under - usar 50% como estimación base
                        real_prob = 0.52 if 'over' in outcome_name.lower() else 0.48
                    
                    elif market_key == 'spreads':
                        # Hándicap: usar probabilidad home/away ajustada
                        name_lower = outcome_name.lower()
                        if home_team and home_team.lower() in name_lower:
                            real_prob = probabilities.get('home', 0.5)
                        else:
                            real_prob = probabilities.get('away', 0.5)
                    
                    if not real_prob or real_prob <= 0:
                        continue
                    
                    # Filter: probabilidad mínima (convertir a 0-1 si está en 0-100)
                    real_prob_pct = real_prob * 100 if real_prob <= 1.0 else real_prob
                    if real_prob_pct < MIN_PROBABILITY:
                        continue
                    
                    # Normalizar real_prob a 0-1 para cálculos
                    if real_prob > 1.0:
                        real_prob = real_prob / 100
                    
                    # === ANÁLISIS DE VIG ===
                    # Calcular vig para este market (todos los outcomes)
                    market_odds = {o.get("name", ""): float(o.get("price", 0)) for o in market.get("outcomes", [])}
                    vig = calculate_vig(market_odds)
                    vig_ok = is_vig_acceptable(vig)
                    efficiency = market_efficiency_score(vig)
                    
                    if not vig_ok:
                        continue  # Rechazar mercados con vig excesivo
                    
                    # Probabilidad implícita (ajustada por vig)
                    implied_prob = (1 / odd) * 100
                    
                    # Calcular valor
                    value = odd * real_prob
                    
                    if value < threshold:
                        continue
                    
                    # === ANÁLISIS DE CONSENSO ===
                    consensus_data = {}
                    outlier_status = "normal"
                    agreement = 0.0
                    
                    if outcome_name in all_books_odds:
                        book_odds_for_outcome = all_books_odds[outcome_name]
                        consensus_data = consensus_score(book_odds_for_outcome, bookmaker)
                        
                        if consensus_data.get('is_outlier'):
                            diff_pct = consensus_data.get('diff_from_mean_pct', 0)
                            if diff_pct > 0:
                                outlier_status = "outlier_alto"
                            else:
                                outlier_status = "outlier_bajo"
                        
                        agreement = market_agreement_score(book_odds_for_outcome)
                    
                    # === ANÁLISIS DE MOVIMIENTO ===
                    # Store odd inicial si no existe
                    store_initial_odd(event_id, bookmaker, market_key, outcome_name, odd)
                    
                    # Detectar movimiento
                    movement_data = detect_movement(event_id, bookmaker, market_key, outcome_name, odd)
                    moved = movement_data.get('moved', False)
                    movement_direction = movement_data.get('direction', 'stable')
                    movement_delta = movement_data.get('delta_pct', 0)
                    
                    # === DETECCIÓN SHARP ===
                    vig_data = {
                        'vig': vig,
                        'is_acceptable': vig_ok,
                        'efficiency_score': efficiency
                    }
                    
                    sharp_data = detect_sharp_signals(movement_data, consensus_data, vig_data)
                    is_sharp = sharp_data.get('is_sharp', False)
                    sharp_score = sharp_data.get('sharp_score', 0)
                    
                    # === SCORE FINAL Y DECISIÓN ===
                    # Calcular score compuesto
                    final_score = 0.0
                    
                    # Base: valor calculado (value - 1.0 es el excess return)
                    final_score += (value - 1.0) * 10  # Normalizar
                    
                    # Bonus: vig bajo
                    if efficiency > 0.8:
                        final_score += 2.0
                    
                    # Bonus: consenso alto (no outlier)
                    if agreement > 0.7 and outlier_status == "normal":
                        final_score += 1.5
                    
                    # Bonus/Penalty: movimiento
                    if moved and movement_direction == 'up':
                        final_score += 1.0  # Línea subiendo = más dinero entrando
                    elif moved and movement_direction == 'down':
                        final_score -= 0.5  # Línea bajando = posible value trap
                    
                    # Bonus: sharp signals
                    final_score += sharp_score * 0.5
                    
                    # Penalty: outlier alto sin sharp signals (posible trap)
                    if outlier_status == "outlier_alto" and not is_sharp:
                        final_score -= 2.0
                    
                    # Threshold final score
                    if final_score < 1.0:
                        continue  # No suficientemente fuerte
                    
                    # === CONSTRUIR CANDIDATO ===
                    
                    # Formatear nombre del mercado en español para mayor claridad
                    market_name_es = market_key
                    if market_key == 'h2h':
                        market_name_es = "Ganador"
                    elif market_key == 'spreads':
                        market_name_es = "Hándicap"
                        # Incluir la línea del hándicap
                        point = outcome.get('point', 0)
                        if point != 0:
                            market_name_es += f" ({point:+.1f})"
                    elif market_key == 'totals':
                        market_name_es = "Totales"
                        # Incluir la línea de totales
                        point = outcome.get('point', 0)
                        if point > 0:
                            market_name_es += f" ({point})"
                    
                    # Formatear selección más clara
                    selection_clear = outcome_name
                    if market_key == 'spreads' and 'point' in outcome:
                        point = outcome['point']
                        if point != 0:
                            selection_clear += f" {point:+.1f}"
                    elif market_key == 'totals' and 'point' in outcome:
                        point = outcome['point']
                        selection_clear = f"{'Over' if 'over' in outcome_name.lower() else 'Under'} {point}"
                    
                    candidate = {
                        "sport": sport_name,
                        "sport_key": event.get('sport_key', ''),
                        "event": f"{home_team} vs {away_team}",
                        "home_team": home_team,
                        "away_team": away_team,
                        "market": market_name_es,
                        "market_key": market_key,
                        "selection": selection_clear,
                        "bookmaker": bookmaker,
                        "odds": odd,
                        "real_probability": real_prob * 100,  # Guardar como porcentaje
                        "implied_probability": implied_prob,
                        "value": value,
                        "edge_percent": (real_prob * 100) - implied_prob,
                        "commence_time": commence_time_str,
                        
                        # Información adicional del mercado
                        "point": outcome.get('point') if 'point' in outcome else None,
                        "total": outcome.get('point') if market_key == 'totals' and 'point' in outcome else None,
                        
                        # Analytics data
                        "vig": vig,
                        "vig_ok": vig_ok,
                        "efficiency": efficiency,
                        
                        "consensus_mean": consensus_data.get('mean', 0),
                        "consensus_diff_pct": consensus_data.get('diff_from_mean_pct', 0),
                        "outlier_status": outlier_status,
                        "agreement_score": agreement,
                        
                        "moved": moved,
                        "movement_direction": movement_direction,
                        "movement_delta_pct": movement_delta,
                        "initial_odd": movement_data.get('initial_odd', odd),
                        
                        "is_sharp": is_sharp,
                        "sharp_score": sharp_score,
                        "sharp_signals": sharp_data.get('signals', []),
                        
                        "final_score": final_score
                    }
                    
                    candidates.append(candidate)
    
    # Ordenar por final_score descendente
    candidates.sort(key=lambda x: x['final_score'], reverse=True)
    
    return candidates


def format_advanced_message(candidate: Dict) -> str:
    """
    Formatea un mensaje enriquecido con toda la inteligencia de trading.
    """
    lines = []
    
    # Header
    lines.append(f"🎯 {candidate['sport']} - {candidate['event']}")
    lines.append(f"📊 {candidate['market']} → {candidate['selection']}")
    lines.append(f"🏠 {candidate['bookmaker']} | Cuota: {candidate['odd']:.2f}")
    lines.append("")
    
    # Probabilidades
    lines.append(f"✅ Prob. Real: {candidate['real_probability']:.1f}%")
    lines.append(f"📉 Prob. Implícita: {candidate['implied_probability']:.1f}%")
    lines.append(f"💎 Valor: {candidate['value']:.3f} | Edge: +{candidate['edge_percent']:.1f}%")
    lines.append("")
    
    # Vig
    lines.append(f"📈 Vig: {candidate['vig']:.2f}% | Eficiencia: {candidate['efficiency']:.2f}")
    
    # Consenso
    if candidate['consensus_mean'] > 0:
        lines.append(f"🌐 Media mercado: {candidate['consensus_mean']:.2f} | Diff: {candidate['consensus_diff_pct']:+.1f}%")
        lines.append(f"   Consenso: {candidate['agreement_score']:.2f} | Status: {candidate['outlier_status']}")
    
    # Movimiento
    if candidate['moved']:
        lines.append(f"📊 Movimiento: {candidate['movement_direction'].upper()} {abs(candidate['movement_delta_pct']):.1f}%")
        lines.append(f"   Inicial: {candidate['initial_odd']:.2f} → Actual: {candidate['odd']:.2f}")
    else:
        lines.append(f"📊 Sin movimiento significativo")
    
    # Sharp
    if candidate['is_sharp']:
        lines.append(f"⚡ SHARP DETECTADO (score: {candidate['sharp_score']:.1f}/5)")
        for signal in candidate['sharp_signals'][:2]:
            lines.append(f"   • {signal}")
    
    lines.append("")
    lines.append(f"🎲 Score Final: {candidate['final_score']:.2f}/10")
    lines.append(f"⏰ {candidate['commence_time']}")
    
    return "\n".join(lines)


# Example usage for testing
if __name__ == "__main__":
    import json
    
    # Load sample data
    sample_path = os.path.join(os.path.dirname(__file__), "..", "data", "sample_odds.json")
    with open(sample_path, "r", encoding="utf-8") as f:
        sample_data = json.load(f)
    
    # Run scanner
    results = asyncio.run(find_value_bets_advanced(sample_data))
    
    print(f"🔍 Encontrados {len(results)} candidatos:\n")
    for i, candidate in enumerate(results[:5], 1):
        print(f"--- Candidato {i} ---")
        print(format_advanced_message(candidate))
        print()
