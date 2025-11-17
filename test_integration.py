"""
test_integration.py - Verificar integración del sistema mejorado

Este script prueba que main.py puede usar el sistema mejorado
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("\n" + "="*60)
print("🔍 VERIFICACIÓN DE INTEGRACIÓN")
print("="*60)

# Test 1: Importar scanner con modelo mejorado
print("\n1️⃣ Verificando scanner...")
try:
    from scanner.scanner import USING_ENHANCED_MODEL
    if USING_ENHANCED_MODEL:
        print("   ✅ Scanner usando modelo mejorado")
    else:
        print("   ⚠️  Scanner usando modelo básico")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Verificar imports en main.py
print("\n2️⃣ Verificando imports de main.py...")
try:
    # Simular imports de main.py
    from data.historical_db import historical_db
    from data.stats_api import injury_scraper
    print("   ✅ Sistema mejorado disponible")
    print(f"   ✅ Base de datos: {historical_db is not None}")
    print(f"   ✅ Scraper de lesiones: {injury_scraper is not None}")
    ENHANCED_AVAILABLE = True
except ImportError as e:
    print(f"   ⚠️  Sistema mejorado no disponible: {e}")
    ENHANCED_AVAILABLE = False

# Test 3: Verificar que main.py puede inicializarse
print("\n3️⃣ Verificando ValueBotMonitor...")
try:
    # No ejecutar main directamente para no iniciar el bot
    # Solo verificar que los imports funcionan
    import main
    print("   ✅ main.py puede importarse correctamente")
    print(f"   ✅ ENHANCED_SYSTEM_AVAILABLE: {main.ENHANCED_SYSTEM_AVAILABLE}")
except Exception as e:
    print(f"   ❌ Error importando main.py: {e}")

# Test 4: Verificar archivos del sistema mejorado
print("\n4️⃣ Verificando archivos del sistema mejorado...")
files_to_check = [
    ('data/stats_api.py', 'APIs de estadísticas'),
    ('data/historical_db.py', 'Base de datos histórica'),
    ('model/enhanced_probabilities.py', 'Modelo mejorado'),
    ('data/historical.db', 'Base de datos SQLite'),
]

for file_path, description in files_to_check:
    full_path = Path(__file__).parent / file_path
    if full_path.exists():
        print(f"   ✅ {description}: {file_path}")
    else:
        print(f"   ❌ {description}: {file_path} NO ENCONTRADO")

# Test 5: Ver estadísticas de la BD
if ENHANCED_AVAILABLE:
    print("\n5️⃣ Estadísticas de la base de datos...")
    try:
        from data.historical_db import historical_db
        
        # Contar registros
        import sqlite3
        conn = sqlite3.connect('data/historical.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM matches")
        matches_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM team_stats")
        stats_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM predictions")
        predictions_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM injuries")
        injuries_count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"   📊 Partidos guardados: {matches_count}")
        print(f"   📊 Estadísticas de equipos: {stats_count}")
        print(f"   📊 Predicciones registradas: {predictions_count}")
        print(f"   📊 Lesiones registradas: {injuries_count}")
        
        if predictions_count > 0:
            performance = historical_db.get_bot_performance(days=30)
            print(f"\n   🎯 Performance del bot (últimos 30 días):")
            print(f"      Total predicciones: {performance['total_predictions']}")
            print(f"      Correctas: {performance['correct']}")
            print(f"      Accuracy: {performance['accuracy']*100:.1f}%")
            print(f"      ROI: {performance['roi']*100:.1f}%")
            
    except Exception as e:
        print(f"   ⚠️  Error leyendo estadísticas: {e}")

# Resumen final
print("\n" + "="*60)
print("📊 RESUMEN DE INTEGRACIÓN")
print("="*60)

if USING_ENHANCED_MODEL and ENHANCED_AVAILABLE:
    print("\n✅ INTEGRACIÓN COMPLETA")
    print("   El bot usará:")
    print("   • Modelo de probabilidades mejorado")
    print("   • Base de datos histórica")
    print("   • Scraping de lesiones")
    print("   • Tracking automático de resultados")
    print("\n💡 El bot está listo para usar datos reales")
    
elif USING_ENHANCED_MODEL or ENHANCED_AVAILABLE:
    print("\n⚠️  INTEGRACIÓN PARCIAL")
    print("   Algunos módulos del sistema mejorado están disponibles")
    print("   pero no todos. Revisa los errores arriba.")
    
else:
    print("\n⚠️  SIN INTEGRACIÓN")
    print("   El bot usará el sistema básico")
    print("   Para activar el sistema mejorado:")
    print("   1. Asegúrate que existen todos los archivos")
    print("   2. Ejecuta: python test_enhanced_system.py")

print("\n🚀 CÓMO EJECUTAR EL BOT:")
print("   cd C:\\BotValueBets")
print("   python main.py")

print("\n📖 Ver documentación completa:")
print("   MEJORAS_IMPLEMENTADAS.md")
print()
