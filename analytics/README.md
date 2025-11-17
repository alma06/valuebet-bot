# Analytics Module - Odds-Trader Intelligence

Este módulo implementa análisis avanzado de comportamiento de casas de apuestas para mejorar la detección de value bets y evitar trampas.

## Módulos

### 1. vig.py - Análisis de Vig/Overround
Calcula el margen de la casa (vig) y ajusta probabilidades para obtener valores "limpios".

**Conceptos:**
- **Overround**: Suma de probabilidades implícitas > 100% (el margen de la casa)
- **Vig**: Porcentaje de comisión que retiene la casa
- **Probabilidades limpias**: Prob. ajustadas removiendo el vig

**Parámetros clave:**
- `VIG_MAX`: 0.12 (12% máximo aceptable)

### 2. movement.py - Detección de Movimientos de Cuota
Rastrea cambios en las cuotas a lo largo del tiempo para detectar movimientos significativos.

**Conceptos:**
- **Line movement**: Cambio en la cuota desde su apertura
- **Steam move**: Movimiento rápido y coordinado entre múltiples casas
- **Reverse line movement**: Cuota se mueve contra el dinero público

**Parámetros clave:**
- `MOVEMENT_WINDOW_HOURS`: 12 (ventana de análisis)
- `MOVEMENT_DELTA_PERCENT`: 6 (umbral de cambio significativo)

### 3. consensus.py - Análisis de Consenso
Compara cuotas entre múltiples bookmakers para detectar outliers y errores.

**Conceptos:**
- **Consensus line**: Media/mediana de cuotas entre casas
- **Outlier**: Cuota que difiere significativamente del consenso
- **Soft line**: Cuota vulnerable (típicamente en casas recreativas)

**Parámetros clave:**
- `OUTLIER_PERCENT`: 8 (diferencia % para marcar como outlier)

### 4. sharp_detector.py - Detección de Sharp Money
Identifica señales de apostadores profesionales ("sharps") basado en patrones de movimiento.

**Señales de Sharp Money:**
1. Movimiento grande (>6%) en ventana corta (<3h) sin noticias
2. Movimiento coordinado entre múltiples sharp books (Pinnacle, Bookmaker, etc.)
3. Reverse line movement (RLM): cuota baja a pesar de % apostado alto en el otro lado
4. Movimiento temprano (línea de apertura)

**Parámetros clave:**
- `SHARP_SCORE_THRESHOLD`: 0.6 (score mínimo para considerar sharp)

## Flujo de Validación

Cada candidato pasa por estos filtros en orden:

1. **Rango de cuota** (1.5 - 2.5) ✓
2. **Value >= umbral** por deporte ✓
3. **Vig check**: vig del mercado < 12%
4. **Consensus check**: cuota no es outlier extremo (o si lo es, validar por qué)
5. **Movement check**: detectar movimientos sospechosos
6. **Sharp detector**: señales positivas incrementan confianza

## Ejemplo de Uso

```python
from analytics.vig import calculate_vig, remove_vig
from analytics.consensus import consensus_score
from analytics.movement import detect_movement
from analytics.sharp_detector import detect_sharp_signals

# Analizar un mercado
odds = [2.10, 3.40, 3.50]  # Home, Draw, Away
overround, vig_per_outcome = calculate_vig(odds)
clean_probs = remove_vig(odds)

# Comparar entre bookmakers
book_odds = {'bet365': 2.10, 'pinnacle': 2.05, 'draftkings': 2.20}
consensus = consensus_score(book_odds, target_book='draftkings')

# Detectar movimientos
movement = detect_movement('event_123', 'bet365', 'h2h')

# Detectar sharp money
sharp_score, reasons = detect_sharp_signals('event_123', history)
```

## Configuración (.env)

```
# Vig Analysis
VIG_MAX=0.12

# Movement Detection
MOVEMENT_WINDOW_HOURS=12
MOVEMENT_DELTA_PERCENT=6

# Consensus Analysis
OUTLIER_PERCENT=8
MIN_BOOKS_CONSENSUS=3

# Sharp Detection
SHARP_SCORE_THRESHOLD=0.6
SHARP_MOVE_PERCENT=6
SHARP_TIME_WINDOW_HOURS=3
```

## Testing

Ejecutar test básico:
```bash
python -m analytics.test_analytics
```

## Mejoras Futuras (TODO)

- [ ] Integrar APIs de noticias para correlacionar movimientos
- [ ] Machine learning para predecir sharp vs public money
- [ ] Base de datos histórica más robusta (SQLite/PostgreSQL)
- [ ] API para consultar sharp books en tiempo real
- [ ] Dashboard web para visualizar movimientos y consensus
