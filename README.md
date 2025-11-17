# Value Bets Telegram Bot

Bot de Telegram para detectar value bets en tiempo real con análisis de probabilidades mejorado.

## Características

- 🎯 Detección automática de value bets en 33 deportes
- 📊 Sistema de verificación de resultados automático
- 💰 Tracking de ROI y accuracy en tiempo real
- 🏥 Análisis de lesiones de equipos (NBA)
- 📈 Base de datos en Supabase (cloud)
- 👥 Sistema de referidos
- 🔔 Alertas automáticas por Telegram

## Stack Técnico

- Python 3.11+
- python-telegram-bot
- Supabase (PostgreSQL)
- The Odds API
- BeautifulSoup4 (scraping)

## Despliegue en Render

Este bot está configurado para ejecutarse en Render 24/7.

### Variables de entorno requeridas:

```
BOT_TOKEN=tu_token_de_telegram
CHAT_ID=tu_chat_id
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu_key_anon
CHECK_INTERVAL_MIN=60
MIN_ODD=1.5
MAX_ODD=2.5
MIN_PROBABILITY=55
```

## Comandos del Bot

- `/start` - Iniciar bot y registrarse
- `/premium` - Ver plan premium
- `/referidos` - Ver tus referidos
- `/stats` - Ver estadísticas de predicciones
- `/canjear` - Canjear semanas gratis
- `/retirar` - Retirar comisiones

## Estadísticas Actuales

- Accuracy: 100%
- ROI: +115%
- Profit: +$28.75

## Autor

Bot desarrollado para análisis profesional de value bets deportivas.
