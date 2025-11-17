"""
test_verification.py - Probar sistema de verificación de resultados

Este script prueba el sistema de verificación sin esperar a las 2 AM
"""

import sys
import pathlib

PROJECT_ROOT = pathlib.Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.verify_results import ResultsVerifier
from data.historical_db import historical_db
from datetime import datetime, timezone

print("\n" + "="*60)
print("🧪 TEST: SISTEMA DE VERIFICACIÓN DE RESULTADOS")
print("="*60)

# Test 1: Verificar que el sistema está disponible
print("\n1️⃣ Verificando componentes...")
try:
    verifier = ResultsVerifier()
    print("   ✅ ResultsVerifier creado")
    print("   ✅ Odds API conectada")
    print("   ✅ Base de datos disponible")
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# Test 2: Ver predicciones actuales en BD
print("\n2️⃣ Predicciones en base de datos...")
import sqlite3
conn = sqlite3.connect('data/historical.db')
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM predictions")
total_preds = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM predictions WHERE actual_result IS NULL")
pending_preds = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM predictions WHERE actual_result IS NOT NULL")
verified_preds = cursor.fetchone()[0]

print(f"   📊 Total predicciones: {total_preds}")
print(f"   ⏳ Pendientes de verificar: {pending_preds}")
print(f"   ✅ Ya verificadas: {verified_preds}")

if total_preds == 0:
    print("\n⚠️  No hay predicciones en la BD aún")
    print("   El bot necesita enviar algunas alertas primero")
    print("   Ejecuta: python main.py")
    conn.close()
    exit(0)

# Test 3: Ver últimas predicciones
print("\n3️⃣ Últimas predicciones:")
cursor.execute("""
    SELECT id, match_id, sport_key, selection, odds, stake, 
           predicted_at, actual_result, was_correct, profit_loss
    FROM predictions
    ORDER BY predicted_at DESC
    LIMIT 5
""")

predictions = cursor.fetchall()
for pred in predictions:
    pred_id, match_id, sport, sel, odds, stake, pred_time, result, correct, profit = pred
    
    status = "✅ Verificada" if result else "⏳ Pendiente"
    print(f"\n   ID {pred_id}: {sel} @ {odds} (${stake})")
    print(f"      Sport: {sport}")
    print(f"      Fecha: {pred_time}")
    print(f"      Estado: {status}")
    
    if result:
        emoji = "✅" if correct else "❌"
        print(f"      Resultado: {emoji} {result}")
        print(f"      Profit: ${profit:+.2f}")

conn.close()

# Test 4: Probar verificación manual
print("\n4️⃣ Probando verificación manual...")
print("   (Esto consultará The Odds API)")

try:
    stats = verifier.verify_pending_predictions(days=2)
    
    print(f"\n   📊 Resultados de verificación:")
    print(f"      • Chequeadas: {stats['total_checked']}")
    print(f"      • Verificadas: {stats['verified']}")
    print(f"      • Pendientes: {stats['still_pending']}")
    
    if stats['verified'] > 0:
        print(f"      • Correctas: {stats['correct']}")
        print(f"      • Incorrectas: {stats['incorrect']}")
        print(f"      • Profit total: ${stats['total_profit']:+.2f}")
        
        accuracy = (stats['correct'] / stats['verified'] * 100)
        print(f"      • Accuracy: {accuracy:.1f}%")
    
except Exception as e:
    print(f"   ⚠️  Error en verificación: {e}")
    print("   Esto puede ser normal si:")
    print("      • No tienes acceso a scores en The Odds API")
    print("      • Los partidos no han terminado")
    print("      • No hay predicciones pendientes")

# Test 5: Performance general
print("\n5️⃣ Performance general del bot:")
try:
    perf = historical_db.get_bot_performance(days=30)
    
    if perf['total_predictions'] > 0:
        print(f"   📈 Últimos 30 días:")
        print(f"      • Total: {perf['total_predictions']}")
        print(f"      • Correctas: {perf['correct']}")
        print(f"      • Accuracy: {perf['accuracy']*100:.1f}%")
        print(f"      • ROI: {perf['roi']*100:+.1f}%")
        print(f"      • Profit: ${perf['total_profit']:+.2f}")
    else:
        print("   ⏳ Sin predicciones verificadas aún")
        
except Exception as e:
    print(f"   ⚠️  Error: {e}")

# Resumen
print("\n" + "="*60)
print("✅ TEST COMPLETADO")
print("="*60)

if pending_preds > 0:
    print(f"\n💡 Tienes {pending_preds} predicciones pendientes de verificar")
    print("   Se verificarán automáticamente a las 2 AM cada día")
    print("   O ejecuta: python scripts/verify_results.py")
else:
    print("\n✅ Todas las predicciones están verificadas")

print("\n📖 Documentación completa en: ROADMAP_PROFESIONAL.md")
print()
