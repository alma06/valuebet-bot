# Sistema de Referidos - Bot Value Bets

## 🎯 Descripción General

Sistema completo de referidos que permite a los usuarios ganar semanas de premium gratis invitando amigos.

## ✨ Características Principales

- **Códigos únicos**: Cada usuario tiene un código de referido de 8 caracteres
- **Links automáticos**: `t.me/tu_bot?start=ref_CODIGO`
- **Recompensas**: 5 referidos = 1 semana premium gratis
- **Sin límites**: Usuarios pueden ganar infinitas semanas
- **Automático**: Todo funciona sin intervención manual

## 🛠️ Implementación Técnica

### Estructura de Datos (User class)

```python
# Nuevos campos en User
referral_code: str          # Código único (ej: "A7K9X2M1")
referrer_id: str           # ID de quien me refirió
referred_users: List[str]  # Lista de IDs que he referido
premium_weeks_earned: int  # Semanas ganadas por referidos
premium_expires_at: str    # Fecha de expiración ISO
is_permanent_premium: bool # Distinguir premium permanente vs temporal
```

### Comandos de Usuario

#### `/referir`
- Genera link único del usuario
- Muestra progreso actual (X/5 referidos)
- Explica cómo funciona el sistema

#### `/mis_referidos`
- Estadísticas completas
- Total de referidos
- Semanas ganadas
- Tiempo premium restante
- Progreso para próxima recompensa

#### `/start ref_CODIGO`
- Procesa nuevos referidos automáticamente
- Verifica que no sea auto-referido
- Actualiza contadores del referidor
- Otorga semana premium si alcanza 5 múltiplos

### Sistema de Notificaciones

#### 🎉 Recompensa Ganada
Se envía cuando un usuario completa 5 referidos:
```
🎉 ¡FELICIDADES! 🎉
👥 ¡Nuevo referido registrado!
🎁 RECOMPENSA DESBLOQUEADA:
⭐ +1 SEMANA PREMIUM GRATIS
```

#### ⚠️ Premium por Expirar
Se envía 3 días antes de que expire:
```
⚠️ ¡POCOS DÍAS!
💎 Tu premium expira en X días
🔄 RENUEVA GRATIS: Invita más amigos
```

## 🔄 Flujo de Trabajo

### 1. Usuario Nuevo se Registra
1. Usuario A comparte: `t.me/bot?start=ref_A7K9X2M1`
2. Usuario B hace clic y envía `/start ref_A7K9X2M1`
3. Sistema detecta código válido
4. Usuario B se registra con `referrer_id = Usuario A`
5. Usuario A suma +1 en `referred_users`

### 2. Verificación de Recompensa
1. Si `len(referred_users) % 5 == 0` → Usuario A gana semana
2. Sistema calcula nueva fecha de expiración
3. `premium_expires_at = hoy + 7 días`
4. `premium_weeks_earned += 1`
5. Envía notificación de recompensa

### 3. Premium Temporal vs Permanente
- **Temporal**: Usuarios con semanas ganadas por referidos
- **Permanente**: Usuarios con suscripción pagada
- **Verificación**: `is_premium_active()` considera ambos tipos

## 📋 Configuración

### Variables de Entorno (.env)
```bash
# Referidos necesarios para 1 semana premium
REFERRALS_FOR_PREMIUM_WEEK=5
```

### Archivos Modificados
- `data/users.py` - Estructura y lógica de referidos
- `commands/user_commands.py` - Comandos `/referir` y `/mis_referidos`  
- `main.py` - Notificaciones automáticas
- `notifier/referral_notifications.py` - Mensajes de notificación

## 🧪 Testing

### Crear Usuario de Prueba
```python
# En main.py - para testing
users_manager = get_users_manager()
test_user = users_manager.get_user("123456789")
print(f"Código: {test_user.referral_code}")
```

### Simular Referido
```python
# Simular que alguien usa el código
new_user = users_manager.get_user("987654321", referral_code="A7K9X2M1")
```

### Verificar Estado
```python
stats = users_manager.get_referral_stats("123456789")
print(f"Referidos: {stats['total_referidos']}")
print(f"Semanas: {stats['semanas_ganadas']}")
```

## 🚀 Uso en Producción

1. **Actualizar username del bot**:
   ```python
   # En handle_referir_command()
   bot_username = "tu_bot_real"  # Cambiar por el username real
   ```

2. **Configurar notificaciones**:
   - Las notificaciones se envían automáticamente cada ciclo
   - Se verifican expirations cada 3 días
   - Se procesan recompensas inmediatamente

3. **Monitorear logs**:
   ```
   🎉 Referral reward sent to 123456789
   ⚠️ Premium expiry warning sent to 987654321
   ```

## 📊 Métricas Disponibles

- Total usuarios con referidos activos
- Promedio de referidos por usuario
- Semanas premium otorgadas
- Tasa de conversión de referidos
- Usuarios con premium temporal vs permanente

## 🛡️ Validaciones Implementadas

- ✅ No auto-referirse (mismo chat_id)
- ✅ Códigos únicos de 8 caracteres
- ✅ Verificación de códigos válidos
- ✅ Manejo de premium expirado
- ✅ Persistencia en JSON
- ✅ Notificaciones no duplicadas

El sistema está completamente funcional y listo para uso en producción! 🎉