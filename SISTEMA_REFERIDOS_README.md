# Sistema Completo de Referidos y Recompensas

## 📋 Descripción General

Sistema profesional de referidos integrado con el bot de Value Bets que permite a los usuarios ganar recompensas por invitar amigos. Incluye:

- 🔗 Enlaces únicos de referido por Telegram
- 💰 Comisión del 10% por cada referido que pague Premium ($5 por referido)
- 🎁 1 semana Premium gratis cada 3 referidos que paguen
- 💳 Sistema de saldo virtual con retiros
- 🛡️ Detección automática de fraude y auto-referidos
- 📊 Auditoría completa de transacciones
- 👑 Tabla de clasificación de mejores referrers

---

## 🏗️ Arquitectura del Sistema

### Módulos Principales

```
referrals/
├── referral_system.py       # Sistema core de referidos
└── __init__.py              # Exports públicos

commands/
└── referral_commands.py     # Comandos de Telegram

payments/
├── premium_integration.py   # Integración con pagos Premium
└── __init__.py             # Exports públicos

tests/
└── test_referral_system.py # Suite completa de tests
```

### Flujo de Datos

```
Usuario comparte link → Nuevo usuario se registra → Sistema vincula referrer
                                                          ↓
Nuevo usuario paga Premium → Sistema calcula comisión → Actualiza saldo referrer
                                                          ↓
                                     Envía notificación → Referrer puede retirar
```

---

## 🚀 Instalación y Configuración

### 1. Dependencias

El sistema ya está integrado con el bot existente. Solo asegúrate de tener:

```python
# Ya incluidas en tu bot
from referrals import ReferralSystem, format_referral_stats
from payments import PremiumPaymentProcessor, format_payment_receipt
from commands.referral_commands import ReferralCommands, AdminReferralCommands
```

### 2. Configuración (variables de entorno)

```bash
# Opcionales - valores por defecto ya configurados
PREMIUM_PRICE_USD=50.0                # Precio semanal Premium
COMMISSION_PERCENTAGE=10.0             # Porcentaje de comisión
PAID_REFERRALS_FOR_FREE_WEEK=3        # Referidos para semana gratis
```

### 3. Archivos de Datos

El sistema crea automáticamente:

- `data/referrals.json` - Base de datos de referidos
- `data/referrals_transactions.json` - Historial de transacciones (opcional)

---

## 💡 Uso del Sistema

### Para Usuarios

#### 1. Obtener tu Código de Referido

Cuando un usuario inicia el bot, automáticamente recibe su código único:

```
/start
```

Respuesta:
```
Bienvenido al Bot de Value Bets!

TU CODIGO DE REFERIDO: A1B2C3D4E5F6
Tu enlace: https://t.me/Valueapuestasbot?start=A1B2C3D4E5F6

Comparte tu enlace y gana:
- $5 USD por cada amigo que pague Premium
- 1 semana gratis cada 3 amigos que paguen
```

#### 2. Invitar Amigos

Los usuarios comparten su enlace único:
```
https://t.me/Valueapuestasbot?start=A1B2C3D4E5F6
```

Cuando un amigo hace clic, se registra automáticamente como referido.

#### 3. Ver Estadísticas

```
/referidos
```

Respuesta:
```
TUS ESTADISTICAS DE REFERIDOS
==================================================

Tu código de referido: A1B2C3D4E5F6
Tu enlace: https://t.me/Valueapuestasbot?start=A1B2C3D4E5F6

REFERIDOS:
  Total invitados: 5
  Pagaron Premium: 3
  Pendientes: 2

GANANCIAS:
  Saldo actual: $15.00
  Total ganado: $15.00

SEMANAS GRATIS:
  Ganadas: 1
  Disponibles: 1
  Próxima en: 3 referidos pagos más

RECOMPENSAS:
  Por cada referido que paga: $5.00
  Cada 3 pagos: 1 semana Premium gratis
```

#### 4. Canjear Semana Gratis

```
/canjear
```

Activa automáticamente 1 semana de Premium gratis si tiene disponibles.

#### 5. Solicitar Retiro

```
/retirar 25.50
```

Solicita retiro de saldo. Mínimo: $5.00 USD.

---

### Para Administradores

#### 1. Ver Reporte Completo

```
/reporte_referidos
```

Muestra estadísticas generales del sistema.

#### 2. Aprobar Retiros

```
/aprobar_retiro USER_ID MONTO
```

Ejemplo:
```
/aprobar_retiro 123456789 25.50
```

#### 3. Detectar Fraude

```
/detectar_fraude USER_ID
```

Analiza patrones sospechosos de un usuario.

---

## 🔧 Integración con Bot Existente

### Paso 1: Inicializar Sistemas

```python
from referrals import ReferralSystem
from payments import PremiumPaymentProcessor
from commands.referral_commands import ReferralCommands, AdminReferralCommands
from data.users import UserManager

# Inicializar
referral_system = ReferralSystem("data/referrals.json")
user_manager = UserManager("data/users.json")
payment_processor = PremiumPaymentProcessor(referral_system, user_manager)

# Comandos de usuario
ref_commands = ReferralCommands(
    referral_system=referral_system,
    user_manager=user_manager,
    bot_username="Valueapuestasbot"
)

# Comandos de admin
admin_commands = AdminReferralCommands(
    referral_system=referral_system,
    admin_ids=["5901833301"]  # Tu ID
)
```

### Paso 2: Registrar Handlers de Telegram

```python
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

application = Application.builder().token(BOT_TOKEN).build()

# Comandos de usuario
application.add_handler(CommandHandler("start", ref_commands.handle_start))
application.add_handler(CommandHandler("referidos", ref_commands.handle_referidos))
application.add_handler(CommandHandler("canjear", ref_commands.handle_canjear))
application.add_handler(CommandHandler("retirar", ref_commands.handle_retirar))
application.add_handler(CallbackQueryHandler(ref_commands.handle_callback_query))

# Comandos de admin
application.add_handler(CommandHandler("aprobar_retiro", admin_commands.handle_aprobar_retiro))
application.add_handler(CommandHandler("reporte_referidos", admin_commands.handle_reporte_referidos))
application.add_handler(CommandHandler("detectar_fraude", admin_commands.handle_detectar_fraude))
```

### Paso 3: Integrar con Pagos Premium

Cuando un usuario paga Premium:

```python
# En tu función de procesamiento de pagos
result = payment_processor.process_payment(
    user_id="123456789",
    amount_usd=50.0,
    weeks=1,
    payment_method="PayPal",
    transaction_id="PAYPAL-ABC123"
)

if result['success']:
    # El sistema automáticamente:
    # 1. Activa Premium para el usuario
    # 2. Calcula y otorga comisión al referrer (si existe)
    # 3. Otorga semana gratis cada 3 referidos
    # 4. Envía notificaciones
    
    print(format_payment_receipt(result))
```

---

## 🧪 Testing

### Ejecutar Suite Completa de Tests

```powershell
python tests/test_referral_system.py
```

Tests incluidos:
1. ✓ Generación de códigos únicos
2. ✓ Registro de usuarios con/sin referrer
3. ✓ Prevención de auto-referidos
4. ✓ Procesamiento de pagos y comisiones
5. ✓ Canje de semanas gratis
6. ✓ Flujo de retiro de saldo
7. ✓ Detección de fraude
8. ✓ Tabla de clasificación
9. ✓ Integración completa con pagos
10. ✓ Reporte del sistema

### Test Manual Rápido

```python
from referrals import ReferralSystem

# Crear sistema
system = ReferralSystem("data/test_referrals.json")

# Registrar usuario 1
result1 = system.register_user("user_123")
print(f"Código: {result1['referral_code']}")
print(f"Link: {result1['referral_link']}")

# Registrar usuario 2 (referido por user_123)
result2 = system.register_user("user_456", referrer_code=result1['referral_code'])
print(f"Referido por: {result2['referred_by']}")

# Simular pago de user_456
payment = system.process_premium_payment("user_456", 50.0)
print(f"Comisión: ${payment['commission']:.2f}")
print(f"Nuevo saldo: ${payment['new_balance']:.2f}")

# Ver stats de user_123
stats = system.get_user_stats("user_123")
print(f"Referidos pagos: {stats['paid_referrals']}")
print(f"Saldo: ${stats['balance_usd']:.2f}")
```

---

## 🔒 Seguridad y Anti-Fraude

### Prevención de Auto-Referidos

El sistema detecta automáticamente cuando un usuario intenta usar su propio código:

```python
result = system.register_user("user_123", referrer_code="CODIGO_DE_USER_123")
# result['success'] = False
# result['reason'] = 'Auto-referido no permitido'
```

### Detección de Patrones Sospechosos

El sistema analiza:

1. **Velocidad de referidos**: Muchos referidos en poco tiempo
2. **Tasa de conversión**: >80% de referidos pagan (sospechoso)
3. **Patrón temporal**: Todos los pagos el mismo día
4. **Profundidad de cadena**: Cadenas demasiado largas (>10 niveles)

Ejemplo:
```python
analysis = system.detect_fraud("user_123")

# {
#   'risk_level': 'HIGH',
#   'risk_score': 8,
#   'risk_factors': [
#     'Muchos referidos en poco tiempo',
#     'Tasa de conversión anormalmente alta',
#     'Todos los pagos en el mismo día'
#   ]
# }
```

### Auditoría de Transacciones

Todas las transacciones se registran:

```python
# Historial completo en system.transactions
for tx in system.transactions:
    print(f"{tx['timestamp']}: {tx['type']} - ${tx['amount']:.2f}")
```

---

## 📊 Recompensas y Economía

### Cálculo de Comisiones

```
Comisión = Pago Premium × 10%
         = $50 × 0.10
         = $5 por referido
```

### Semanas Gratis

```
Cada 3 referidos que paguen = 1 semana Premium gratis
Valor = $50 USD por semana
```

### Retiros

- **Mínimo**: $5.00 USD
- **Métodos**: PayPal, Transferencia, Criptomonedas
- **Tiempo**: 24-48 horas
- **Aprobación**: Manual por administrador

---

## 📈 Ejemplos de Uso

### Ejemplo 1: Usuario Activo

María invita a 10 amigos:
- 6 amigos pagan Premium ($50 cada uno)
- Comisión de María: 6 × $5 = $30 USD
- Semanas gratis: 6 ÷ 3 = 2 semanas ($100 de valor)
- **Total ganado: $130 USD de valor**

### Ejemplo 2: Super Referrer

Juan invita a 50 amigos:
- 30 amigos pagan Premium
- Comisión: 30 × $5 = $150 USD
- Semanas gratis: 30 ÷ 3 = 10 semanas ($500 de valor)
- **Total ganado: $650 USD de valor**

---

## 🐛 Troubleshooting

### Problema: Código de Referido No Funciona

```python
# Verificar que el código existe
code = "A1B2C3D4E5F6"
user_id = system._find_user_by_code(code)
if user_id:
    print(f"Código válido, pertenece a {user_id}")
else:
    print("Código no encontrado")
```

### Problema: Comisión No Se Otorgó

```python
# Verificar historial de transacciones
user_id = "123456789"
for tx in system.transactions:
    if tx['user_id'] == user_id and tx['type'] == 'commission_earned':
        print(f"Comisión: ${tx['amount']:.2f} en {tx['timestamp']}")
```

### Problema: Datos Corruptos

```python
# Hacer backup
import shutil
shutil.copy("data/referrals.json", "data/referrals_backup.json")

# Reinicializar (CUIDADO: borra datos)
system = ReferralSystem("data/referrals.json")
system.referrals = {}
system.transactions = []
system._save_data()
```

---

## 📚 API Reference

### ReferralSystem

#### `register_user(user_id, referrer_code=None)`
Registra un nuevo usuario en el sistema.

**Returns**: `Dict` con `success`, `referral_code`, `referral_link`, `referred_by`

#### `process_premium_payment(user_id, amount_usd, payment_method='manual')`
Procesa un pago Premium y otorga comisión al referrer.

**Returns**: `Dict` con `success`, `reward_granted`, `commission`, `new_balance`, etc.

#### `get_user_stats(user_id)`
Obtiene estadísticas completas de un usuario.

**Returns**: `Dict` con todos los stats o `None`

#### `redeem_free_week(user_id)`
Canjea una semana gratis ganada.

**Returns**: `Tuple[bool, str]` (éxito, mensaje)

#### `withdraw_balance(user_id, amount)`
Solicita retiro de saldo.

**Returns**: `Tuple[bool, str]` (éxito, mensaje)

#### `detect_fraud(user_id)`
Analiza patrones de fraude.

**Returns**: `Dict` con `risk_level`, `risk_score`, `risk_factors`

#### `get_leaderboard(limit=10)`
Obtiene ranking de mejores referrers.

**Returns**: `List[Dict]` ordenado por referidos pagos

---

## 🔮 Roadmap Futuro

Posibles mejoras:

- [ ] Dashboard web para estadísticas
- [ ] Pagos automáticos (PayPal API)
- [ ] Códigos promocionales personalizados
- [ ] Sistema de niveles (Bronze, Silver, Gold)
- [ ] Bonos por hitos (10, 50, 100 referidos)
- [ ] Webhooks para notificaciones
- [ ] API REST para integraciones
- [ ] Soporte multi-idioma

---

## 📞 Soporte

Para problemas o preguntas:

1. Revisar logs: `logs/referral_system.log`
2. Ejecutar tests: `python tests/test_referral_system.py`
3. Verificar datos: `data/referrals.json`
4. Contactar administrador en Telegram

---

## 📄 Licencia

Sistema propietario integrado con Bot de Value Bets.
© 2024 - Todos los derechos reservados.

---

**Versión**: 1.0.0  
**Última actualización**: 2024  
**Autor**: GitHub Copilot & Sistema Profesional de Value Bets
