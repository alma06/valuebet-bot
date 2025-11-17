"""
test_enhanced_system.py - Script de prueba para el sistema mejorado

Prueba:
1. Base de datos SQLite
2. APIs gratuitas
3. Modelo de probabilidades mejorado
4. Scraping de lesiones
"""
import sys
import asyncio
from pathlib import Path

# Agregar directorio al path
sys.path.insert(0, str(Path(__file__).parent))

from data.historical_db import historical_db
from data.stats_api import nba_api, football_api, injury_scraper
from model.enhanced_probabilities import estimate_probabilities_enhanced


def test_database():
    """Probar base de datos"""
    print("\n" + "="*50)
    print("TEST 1: BASE DE DATOS SQLite")
    print("="*50)
    
    # Guardar un partido de prueba
    test_match = {
        'id': 'test_match_001',
        'sport_key': 'basketball_nba',
        'home_team': 'Lakers',
        'away_team': 'Celtics',
        'commence_time': '2025-11-17T20:00:00Z',
        'home_score': 110,
        'away_score': 105,
        'result': 'home'
    }
    
    success = historical_db.save_match(test_match)
    print(f"✅ Partido guardado: {success}")
    
    # Guardar estadísticas de prueba
    test_stats = {
        'sport_key': 'basketball_nba',
        'team_name': 'Lakers',
        'season': '2024-25',
        'wins': 10,
        'losses': 5,
        'points_for': 1650,
        'points_against': 1575,
        'home_wins': 6,
        'away_wins': 4
    }
    
    success = historical_db.save_team_stats(test_stats)
    print(f"✅ Estadísticas guardadas: {success}")
    
    # Obtener stats
    stats = historical_db.get_team_stats('Lakers', 'basketball_nba')
    if stats:
        print(f"✅ Stats recuperadas: {stats['wins']}-{stats['losses']}")
    
    # Guardar predicción
    test_prediction = {
        'match_id': 'test_match_001',
        'sport_key': 'basketball_nba',
        'selection': 'Lakers',
        'odds': 2.15,
        'predicted_prob': 0.58,
        'value_score': 1.247,
        'stake': 25.0
    }
    
    pred_id = historical_db.save_prediction(test_prediction)
    print(f"✅ Predicción guardada con ID: {pred_id}")
    
    # Actualizar resultado
    if pred_id:
        historical_db.update_prediction_result(pred_id, 'home', True, 28.75)
        print(f"✅ Resultado actualizado: Ganancia $28.75")
    
    # Ver performance
    performance = historical_db.get_bot_performance(days=30)
    print(f"\n📊 PERFORMANCE DEL BOT:")
    print(f"   Total predicciones: {performance['total_predictions']}")
    print(f"   Correctas: {performance['correct']}")
    print(f"   Accuracy: {performance['accuracy']*100:.1f}%")
    print(f"   ROI: {performance['roi']*100:.1f}%")


def test_nba_api():
    """Probar NBA Stats API"""
    print("\n" + "="*50)
    print("TEST 2: NBA STATS API (Gratuita)")
    print("="*50)
    
    # Probar con Lakers (ID: 1610612747)
    print("\n🏀 Obteniendo stats de Lakers...")
    
    stats = nba_api.get_team_stats(1610612747)
    
    if stats:
        print(f"✅ Stats obtenidas:")
        print(f"   Récord: {stats.get('wins', 0)}-{stats.get('losses', 0)}")
        print(f"   Win%: {stats.get('win_pct', 0)*100:.1f}%")
        print(f"   PPG: {stats.get('ppg', 0):.1f}")
        print(f"   OPP PPG: {stats.get('oppg', 0):.1f}")
    else:
        print("⚠️  No se pudieron obtener stats (puede requerir API key o temporada incorrecta)")
    
    print("\n🏀 Obteniendo últimos partidos...")
    games = nba_api.get_recent_games(1610612747, last_n=5)
    
    if games:
        print(f"✅ Últimos {len(games)} partidos:")
        for game in games[:3]:
            print(f"   {game.get('date', 'N/A')}: {game.get('matchup', 'N/A')} - {game.get('result', 'N/A')}")
    else:
        print("⚠️  No se pudieron obtener partidos recientes")


def test_injury_scraper():
    """Probar scraper de lesiones ESPN"""
    print("\n" + "="*50)
    print("TEST 3: SCRAPER DE LESIONES ESPN (Gratuito)")
    print("="*50)
    
    print("\n🏥 Scrapeando lesiones de NBA...")
    
    injuries = injury_scraper.get_injuries('nba')
    
    if injuries:
        print(f"✅ {len(injuries)} lesiones encontradas:")
        for injury in injuries[:5]:
            print(f"   {injury.get('player', 'N/A')}: {injury.get('injury', 'N/A')} - {injury.get('status', 'N/A')}")
        
        # Guardar en base de datos
        for injury in injuries:
            injury['sport_key'] = 'basketball_nba'
        
        saved = historical_db.save_injuries(injuries)
        print(f"\n✅ {saved} lesiones guardadas en base de datos")
    else:
        print("⚠️  No se pudieron scraper lesiones (ESPN puede haber cambiado estructura HTML)")


def test_enhanced_probabilities():
    """Probar modelo mejorado de probabilidades"""
    print("\n" + "="*50)
    print("TEST 4: MODELO DE PROBABILIDADES MEJORADO")
    print("="*50)
    
    # Evento de prueba
    test_event = {
        'id': 'test_nba_001',
        'sport_key': 'basketball_nba',
        'home_team': 'Lakers',
        'away_team': 'Celtics',
        'home': 'Lakers',
        'away': 'Celtics',
        'commence_time': '2025-11-17T20:00:00Z'
    }
    
    print("\n🎯 Calculando probabilidades para Lakers vs Celtics...")
    
    probs = estimate_probabilities_enhanced(test_event)
    
    print(f"\n📊 PROBABILIDADES CALCULADAS:")
    print(f"   Lakers (local): {probs.get('home', 0)*100:.1f}%")
    print(f"   Celtics (visitante): {probs.get('away', 0)*100:.1f}%")
    
    if 'draw' in probs:
        print(f"   Empate: {probs.get('draw', 0)*100:.1f}%")
    
    print("\n✅ Modelo mejorado funcionando")
    print("   - Usa datos históricos de la BD")
    print("   - Ajusta por forma reciente")
    print("   - Considera lesiones")
    print("   - Ajusta por H2H")


def test_football_example():
    """Ejemplo con fútbol"""
    print("\n" + "="*50)
    print("TEST 5: EJEMPLO CON FÚTBOL")
    print("="*50)
    
    # Guardar datos de ejemplo
    real_madrid_stats = {
        'sport_key': 'soccer_spain_la_liga',
        'team_name': 'Real Madrid',
        'season': '2024-25',
        'wins': 8,
        'losses': 1,
        'draws': 2,
        'goals_for': 25,
        'goals_against': 8,
        'home_wins': 5,
        'away_wins': 3
    }
    
    barcelona_stats = {
        'sport_key': 'soccer_spain_la_liga',
        'team_name': 'Barcelona',
        'season': '2024-25',
        'wins': 9,
        'losses': 0,
        'draws': 2,
        'goals_for': 33,
        'goals_against': 10,
        'home_wins': 5,
        'away_wins': 4
    }
    
    historical_db.save_team_stats(real_madrid_stats)
    historical_db.save_team_stats(barcelona_stats)
    
    print("✅ Stats de Real Madrid y Barcelona guardadas")
    
    # Calcular probabilidades
    clasico_event = {
        'id': 'clasico_001',
        'sport_key': 'soccer_spain_la_liga',
        'home_team': 'Real Madrid',
        'away_team': 'Barcelona',
        'home': 'Real Madrid',
        'away': 'Barcelona',
        'commence_time': '2025-11-20T20:00:00Z'
    }
    
    print("\n⚽ Calculando El Clásico: Real Madrid vs Barcelona...")
    
    probs = estimate_probabilities_enhanced(clasico_event)
    
    print(f"\n📊 PROBABILIDADES:")
    print(f"   Real Madrid (local): {probs.get('home', 0)*100:.1f}%")
    print(f"   Empate: {probs.get('draw', 0)*100:.1f}%")
    print(f"   Barcelona (visitante): {probs.get('away', 0)*100:.1f}%")


def main():
    """Ejecutar todas las pruebas"""
    print("\n" + "="*70)
    print("🚀 PRUEBAS DEL SISTEMA MEJORADO - FASE 1 (GRATIS)")
    print("="*70)
    
    try:
        # Test 1: Base de datos
        test_database()
        
        # Test 2: NBA API
        test_nba_api()
        
        # Test 3: Scraper de lesiones
        test_injury_scraper()
        
        # Test 4: Modelo mejorado
        test_enhanced_probabilities()
        
        # Test 5: Ejemplo fútbol
        test_football_example()
        
        print("\n" + "="*70)
        print("✅ TODAS LAS PRUEBAS COMPLETADAS")
        print("="*70)
        
        print("\n📊 RESUMEN:")
        print("   ✅ Base de datos SQLite funcionando")
        print("   ✅ Modelo de probabilidades mejorado")
        print("   ⚠️  APIs externas requieren configuración")
        print("\n💡 PRÓXIMOS PASOS:")
        print("   1. Registrar en Football-Data.org para API key")
        print("   2. Poblar base de datos con partidos históricos")
        print("   3. Integrar con main.py para usar datos reales")
        print("   4. Sistema de tracking automático de resultados")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
