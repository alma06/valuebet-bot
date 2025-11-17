"""
utils/quality_filter.py - Filtro de calidad para seleccionar los mejores candidatos

Selecciona máximo 5 alertas diarias de máxima calidad para usuarios premium.
Criterios de calidad:
- Score de confianza (confidence_score)
- Valor esperado ajustado
- Calidad de información deportiva  
- Consistencia del análisis
"""

from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class QualityFilter:
    def __init__(self, max_daily_alerts: int = 5):
        self.max_daily_alerts = max_daily_alerts
        
        # Pesos para el cálculo de calidad total
        self.weights = {
            'confidence_score': 0.30,     # 30% - Qué tan confiable es la información
            'value': 0.25,                # 25% - Valor esperado de la apuesta
            'probability_adjustment': 0.20, # 20% - Qué tanto se ajustó con info real
            'data_quality': 0.15,         # 15% - Calidad de datos deportivos
            'market_efficiency': 0.10     # 10% - Eficiencia del mercado
        }

    def select_best_candidates(self, candidates: List[Dict]) -> List[Dict]:
        """
        Selecciona los mejores candidatos basado en múltiples criterios de calidad
        
        Args:
            candidates: Lista de todos los candidatos ajustados
            
        Returns:
            Lista de máximo 5 candidatos de mejor calidad
        """
        if not candidates:
            return []
        
        # Calcular score de calidad para cada candidato
        candidates_with_scores = []
        for candidate in candidates:
            quality_score = self._calculate_quality_score(candidate)
            candidate_with_score = candidate.copy()
            candidate_with_score['quality_score'] = quality_score
            candidates_with_scores.append(candidate_with_score)
        
        # Ordenar por score de calidad (mayor es mejor)
        sorted_candidates = sorted(
            candidates_with_scores, 
            key=lambda x: x['quality_score'], 
            reverse=True
        )
        
        # Tomar los mejores (máximo 5)
        best_candidates = sorted_candidates[:self.max_daily_alerts]
        
        # Agregar ranking de calidad
        for i, candidate in enumerate(best_candidates, 1):
            candidate['quality_rank'] = i
            candidate['total_candidates'] = len(candidates)
        
        logger.info(
            f"Selected {len(best_candidates)} best candidates from {len(candidates)} total. "
            f"Quality scores: {[round(c['quality_score'], 3) for c in best_candidates]}"
        )
        
        return best_candidates

    def _calculate_quality_score(self, candidate: Dict) -> float:
        """
        Calcula un score de calidad compuesto para un candidato
        
        Returns:
            Score entre 0.0 y 1.0 donde 1.0 es la máxima calidad
        """
        scores = {}
        
        # 1. Score de confianza (de probability_adjuster)
        confidence_score = candidate.get('confidence_score', 0.7)
        scores['confidence_score'] = min(1.0, max(0.0, confidence_score))
        
        # 2. Valor esperado normalizado
        value = candidate.get('value', 1.0)
        # Normalizar valor entre 0 y 1 (1.0 = no value, 1.20 = excelente value)
        value_normalized = min(1.0, max(0.0, (value - 1.0) / 0.20))
        scores['value'] = value_normalized
        
        # 3. Magnitud del ajuste de probabilidad (más ajuste = mejor información)
        prob_adjustment = abs(candidate.get('probability_adjustment', 0.0))
        # Normalizar: 0 ajuste = 0 score, 0.1+ ajuste = 1.0 score  
        adjustment_normalized = min(1.0, prob_adjustment / 0.10)
        scores['probability_adjustment'] = adjustment_normalized
        
        # 4. Calidad de datos deportivos
        sports_info = candidate.get('sports_info_summary', {})
        data_quality = sports_info.get('data_quality', 'MEDIUM')
        
        data_quality_scores = {
            'HIGH': 1.0,
            'MEDIUM': 0.6,
            'LOW': 0.3,
            'UNKNOWN': 0.1
        }
        scores['data_quality'] = data_quality_scores.get(data_quality, 0.5)
        
        # 5. Eficiencia del mercado (vig bajo = mercado más eficiente = mejor apuesta)
        vig = candidate.get('vig', 5.0)
        # Normalizar: vig 0% = 1.0, vig 10%+ = 0.0
        vig_normalized = min(1.0, max(0.0, 1.0 - (vig / 10.0)))
        scores['market_efficiency'] = vig_normalized
        
        # Calcular score ponderado total
        total_score = 0.0
        for metric, weight in self.weights.items():
            score = scores.get(metric, 0.5)  # Default 0.5 si no está disponible
            total_score += score * weight
        
        # Añadir información de scoring para debug
        breakdown = {}
        for k, v in self.weights.items():
            score_val = scores.get(k, 0.5)
            weighted = score_val * v
            breakdown[k] = f"{round(score_val, 3)} * {v:.2f} = {round(weighted, 3)}"
        
        candidate['quality_breakdown'] = {
            'scores': scores,
            'weighted_total': total_score,
            'breakdown': breakdown
        }
        
        return total_score

    def get_quality_summary(self, selected_candidates: List[Dict]) -> Dict:
        """
        Genera un resumen de la calidad de los candidatos seleccionados
        """
        if not selected_candidates:
            return {
                'total_selected': 0,
                'avg_quality_score': 0.0,
                'quality_range': '0.0-0.0',
                'confidence_level': 'LOW'
            }
        
        quality_scores = [c.get('quality_score', 0.0) for c in selected_candidates]
        avg_score = sum(quality_scores) / len(quality_scores)
        min_score = min(quality_scores)
        max_score = max(quality_scores)
        
        # Determinar nivel de confianza general
        if avg_score >= 0.8:
            confidence_level = 'EXCELLENT'
        elif avg_score >= 0.7:
            confidence_level = 'HIGH'
        elif avg_score >= 0.6:
            confidence_level = 'GOOD'
        elif avg_score >= 0.5:
            confidence_level = 'MEDIUM'
        else:
            confidence_level = 'LOW'
        
        return {
            'total_selected': len(selected_candidates),
            'avg_quality_score': avg_score,
            'quality_range': f"{min_score:.2f}-{max_score:.2f}",
            'confidence_level': confidence_level,
            'individual_scores': [f"#{i}: {round(score, 3)}" for i, score in enumerate(quality_scores, 1)],
            'top_value_bets': [
                f"{c.get('event', 'Unknown')} ({round(c.get('quality_score', 0), 3)})"
                for c in selected_candidates[:3]
            ]
        }

    def should_skip_low_quality_day(self, candidates: List[Dict], min_threshold: float = 0.5) -> Tuple[bool, str]:
        """
        Determina si se debe saltar el día por baja calidad general
        
        Returns:
            (should_skip, reason)
        """
        if not candidates:
            return True, "No hay candidatos disponibles"
        
        best_candidates = self.select_best_candidates(candidates)
        
        if not best_candidates:
            return True, "No se encontraron candidatos de calidad suficiente"
        
        avg_quality = sum(c.get('quality_score', 0.0) for c in best_candidates) / len(best_candidates)
        
        if avg_quality < min_threshold:
            return True, f"Calidad promedio muy baja ({avg_quality:.3f} < {min_threshold})"
        
        # Verificar que al menos el 60% tengan ajustes significativos de probabilidad
        significant_adjustments = sum(
            1 for c in best_candidates 
            if abs(c.get('probability_adjustment', 0.0)) > 0.02
        )
        
        adjustment_ratio = significant_adjustments / len(best_candidates)
        if adjustment_ratio < 0.4:  # Menos del 40% tienen ajustes significativos
            return True, f"Pocos ajustes significativos de información real ({adjustment_ratio:.1%})"
        
        return False, f"Calidad suficiente: {len(best_candidates)} candidatos, avg {avg_quality:.3f}"


# Función helper para uso directo
def filter_best_candidates(candidates: List[Dict], max_alerts: int = 5) -> List[Dict]:
    """
    Función de conveniencia para filtrar mejores candidatos
    """
    quality_filter = QualityFilter(max_daily_alerts=max_alerts)
    return quality_filter.select_best_candidates(candidates)


def get_quality_report(candidates: List[Dict]) -> str:
    """
    Genera un reporte de calidad legible para logs
    """
    quality_filter = QualityFilter()
    best = quality_filter.select_best_candidates(candidates)
    summary = quality_filter.get_quality_summary(best)
    
    report = [
        f"📊 QUALITY REPORT:",
        f"  Selected: {summary['total_selected']}/5 candidates",
        f"  Avg Quality: {summary['avg_quality_score']:.3f}",
        f"  Range: {summary['quality_range']}",
        f"  Confidence: {summary['confidence_level']}",
    ]
    
    if best:
        report.append("  Top picks:")
        for candidate in best[:3]:
            event = candidate.get('event', 'Unknown')
            score = candidate.get('quality_score', 0.0)
            value = candidate.get('value', 1.0)
            report.append(f"    • {event} (Q:{round(score, 3)}, V:{round(value, 3)})")
    
    return "\n".join(report)


# Ejemplo de uso
if __name__ == "__main__":
    # Candidatos de prueba
    test_candidates = [
        {
            'event': 'Test Game 1',
            'confidence_score': 0.8,
            'value': 1.15,
            'probability_adjustment': 0.05,
            'vig': 3.0,
            'sports_info_summary': {'data_quality': 'HIGH'}
        },
        {
            'event': 'Test Game 2', 
            'confidence_score': 0.6,
            'value': 1.20,
            'probability_adjustment': 0.02,
            'vig': 5.0,
            'sports_info_summary': {'data_quality': 'MEDIUM'}
        }
    ]
    
    quality_filter = QualityFilter()
    best = quality_filter.select_best_candidates(test_candidates)
    
    print(get_quality_report(test_candidates))