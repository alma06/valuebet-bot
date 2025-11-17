"""
analytics/sharp_detector.py - Detector de "dinero profesional" (sharp money).

Identifica señales de que apostadores profesionales están tomando una línea,
indicadores más fuertes de valor real que el análisis de solo cuotas.
"""
from typing import Dict, List, Tuple
import os


SHARP_MOVE_THRESHOLD = float(os.getenv("SHARP_MOVE_THRESHOLD", "6.0"))
SHARP_WINDOW_HOURS = float(os.getenv("SHARP_WINDOW_HOURS", "3.0"))
SHARP_SCORE_THRESHOLD = float(os.getenv("SHARP_SCORE_THRESHOLD", "3.0"))


def detect_sharp_signals(
    movement_data: Dict,
    consensus_data: Dict,
    vig_data: Dict
) -> Dict:
    """
    Detecta señales de dinero profesional combinando múltiples heurísticas.
    
    Args:
        movement_data: resultado de detect_movement() con delta, direction, timestamps
        consensus_data: resultado de consensus_score() con outlier info
        vig_data: {vig, is_acceptable, efficiency_score}
    
    Returns:
        {
            'sharp_score': float (0-5),
            'signals': List[str],
            'is_sharp': bool,
            'confidence': str ('LOW', 'MEDIUM', 'HIGH')
        }
    
    Señales detectadas:
    - Large move en ventana corta (movimiento >6% en <3h) +2 pts
    - Reverse line movement (cuota sube cuando debería bajar) +2 pts
    - Low vig + movimiento (eficiencia >0.8 + movimiento) +1 pt
    - Outlier + movimiento en misma dirección +1 pt
    - Movimiento coordinado en múltiples books +1 pt
    """
    score = 0.0
    signals = []
    
    # Señal 1: Large move en ventana corta
    if movement_data and movement_data.get('moved'):
        delta = abs(movement_data.get('delta_pct', 0))
        window = movement_data.get('window_hours', 24)
        
        if delta >= SHARP_MOVE_THRESHOLD and window <= SHARP_WINDOW_HOURS:
            score += 2.0
            signals.append(f"movimiento_rapido: {delta:.1f}% en {window:.1f}h")
    
    # Señal 2: Reverse line movement (requiere contexto adicional, placeholder)
    # En producción: comparar con % de apuestas públicas
    # Si público apuesta A pero línea se mueve hacia B = sharp money en B
    # TODO: implementar con datos de betting percentages
    
    # Señal 3: Low vig + movimiento (mercado eficiente con acción)
    if vig_data and movement_data:
        efficiency = vig_data.get('efficiency_score', 0)
        moved = movement_data.get('moved', False)
        
        if efficiency > 0.8 and moved:
            score += 1.0
            signals.append(f"mercado_eficiente_activo: eff={efficiency:.2f}")
    
    # Señal 4: Outlier + movimiento en misma dirección
    if consensus_data and movement_data:
        is_outlier = consensus_data.get('is_outlier', False)
        diff_pct = consensus_data.get('diff_from_mean_pct', 0)
        direction = movement_data.get('direction', 'stable')
        
        # Si cuota es outlier alto y se mueve hacia arriba = sharp taking the high line
        if is_outlier and diff_pct > 0 and direction == 'up':
            score += 1.0
            signals.append(f"outlier_subiendo: {diff_pct:.1f}% sobre media")
        
        # Si cuota es outlier bajo y se mueve hacia abajo = sharp taking the low line
        elif is_outlier and diff_pct < 0 and direction == 'down':
            score += 1.0
            signals.append(f"outlier_bajando: {abs(diff_pct):.1f}% bajo media")
    
    # Señal 5: Movimiento coordinado (requiere múltiples books, placeholder)
    # TODO: implementar con history de múltiples books
    
    is_sharp = score >= SHARP_SCORE_THRESHOLD
    
    if score >= 4.0:
        confidence = 'HIGH'
    elif score >= 2.0:
        confidence = 'MEDIUM'
    else:
        confidence = 'LOW'
    
    return {
        'sharp_score': score,
        'signals': signals,
        'is_sharp': is_sharp,
        'confidence': confidence
    }


def analyze_sharp_book_preference(history: Dict, book: str) -> Dict:
    """
    Analiza si un book específico tiende a tener líneas sharp.
    
    Args:
        history: {event_id: {book: {market: [{timestamp, odd}]}}}
        book: bookmaker name
    
    Returns:
        {
            'total_movements': int,
            'sharp_movements': int,
            'sharp_ratio': float,
            'is_sharp_book': bool
        }
    
    Heurística: books con muchos movimientos grandes son más "sharp"
    """
    total_movements = 0
    sharp_movements = 0
    
    for event_id, books_data in history.items():
        if book not in books_data:
            continue
        
        for market, odds_history in books_data[book].items():
            if len(odds_history) < 2:
                continue
            
            total_movements += 1
            
            # Calcular delta entre primer y último odd
            first_odd = odds_history[0]['odd']
            last_odd = odds_history[-1]['odd']
            delta = abs((last_odd - first_odd) / first_odd * 100)
            
            if delta >= SHARP_MOVE_THRESHOLD:
                sharp_movements += 1
    
    sharp_ratio = sharp_movements / total_movements if total_movements > 0 else 0.0
    is_sharp_book = sharp_ratio > 0.3  # >30% movimientos significativos
    
    return {
        'total_movements': total_movements,
        'sharp_movements': sharp_movements,
        'sharp_ratio': sharp_ratio,
        'is_sharp_book': is_sharp_book
    }


def get_sharp_summary(sharp_data: Dict) -> str:
    """
    Genera un resumen legible de señales sharp.
    
    Returns:
        str: "⚡ SHARP DETECTADO (score: 4.5/5, conf: HIGH): movimiento_rapido, mercado_eficiente"
    """
    if not sharp_data or not sharp_data.get('is_sharp'):
        return "Sin señales sharp"
    
    score = sharp_data.get('sharp_score', 0)
    conf = sharp_data.get('confidence', 'LOW')
    signals = sharp_data.get('signals', [])
    
    icon = "⚡" if conf == "HIGH" else "⚠️"
    signals_str = ", ".join(signals[:2])  # Primeras 2 señales
    
    return f"{icon} SHARP (score: {score:.1f}/5, {conf}): {signals_str}"


# TODO: Implementar
# - reverse_line_movement(): detectar RLM con betting percentages
# - coordinated_steam(): movimiento sincronizado en múltiples books
# - sharp_book_classifier(): clasificar permanentemente books por sharpness
# - closing_line_sharp_test(): validar histórico contra CLV
