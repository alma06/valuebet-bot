-- Schema para odds_snapshots
-- Almacena histórico de cuotas para análisis de line movement

CREATE TABLE IF NOT EXISTS odds_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Información del evento
    event_id TEXT NOT NULL,
    sport_key TEXT NOT NULL,
    
    -- Información del mercado
    bookmaker TEXT NOT NULL,
    market TEXT NOT NULL,
    selection TEXT NOT NULL,
    odds DECIMAL(10, 2) NOT NULL,
    point DECIMAL(10, 2),  -- Para spreads/totals (puede ser NULL para h2h)
    
    -- Timestamp
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    
    -- Índices para consultas rápidas
    CONSTRAINT odds_snapshots_check_odds CHECK (odds >= 1.0 AND odds <= 1000.0)
);

-- Crear índices para mejorar performance
CREATE INDEX IF NOT EXISTS idx_odds_snapshots_event ON odds_snapshots(event_id);
CREATE INDEX IF NOT EXISTS idx_odds_snapshots_event_market ON odds_snapshots(event_id, market);
CREATE INDEX IF NOT EXISTS idx_odds_snapshots_timestamp ON odds_snapshots(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_odds_snapshots_event_selection ON odds_snapshots(event_id, market, selection);

-- Índice compuesto para consultas de line movement
CREATE INDEX IF NOT EXISTS idx_odds_snapshots_lookup 
ON odds_snapshots(event_id, market, selection, timestamp DESC);

-- Comentarios
COMMENT ON TABLE odds_snapshots IS 'Histórico de cuotas para análisis de line movement';
COMMENT ON COLUMN odds_snapshots.event_id IS 'ID del evento de la API';
COMMENT ON COLUMN odds_snapshots.sport_key IS 'Deporte del evento (e.g., basketball_nba)';
COMMENT ON COLUMN odds_snapshots.bookmaker IS 'Nombre de la casa de apuestas';
COMMENT ON COLUMN odds_snapshots.market IS 'Tipo de mercado (h2h, spreads, totals)';
COMMENT ON COLUMN odds_snapshots.selection IS 'Nombre del outcome/selección';
COMMENT ON COLUMN odds_snapshots.odds IS 'Cuota decimal';
COMMENT ON COLUMN odds_snapshots.point IS 'Línea de spread o total (NULL para h2h)';
COMMENT ON COLUMN odds_snapshots.timestamp IS 'Momento en que se registró la cuota';

-- Política de retención: eliminar snapshots de más de 30 días
-- (ejecutar periódicamente como tarea de mantenimiento)
-- DELETE FROM odds_snapshots WHERE timestamp < NOW() - INTERVAL '30 days';
