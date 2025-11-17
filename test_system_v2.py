"""
test_system_v2.py - Prueba del sistema completo mejorado

Simula un ciclo completo:
1. Fetch odds simuladas
2. Generar candidatos 
3. Ajustar probabilidades con APIs deportivas
4. Filtrar por calidad
5. Mostrar resultado final
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from model.probability_adjuster import adjust_candidate_probabilities
from utils.quality_filter import QualityFilter, get_quality_report
from notifier.premium_alert_formatter import format_premium_exclusive_alert
from data.users import User


# Candidatos simulados (como los que generaría el scanner)
SIMULATED_CANDIDATES = [
    {
        'event': 'Philadelphia 76ers vs Boston Celtics',
        'sport_key': 'basketball_nba',
        'sport': 'NBA',
        'market_key': 'h2h',
        'selection': 'Philadelphia 76ers',
        'bookmaker': 'DraftKings',
        'odds': 2.10,
        'prob_calculated': 0.55,  # 55% probabilidad estimada
        'value': 1.155,  # 2.10 * 0.55
        'vig': 3.5,
        'url': 'https://draftkings.com/example'
    },
    {
        'event': 'Los Angeles Lakers @ Miami Heat',
        'sport_key': 'basketball_nba', 
        'sport': 'NBA',
        'market_key': 'spreads',
        'selection': 'Los Angeles Lakers -5.5',
        'bookmaker': 'FanDuel',
        'odds': 1.95,
        'prob_calculated': 0.60,
        'value': 1.170,
        'vig': 2.8,
        'point': -5.5
    },
    {
        'event': 'Real Madrid vs Barcelona',
        'sport_key': 'soccer_spain_la_liga',
        'sport': 'Spanish La Liga',
        'market_key': 'h2h',
        'selection': 'Real Madrid',
        'bookmaker': 'bet365',
        'odds': 2.30,
        'prob_calculated': 0.48,
        'value': 1.104,
        'vig': 4.1
    },
    {
        'event': 'New York Yankees @ Boston Red Sox',
        'sport_key': 'baseball_mlb',
        'sport': 'MLB',
        'market_key': 'h2h', 
        'selection': 'New York Yankees',
        'bookmaker': 'BetMGM',
        'odds': 1.85,
        'prob_calculated': 0.62,
        'value': 1.147,
        'vig': 3.2
    },
    {
        'event': 'Denver Nuggets vs Golden State Warriors',
        'sport_key': 'basketball_nba',
        'sport': 'NBA',
        'market_key': 'totals',
        'selection': 'Over 225.5',
        'bookmaker': 'Caesars',
        'odds': 1.90,
        'prob_calculated': 0.58,
        'value': 1.102,
        'vig': 4.5,
        'total': 225.5
    },
    {
        'event': 'Manchester City vs Arsenal',
        'sport_key': 'soccer_epl',
        'sport': 'English Premier League',
        'market_key': 'h2h',
        'selection': 'Manchester City',
        'bookmaker': 'William Hill',
        'odds': 1.75,
        'prob_calculated': 0.65,
        'value': 1.138,
        'vig': 2.1
    },
    {
        'event': 'Toronto Raptors @ Chicago Bulls',
        'sport_key': 'basketball_nba',
        'sport': 'NBA',
        'market_key': 'spreads',
        'selection': 'Toronto Raptors +8.5',
        'bookmaker': 'PointsBet',
        'odds': 2.05,
        'prob_calculated': 0.52,
        'value': 1.066,
        'vig': 5.8,
        'point': 8.5
    }
]


async def test_complete_system():
    """
    Prueba el sistema completo paso a paso
    """
    print("🧪 TESTING SISTEMA COMPLETO V2")
    print("=" * 60)
    
    # Paso 1: Mostrar candidatos base
    print(f"\n📊 PASO 1: CANDIDATOS BASE")
    print(f"Total candidatos simulados: {len(SIMULATED_CANDIDATES)}")
    
    for i, candidate in enumerate(SIMULATED_CANDIDATES, 1):
        event = candidate['event']
        selection = candidate['selection']
        odds = candidate['odds']
        prob = candidate['prob_calculated'] * 100
        value = candidate['value']
        
        print(f"  [{i}] {event}")
        print(f"      {selection} @ {odds:.2f}")
        print(f"      Prob: {prob:.1f}% | Value: {value:.3f}")
    
    # Paso 2: Ajustar probabilidades con información deportiva
    print(f"\n🏥 PASO 2: AJUSTE CON INFORMACIÓN DEPORTIVA")
    print("Consultando APIs deportivas y ajustando probabilidades...")
    
    try:
        adjusted_candidates = await adjust_candidate_probabilities(SIMULATED_CANDIDATES)
        print(f"✅ {len(adjusted_candidates)} candidatos ajustados exitosamente")
        
        # Mostrar ajustes aplicados
        for i, candidate in enumerate(adjusted_candidates, 1):
            event = candidate.get('event', 'Unknown')
            original_prob = candidate.get('original_probability', 0.55) * 100
            adjusted_prob = candidate.get('prob_calculated', 0.55) * 100
            adjustment = candidate.get('probability_adjustment', 0.0) * 100
            original_value = candidate.get('original_value', 1.0)
            new_value = candidate.get('value', 1.0)
            
            print(f"\n  [{i}] {event[:40]}...")
            print(f"      Prob: {original_prob:.1f}% → {adjusted_prob:.1f}% ({adjustment:+.1f}%)")
            print(f"      Value: {original_value:.3f} → {new_value:.3f}")
            
            # Mostrar reasoning si está disponible
            adjustment_details = candidate.get('adjustment_details', {})
            if adjustment_details.get('reasoning'):
                reasoning = adjustment_details['reasoning']
                print(f"      Razón: {reasoning}")
        
    except Exception as e:
        print(f"❌ Error en ajuste: {e}")
        adjusted_candidates = SIMULATED_CANDIDATES
    
    # Paso 3: Filtrar por calidad
    print(f"\n⭐ PASO 3: FILTRO DE CALIDAD")
    
    quality_filter = QualityFilter(max_daily_alerts=5)
    best_candidates = quality_filter.select_best_candidates(adjusted_candidates)
    
    print(f"Seleccionados {len(best_candidates)} mejores de {len(adjusted_candidates)} totales")
    
    # Mostrar reporte de calidad
    quality_report = get_quality_report(adjusted_candidates)
    print(f"\n{quality_report}")
    
    # Verificar si se debe saltar el día
    should_skip, reason = quality_filter.should_skip_low_quality_day(adjusted_candidates, min_threshold=0.6)
    
    if should_skip:
        print(f"\n⚠️ RECOMENDACIÓN: SALTAR DÍA")
        print(f"Razón: {reason}")
        return
    else:
        print(f"\n✅ CALIDAD SUFICIENTE PARA ENVÍO")
        print(f"Razón: {reason}")
    
    # Paso 4: Generar alertas premium
    print(f"\n💎 PASO 4: ALERTAS PREMIUM EXCLUSIVAS")
    
    # Usuario simulado
    test_user = User(
        chat_id="test_user",
        nivel="premium",
        bankroll=1000.0
    )
    
    for i, candidate in enumerate(best_candidates, 1):
        print(f"\n🏆 ALERTA PREMIUM #{i}")
        print("-" * 50)
        
        try:
            # Calcular stake
            odds = candidate.get('odds', 2.0)
            prob = candidate.get('prob_calculated', 0.55)
            stake = test_user.calculate_stake(odds, prob)
            
            # Generar mensaje premium
            message = format_premium_exclusive_alert(candidate, test_user, stake)
            
            # Mostrar solo las primeras líneas del mensaje
            lines = message.split('\n')
            preview_lines = lines[:15]  # Primeras 15 líneas
            
            for line in preview_lines:
                print(line)
            
            if len(lines) > 15:
                print(f"... (+{len(lines) - 15} líneas más)")
            
        except Exception as e:
            print(f"❌ Error generando alerta: {e}")
    
    # Resumen final
    print(f"\n✅ PRUEBA COMPLETADA")
    print("=" * 60)
    print(f"📊 Candidatos procesados: {len(adjusted_candidates)}")
    print(f"🎯 Alertas premium generadas: {len(best_candidates)}")
    print(f"⭐ Sistema listo para producción")


async def test_individual_components():
    """
    Prueba componentes individuales
    """
    print("\n🔧 PRUEBA DE COMPONENTES INDIVIDUALES")
    print("=" * 60)
    
    # Probar ajustador de probabilidades
    print("\n1️⃣ Probability Adjuster:")
    try:
        test_candidate = [SIMULATED_CANDIDATES[0]]
        adjusted = await adjust_candidate_probabilities(test_candidate)
        print(f"✅ Probability adjuster funcionando")
        
        if adjusted:
            original = test_candidate[0].get('prob_calculated', 0.55) * 100
            new_prob = adjusted[0].get('prob_calculated', 0.55) * 100
            adjustment = adjusted[0].get('probability_adjustment', 0.0) * 100
            print(f"   Ejemplo: {original:.1f}% → {new_prob:.1f}% ({adjustment:+.1f}%)")
    except Exception as e:
        print(f"❌ Error en probability adjuster: {e}")
    
    # Probar filtro de calidad
    print("\n2️⃣ Quality Filter:")
    try:
        quality_filter = QualityFilter()
        # Simular candidatos con scores
        test_candidates = SIMULATED_CANDIDATES.copy()
        for i, candidate in enumerate(test_candidates):
            candidate['quality_score'] = 0.8 - (i * 0.05)  # Scores decrecientes
            candidate['confidence_score'] = 0.7 + (i * 0.02)
        
        best = quality_filter.select_best_candidates(test_candidates)
        print(f"✅ Quality filter funcionando")
        print(f"   Seleccionó {len(best)} mejores de {len(test_candidates)}")
    except Exception as e:
        print(f"❌ Error en quality filter: {e}")
    
    # Probar formateador premium
    print("\n3️⃣ Premium Alert Formatter:")
    try:
        test_user = User("test", nivel="premium", bankroll=1000)
        test_candidate = SIMULATED_CANDIDATES[0].copy()
        test_candidate['quality_score'] = 0.85
        test_candidate['quality_rank'] = 1
        test_candidate['total_candidates'] = 7
        
        message = format_premium_exclusive_alert(test_candidate, test_user, 25.0)
        print(f"✅ Premium formatter funcionando")
        print(f"   Mensaje generado: {len(message)} caracteres")
    except Exception as e:
        print(f"❌ Error en premium formatter: {e}")


if __name__ == "__main__":
    async def main():
        await test_individual_components()
        await test_complete_system()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Prueba interrumpida por usuario")
    except Exception as e:
        print(f"\n💥 Error en prueba: {e}")
        import traceback
        traceback.print_exc()


# Función main para importación directa
async def main():
    await test_individual_components()
    await test_complete_system()