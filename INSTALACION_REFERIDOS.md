# SISTEMA DE REFERIDOS - INSTALACION E INTEGRACION

## ESTADO: INSTALADO Y PROBADO ✓

El sistema completo de referidos ha sido implementado y probado exitosamente.

---

## ARCHIVOS CREADOS

### Modulos Core
- `referrals/referral_system.py` - Sistema principal de referidos (639 líneas)
- `referrals/__init__.py` - Exports del módulo
- `payments/premium_integration.py` - Integración con pagos Premium (520 líneas)
- `payments/__init__.py` - Exports del módulo
- `commands/referral_commands.py` - Comandos de Telegram (530 líneas)

### Testing y Documentación
- `test_referrals_simple.py` - Test simple funcional (PROBADO ✓)
- `SISTEMA_REFERIDOS_README.md` - Documentación completa (450 líneas)

### Datos
- `data/referrals.json` - Base de datos de referidos (se crea automáticamente)
- `data/test_referrals.json` - Datos de prueba

---

## RESULTADO DE PRUEBAS

```
TODAS LAS FUNCIONALIDADES PROBADAS:
✓ Generación de códigos únicos (2A62C397B14F)
✓ Registro de usuarios con/sin referrer
✓ Prevención de auto-referidos
✓ Procesamiento de pagos Premium
✓ Cálculo automático de comisiones ($5 por referido)
✓ Otorgamiento de semanas gratis (cada 3 referidos)
✓ Canje de semanas gratis
✓ Solicitudes de retiro de saldo
✓ Reporte completo del sistema
```

---

## INTEGRACION CON TU BOT

### Paso 1: Importar en main.py

Agrega al inicio de tu `main.py`:

```python
from referrals import ReferralSystem
from payments import PremiumPaymentProcessor
from commands.referral_commands import ReferralCommands, AdminReferralCommands
```

### Paso 2: Inicializar sistemas

Donde inicializas tus objetos:

```python
# Sistema de referidos
referral_system = ReferralSystem("data/referrals.json")

# Procesador de pagos con referidos
payment_processor = PremiumPaymentProcessor(
    referral_system=referral_system,
    user_manager=users_manager,  # Tu UsersManager existente
    notifier=telegram_notifier   # Tu TelegramNotifier existente
)

# Comandos de referidos
ref_commands = ReferralCommands(
    referral_system=referral_system,
    user_manager=users_manager,
    bot_username="Valueapuestasbot"  # Tu bot username
)

# Comandos de admin
admin_commands = AdminReferralCommands(
    referral_system=referral_system,
    admin_ids=["5901833301"]  # Tu chat ID
)
```

### Paso 3: Registrar comandos de Telegram

Si usas python-telegram-bot v20+:

```python
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

# Al configurar la aplicación
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

### Paso 4: Integrar con procesamiento de pagos

Cuando proceses un pago Premium, usa el nuevo procesador:

```python
# ANTES (tu código actual)
# user.process_premium_payment(50.0)
# user.nivel = "premium"
# users_manager.update_user(user)

# AHORA (con sistema de referidos)
result = payment_processor.process_payment(
    user_id=user_id,
    amount_usd=50.0,
    weeks=1,
    payment_method="Manual",  # o "PayPal", "Transferencia", etc.
    transaction_id=None       # ID de transacción si existe
)

if result['success']:
    print("Pago procesado:")
    print(f"  Premium activado hasta: {result['premium_activated']['new_expiry']}")
    
    # Si había referrer
    if result.get('referral_reward', {}).get('reward_granted'):
        print(f"  Comisión otorgada: ${result['referral_reward']['commission']:.2f}")
        print(f"  A usuario: {result['referral_reward']['referrer_id']}")
else:
    print(f"Error: {result['errors']}")
```

---

## COMANDOS DISPONIBLES

### Para Usuarios

| Comando | Descripción |
|---------|-------------|
| `/start` | Inicia el bot y muestra código de referido |
| `/start CODIGO` | Inicia con código de referido |
| `/referidos` | Muestra estadísticas y enlace de referido |
| `/canjear` | Canjea una semana Premium gratis |
| `/retirar [monto]` | Solicita retiro de saldo (ej: `/retirar 25.50`) |

### Para Administradores

| Comando | Descripción |
|---------|-------------|
| `/aprobar_retiro USER_ID MONTO` | Aprueba un retiro |
| `/reporte_referidos` | Reporte completo del sistema |
| `/detectar_fraude USER_ID` | Analiza patrones de fraude |

---

## FLUJO DE USUARIO

```
1. Usuario A inicia el bot
   → Recibe código único: A1B2C3D4E5F6
   → Recibe enlace: https://t.me/Valueapuestasbot?start=A1B2C3D4E5F6

2. Usuario A comparte su enlace con amigos

3. Usuario B hace clic en el enlace
   → Se registra automáticamente como referido de A
   → Usuario A recibe notificación

4. Usuario B paga Premium ($50)
   → Sistema activa Premium para B
   → Sistema otorga $5 a A (10% comisión)
   → A recibe notificación

5. Cuando A tenga 3 referidos que paguen
   → Sistema otorga 1 semana Premium gratis a A
   → A recibe notificación

6. Usuario A puede:
   → Ver saldo con /referidos
   → Canjear semanas gratis con /canjear
   → Solicitar retiro con /retirar 25.00
```

---

## ECONOMIA DEL SISTEMA

### Recompensas por Referido

```
Por cada amigo que pague Premium ($50):
- Comisión: $5 USD (10%)
- Se acumula en saldo virtual

Cada 3 amigos que paguen:
- 1 semana Premium gratis (valor $50)
```

### Ejemplo Real

Usuario invita 10 amigos, 6 pagan:

```
Comisiones: 6 × $5 = $30 USD
Semanas gratis: 6 ÷ 3 = 2 semanas ($100 de valor)
Total ganado: $130 USD equivalente
```

---

## SEGURIDAD

### Anti-Fraude Automático

El sistema detecta:
- Auto-referidos (usar propio código)
- Muchos referidos en poco tiempo
- Tasa de conversión sospechosa (>80%)
- Todos los pagos el mismo día
- Cadenas de referidos demasiado largas

### Auditoría Completa

Todas las transacciones se registran:
- Registros de referidos
- Pagos procesados
- Comisiones otorgadas
- Semanas gratis canjeadas
- Retiros solicitados/aprobados

Ver historial:
```python
for tx in referral_system.transactions:
    print(f"{tx['timestamp']}: {tx['type']} - ${tx['amount']:.2f}")
```

---

## MANTENIMIENTO

### Ver estadísticas generales

```python
report = referral_system.generate_report()
print(report)
```

### Backup de datos

```powershell
Copy-Item data\referrals.json data\referrals_backup_$(Get-Date -Format 'yyyyMMdd').json
```

### Limpiar datos de prueba

```powershell
Remove-Item data\test_*.json
```

---

## NOTAS IMPORTANTES

1. **El sistema ya está instalado y funcionando** - Solo necesitas integrar los comandos en tu bot

2. **Compatible con tu sistema actual** - No afecta ninguna funcionalidad existente

3. **Notificaciones automáticas** - El sistema notifica automáticamente cuando:
   - Alguien usa tu código
   - Un referido paga
   - Ganas una semana gratis

4. **Retiros manuales** - Los retiros requieren aprobación del admin por seguridad

5. **Datos persistentes** - Todo se guarda en `data/referrals.json`

---

## PROXIMOS PASOS

1. Agregar los imports en `main.py`
2. Inicializar los objetos al arrancar el bot
3. Registrar los handlers de comandos
4. Reemplazar el procesamiento de pagos actual con `payment_processor.process_payment()`
5. ¡Probar con usuarios reales!

---

## SOPORTE

Si tienes problemas:

1. Ejecuta el test: `python test_referrals_simple.py`
2. Revisa los logs
3. Verifica `data/referrals.json`
4. Lee la documentación completa en `SISTEMA_REFERIDOS_README.md`

---

**Sistema creado por**: GitHub Copilot  
**Probado**: 2024  
**Estado**: LISTO PARA PRODUCCION ✓
