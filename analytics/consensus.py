"""
analytics/consensus.py - Análisis de consenso entre bookmakers.

Compara cuotas entre múltiples casas para detectar outliers, errores de precio,
y validar si una cuota es "soft" (vulnerable) o "sharp" (eficiente).
"""
from typing import Dict, List, Tuple
import statistics
import os


OUTLIER_PERCENT = float(os.getenv("OUTLIER_PERCENT", "8.0"))
MIN_BOOKS_CONSENSUS = int(os.getenv("MIN_BOOKS_CONSENSUS", "3"))


def consensus_score(book_odds: Dict[str, float], target_book: str = None) -> Dict:
    """
    Calcula el consensus y detecta outliers.
    
    Args:
        book_odds: {bookmaker: odd} para un mercado/selección específica
        target_book: Book a analizar (si None, analiza todos)
    
    Returns:
        {
            'mean': float,
            'median': float,
            'std': float,
            'target_odd': float,
            'diff_from_mean_pct': float,
            'is_outlier': bool,
            'z_score': float,
            'num_books': int
        }
    
    Example:
        >>> odds = {'bet365': 2.10, 'pinnacle': 2.05, 'draftkings': 2.30}
        >>> consensus_score(odds, 'draftkings')
        {'mean': 2.15, 'median': 2.10, 'diff_from_mean_pct': 6.98, 'is_outlier': False, ...}
    """
    if not book_odds or len(book_odds) < MIN_BOOKS_CONSENSUS:
        return {'error': 'insufficient_books', 'num_books': len(book_odds)}
    
    odds_list = list(book_odds.values())
    mean_odd = statistics.mean(odds_list)
    median_odd = statistics.median(odds_list)
    std_odd = statistics.stdev(odds_list) if len(odds_list) > 1 else 0.0
    
    result = {
        'mean': mean_odd,
        'median': median_odd,
        'std': std_odd,
        'num_books': len(book_odds)
    }
    
    if target_book and target_book in book_odds:
        target_odd = book_odds[target_book]
        diff_pct = ((target_odd - mean_odd) / mean_odd) * 100
        z_score = (target_odd - mean_odd) / std_odd if std_odd > 0 else 0.0
        is_outlier = abs(diff_pct) > OUTLIER_PERCENT
        
        result.update({
            'target_odd': target_odd,
            'diff_from_mean_pct': diff_pct,
            'z_score': z_score,
            'is_outlier': is_outlier
        })
    
    return result


def find_best_value_book(book_odds: Dict[str, float]) -> Tuple[str, float, float]:
    """
    Encuentra el book con la mejor cuota (más alejado del consensus hacia arriba).
    
    Returns:
        (bookmaker, odd, diff_from_mean_pct)
    """
    if not book_odds:
        return None, 0.0, 0.0
    
    mean_odd = statistics.mean(book_odds.values())
    
    best_book = max(book_odds.items(), key=lambda x: x[1])
    best_name, best_odd = best_book
    diff_pct = ((best_odd - mean_odd) / mean_odd) * 100
    
    return best_name, best_odd, diff_pct


def detect_consensus_outliers(book_odds: Dict[str, float]) -> List[Dict]:
    """
    Detecta todos los outliers en un conjunto de cuotas.
    
    Returns:
        Lista de {book, odd, diff_pct, z_score, is_high}
    """
    outliers = []
    
    for book in book_odds:
        result = consensus_score(book_odds, book)
        if result.get('is_outlier'):
            outliers.append({
                'book': book,
                'odd': result['target_odd'],
                'diff_pct': result['diff_from_mean_pct'],
                'z_score': result['z_score'],
                'is_high': result['diff_from_mean_pct'] > 0
            })
    
    return outliers


def market_agreement_score(book_odds: Dict[str, float]) -> float:
    """
    Calcula un score de acuerdo entre books (0-1, donde 1 = perfecto acuerdo).
    
    Basado en coefficient of variation (CV): std / mean
    """
    if not book_odds or len(book_odds) < 2:
        return 0.0
    
    odds_list = list(book_odds.values())
    mean_odd = statistics.mean(odds_list)
    std_odd = statistics.stdev(odds_list)
    
    cv = std_odd / mean_odd if mean_odd > 0 else 1.0
    
    # Convertir CV a score (menos variación = más acuerdo)
    agreement = max(0.0, 1.0 - (cv * 5))  # Scale factor 5 es ajustable
    
    return agreement


# TODO: Implementar
# - sharp_vs_soft_books(): clasificar books por sharpness
# - steam_across_books(): detectar steam coordinado
# - closing_line_value(): comparar con línea de cierre
