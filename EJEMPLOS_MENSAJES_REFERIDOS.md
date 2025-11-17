# SISTEMA DE REFERIDOS - EJEMPLOS DE MENSAJES

Este documento muestra cómo se verán los mensajes del bot en Telegram.

---

## 1. COMANDO /start (Usuario Nuevo)

**Usuario envía**: `/start`

**Bot responde**:
```
Bienvenido al Bot de Value Bets, Juan!

Te has registrado exitosamente!

TU CODIGO DE REFERIDO: 2A62C397B14F
Tu enlace: https://t.me/Valueapuestasbot?start=2A62C397B14F

Comparte tu enlace y gana:
- $5 USD por cada amigo que pague Premium
- 1 semana gratis cada 3 amigos que paguen

COMANDOS DISPONIBLES:
/referidos - Ver tus estadísticas
/canjear - Canjear semana gratis
/retirar [monto] - Solicitar retiro
/premium - Suscribirse a Premium
/help - Ayuda completa

[Botones: Ver mis referidos | Suscribirse Premium]
[Botón: Compartir mi enlace]
```

---

## 2. COMANDO /start con Código de Referido

**Usuario envía**: `/start 2A62C397B14F`

**Bot responde**:
```
Bienvenido al Bot de Value Bets, María!

Te has registrado exitosamente usando un código de referido!
Tu amigo recibirá una recompensa cuando te suscribas a Premium.

TU CODIGO DE REFERIDO: 8F3D5B2A1C7E
Tu enlace: https://t.me/Valueapuestasbot?start=8F3D5B2A1C7E

Comparte tu enlace y gana:
- $5 USD por cada amigo que pague Premium
- 1 semana gratis cada 3 amigos que paguen

COMANDOS DISPONIBLES:
/referidos - Ver tus estadísticas
/canjear - Canjear semana gratis
/retirar [monto] - Solicitar retiro
/premium - Suscribirse a Premium
/help - Ayuda completa

[Botones: Ver mis referidos | Suscribirse Premium]
[Botón: Compartir mi enlace]
```

**Bot notifica al referrer (Juan)**:
```
NUEVO REFERIDO!

María se registró usando tu código.
Cuando se suscriba a Premium, ganarás $5 USD!

Total referidos: 1
Han pagado: 0
```

---

## 3. COMANDO /referidos (Ver Estadísticas)

**Usuario envía**: `/referidos`

**Bot responde**:
```
TUS ESTADISTICAS DE REFERIDOS
==================================================

Tu código de referido: 2A62C397B14F
Tu enlace: https://t.me/Valueapuestasbot?start=2A62C397B14F

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

[Botón: Compartir mi enlace]
[Botones: Canjear semana gratis | Solicitar retiro]
```

---

## 4. PAGO PREMIUM DE REFERIDO

Cuando María (referida) paga Premium:

**Bot notifica a Juan (referrer)**:
```
FELICIDADES! Ganaste una recompensa!

Uno de tus referidos pagó Premium y ganaste $5.00 USD!

Tu saldo actual: $5.00
Referidos que pagaron: 1

Usa /referidos para ver tus estadísticas.
Usa /retirar [monto] para solicitar retiro.
```

**Bot notifica a María (quien pagó)**:
```
PAGO EXITOSO!

Tu suscripción Premium ha sido activada por 1 semana(s).

Válida hasta: 2024-12-21 15:30 UTC

Ahora recibirás hasta 5 alertas diarias de máxima calidad con:
- Análisis profesional con Kelly Criterion
- Pronósticos con IA y datos en tiempo real
- Seguimiento de resultados y ROI
- Soporte prioritario

Recuerda compartir tu código de referido y ganar recompensas!
Usa /referidos para ver tu enlace.
```

---

## 5. SEMANA GRATIS GANADA

Cuando Juan completa 3 referidos que pagaron:

**Bot notifica a Juan**:
```
FELICIDADES! Ganaste una recompensa!

Uno de tus referidos pagó Premium y ganaste $5.00 USD!

Tu saldo actual: $15.00
Referidos que pagaron: 3

BONUS! También ganaste 1 semana Premium GRATIS!
Total semanas gratis: 1
Usa /canjear para activarla.

Usa /referidos para ver tus estadísticas.
Usa /retirar [monto] para solicitar retiro.
```

---

## 6. COMANDO /canjear (Canjear Semana Gratis)

**Usuario envía**: `/canjear`

**Bot responde con éxito**:
```
Semana Premium gratis activada! Te quedan 0 disponibles

Tu suscripción Premium ha sido extendida por 7 días!
```

**Bot responde sin semanas disponibles**:
```
No tienes semanas gratis disponibles

Invita 3 amigos que paguen Premium para ganar 1 semana gratis!
Usa /referidos para ver cuántos te faltan.
```

---

## 7. COMANDO /retirar (Solicitar Retiro)

**Usuario envía**: `/retirar 25.50`

**Bot responde con éxito**:
```
Solicitud de retiro de $25.50 registrada. Contacta al admin para procesar.

El administrador procesará tu solicitud en las próximas 24-48 horas.
Métodos de pago: PayPal, Transferencia, Criptomonedas.
```

**Bot responde con saldo insuficiente**:
```
Saldo insuficiente (disponible: $15.00)

Invita más amigos para aumentar tu saldo!
Cada amigo que paga Premium te da $5.00.
```

**Bot responde con monto muy bajo**:
```
El monto mínimo de retiro es $5.00 USD
```

**Bot notifica al admin**:
```
SOLICITUD DE RETIRO

Usuario: 123456789
Monto: $25.50 USD
Fecha: 2024-12-14 15:30:45

Usa /aprobar_retiro 123456789 25.50 para aprobar
```

---

## 8. COMANDO /aprobar_retiro (Solo Admin)

**Admin envía**: `/aprobar_retiro 123456789 25.50`

**Bot responde al admin**:
```
RETIRO APROBADO

Retiro de $25.50 procesado exitosamente
```

**Bot notifica al usuario**:
```
Tu retiro de $25.50 ha sido aprobado y procesado!

El pago será enviado a tu cuenta en las próximas horas.
```

---

## 9. COMANDO /reporte_referidos (Solo Admin)

**Admin envía**: `/reporte_referidos`

**Bot responde**:
```
======================================================================
REPORTE DEL SISTEMA DE REFERIDOS
======================================================================

ESTADISTICAS GENERALES:
  Total usuarios: 150
  Total referidos: 420
  Referidos pagos: 180
  Tasa conversión: 42.9%

FINANZAS:
  Comisiones totales: $900.00
  Saldo pendiente: $450.00
  Comisiones pagadas: $450.00

TOP 5 REFERRERS:
  #1: User 12345678... - 25 pagos, $125.00 ganado
  #2: User 87654321... - 18 pagos, $90.00 ganado
  #3: User 55443322... - 15 pagos, $75.00 ganado
  #4: User 99887766... - 12 pagos, $60.00 ganado
  #5: User 11223344... - 10 pagos, $50.00 ganado

======================================================================
```

---

## 10. COMANDO /detectar_fraude (Solo Admin)

**Admin envía**: `/detectar_fraude 123456789`

**Bot responde con usuario normal**:
```
ANALISIS DE FRAUDE

Usuario: 123456789
Nivel de riesgo: SAFE
Score: 0/10

Total referidos: 5
Referidos pagos: 3
Total ganado: $15.00

No se detectaron factores de riesgo.
```

**Bot responde con usuario sospechoso**:
```
ANALISIS DE FRAUDE

Usuario: 987654321
Nivel de riesgo: HIGH
Score: 8/10

Total referidos: 20
Referidos pagos: 18
Total ganado: $90.00

FACTORES DE RIESGO:
- Muchos referidos en poco tiempo
- Tasa de conversión anormalmente alta
- Todos los pagos en el mismo día
```

---

## COMPARTIR ENLACE EN REDES SOCIALES

**Mensaje sugerido para el usuario**:
```
🎯 Únete al mejor bot de apuestas de valor!

✅ Pronósticos profesionales con IA
✅ Análisis con Kelly Criterion
✅ Hasta 5 alertas diarias de alta calidad
✅ ROI verificado y tracking completo

💰 Suscripción Premium: $50/semana

👉 Únete usando mi enlace:
https://t.me/Valueapuestasbot?start=2A62C397B14F

Cuando te suscribas, ¡yo también gano una recompensa!
```

---

## EXPERIENCIA COMPLETA DE USUARIO

### Semana 1
- Juan se registra → Recibe código 2A62C397B14F
- Comparte con 5 amigos
- 2 amigos se registran usando su código
- Juan ve en /referidos: "Total invitados: 2, Pagaron: 0"

### Semana 2
- 1 amigo paga Premium ($50)
- Juan recibe notificación: "¡Ganaste $5.00!"
- Juan ve en /referidos: "Saldo actual: $5.00, Pagaron: 1"

### Semana 3
- 2 amigos más pagan Premium
- Juan recibe 2 notificaciones de $5.00 cada una
- Al 3er pago, recibe BONUS: "¡1 semana Premium gratis!"
- Juan ve en /referidos: "Saldo: $15.00, Semanas gratis: 1"

### Semana 4
- Juan usa /canjear → 7 días de Premium gratis activados
- Juan invita 2 amigos más
- Total: 5 invitados, 3 pagos, $15.00 saldo

### Semana 5
- Juan usa /retirar 15.00
- Admin aprueba en 24h
- Juan recibe $15 por PayPal
- Juan sigue invitando más amigos...

---

**Este es el flujo completo que experimentarán tus usuarios!**

El sistema está diseñado para ser:
- ✅ Fácil de entender
- ✅ Motivador (recompensas claras)
- ✅ Transparente (estadísticas visibles)
- ✅ Justo (comisiones automáticas)
- ✅ Seguro (anti-fraude integrado)
