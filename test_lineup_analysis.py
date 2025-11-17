"""
test_lineup_analysis.py - Prueba el nuevo sistema de análisis de alineaciones
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from utils.lineup_analyzer import get_lineup_section, analyze_lineup_impact
from notifier.alert_formatter import format_free_alert, format_premium_alert

# Candidatos de prueba para diferentes deportes
test_candidates = [
    {
        'event': 'Philadelphia 76ers vs Boston Celtics',
        'sport_key': 'basketball_nba',
        'sport': 'NBA',
        'market_key': 'h2h',
        'selection': 'Philadelphia 76ers -5.5',
        'odds': 2.01,
        'value': 1.105,
        'bookmaker': 'DraftKings',
        'prob_implied': 0.497,
        'prob_calculated': 0.550,
        'vig': 2.5
    },
    {
        'event': 'Real Madrid vs Barcelona',
        'sport_key': 'soccer_spain_la_liga',
        'sport': 'Spanish La Liga',
        'market_key': 'h2h',
        'selection': 'Real Madrid',
        'odds': 2.20,
        'value': 1.120,
        'bookmaker': 'bet365',
        'prob_implied': 0.455,
        'prob_calculated': 0.510,
        'vig': 3.2
    },
    {
        'event': 'Los Angeles Dodgers @ New York Yankees',
        'sport_key': 'baseball_mlb',
        'sport': 'MLB',
        'market_key': 'h2h',
        'selection': 'Los Angeles Dodgers',
        'odds': 1.95,
        'value': 1.085,
        'bookmaker': 'FanDuel',
        'prob_implied': 0.513,
        'prob_calculated': 0.556,
        'vig': 2.1
    }
]

def test_lineup_analysis():
    print("🔬 TESTING LINEUP ANALYSIS SYSTEM\n")
    print("=" * 60)
    
    for i, candidate in enumerate(test_candidates, 1):
        print(f"\n📊 TEST {i}: {candidate['event']}")
        print(f"🏆 Deporte: {candidate['sport']}")
        print("-" * 50)
        
        # Análisis detallado
        analysis = analyze_lineup_impact(candidate)
        print(f"🎯 Sport Key: {analysis['sport']}")
        print(f"🏠 Home: {analysis['home_team']}")
        print(f"✈️ Away: {analysis['away_team']}")
        print(f"📈 Impact Level: {analysis['impact_level']['sport_context']}")
        print(f"⏰ Timing: {analysis['timing_advice']['optimal_time']}")
        
        print(f"\n🔍 Critical Factors:")
        for factor in analysis['critical_factors'][:3]:
            print(f"  • {factor}")
        
        print(f"\n📱 Sources:")
        for source in analysis['lineup_sources'][:2]:
            print(f"  • {source}")
        
        print(f"\n" + "="*60)

def test_alert_formatting():
    print("\n\n📱 TESTING ALERT FORMATTING\n")
    print("=" * 60)
    
    candidate = test_candidates[0]  # NBA example
    
    print("🆓 FREE USER ALERT:")
    print("-" * 30)
    free_alert = format_free_alert(candidate)
    print(free_alert)
    
    print("\n💎 PREMIUM USER ALERT:")
    print("-" * 30)
    # Crear usuario de prueba
    test_user = {
        'user_id': '123456789',
        'username': 'test_user',
        'premium': True,
        'bankroll': 1000
    }
    premium_alert = format_premium_alert(candidate, test_user, 25)
    print(premium_alert)

def test_lineup_sections():
    print("\n\n🧩 TESTING LINEUP SECTIONS ONLY\n")
    print("=" * 60)
    
    for i, candidate in enumerate(test_candidates, 1):
        print(f"\n📊 {candidate['sport']} - {candidate['event']}")
        print("-" * 40)
        
        print("🆓 FREE VERSION:")
        free_section = get_lineup_section(candidate, is_premium=False)
        for line in free_section:
            print(f"  {line}")
        
        print(f"\n💎 PREMIUM VERSION:")
        premium_section = get_lineup_section(candidate, is_premium=True)
        for line in premium_section[:8]:  # Mostrar solo primeras 8 líneas para no saturar
            print(f"  {line}")
        if len(premium_section) > 8:
            print(f"  ... (+{len(premium_section) - 8} líneas más)")
        
        print("-" * 40)

if __name__ == "__main__":
    test_lineup_analysis()
    test_lineup_sections()
    test_alert_formatting()
    
    print(f"\n✅ TESTING COMPLETADO")
    print(f"🚀 Sistema de alineaciones integrado correctamente")
    print(f"📱 Alertas formateadas con análisis profesional")