"""
Script para migrar datos de SQLite a Supabase PostgreSQL
Ejecutar después de configurar las tablas en Supabase
"""

import os
import sys
import sqlite3
import psycopg2
from datetime import datetime

# Agregar ruta raíz del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

# Conexión a SQLite (origen)
SQLITE_DB = "data/historical.db"

# Conexión a Supabase (destino)
DATABASE_URL = os.getenv("DATABASE_URL")

def connect_sqlite():
    """Conectar a SQLite"""
    return sqlite3.connect(SQLITE_DB)

def connect_postgres():
    """Conectar a Supabase PostgreSQL"""
    return psycopg2.connect(DATABASE_URL)

def create_tables_postgres(pg_conn):
    """Crear tablas en PostgreSQL"""
    cursor = pg_conn.cursor()
    
    # Tabla matches
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id SERIAL PRIMARY KEY,
            match_id VARCHAR(255) UNIQUE NOT NULL,
            sport VARCHAR(100),
            league VARCHAR(200),
            home_team VARCHAR(200),
            away_team VARCHAR(200),
            commence_time TIMESTAMP,
            final_score_home INTEGER,
            final_score_away INTEGER,
            result VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabla team_stats
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS team_stats (
            id SERIAL PRIMARY KEY,
            team_name VARCHAR(200),
            sport VARCHAR(100),
            league VARCHAR(200),
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            draws INTEGER DEFAULT 0,
            goals_for INTEGER DEFAULT 0,
            goals_against INTEGER DEFAULT 0,
            points INTEGER DEFAULT 0,
            form VARCHAR(50),
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabla predictions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id SERIAL PRIMARY KEY,
            match_id VARCHAR(255) NOT NULL,
            sport VARCHAR(100),
            league VARCHAR(200),
            home_team VARCHAR(200),
            away_team VARCHAR(200),
            prediction_type VARCHAR(100),
            prediction_value VARCHAR(100),
            odds DECIMAL(10, 2),
            probability DECIMAL(5, 4),
            stake DECIMAL(10, 2),
            expected_value DECIMAL(10, 2),
            result VARCHAR(50),
            profit_loss DECIMAL(10, 2),
            verified BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            verified_at TIMESTAMP
        )
    """)
    
    # Tabla injuries
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS injuries (
            id SERIAL PRIMARY KEY,
            team_name VARCHAR(200),
            player_name VARCHAR(200),
            status VARCHAR(100),
            injury_type VARCHAR(200),
            sport VARCHAR(100),
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    pg_conn.commit()
    print("✅ Tablas creadas en Supabase")

def migrate_table(table_name, sqlite_conn, pg_conn):
    """Migrar una tabla de SQLite a PostgreSQL"""
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    # Obtener datos de SQLite
    sqlite_cursor.execute(f"SELECT * FROM {table_name}")
    rows = sqlite_cursor.fetchall()
    
    if not rows:
        print(f"⚠️  Tabla {table_name}: Sin datos para migrar")
        return
    
    # Obtener nombres de columnas (excluyendo el id autoincremental)
    columns = [description[0] for description in sqlite_cursor.description if description[0] != 'id']
    
    # Construir query de inserción
    placeholders = ', '.join(['%s'] * len(columns))
    columns_str = ', '.join(columns)
    
    insert_query = f"""
        INSERT INTO {table_name} ({columns_str})
        VALUES ({placeholders})
        ON CONFLICT DO NOTHING
    """
    
    # Insertar datos
    migrated = 0
    for row in rows:
        # Excluir el primer campo (id) de SQLite
        data = row[1:]
        try:
            pg_cursor.execute(insert_query, data)
            migrated += 1
        except Exception as e:
            print(f"⚠️  Error en {table_name}: {e}")
            continue
    
    pg_conn.commit()
    print(f"✅ Tabla {table_name}: {migrated}/{len(rows)} registros migrados")

def verify_migration(pg_conn):
    """Verificar migración"""
    cursor = pg_conn.cursor()
    
    tables = ['matches', 'team_stats', 'predictions', 'injuries']
    
    print("\n" + "="*50)
    print("📊 VERIFICACIÓN DE MIGRACIÓN")
    print("="*50)
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"   {table}: {count} registros")
    
    # Mostrar última predicción si existe
    cursor.execute("""
        SELECT home_team, away_team, prediction_type, odds, 
               probability, result, profit_loss
        FROM predictions
        ORDER BY created_at DESC
        LIMIT 1
    """)
    
    pred = cursor.fetchone()
    if pred:
        print("\n📈 Última predicción:")
        print(f"   {pred[0]} vs {pred[1]}")
        print(f"   Tipo: {pred[2]}")
        print(f"   Odds: {pred[3]}, Prob: {pred[4]}")
        print(f"   Resultado: {pred[5]}, P/L: ${pred[6]}")
    
    print("="*50 + "\n")

def main():
    """Ejecutar migración completa"""
    print("\n" + "="*50)
    print("🚀 MIGRACIÓN SQLITE → SUPABASE")
    print("="*50 + "\n")
    
    if not DATABASE_URL:
        print("❌ Error: DATABASE_URL no configurado en .env")
        print("\nAgrega a .env:")
        print("DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]/postgres")
        return
    
    try:
        # Conectar a ambas bases de datos
        print("🔌 Conectando a SQLite...")
        sqlite_conn = connect_sqlite()
        
        print("🔌 Conectando a Supabase...")
        pg_conn = connect_postgres()
        
        # Crear tablas en PostgreSQL
        print("\n📋 Creando tablas en Supabase...")
        create_tables_postgres(pg_conn)
        
        # Migrar cada tabla
        print("\n📦 Migrando datos...")
        tables = ['matches', 'team_stats', 'predictions', 'injuries']
        
        for table in tables:
            migrate_table(table, sqlite_conn, pg_conn)
        
        # Verificar migración
        verify_migration(pg_conn)
        
        # Cerrar conexiones
        sqlite_conn.close()
        pg_conn.close()
        
        print("✅ Migración completada exitosamente!\n")
        print("🎯 Próximos pasos:")
        print("   1. Verifica los datos en Supabase Dashboard")
        print("   2. El bot ya usará Supabase automáticamente")
        print("   3. Puedes eliminar data/historical.db si todo funciona\n")
        
    except Exception as e:
        print(f"\n❌ Error durante la migración: {e}")
        print("\nRevisa:")
        print("   1. DATABASE_URL en .env está correcto")
        print("   2. Credenciales de Supabase son válidas")
        print("   3. La base de datos SQLite existe\n")

if __name__ == "__main__":
    main()
