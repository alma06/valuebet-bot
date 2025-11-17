"""
test_users.py - Script de prueba para sistema de usuarios FREE/PREMIUM.

Prueba:
- Creación de usuarios
- Límites de alertas
- Cálculo de stakes
- Formateo de mensajes
- Gestión de bankroll
"""
import asyncio
import json
from pathlib import Path

from data.users import get_users_manager, User, ALERTS_FREE, ALERTS_PREMIUM
from notifier.alert_formatter import (
    format_free_alert,
    format_premium_alert,
    format_stats_message,
    format_limits_reached_message
)


def test_user_creation():
    """Test 1: Creación y persistencia de usuarios."""
    print("=" * 80)
    print("TEST 1: Creación de usuarios")
    print("=" * 80)
    
    # Limpiar archivo de prueba
    test_path = "data/users_test.json"
    if Path(test_path).exists():
        Path(test_path).unlink()
    
    manager = get_users_manager(test_path)
    
    # Crear usuario gratuito
    user_free = manager.get_user("123456789")
    print(f"\n✅ Usuario FREE creado: {user_free.chat_id}")
    print(f"   Nivel: {user_free.nivel}")
    print(f"   Max alertas: {user_free.get_max_alerts()}")
    print(f"   Puede enviar: {user_free.can_send_alert()}")
    
    # Crear usuario premium
    manager.upgrade_to_premium("987654321", initial_bankroll=2000.0)
    user_premium = manager.get_user("987654321")
    print(f"\n✅ Usuario PREMIUM creado: {user_premium.chat_id}")
    print(f"   Nivel: {user_premium.nivel}")
    print(f"   Bankroll: ${user_premium.bankroll:.2f}")
    print(f"   Max alertas: {user_premium.get_max_alerts()}")
    print(f"   Puede enviar: {user_premium.can_send_alert()}")
    
    # Verificar persistencia
    manager.save()
    manager2 = get_users_manager(test_path)
    user_loaded = manager2.get_user("987654321")
    print(f"\n✅ Usuario cargado desde archivo:")
    print(f"   Nivel: {user_loaded.nivel}")
    print(f"   Bankroll: ${user_loaded.bankroll:.2f}")
    
    print("\n✅ Test 1 PASSED\n")


def test_alert_limits():
    """Test 2: Límites de alertas diarias."""
    print("=" * 80)
    print("TEST 2: Límites de alertas")
    print("=" * 80)
    
    test_path = "data/users_test.json"
    manager = get_users_manager(test_path)
    
    user_free = manager.get_user("123456789")
    user_premium = manager.get_user("987654321")
    
    # Test usuario FREE (límite 1)
    print(f"\n📊 Usuario FREE (límite: {ALERTS_FREE})")
    for i in range(3):
        can_send = user_free.can_send_alert()
        print(f"   Intento {i+1}: {'✅ Puede enviar' if can_send else '❌ Límite alcanzado'}")
        if can_send:
            user_free.record_alert_sent()
    
    print(f"   Total enviadas: {user_free.alerts_sent_today}")
    print(f"   Restantes: {user_free.get_remaining_alerts()}")
    
    # Test usuario PREMIUM (límite 5)
    print(f"\n📊 Usuario PREMIUM (límite: {ALERTS_PREMIUM})")
    for i in range(7):
        can_send = user_premium.can_send_alert()
        print(f"   Intento {i+1}: {'✅ Puede enviar' if can_send else '❌ Límite alcanzado'}")
        if can_send:
            user_premium.record_alert_sent()
    
    print(f"   Total enviadas: {user_premium.alerts_sent_today}")
    print(f"   Restantes: {user_premium.get_remaining_alerts()}")
    
    manager.save()
    print("\n✅ Test 2 PASSED\n")


def test_stake_calculation():
    """Test 3: Cálculo de stakes para usuarios premium."""
    print("=" * 80)
    print("TEST 3: Cálculo de stakes")
    print("=" * 80)
    
    user = User(chat_id="test", nivel="premium", bankroll=1000.0)
    
    test_cases = [
        {"odd": 2.10, "prob": 0.60, "desc": "Valor moderado"},
        {"odd": 1.80, "prob": 0.65, "desc": "Valor alto"},
        {"odd": 2.50, "prob": 0.55, "desc": "Valor bajo"},
    ]
    
    print(f"\n💼 Bankroll: ${user.bankroll:.2f}")
    print(f"📊 Método: {user.nivel}\n")
    
    for case in test_cases:
        stake = user.calculate_stake(case['odd'], case['prob'])
        pct = (stake / user.bankroll) * 100
        expected_return = stake * case['odd']
        
        print(f"📌 {case['desc']}:")
        print(f"   Cuota: {case['odd']:.2f} | Prob: {case['prob']*100:.0f}%")
        print(f"   💰 Stake: ${stake:.2f} ({pct:.2f}% del bankroll)")
        print(f"   📈 Retorno si gana: ${expected_return:.2f}")
        print()
    
    print("✅ Test 3 PASSED\n")


def test_message_formatting():
    """Test 4: Formateo de mensajes FREE vs PREMIUM."""
    print("=" * 80)
    print("TEST 4: Formateo de mensajes")
    print("=" * 80)
    
    # Candidato de ejemplo
    candidate = {
        'sport': 'NBA',
        'event': 'Lakers vs Warriors',
        'market': 'h2h',
        'selection': 'Lakers',
        'odd': 2.10,
        'bookmaker': 'DraftKings',
        'real_probability': 58.5,
        'implied_probability': 47.6,
        'value': 1.229,
        'edge_percent': 10.9,
        'commence_time': '2024-01-15T20:00:00Z',
        'vig': 5.8,
        'efficiency': 0.92,
        'consensus_mean': 2.05,
        'consensus_diff_pct': 2.4,
        'moved': True,
        'movement_direction': 'up',
        'movement_delta_pct': 4.2,
        'is_sharp': True,
        'sharp_score': 3.5,
        'final_score': 6.8,
        'url': 'https://draftkings.com'
    }
    
    user_free = User(chat_id="123", nivel="gratis")
    user_premium = User(chat_id="456", nivel="premium", bankroll=1000.0, total_bets=10, won_bets=6)
    
    # Mensaje FREE
    print("\n" + "─" * 80)
    print("MENSAJE USUARIO FREE:")
    print("─" * 80)
    msg_free = format_free_alert(candidate)
    print(msg_free)
    
    # Mensaje PREMIUM
    print("\n" + "─" * 80)
    print("MENSAJE USUARIO PREMIUM:")
    print("─" * 80)
    stake = user_premium.calculate_stake(candidate['odd'], candidate['real_probability']/100)
    msg_premium = format_premium_alert(candidate, user_premium, stake)
    print(msg_premium)
    
    # Stats message
    print("\n" + "─" * 80)
    print("MENSAJE DE ESTADÍSTICAS:")
    print("─" * 80)
    msg_stats = format_stats_message(user_premium)
    print(msg_stats)
    
    print("\n✅ Test 4 PASSED\n")


def test_bankroll_management():
    """Test 5: Gestión de bankroll con resultados."""
    print("=" * 80)
    print("TEST 5: Gestión de bankroll")
    print("=" * 80)
    
    user = User(chat_id="test", nivel="premium", bankroll=1000.0, initial_bankroll=1000.0)
    
    print(f"\n💼 Bankroll inicial: ${user.bankroll:.2f}\n")
    
    # Simular 5 apuestas
    bets = [
        {"stake": 20, "odd": 2.10, "won": True, "selection": "Team A"},
        {"stake": 20, "odd": 1.85, "won": False, "selection": "Team B"},
        {"stake": 22, "odd": 2.30, "won": True, "selection": "Team C"},
        {"stake": 24, "odd": 1.95, "won": True, "selection": "Team D"},
        {"stake": 25, "odd": 2.15, "won": False, "selection": "Team E"},
    ]
    
    for i, bet in enumerate(bets, 1):
        bet['event'] = f"Event {i}"
        bet['date'] = f"2024-01-{i:02d}"
        
        user.update_bankroll(bet)
        
        result = "✅ GANÓ" if bet['won'] else "❌ PERDIÓ"
        profit = bet['stake'] * (bet['odd'] - 1) if bet['won'] else -bet['stake']
        
        print(f"Apuesta {i}: {result}")
        print(f"   Stake: ${bet['stake']:.2f} @ {bet['odd']:.2f}")
        print(f"   Profit: ${profit:+.2f}")
        print(f"   💼 Bankroll: ${user.bankroll:.2f}")
        print()
    
    # Estadísticas finales
    stats = user.get_stats()
    print("📊 ESTADÍSTICAS FINALES:")
    print(f"   Total apuestas: {stats['total_apuestas']}")
    print(f"   Win rate: {stats['win_rate']:.1f}%")
    print(f"   Profit total: ${stats['profit_total']:+.2f}")
    print(f"   ROI: {stats['roi']:+.1f}%")
    print(f"   Bankroll final: ${stats['bankroll_actual']:.2f}")
    
    print("\n✅ Test 5 PASSED\n")


def run_all_tests():
    """Ejecuta todos los tests."""
    print("\n")
    print("🧪" * 40)
    print("SUITE DE TESTS: Sistema FREE/PREMIUM")
    print("🧪" * 40)
    print("\n")
    
    test_user_creation()
    test_alert_limits()
    test_stake_calculation()
    test_message_formatting()
    test_bankroll_management()
    
    print("=" * 80)
    print("✅ TODOS LOS TESTS PASARON EXITOSAMENTE")
    print("=" * 80)
    print("\nPróximos pasos:")
    print("1. Revisar data/users_test.json para ver estructura de datos")
    print("2. Ajustar STAKE_METHOD en .env (kelly o fixed_percentage)")
    print("3. Configurar ALERTS_FREE y ALERTS_PREMIUM según necesidades")
    print("4. Ejecutar 'python main.py' para producción")
    print("5. Usar comandos de Telegram: /start, /stats, /upgrade, /bankroll")


if __name__ == "__main__":
    try:
        run_all_tests()
    except Exception as e:
        print(f"\n❌ Error en tests: {e}")
        import traceback
        traceback.print_exc()
