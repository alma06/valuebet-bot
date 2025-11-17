"""
Bankroll Manager - Gestión profesional de stake con Kelly Criterion

Características:
- Kelly Criterion completo y fractional Kelly
- Ajuste dinámico según confidence y edge
- Protección de bankroll con límites
- Cálculo de ROI esperado y riesgo
"""
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class BankrollManager:
    """
    Gestión profesional de stake basada en Kelly Criterion y gestión de riesgo
    """
    
    def __init__(
        self,
        bankroll: float = 1000.0,
        kelly_fraction: float = 0.25,
        max_stake_percent: float = 5.0,
        min_stake_percent: float = 0.5
    ):
        """
        Args:
            bankroll: Bankroll total en unidades monetarias
            kelly_fraction: Fracción de Kelly a usar (0.25 = 25% de Kelly completo)
            max_stake_percent: Máximo % del bankroll por apuesta (default 5%)
            min_stake_percent: Mínimo % del bankroll por apuesta (default 0.5%)
        """
        self.bankroll = bankroll
        self.kelly_fraction = kelly_fraction
        self.max_stake_percent = max_stake_percent / 100
        self.min_stake_percent = min_stake_percent / 100
        
        logger.info(f"BankrollManager initialized: ${bankroll:.2f}, Kelly fraction: {kelly_fraction}")
    
    def calculate_kelly_stake(self, odds: float, probability: float) -> float:
        """
        Calcula el stake óptimo usando Kelly Criterion
        
        Formula: f = (bp - q) / b
        donde:
            f = fracción del bankroll a apostar
            b = odds decimales - 1
            p = probabilidad de ganar
            q = probabilidad de perder (1 - p)
        
        Args:
            odds: Cuota decimal (ej: 1.85)
            probability: Probabilidad estimada (0-1)
            
        Returns:
            float: Stake recomendado en unidades monetarias
        """
        if odds <= 1 or probability <= 0 or probability >= 1:
            return 0.0
        
        b = odds - 1  # Net odds
        p = probability
        q = 1 - p
        
        # Kelly formula
        f = (b * p - q) / b
        
        # Si Kelly es negativo o cero, no hay valor
        if f <= 0:
            return 0.0
        
        # Aplicar fracción de Kelly
        f = f * self.kelly_fraction
        
        # Calcular stake
        stake = self.bankroll * f
        
        # Aplicar límites
        max_stake = self.bankroll * self.max_stake_percent
        min_stake = self.bankroll * self.min_stake_percent
        
        stake = max(min_stake, min(stake, max_stake))
        
        return round(stake, 2)
    
    def calculate_ev(self, odds: float, probability: float, stake: float) -> float:
        """
        Calcula el valor esperado (Expected Value)
        
        EV = (probability * profit) - ((1 - probability) * stake)
        
        Args:
            odds: Cuota decimal
            probability: Probabilidad estimada
            stake: Cantidad apostada
            
        Returns:
            float: Valor esperado de la apuesta
        """
        profit = stake * (odds - 1)
        loss = stake
        
        ev = (probability * profit) - ((1 - probability) * loss)
        return round(ev, 2)
    
    def calculate_edge(self, odds: float, probability: float) -> float:
        """
        Calcula el edge (ventaja) sobre la casa
        
        Edge = (probability * odds) - 1
        
        Args:
            odds: Cuota decimal
            probability: Probabilidad estimada
            
        Returns:
            float: Edge como decimal (ej: 0.15 = 15% edge)
        """
        edge = (probability * odds) - 1
        return edge
    
    def calculate_roi(self, odds: float, probability: float) -> float:
        """
        Calcula el ROI esperado
        
        ROI = Edge * 100
        
        Args:
            odds: Cuota decimal
            probability: Probabilidad estimada
            
        Returns:
            float: ROI esperado en porcentaje
        """
        edge = self.calculate_edge(odds, probability)
        return round(edge * 100, 2)
    
    def calculate_variance(self, odds: float, probability: float) -> float:
        """
        Calcula la varianza de la apuesta
        
        Args:
            odds: Cuota decimal
            probability: Probabilidad estimada
            
        Returns:
            float: Varianza normalizada
        """
        p = probability
        q = 1 - p
        
        # Varianza de una apuesta binaria
        variance = p * ((odds - 1) ** 2) + q * ((-1) ** 2) - ((p * (odds - 1) + q * (-1)) ** 2)
        
        return round(variance, 4)
    
    def get_recommendation(
        self,
        odds: float,
        probability: float,
        confidence_score: float = 1.0
    ) -> Dict:
        """
        Genera recomendación completa de stake con análisis de riesgo
        
        Args:
            odds: Cuota decimal
            probability: Probabilidad estimada
            confidence_score: Score de confianza (0-1), ajusta el stake
            
        Returns:
            Dict con recomendación completa
        """
        # Calcular métricas base
        edge = self.calculate_edge(odds, probability)
        
        # Si no hay edge, no apostar
        if edge <= 0:
            return {
                'should_bet': False,
                'stake': 0.0,
                'reason': 'No hay valor positivo (edge <= 0)'
            }
        
        # Calcular stake base con Kelly
        base_stake = self.calculate_kelly_stake(odds, probability)
        
        # Ajustar stake según confidence
        adjusted_stake = base_stake * confidence_score
        
        # Aplicar límites finales
        max_stake = self.bankroll * self.max_stake_percent
        min_stake = self.bankroll * self.min_stake_percent
        final_stake = max(min_stake, min(adjusted_stake, max_stake))
        
        # Calcular métricas adicionales
        ev = self.calculate_ev(odds, probability, final_stake)
        roi = self.calculate_roi(odds, probability)
        variance = self.calculate_variance(odds, probability)
        
        # Determinar categoría de riesgo
        risk_category = self._categorize_risk(variance, edge)
        
        # Calcular stake como porcentaje del bankroll
        stake_percent = (final_stake / self.bankroll) * 100
        
        return {
            'should_bet': True,
            'stake': round(final_stake, 2),
            'stake_percent': round(stake_percent, 2),
            'edge': round(edge * 100, 2),  # En porcentaje
            'expected_value': ev,
            'roi': roi,
            'variance': variance,
            'risk_category': risk_category,
            'confidence_adjusted': confidence_score,
            'kelly_fraction_used': self.kelly_fraction,
            'potential_profit': round(final_stake * (odds - 1), 2),
            'potential_loss': round(final_stake, 2)
        }
    
    def _categorize_risk(self, variance: float, edge: float) -> str:
        """
        Categoriza el riesgo de la apuesta
        
        Args:
            variance: Varianza calculada
            edge: Edge calculado
            
        Returns:
            str: Categoría de riesgo
        """
        if edge >= 0.15 and variance < 0.5:
            return "BAJO"  # Alto edge, baja varianza
        elif edge >= 0.10 and variance < 1.0:
            return "MEDIO"  # Edge moderado, varianza moderada
        elif edge >= 0.05:
            return "MEDIO-ALTO"  # Edge bajo o varianza alta
        else:
            return "ALTO"  # Edge muy bajo
    
    def update_bankroll(self, new_bankroll: float):
        """
        Actualiza el bankroll después de ganancias/pérdidas
        
        Args:
            new_bankroll: Nuevo bankroll total
        """
        old_bankroll = self.bankroll
        self.bankroll = new_bankroll
        
        change = new_bankroll - old_bankroll
        change_percent = (change / old_bankroll) * 100 if old_bankroll > 0 else 0
        
        logger.info(
            f"Bankroll updated: ${old_bankroll:.2f} -> ${new_bankroll:.2f} "
            f"({change_percent:+.2f}%)"
        )
    
    def get_bankroll_stats(self) -> Dict:
        """
        Obtiene estadísticas actuales del bankroll
        
        Returns:
            Dict con estadísticas del bankroll
        """
        return {
            'current_bankroll': round(self.bankroll, 2),
            'max_stake_amount': round(self.bankroll * self.max_stake_percent, 2),
            'min_stake_amount': round(self.bankroll * self.min_stake_percent, 2),
            'kelly_fraction': self.kelly_fraction,
            'max_stake_percent': round(self.max_stake_percent * 100, 2),
            'min_stake_percent': round(self.min_stake_percent * 100, 2)
        }


def format_stake_recommendation(rec: Dict) -> str:
    """
    Formatea la recomendación de stake para mostrar al usuario
    
    Args:
        rec: Dict con recomendación de get_recommendation()
        
    Returns:
        str: Texto formateado
    """
    if not rec['should_bet']:
        return f"NO APOSTAR: {rec['reason']}"
    
    lines = [
        f"STAKE RECOMENDADO: ${rec['stake']:.2f} ({rec['stake_percent']:.1f}% del bankroll)",
        f"",
        f"ANALISIS DE VALOR:",
        f"  Edge: {rec['edge']:+.2f}%",
        f"  ROI Esperado: {rec['roi']:+.2f}%",
        f"  Valor Esperado: ${rec['expected_value']:+.2f}",
        f"",
        f"POTENCIAL:",
        f"  Ganancia: ${rec['potential_profit']:.2f}",
        f"  Perdida: -${rec['potential_loss']:.2f}",
        f"",
        f"RIESGO: {rec['risk_category']}",
        f"  Varianza: {rec['variance']:.4f}",
        f"  Confidence: {rec['confidence_adjusted']*100:.0f}%",
    ]
    
    return "\n".join(lines)


# Ejemplo de uso
if __name__ == "__main__":
    # Crear manager con bankroll de $1000
    manager = BankrollManager(
        bankroll=1000.0,
        kelly_fraction=0.25,  # Usar 25% de Kelly completo (conservador)
        max_stake_percent=5.0,  # Máximo 5% del bankroll por apuesta
        min_stake_percent=0.5   # Mínimo 0.5% del bankroll
    )
    
    # Ejemplo 1: Apuesta con buen valor
    print("="*60)
    print("EJEMPLO 1: Apuesta con buen edge")
    print("="*60)
    rec1 = manager.get_recommendation(
        odds=1.95,
        probability=0.60,  # 60% de probabilidad
        confidence_score=0.85  # 85% de confianza en la estimación
    )
    print(format_stake_recommendation(rec1))
    
    # Ejemplo 2: Apuesta con poco valor
    print("\n" + "="*60)
    print("EJEMPLO 2: Apuesta con poco edge")
    print("="*60)
    rec2 = manager.get_recommendation(
        odds=1.75,
        probability=0.52,  # 52% de probabilidad
        confidence_score=0.70  # 70% de confianza
    )
    print(format_stake_recommendation(rec2))
    
    # Ejemplo 3: Sin valor (no apostar)
    print("\n" + "="*60)
    print("EJEMPLO 3: Sin valor positivo")
    print("="*60)
    rec3 = manager.get_recommendation(
        odds=1.60,
        probability=0.55,  # Edge negativo
        confidence_score=0.90
    )
    print(format_stake_recommendation(rec3))
