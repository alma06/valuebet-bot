# 🚀 GUÍA DE DESPLIEGUE EN RENDER

## ¿Por qué Render?

✅ **Gratis 24/7** - 750 horas/mes (suficiente para 1 bot)
✅ **No requiere tarjeta** - Plan gratuito completo
✅ **Auto-deploy** - Se actualiza solo desde GitHub
✅ **Logs en tiempo real** - Ve qué está pasando
✅ **Más estable que Railway** - Mejor uptime

---

## Paso 1: Preparar GitHub (5 minutos)

### 1.1 Crear repositorio en GitHub

1. Ve a https://github.com/new
2. Nombre: `valuebet-bot` (o el que quieras)
3. **Privado** (recomendado para proteger tokens)
4. Click "Create repository"

### 1.2 Subir código desde tu PC

Abre PowerShell en `C:\BotValueBets`:

```powershell
# Inicializar Git
git init

# Agregar archivos
git add .

# Hacer commit
git commit -m "Initial commit - Value Bets Bot"

# Conectar con GitHub (reemplaza TU_USUARIO y TU_REPO)
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git

# Subir código
git branch -M main
git push -u origin main
```

**Nota:** Si no tienes Git instalado:
```powershell
winget install --id Git.Git
```

---

## Paso 2: Crear cuenta en Render (2 minutos)

1. Ve a https://render.com
2. Click en **"Get Started"**
3. Sign up con GitHub (más fácil)
4. Autoriza Render a acceder a tus repos

---

## Paso 3: Crear Web Service en Render (5 minutos)

### 3.1 Nuevo servicio

1. Click en **"New +"** → **"Web Service"**
2. Conecta tu repositorio `valuebet-bot`
3. Si es privado, autoriza acceso

### 3.2 Configuración del servicio

**Configuración básica:**
- **Name:** `valuebet-bot`
- **Region:** Oregon (US West) - más cercano a Supabase
- **Branch:** `main`
- **Runtime:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python main.py`

**Plan:**
- Selecciona **"Free"** ($0/mes)
- ⚠️ Se duerme después de 15 min de inactividad
- Para mantenerlo despierto 24/7, ver **Paso 5**

### 3.3 Variables de entorno

Click en **"Advanced"** → **"Add Environment Variable"**

Agrega estas variables (una por una):

```
BOT_TOKEN = 8434362952:AAHlSy0-xNNpsxuWF2Db92V8FPLawW26tMI
CHAT_ID = 5901833301
SUPABASE_URL = https://ihdllnlbfcwrbftjzrjz.supabase.co
SUPABASE_KEY = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImloZGxsbmxiZmN3cmJmdGp6cmp6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMzOTQyODcsImV4cCI6MjA3ODk3MDI4N30.yUUBm4vfxVuAfILv_Lku9LZU62TIDA5isXo96ibFgdY
CHECK_INTERVAL_MIN = 60
MIN_ODD = 1.5
MAX_ODD = 2.5
MIN_PROBABILITY = 55
ALERTS_FREE = 1
ALERTS_PREMIUM = 5
DEFAULT_BANKROLL = 1000.0
STAKE_METHOD = fixed_percentage
FIXED_PERCENTAGE = 2.0
SPORTS = basketball_nba,basketball_euroleague,soccer_epl,soccer_spain_la_liga,americanfootball_nfl,icehockey_nhl,baseball_mlb
```

### 3.4 Desplegar

1. Click en **"Create Web Service"**
2. Render comenzará a desplegar (tarda 2-3 minutos)
3. Verás logs en tiempo real

---

## Paso 4: Verificar que funciona (2 minutos)

### 4.1 Ver logs

En el dashboard de Render:
- Pestaña **"Logs"**
- Deberías ver: "Bot iniciado correctamente!" o "Conectado a Supabase"

### 4.2 Probar bot en Telegram

1. Abre Telegram
2. Busca tu bot: `@Valueapuestasbot`
3. Envía `/start`
4. Deberías recibir respuesta

---

## Paso 5: Mantener bot despierto 24/7 (IMPORTANTE)

El plan gratuito de Render **se duerme después de 15 minutos** sin actividad.

### Opción A: UptimeRobot (GRATIS y recomendado)

1. Ve a https://uptimerobot.com (gratis, sin tarjeta)
2. Crear cuenta
3. Add New Monitor:
   - **Monitor Type:** HTTP(s)
   - **Friendly Name:** ValueBet Bot
   - **URL:** La URL de tu servicio en Render (algo como `https://valuebet-bot.onrender.com`)
   - **Monitoring Interval:** 5 minutes
4. Click "Create Monitor"

✅ **Resultado:** El bot estará despierto 24/7 gratis

### Opción B: Cron-job.org (alternativa)

1. Ve a https://cron-job.org
2. Crear cuenta gratis
3. Create cronjob:
   - **Title:** Keep ValueBet Alive
   - **URL:** Tu URL de Render
   - **Schedule:** Every 5 minutes
4. Save

### Opción C: Upgrade a Render Paid ($7/mes)

Si prefieres pagar, el plan Starter ($7/mes) mantiene el bot despierto 24/7 automáticamente.

---

## Paso 6: Actualizar el bot (cuando hagas cambios)

```powershell
# Hacer cambios en tu código local
# Luego:

git add .
git commit -m "Descripción del cambio"
git push
```

✅ **Render detecta el push y redespliega automáticamente**

---

## Problemas Comunes

### ❌ "Application failed to respond"

**Solución:**
- El bot está funcionando, es normal
- Render espera una web app con puerto HTTP
- Como es un bot de Telegram, no responde a HTTP
- Ignora este error, verifica los logs

### ❌ "ModuleNotFoundError"

**Solución:**
- Falta una librería en `requirements.txt`
- Agrégala y haz push de nuevo

### ❌ Bot no responde en Telegram

**Solución:**
1. Verifica logs en Render
2. Confirma que `BOT_TOKEN` es correcto
3. Revisa que no haya errores de conexión a Supabase

---

## Monitoreo

### Ver estadísticas en tiempo real:

**Supabase Dashboard:**
https://ihdllnlbfcwrbftjzrjz.supabase.co/project/default/editor
- Table Editor → `predictions` (ver accuracy, ROI)
- Table Editor → `injuries` (lesiones actualizadas)

**Render Dashboard:**
https://dashboard.render.com
- Ver logs en tiempo real
- Métricas de CPU/memoria
- Últimos deploys

**Telegram:**
- Envía `/stats` a tu bot
- Verás últimas 7 y 30 días

---

## Costos

- **Render Free:** $0/mes (750 horas)
- **UptimeRobot:** $0/mes
- **Supabase:** $0/mes (500MB)
- **GitHub:** $0/mes (repos privados ilimitados)

**Total: $0/mes para bot 24/7** 🎉

---

## Comandos útiles para Git

```powershell
# Ver status
git status

# Ver cambios
git diff

# Deshacer cambios (antes de commit)
git checkout -- archivo.py

# Ver historial
git log --oneline

# Crear nueva rama
git checkout -b nueva-feature

# Volver a main
git checkout main
```

---

## Siguiente nivel (opcional)

### 1. Agregar API Key de The Odds API

En Render, agregar variable:
```
API_KEY = tu_api_key
```

Descomentar en `.env` o agregar directamente en Render.

### 2. Agregar más deportes

Editar variable `SPORTS` en Render con más ligas.

### 3. Notificaciones por email

Usar SendGrid (100 emails gratis/día) para reportes diarios.

---

## Soporte

Si tienes problemas:
1. Revisa logs en Render
2. Verifica variables de entorno
3. Prueba localmente primero con `python main.py`

---

## Resumen de URLs importantes

- **Render Dashboard:** https://dashboard.render.com
- **GitHub:** https://github.com/TU_USUARIO/TU_REPO
- **Supabase:** https://ihdllnlbfcwrbftjzrjz.supabase.co
- **UptimeRobot:** https://uptimerobot.com
- **Bot Telegram:** https://t.me/Valueapuestasbot

¡Tu bot está listo para funcionar 24/7! 🚀
