"""
Script para migrar datos de SQLite a Supabase usando API REST
"""

import os
import sys
import sqlite3
from supabase import create_client
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

# Configuración
SQLITE_DB = "data/historical.db"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def connect_supabase():
    """Conectar a Supabase"""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def create_tables_supabase(supabase):
    """Crear tablas en Supabase (SQL directo)"""
    print("\n📋 Creando tablas en Supabase...")
    
    # Nota: Las tablas deben crearse manualmente en Supabase Dashboard
    # O usando el SQL Editor con este script:
    
    sql_script = """
-- Tabla matches
CREATE TABLE IF NOT EXISTS matches (
    id VARCHAR(255) PRIMARY KEY,
    sport_key VARCHAR(100) NOT NULL,
    home_team VARCHAR(200) NOT NULL,
    away_team VARCHAR(200) NOT NULL,
    commence_time TIMESTAMP NOT NULL,
    home_score INTEGER,
    away_score INTEGER,
    result VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tabla team_stats
CREATE TABLE IF NOT EXISTS team_stats (
    id BIGSERIAL PRIMARY KEY,
    sport_key VARCHAR(100) NOT NULL,
    team_name VARCHAR(200) NOT NULL,
    season VARCHAR(50) NOT NULL,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    draws INTEGER DEFAULT 0,
    goals_for INTEGER DEFAULT 0,
    goals_against INTEGER DEFAULT 0,
    points_for INTEGER DEFAULT 0,
    points_against INTEGER DEFAULT 0,
    home_wins INTEGER DEFAULT 0,
    away_wins INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT NOW(),
    UNIQUE(sport_key, team_name, season)
);

-- Tabla predictions
CREATE TABLE IF NOT EXISTS predictions (
    id BIGSERIAL PRIMARY KEY,
    match_id VARCHAR(255) NOT NULL,
    sport_key VARCHAR(100) NOT NULL,
    selection TEXT NOT NULL,
    odds DECIMAL(10, 2) NOT NULL,
    predicted_prob DECIMAL(5, 4) NOT NULL,
    value_score DECIMAL(10, 2) NOT NULL,
    stake DECIMAL(10, 2),
    predicted_at TIMESTAMP DEFAULT NOW(),
    actual_result VARCHAR(50),
    was_correct BOOLEAN,
    profit_loss DECIMAL(10, 2),
    verified_at TIMESTAMP
);

-- Tabla injuries
CREATE TABLE IF NOT EXISTS injuries (
    id BIGSERIAL PRIMARY KEY,
    sport_key VARCHAR(100) NOT NULL,
    team_name VARCHAR(200) NOT NULL,
    player_name VARCHAR(200) NOT NULL,
    position VARCHAR(50),
    injury_type VARCHAR(200),
    status VARCHAR(100) NOT NULL,
    reported_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_matches_teams ON matches(home_team, away_team);
CREATE INDEX IF NOT EXISTS idx_matches_sport ON matches(sport_key);
CREATE INDEX IF NOT EXISTS idx_predictions_match ON predictions(match_id);
CREATE INDEX IF NOT EXISTS idx_team_stats_team ON team_stats(sport_key, team_name);
"""
    
    print("\n⚠️  IMPORTANTE: Copia y ejecuta este SQL en Supabase Dashboard:")
    print("   1. Ve a: SQL Editor en tu proyecto Supabase")
    print("   2. Pega el script de arriba")
    print("   3. Click en 'Run'")
    print("\nPor ahora, vamos a intentar insertar datos...")
    
    return True

def migrate_predictions(sqlite_conn, supabase):
    """Migrar predicciones de SQLite a Supabase"""
    try:
        cursor = sqlite_conn.cursor()
        cursor.execute("SELECT * FROM predictions")
        rows = cursor.fetchall()
        
        if not rows:
            print("⚠️  No hay predicciones para migrar")
            return 0
        
        columns = [desc[0] for desc in cursor.description]
        migrated = 0
        
        for row in rows:
            data = dict(zip(columns, row))
            
            # Convertir formato para Supabase
            supabase_data = {
                'match_id': data.get('match_id'),
                'sport_key': data.get('sport_key'),
                'selection': data.get('selection'),
                'odds': float(data.get('odds', 0)),
                'predicted_prob': float(data.get('predicted_prob', 0)),
                'value_score': float(data.get('value_score', 0)),
                'stake': float(data.get('stake', 0)) if data.get('stake') else None,
                'predicted_at': data.get('predicted_at'),
                'actual_result': data.get('actual_result'),
                'was_correct': bool(data.get('was_correct')) if data.get('was_correct') is not None else None,
                'profit_loss': float(data.get('profit_loss', 0)) if data.get('profit_loss') else None,
                'verified_at': data.get('verified_at')
            }
            
            try:
                supabase.table('predictions').insert(supabase_data).execute()
                migrated += 1
            except Exception as e:
                print(f"⚠️  Error migrando predicción: {e}")
                continue
        
        print(f"✅ Predicciones: {migrated}/{len(rows)} migradas")
        return migrated
        
    except Exception as e:
        print(f"❌ Error en migración de predicciones: {e}")
        return 0

def migrate_injuries(sqlite_conn, supabase):
    """Migrar lesiones de SQLite a Supabase"""
    try:
        cursor = sqlite_conn.cursor()
        cursor.execute("SELECT * FROM injuries")
        rows = cursor.fetchall()
        
        if not rows:
            print("⚠️  No hay lesiones para migrar")
            return 0
        
        columns = [desc[0] for desc in cursor.description]
        migrated = 0
        
        for row in rows:
            data = dict(zip(columns, row))
            
            supabase_data = {
                'sport_key': data.get('sport_key'),
                'team_name': data.get('team_name'),
                'player_name': data.get('player_name'),
                'position': data.get('position'),
                'injury_type': data.get('injury_type'),
                'status': data.get('status'),
                'reported_at': data.get('reported_at'),
                'resolved_at': data.get('resolved_at')
            }
            
            try:
                supabase.table('injuries').insert(supabase_data).execute()
                migrated += 1
            except:
                continue
        
        print(f"✅ Lesiones: {migrated}/{len(rows)} migradas")
        return migrated
        
    except Exception as e:
        print(f"❌ Error en migración de lesiones: {e}")
        return 0

def verify_migration(supabase):
    """Verificar migración"""
    print("\n" + "="*50)
    print("📊 VERIFICACIÓN DE MIGRACIÓN")
    print("="*50)
    
    try:
        # Contar predicciones
        preds = supabase.table('predictions').select('*', count='exact').execute()
        print(f"   predictions: {preds.count} registros")
        
        # Contar lesiones
        injuries = supabase.table('injuries').select('*', count='exact').execute()
        print(f"   injuries: {injuries.count} registros")
        
        # Mostrar última predicción
        if preds.data:
            pred = preds.data[-1]
            print(f"\n📈 Última predicción:")
            print(f"   Match: {pred.get('match_id')}")
            print(f"   Tipo: {pred.get('selection')}")
            print(f"   Odds: {pred.get('odds')}, Prob: {pred.get('predicted_prob')}")
            print(f"   Resultado: {pred.get('actual_result')}, P/L: ${pred.get('profit_loss')}")
        
        print("="*50 + "\n")
        
    except Exception as e:
        print(f"⚠️  Error en verificación: {e}")

def main():
    """Ejecutar migración"""
    print("\n" + "="*50)
    print("🚀 MIGRACIÓN SQLITE → SUPABASE (API)")
    print("="*50 + "\n")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Error: SUPABASE_URL y SUPABASE_KEY no configurados en .env")
        return
    
    if not os.path.exists(SQLITE_DB):
        print(f"❌ Error: No se encuentra {SQLITE_DB}")
        return
    
    try:
        # Conectar
        print("🔌 Conectando a SQLite...")
        sqlite_conn = sqlite3.connect(SQLITE_DB)
        
        print("🔌 Conectando a Supabase...")
        supabase = connect_supabase()
        
        # Crear tablas (instrucciones)
        create_tables_supabase(supabase)
        
        # Migrar datos
        print("\n📦 Migrando datos...")
        migrate_predictions(sqlite_conn, supabase)
        migrate_injuries(sqlite_conn, supabase)
        
        # Verificar
        verify_migration(supabase)
        
        sqlite_conn.close()
        
        print("✅ Migración completada!\n")
        print("🎯 Próximos pasos:")
        print("   1. Verifica los datos en Supabase Dashboard")
        print("   2. Si faltan tablas, ejecuta el SQL en SQL Editor")
        print("   3. Ejecuta: python -c \"from data.historical_db_api import historical_db; print('OK')\"")
        print("   4. Reinicia el bot\n")
        
    except Exception as e:
        print(f"\n❌ Error durante la migración: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
