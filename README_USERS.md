"""
README_USERS.md - Documentación del Sistema FREE/PREMIUM

# Sistema de Usuarios Gratuitos y Premium

## 📋 Descripción General

El bot ahora soporta dos niveles de usuarios:

### 🆓 USUARIOS GRATUITOS
- **Límite**: 1 alerta diaria
- **Contenido**: Mensaje resumido (equipos, cuota, mercado, selección)
- **Sin**: Análisis detallado, stake recomendado, tracking de bankroll

### 💎 USUARIOS PREMIUM
- **Límite**: 5 alertas diarias (configurable)
- **Contenido completo**:
  - Análisis de valor completo con estadísticas
  - Probabilidades (real vs implícita)
  - Edge sobre el mercado
  - Vig y eficiencia del mercado
  - Consenso entre bookmakers
  - Detección de movimientos de línea
  - Señales sharp (dinero profesional)
  - **Stake recomendado** según bankroll
  - Link a bookmaker
- **Gestión de bankroll**: Tracking automático de profit/loss
- **Estadísticas**: Win rate, ROI, profit total

---

## 🗂️ Estructura de Archivos

```
BotValueBets/
├── data/
│   ├── users.py              # Gestión de usuarios y bankroll
│   └── users.json            # Persistencia de usuarios
├── notifier/
│   └── alert_formatter.py    # Formatos de mensaje FREE vs PREMIUM
├── commands/
│   └── user_commands.py      # Comandos de Telegram (/start, /stats, etc.)
├── test_users.py             # Suite de tests del sistema
└── main.py                   # Integrado con sistema de usuarios
```

---

## ⚙️ Configuración (.env)

```bash
# Límites de alertas
ALERTS_FREE=1                # Alertas diarias para usuarios gratis
ALERTS_PREMIUM=5             # Alertas diarias para usuarios premium

# Gestión de bankroll (solo premium)
DEFAULT_BANKROLL=1000.0      # Bankroll inicial por defecto ($)
STAKE_METHOD=fixed_percentage # "kelly" o "fixed_percentage"
FRACTION_KELLY=0.25          # Fracción de Kelly (1/4 = conservador)
FIXED_PERCENTAGE=2.0         # % fijo del bankroll por apuesta
```

---

## 🚀 Uso

### 1. Ejecutar Tests

```powershell
python test_users.py
```

Esto probará:
- ✅ Creación de usuarios
- ✅ Límites de alertas
- ✅ Cálculo de stakes
- ✅ Formateo de mensajes
- ✅ Gestión de bankroll

### 2. Iniciar el Bot

```powershell
python main.py
```

El bot:
- Cargará usuarios desde `data/users.json`
- Si no hay usuarios, creará uno automáticamente con el CHAT_ID del .env
- Enviará alertas según el nivel de cada usuario
- Guardará automáticamente después de cada alerta

### 3. Upgradar un Usuario a Premium

**Manualmente** (editando `data/users.json`):
```json
{
  "123456789": {
    "chat_id": "123456789",
    "nivel": "premium",
    "bankroll": 1000.0,
    "initial_bankroll": 1000.0,
    "alerts_sent_today": 0,
    "last_reset_date": "2024-01-15",
    "total_bets": 0,
    "won_bets": 0,
    "total_profit": 0.0,
    "bet_history": []
  }
}
```

**Por código** (en main.py, solo para testing):
```python
# Descomentar para hacer premium al usuario de prueba
users_manager.upgrade_to_premium(TELEGRAM_CHAT_ID, initial_bankroll=1000.0)
```

---

## 💬 Comandos de Telegram

### Para Todos los Usuarios:
- `/start` - Registro inicial y bienvenida
- `/upgrade` - Información sobre cuenta premium

### Solo Premium:
- `/stats` - Ver estadísticas (win rate, ROI, profit, bankroll)
- `/bankroll <monto>` - Ajustar bankroll (ej: `/bankroll 2000`)
- `/result won` - Registrar apuesta ganada *(próximamente)*
- `/result lost` - Registrar apuesta perdida *(próximamente)*

**Nota**: Los comandos aún no están integrados con el bot de Telegram. Requiere configurar un webhook o polling para escuchar mensajes. Ver `commands/user_commands.py` para la implementación.

---

## 📊 Cálculo de Stakes (Premium)

### Método 1: Fixed Percentage (Recomendado)
```python
STAKE_METHOD=fixed_percentage
FIXED_PERCENTAGE=2.0  # 2% del bankroll por apuesta
```

**Ventajas**: Simple, conservador, fácil de entender

### Método 2: Kelly Criterion
```python
STAKE_METHOD=kelly
FRACTION_KELLY=0.25  # 1/4 Kelly
```

**Fórmula**: `f = (p*odd - 1) / (odd - 1)`

**Ventajas**: Maximiza crecimiento logarítmico del bankroll  
**Riesgo**: Puede sugerir stakes altos, usar fracción (1/4 o 1/2)

**Límites aplicados**: Stake siempre entre $1 y 10% del bankroll

---

## 📈 Ejemplo de Mensajes

### Mensaje FREE:
```
🎯 NBA
⚽ Lakers vs Warriors

📊 Mercado: h2h
✅ Selección: Lakers
💰 Cuota: 2.10
🏠 Casa: DraftKings

━━━━━━━━━━━━━━━━━━━━
🌟 UPGRADE A PREMIUM 🌟
━━━━━━━━━━━━━━━━━━━━

Desbloquea:
✨ Hasta 5 alertas diarias
📊 Análisis completo con estadísticas
💎 Probabilidades y valor esperado
💰 Stake recomendado según bankroll
...
```

### Mensaje PREMIUM:
```
━━━━━━━━━━━━━━━━━━━━
💎 ALERTA PREMIUM 💎
━━━━━━━━━━━━━━━━━━━━

🎯 NBA - Lakers vs Warriors
📊 h2h → Lakers
🏠 DraftKings | Cuota: 2.10
⏰ 2024-01-15T20:00:00Z

📈 ANÁLISIS DE VALOR:
✅ Prob. Real: 58.5%
📉 Prob. Implícita: 47.6%
💎 Valor: 1.229
🎯 Edge: +10.9%

🔍 INTELIGENCIA DE MERCADO:
📈 Vig: 5.8% | Eficiencia: 0.92
🌐 Media mercado: 2.05 | Diff: +2.4%
📊 Movimiento: UP 4.2%
⚡ SHARP DETECTADO (score: 3.5/5)

━━━━━━━━━━━━━━━━━━━━
💰 GESTIÓN DE BANKROLL
━━━━━━━━━━━━━━━━━━━━
💵 Stake recomendado: $20.00
💼 Bankroll actual: $1000.00
📊 % del bankroll: 2.00%
📈 Retorno si gana: $42.00 (profit: +$22.00)

📊 TUS ESTADÍSTICAS:
🎯 Apuestas: 10 | Win Rate: 60.0%
💰 Profit total: +$120.00 | ROI: +12.0%

🔗 Link: https://draftkings.com

🎲 Score Final: 6.8/10
📬 Alertas restantes hoy: 4/5
```

---

## 🔄 Reset Diario

- **Hora**: 6 AM Eastern Time (America/New_York)
- **Acción**: Resetea contadores de alertas enviadas
- **Automático**: Se verifica en cada ciclo (`user._check_reset()`)

---

## 🧪 Testing

El archivo `test_users.py` incluye 5 suites de tests:

1. **test_user_creation()**: Creación y persistencia
2. **test_alert_limits()**: Límites FREE (1) vs PREMIUM (5)
3. **test_stake_calculation()**: Kelly vs Fixed percentage
4. **test_message_formatting()**: Mensajes diferenciados
5. **test_bankroll_management()**: Simulación de apuestas y ROI

**Ejecutar**:
```powershell
python test_users.py
```

---

## 📝 TODO / Próximas Mejoras

- [ ] Integrar comandos con Telegram webhook/polling
- [ ] Implementar `/result` para tracking automático de resultados
- [ ] Dashboard web para gestión de usuarios
- [ ] Sistema de pagos/suscripciones automático
- [ ] Alertas personalizadas por deporte/mercado (premium)
- [ ] Notificaciones de límite alcanzado (opcional)
- [ ] Histórico de apuestas exportable (CSV/JSON)
- [ ] Recomendaciones de bankroll management según perfil de riesgo

---

## 🆘 Troubleshooting

### Usuario no recibe alertas
1. Verificar que existe en `data/users.json`
2. Verificar que `can_send_alert()` retorna True
3. Revisar `alerts_sent_today` vs límite
4. Verificar reset diario (6 AM ET)

### Stakes muy altos/bajos
1. Ajustar `FIXED_PERCENTAGE` (recomendado: 1-3%)
2. Si usas Kelly, reducir `FRACTION_KELLY` (0.25 = conservador)
3. Verificar que bankroll es realista (>$100)

### Usuarios no persisten
1. Verificar permisos de escritura en `data/`
2. Revisar logs de error en `users_manager.save()`
3. Verificar formato JSON en `data/users.json`

---

## 📞 Soporte

Para más información o problemas técnicos, revisar:
- `data/users.py` - Lógica de gestión de usuarios
- `notifier/alert_formatter.py` - Formatos de mensajes
- `test_users.py` - Tests y ejemplos de uso
