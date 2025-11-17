# Instrucciones para configurar la tabla odds_snapshots en Supabase

## Paso 1: Acceder a Supabase
1. Ve a https://supabase.com/dashboard
2. Selecciona tu proyecto: `ihdllnlbfcwrbftjzrjz`
3. En el menú lateral, haz clic en "SQL Editor"

## Paso 2: Ejecutar el schema
1. Haz clic en "New Query"
2. Copia y pega el contenido del archivo: `database/schema/odds_snapshots.sql`
3. Haz clic en "Run" o presiona Ctrl+Enter

## Paso 3: Verificar creación
Ejecuta esta consulta para verificar:

```sql
SELECT 
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name = 'odds_snapshots'
ORDER BY ordinal_position;
```

Deberías ver las columnas:
- id (uuid)
- event_id (text)
- sport_key (text)
- bookmaker (text)
- market (text)
- selection (text)
- odds (numeric)
- point (numeric)
- timestamp (timestamp with time zone)

## Paso 4: Verificar índices
```sql
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'odds_snapshots';
```

Deberías ver 5 índices:
1. odds_snapshots_pkey (PRIMARY KEY)
2. idx_odds_snapshots_event
3. idx_odds_snapshots_event_market
4. idx_odds_snapshots_timestamp
5. idx_odds_snapshots_event_selection
6. idx_odds_snapshots_lookup

## Configuración completada
Una vez ejecutado, el sistema de line movement estará listo para:
- Guardar snapshots de cuotas cada 10 minutos
- Detectar steam moves (>5% movimiento en 30 min)
- Identificar RLM (Reverse Line Movement)
- Rankear oportunidades por confidence score

## Mantenimiento
Ejecutar periódicamente (cada mes) para limpiar datos antiguos:

```sql
DELETE FROM odds_snapshots 
WHERE timestamp < NOW() - INTERVAL '30 days';
```

O crear un cron job en Supabase:
1. Ve a "Database" → "Cron Jobs"
2. Crea nuevo job: "cleanup_old_odds"
3. Schedule: `0 3 1 * *` (3 AM del día 1 de cada mes)
4. SQL: El DELETE de arriba
