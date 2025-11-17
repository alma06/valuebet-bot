"""
test_analytics.py - Script de prueba para el módulo analytics.

Carga sample_odds.json y ejecuta el scanner avanzado, mostrando análisis completo
de cada candidato incluyendo vig, consensus, movement y sharp signals.
"""
import asyncio
import json
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from scanner.advanced_scanner import find_value_bets_advanced, format_advanced_message
from analytics.vig import calculate_vig, is_vig_acceptable, market_efficiency_score
from analytics.consensus import consensus_score, market_agreement_score
from analytics.movement import load_history_from_file, get_movement_summary
from analytics.sharp_detector import detect_sharp_signals


async def test_analytics():
    """Run analytics test with sample odds data."""
    
    print("=" * 80)
    print("🧪 TEST: Módulo Analytics - Odds-Trader Intelligence")
    print("=" * 80)
    
    # Load sample data
    sample_path = PROJECT_ROOT / "data" / "sample_odds.json"
    
    if not sample_path.exists():
        print(f"❌ Error: No se encuentra {sample_path}")
        return
    
    with open(sample_path, "r", encoding="utf-8") as f:
        sample_data = json.load(f)
    
    print(f"\n📊 Cargados {len(sample_data)} eventos de prueba")
    
    # Run advanced scanner
    print("\n🔍 Ejecutando scanner avanzado...\n")
    candidates = await find_value_bets_advanced(sample_data)
    
    print(f"\n✅ Encontrados {len(candidates)} candidatos\n")
    
    if not candidates:
        print("⚠️  No se encontraron candidatos con los filtros actuales.")
        print("Tip: Ajusta los thresholds en .env o revisa sample_odds.json")
        return
    
    # Display top candidates
    print("=" * 80)
    print("🏆 TOP CANDIDATOS")
    print("=" * 80)
    
    for i, candidate in enumerate(candidates[:5], 1):
        print(f"\n{'─' * 80}")
        print(f"CANDIDATO #{i}")
        print(f"{'─' * 80}")
        print(format_advanced_message(candidate))
        print()
        
        # Additional debug info
        print("DEBUG INFO:")
        print(f"  - Outlier status: {candidate.get('outlier_status', 'N/A')}")
        print(f"  - Agreement score: {candidate.get('agreement_score', 0):.3f}")
        print(f"  - Sharp signals: {', '.join(candidate.get('sharp_signals', []))}")
        print()
    
    # Statistics
    print("\n" + "=" * 80)
    print("📈 ESTADÍSTICAS")
    print("=" * 80)
    
    sharp_count = sum(1 for c in candidates if c.get('is_sharp'))
    moved_count = sum(1 for c in candidates if c.get('moved'))
    outlier_count = sum(1 for c in candidates if 'outlier' in c.get('outlier_status', ''))
    
    avg_score = sum(c.get('final_score', 0) for c in candidates) / len(candidates)
    avg_vig = sum(c.get('vig', 0) for c in candidates) / len(candidates)
    avg_efficiency = sum(c.get('efficiency', 0) for c in candidates) / len(candidates)
    
    print(f"Total candidatos: {len(candidates)}")
    print(f"Con señales sharp: {sharp_count} ({sharp_count/len(candidates)*100:.1f}%)")
    print(f"Con movimiento: {moved_count} ({moved_count/len(candidates)*100:.1f}%)")
    print(f"Outliers: {outlier_count} ({outlier_count/len(candidates)*100:.1f}%)")
    print()
    print(f"Score promedio: {avg_score:.2f}/10")
    print(f"Vig promedio: {avg_vig:.2f}%")
    print(f"Eficiencia promedio: {avg_efficiency:.2f}")
    
    # Test individual modules
    print("\n" + "=" * 80)
    print("🔬 PRUEBAS UNITARIAS DE MÓDULOS")
    print("=" * 80)
    
    # Test vig module
    print("\n1️⃣  VIG MODULE:")
    test_odds = {"Home": 2.10, "Away": 2.20, "Draw": 3.50}
    vig = calculate_vig(test_odds)
    vig_ok = is_vig_acceptable(vig)
    efficiency = market_efficiency_score(vig)
    print(f"   Test odds: {test_odds}")
    print(f"   Vig: {vig:.2f}% | OK: {vig_ok} | Efficiency: {efficiency:.2f}")
    
    # Test consensus module
    print("\n2️⃣  CONSENSUS MODULE:")
    book_odds = {"bet365": 2.10, "pinnacle": 2.05, "draftkings": 2.30, "betmgm": 2.08}
    consensus = consensus_score(book_odds, "draftkings")
    agreement = market_agreement_score(book_odds)
    print(f"   Book odds: {book_odds}")
    print(f"   Mean: {consensus.get('mean', 0):.2f} | Target: {consensus.get('target_odd', 0):.2f}")
    print(f"   Diff: {consensus.get('diff_from_mean_pct', 0):+.1f}% | Outlier: {consensus.get('is_outlier', False)}")
    print(f"   Agreement: {agreement:.2f}")
    
    # Test movement module
    print("\n3️⃣  MOVEMENT MODULE:")
    # Movement requires history, check if file exists
    history_path = PROJECT_ROOT / "data" / "odds_history.json"
    if history_path.exists():
        history = load_history_from_file(str(history_path))
        print(f"   History loaded: {len(history)} events tracked")
        
        # Show sample movement
        for event_id in list(history.keys())[:1]:
            summary = get_movement_summary(event_id)
            print(f"   Event {event_id}: {summary}")
    else:
        print(f"   No history file found (normal en primera ejecución)")
    
    # Test sharp detector
    print("\n4️⃣  SHARP DETECTOR MODULE:")
    test_movement = {'moved': True, 'delta_pct': 7.5, 'direction': 'up', 'window_hours': 2.0}
    test_consensus_data = {'is_outlier': False, 'diff_from_mean_pct': 3.0}
    test_vig_data = {'vig': 5.0, 'is_acceptable': True, 'efficiency_score': 0.9}
    
    sharp_result = detect_sharp_signals(test_movement, test_consensus_data, test_vig_data)
    print(f"   Test scenario: Movimiento rápido (7.5% en 2h), mercado eficiente")
    print(f"   Sharp score: {sharp_result.get('sharp_score', 0):.1f}/5")
    print(f"   Is sharp: {sharp_result.get('is_sharp', False)}")
    print(f"   Signals: {', '.join(sharp_result.get('signals', []))}")
    
    print("\n" + "=" * 80)
    print("✅ Test completado!")
    print("=" * 80)
    print("\nPróximos pasos:")
    print("  1. Ajusta los thresholds en .env según tus preferencias")
    print("  2. Ejecuta 'python main.py' para iniciar el bot en producción")
    print("  3. Monitorea data/odds_history.json para ver el tracking de movimientos")
    print("  4. Revisa los mensajes de Telegram con análisis completo")


if __name__ == "__main__":
    try:
        asyncio.run(test_analytics())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrumpido por usuario")
    except Exception as e:
        print(f"\n\n❌ Error durante el test: {e}")
        import traceback
        traceback.print_exc()
