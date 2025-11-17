# 🚀 Configuración de Supabase para Value Bets Bot

## Paso 1: Crear proyecto en Supabase (2 minutos)

1. Ve a https://supabase.com
2. Inicia sesión o crea cuenta (gratis)
3. Click en "New Project"
4. Completa:
   - **Name**: `valuebet-bot`
   - **Database Password**: Crea una contraseña segura (guárdala)
   - **Region**: Elige la más cercana (ej: South America - São Paulo)
5. Click "Create new project" (tarda ~1 minuto)

## Paso 2: Obtener credenciales (1 minuto)

Una vez creado el proyecto:

1. En el menú izquierdo, click en **Settings** (⚙️)
2. Click en **Database**
3. Scroll hasta **Connection string**
4. Selecciona **URI** 
5. Copia la cadena completa que se ve así:
   ```
   postgresql://postgres.xxxxx:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
   ```
6. Reemplaza `[YOUR-PASSWORD]` con la contraseña que creaste

## Paso 3: Actualizar .env (30 segundos)

Abre `C:\BotValueBets\.env` y agrega al final:

```bash
# ==============================================================================
# SUPABASE CONFIGURATION
# ==============================================================================
DATABASE_URL=postgresql://postgres.xxxxx:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

**Ejemplo real:**
```bash
DATABASE_URL=postgresql://postgres.abcdefgh123:MiPassword123!@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

## Paso 4: Ejecutar migración (2 minutos)

Abre PowerShell en `C:\BotValueBets` y ejecuta:

```powershell
python scripts/migrate_to_supabase.py
```

Deberías ver:
```
🚀 MIGRACIÓN SQLITE → SUPABASE
🔌 Conectando a SQLite...
🔌 Conectando a Supabase...
📋 Creando tablas en Supabase...
✅ Tablas creadas en Supabase
📦 Migrando datos...
✅ Tabla matches: X/X registros migrados
✅ Tabla predictions: 1/1 registros migrados
✅ Migración completada exitosamente!
```

## Paso 5: Actualizar imports en el bot (1 minuto)

El bot necesita usar la nueva versión. Ejecuta:

```powershell
# Hacer backup de la versión SQLite
Move-Item data/historical_db.py data/historical_db_sqlite_backup.py

# Usar versión Supabase
Move-Item data/historical_db_supabase.py data/historical_db.py
```

## Paso 6: Reiniciar bot (30 segundos)

```powershell
# Detener bots actuales
Get-Process python | Stop-Process -Force

# Iniciar con Supabase
Start-Process python -ArgumentList "main.py" -WindowStyle Hidden
```

## ✅ Verificación

Para verificar que todo funciona:

```powershell
python -c "from data.historical_db import historical_db; perf = historical_db.get_bot_performance(30); print(f'Total predicciones: {perf[\"total_predictions\"]}'); print('✅ Conectado a Supabase!')"
```

## 🎯 Ventajas de Supabase

✅ **Acceso desde cualquier lugar** - No depende de tu PC
✅ **Backups automáticos** - Nunca pierdas datos
✅ **Dashboard web** - Ve tus datos en https://supabase.com
✅ **Escalabilidad** - Soporta millones de registros
✅ **Gratis** - 500MB, más que suficiente

## 🔍 Ver datos en Supabase

1. Ve a https://supabase.com
2. Abre tu proyecto "valuebet-bot"
3. Click en **Table Editor** (📊)
4. Selecciona tabla: `predictions`, `matches`, `injuries`, etc.
5. Ve todos tus datos en tiempo real

## 🆘 Solución de problemas

**Error: "could not connect to server"**
- Verifica que DATABASE_URL esté correcto en .env
- Asegúrate de haber reemplazado [YOUR-PASSWORD]

**Error: "psycopg2 not found"**
```powershell
python -m pip install psycopg2-binary
```

**Error: "no module named historical_db"**
- Verifica que moviste historical_db_supabase.py → historical_db.py

**Quiero volver a SQLite:**
```powershell
Move-Item data/historical_db.py data/historical_db_supabase_backup.py
Move-Item data/historical_db_sqlite_backup.py data/historical_db.py
```

## 📝 Notas

- El archivo `data/historical.db` (SQLite) se conserva como backup
- Puedes eliminar SQLite después de verificar que Supabase funciona
- La migración es reversible (backup preservado)
- Costo: $0/mes con límite de 500MB (suficiente para años)
