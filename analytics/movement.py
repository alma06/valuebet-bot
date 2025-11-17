"""
analytics/movement.py - Detección de movimientos de cuotas (odds line movement).

Rastrea cambios en las cuotas a lo largo del tiempo para detectar:
- Steam moves (movimientos coordinados rápidos)
- Reverse line movements (contra el dinero público)
- Drift (cuota sube = menos confianza)
- Drop (cuota baja = más dinero llegando)

Persistencia: usa data/odds_history.json para guardar snapshots de cuotas.
"""
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta, timezone
import json
import os


# Config
MOVEMENT_WINDOW_HOURS = int(os.getenv("MOVEMENT_WINDOW_HOURS", "12"))
MOVEMENT_DELTA_PERCENT = float(os.getenv("MOVEMENT_DELTA_PERCENT", "6.0"))

# Estructura: {event_id: {book: {market: [{timestamp, odd}]}}}
_history_cache: Dict = {}


def store_initial_odd(event_id: str, book: str, market: str, outcome: str, odd: float, timestamp: datetime = None):
    """
    Guarda la cuota inicial (apertura) para un evento/book/market/outcome.
    
    Args:
        event_id: ID único del evento
        book: Nombre del bookmaker
        market: Tipo de mercado (h2h, totals, spreads)
        outcome: Nombre del outcome (equipo/selección)
        odd: Cuota registrada
        timestamp: Momento del registro (default: ahora UTC)
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    
    if event_id not in _history_cache:
        _history_cache[event_id] = {}
    if book not in _history_cache[event_id]:
        _history_cache[event_id][book] = {}
    if market not in _history_cache[event_id][book]:
        _history_cache[event_id][book][market] = {}
    if outcome not in _history_cache[event_id][book][market]:
        _history_cache[event_id][book][market][outcome] = []
    
    # Solo agregar si no existe ya para este outcome
    existing = _history_cache[event_id][book][market][outcome]
    if not existing:
        _history_cache[event_id][book][market][outcome].append({
            'timestamp': timestamp.isoformat(),
            'odd': odd
        })


def update_history(event_id: str, book: str, market: str, odd: float, timestamp: datetime = None):
    """
    Actualiza el historial con una nueva cuota.
    
    Alias de store_initial_odd (usa la misma estructura).
    """
    store_initial_odd(event_id, book, market, odd, timestamp)


def detect_movement(event_id: str, book: str, market: str, outcome: str, current_odd: float,
                   window_hours: float = None) -> Dict:
    """
    Detecta movimiento de cuota para un evento/book/market/outcome.
    
    Args:
        event_id: ID del evento
        book: Bookmaker
        market: Mercado  
        outcome: Outcome específico
        current_odd: Cuota actual
        window_hours: Ventana de tiempo a analizar (default: MOVEMENT_WINDOW_HOURS)
    
    Returns:
        {
            'initial_odd': float,
            'last_odd': float,
            'delta_pct': float,
            'moved': bool,
            'direction': 'up' | 'down' | 'stable',
            'window_hours': float
        }
    """
    if window_hours is None:
        window_hours = MOVEMENT_WINDOW_HOURS
    
    # Default response
    result = {
        'initial_odd': current_odd,
        'last_odd': current_odd,
        'delta_pct': 0.0,
        'moved': False,
        'direction': 'stable',
        'window_hours': window_hours
    }
    
    # Obtener historial
    if event_id not in _history_cache:
        return result
    if book not in _history_cache[event_id]:
        return result
    if market not in _history_cache[event_id][book]:
        return result
    if outcome not in _history_cache[event_id][book][market]:
        return result
    
    history = _history_cache[event_id][book][market][outcome]
    if not history or len(history) < 1:
        return result
    
    # Obtener primera y última cuota
    initial_odd = history[0]['odd']
    last_odd = history[-1]['odd']
    
    # Calcular movimiento
    delta_pct = ((last_odd - initial_odd) / initial_odd) * 100 if initial_odd > 0 else 0
    
    moved = abs(delta_pct) >= MOVEMENT_DELTA_PERCENT
    
    if delta_pct > 0.5:
        direction = 'up'
    elif delta_pct < -0.5:
        direction = 'down'
    else:
        direction = 'stable'
    
    result.update({
        'initial_odd': initial_odd,
        'last_odd': last_odd,
        'delta_pct': delta_pct,
        'moved': moved,
        'direction': direction,
        'window_hours': window_hours
    })
    
    return result


def load_history_from_file(filepath: str = "data/odds_history.json"):
    """
    Carga el historial de cuotas desde un archivo JSON.
    
    Args:
        filepath: Ruta al archivo de historial
    """
    global _history_cache
    
    if not os.path.exists(filepath):
        _history_cache = {}
        return
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            _history_cache = json.load(f)
    except Exception as e:
        print(f"Error loading odds history: {e}")
        _history_cache = {}


def save_history_to_file(filepath: str = "data/odds_history.json"):
    """
    Guarda el historial de cuotas en un archivo JSON.
    
    Args:
        filepath: Ruta al archivo de historial
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(_history_cache, f, indent=2)
    except Exception as e:
        print(f"Error saving odds history: {e}")


def get_movement_summary(event_id: str) -> Dict:
    """
    Obtiene un resumen de movimientos para todos los books/markets de un evento.
    
    Returns:
        {book: {market: movement_data}}
    """
    summary = {}
    
    if event_id not in _history_cache:
        return summary
    
    for book, markets in _history_cache[event_id].items():
        summary[book] = {}
        for market in markets:
            summary[book][market] = detect_movement(event_id, book, market)
    
    return summary


# TODO: Implementar
# - steam_move_detector(): detecta movimientos coordinados entre múltiples books
# - reverse_line_movement(): detecta RLM (cuota se mueve contra % de apuestas)
# - velocity_analysis(): velocidad del movimiento (rápido vs gradual)
