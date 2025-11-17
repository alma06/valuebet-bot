# encoding: utf-8
"""
test_referrals_simple.py - Test simple del sistema de referidos
"""

import sys
sys.path.insert(0, 'C:/BotValueBets')

import os
from referrals import ReferralSystem, format_referral_stats

print("\n" + "="*60)
print("TEST SIMPLE - SISTEMA DE REFERIDOS")
print("="*60)

# Limpiar datos de prueba anteriores
test_file = "data/test_referrals.json"
if os.path.exists(test_file):
    os.remove(test_file)
    print("\n[Limpiando datos de prueba anteriores...]")

# Test 1: Crear sistema
print("\n1. Inicializando sistema...")
system = ReferralSystem(test_file)
print("   Sistema creado OK")

# Test 2: Registrar usuario sin referrer
print("\n2. Registrando usuario sin referrer...")
result1 = system.register_user("user_123")
print(f"   Exito: {result1['success']}")
print(f"   Codigo: {result1['referral_code']}")
if 'referral_link' in result1:
    print(f"   Link: {result1['referral_link']}")
else:
    # Usuario ya existia, obtener stats
    stats = system.get_user_stats("user_123")
    if stats:
        print(f"   Link: {stats['referral_link']}")
        print(f"   (Usuario ya existia)")

# Test 3: Registrar usuario con referrer
print("\n3. Registrando usuario con referrer...")
result2 = system.register_user("user_456", referrer_code=result1['referral_code'])
print(f"   Exito: {result2['success']}")
print(f"   Referido por: {result2['referred_by']}")

# Test 4: Procesar pago
print("\n4. Procesando pago de referido...")
payment = system.process_premium_payment("user_456", 50.0)
print(f"   Exito: {payment['success']}")
print(f"   Recompensa otorgada: {payment['reward_granted']}")
print(f"   Comision: ${payment['commission']:.2f}")
print(f"   Nuevo saldo: ${payment['new_balance']:.2f}")

# Test 5: Ver estadisticas
print("\n5. Estadisticas del referrer...")
stats = system.get_user_stats("user_123")
print(f"   Total referidos: {stats['total_referrals']}")
print(f"   Referidos pagos: {stats['paid_referrals']}")
print(f"   Saldo: ${stats['balance_usd']:.2f}")
print(f"   Total ganado: ${stats['total_earned']:.2f}")

# Test 6: Auto-referido (debe fallar)
print("\n6. Probando prevencion de auto-referidos...")
result3 = system.register_user("user_123", referrer_code=result1['referral_code'])
print(f"   Bloqueado: {not result3['success']}")
if not result3['success']:
    print(f"   Razon: {result3['reason']}")

# Test 7: Mas referidos para semana gratis
print("\n7. Procesando 2 referidos mas para semana gratis...")
system.register_user("user_789", referrer_code=result1['referral_code'])
system.process_premium_payment("user_789", 50.0)

system.register_user("user_abc", referrer_code=result1['referral_code'])
payment3 = system.process_premium_payment("user_abc", 50.0)

print(f"   Referidos pagos: {payment3['paid_referrals']}")
print(f"   Semana gratis otorgada: {payment3.get('free_week_granted', False)}")
print(f"   Total semanas gratis: {payment3.get('free_weeks_total', 0)}")

# Test 8: Canjear semana gratis
print("\n8. Canjeando semana gratis...")
success, message = system.redeem_free_week("user_123")
print(f"   Exito: {success}")
print(f"   Mensaje: {message}")

# Test 9: Solicitar retiro
print("\n9. Solicitando retiro...")
success, message = system.withdraw_balance("user_123", 10.0)
print(f"   Exito: {success}")
print(f"   Mensaje: {message[:50]}...")

# Test 10: Reporte final
print("\n10. Reporte del sistema:")
print(system.generate_report())

print("\n" + "="*60)
print("TODOS LOS TESTS COMPLETADOS")
print("="*60)
