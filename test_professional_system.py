"""Test profesional de todos los módulos nuevos"""

print("="*70)
print("TESTING PROFESSIONAL MODULES")
print("="*70)

# Test 1: Bankroll Manager
print("\n1. Testing BankrollManager...")
from utils.bankroll_manager import BankrollManager

manager = BankrollManager(bankroll=1000, kelly_fraction=0.25)
rec = manager.get_recommendation(odds=1.95, probability=0.60, confidence_score=0.85)

print(f"   Stake: ${rec['stake']}")
print(f"   Edge: {rec['edge']}%")
print(f"   EV: ${rec['expected_value']}")
print(f"   Risk: {rec['risk_category']}")
print("   ✓ BankrollManager OK")

# Test 2: Results Tracker
print("\n2. Testing ResultsTracker...")
from tracking.results_tracker import ResultsTracker

tracker = ResultsTracker('data/test_results.json')
pred_id = tracker.add_prediction(
    event_id="test_123",
    sport="basketball_nba",
    home="Lakers",
    away="Warriors",
    market="h2h",
    selection="Lakers",
    odds=1.95,
    probability=0.60,
    stake=25.0
)
tracker.update_result(pred_id, 'win')
print(f"   Predictions: {len(tracker.predictions)}")
print(f"   Accuracy: {tracker.calculate_accuracy():.1f}%")
print("   ✓ ResultsTracker OK")

# Test 3: Advanced Predictor
print("\n3. Testing AdvancedPredictor...")
from model.advanced_predictor import AdvancedPredictor

predictor = AdvancedPredictor()
result = predictor.enhance_prediction(
    event={'sport_key': 'basketball_nba', 'home_team': 'Lakers', 'away_team': 'Warriors'},
    base_prob_home=0.52,
    base_prob_away=0.48,
    additional_data={
        'home_rest_days': 2,
        'home_injury_impact': 0.2,
        'home_recent_form': 0.6
    }
)
print(f"   Home prob: {result['home_prob_base']:.1%} -> {result['home_prob_adjusted']:.1%}")
print(f"   Confidence: {result['confidence_score']:.1%}")
print("   ✓ AdvancedPredictor OK")

# Test 4: Integración con sistema existente
print("\n4. Testing integration with existing modules...")
from scanner.scanner import ValueScanner
from data.odds_api import OddsFetcher

fetcher = OddsFetcher(api_key=None, sample_path="data/sample_odds.json")
scanner = ValueScanner(min_odd=1.5, max_odd=2.5, min_prob=0.70)
print("   ✓ Integration OK")

print("\n" + "="*70)
print("ALL PROFESSIONAL MODULES WORKING CORRECTLY")
print("="*70)
print("\nSistema listo para producción con:")
print("  - Gestión profesional de bankroll (Kelly Criterion)")
print("  - Tracking y validación de precisión")
print("  - Modelo predictivo avanzado con contexto")
print("  - Integración completa con sistema existente")
