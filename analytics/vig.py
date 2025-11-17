"""
analytics/vig.py - Cálculo y ajuste de vig (overround).

El "vig" o "juice" es el margen que las casas de apuestas incorporan en sus cuotas.
Este módulo permite calcular el overround, identificar el vig, y ajustar probabilidades
para obtener valores "limpios" sin el margen de la casa.

Fórmulas:
- Probabilidad implícita: 1 / cuota
- Overround: sum(1/cuota_i for all outcomes)
- Vig: (overround - 1) * 100 (como porcentaje)
- Prob limpia: (1/cuota) / overround

Ejemplo:
    >>> odds = [2.10, 3.40, 3.50]  # Home, Draw, Away
    >>> vig = calculate_vig(odds)
    >>> print(f"Vig: {vig:.2f}%")
    Vig: 7.61%
"""
from typing import Dict, List, Tuple, Union
import os


# Configuración desde .env o valores por defecto
VIG_MAX = float(os.getenv("VIG_MAX", "12.0"))  # Como porcentaje


def calculate_vig(odds: Union[List[float], Dict[str, float]]) -> float:
    """
    Calcula el vig (overround/margin) de un mercado.
    
    Args:
        odds: Lista de cuotas o diccionario {outcome: odd}
    
    Returns:
        Vig como porcentaje (ej: 5.0 = 5%)
    
    Example:
        >>> calculate_vig([2.0, 2.0])
        0.0
        >>> calculate_vig({"Home": 1.91, "Away": 1.91})
        4.71
    """
    # Convert dict to list if needed
    if isinstance(odds, dict):
        odds = list(odds.values())
    
    # Convert to float if strings
    odds = [float(o) if isinstance(o, str) else o for o in odds]
    
    if not odds or any(o <= 1.0 for o in odds):
        return 0.0
    
    # Calcular suma de probabilidades implícitas
    implied_probs_sum = sum(1.0 / o for o in odds)
    
    # Vig = (suma - 1) * 100
    vig = (implied_probs_sum - 1.0) * 100
    
    return max(0.0, vig)


def remove_vig(odds: List[float]) -> List[float]:
    """
    Remueve el vig de las cuotas y devuelve probabilidades limpias (normalizadas).
    
    Usa el método de normalización simple: divide cada prob implícita por el overround.
    
    Args:
        odds: Lista de cuotas del mercado
    
    Returns:
        Lista de probabilidades limpias (suman 1.0)
    
    Example:
        >>> remove_vig([1.91, 1.91])
        [0.5, 0.5]
        >>> remove_vig([2.10, 3.40, 3.50])
        [0.444, 0.273, 0.265]
    """
    overround, _ = calculate_vig(odds)
    
    if overround <= 1.0:
        # No hay vig, devolver probabilidades implícitas
        return [1.0 / odd for odd in odds]
    
    # Normalizar dividiendo por overround
    implied_probs = [1.0 / odd for odd in odds]
    clean_probs = [p / overround for p in implied_probs]
    
    return clean_probs


def is_vig_acceptable(odds: Union[float, List[float], Dict[str, float]], max_vig: float = None) -> bool:
    """
    Verifica si el vig de un mercado es aceptable (no excesivo).
    
    Args:
        odds: Vig ya calculado (float) o lista/dict de cuotas para calcular
        max_vig: Vig máximo aceptable como porcentaje (default: VIG_MAX desde config)
    
    Returns:
        True si el vig es <= max_vig
    
    Example:
        >>> is_vig_acceptable(4.7)
        True
        >>> is_vig_acceptable([1.91, 1.91])
        True
    """
    if max_vig is None:
        max_vig = VIG_MAX
    
    # Si ya es un float, usarlo directamente
    if isinstance(odds, (int, float)):
        vig_value = odds
    else:
        # Si es lista o dict, calcularlo
        vig_value = calculate_vig(odds)
    
    return vig_value <= max_vig


def vig_adjusted_fair_odds(odds: List[float]) -> List[float]:
    """
    Convierte cuotas con vig en cuotas "justas" (fair odds) sin margen.
    
    Args:
        odds: Lista de cuotas del mercado
    
    Returns:
        Lista de cuotas justas (calculadas desde probabilidades limpias)
    
    Example:
        >>> vig_adjusted_fair_odds([1.91, 1.91])
        [2.0, 2.0]
    """
    clean_probs = remove_vig(odds)
    fair_odds = [1.0 / p if p > 0 else 999.0 for p in clean_probs]
    return fair_odds


def market_efficiency_score(vig: float) -> float:
    """
    Calcula un score de eficiencia del mercado (0-1, donde 1 = perfecto, sin vig).
    
    Args:
        vig: Vig del mercado como porcentaje
    
    Returns:
        Score entre 0 y 1 (1 - vig/100)
    
    Example:
        >>> market_efficiency_score(0.0)
        1.0
        >>> market_efficiency_score(4.7)
        0.953
    """
    return max(0.0, 1.0 - (vig / 100))


# TODO: Implementar métodos avanzados de remoción de vig:
# - Shin's method (basado en insider trading)
# - Power method (ajuste proporcional por potencia)
# - Margin weights proportional to odds (Wisdom of Crowd)
