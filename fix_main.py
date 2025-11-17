"""Script para corregir main.py"""
import re

# Leer main.py
with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Corregir validación de API_KEY para permitir funcionamiento sin ella
content = content.replace(
    '        if not API_KEY or not BOT_TOKEN:\n'
    '            logger.error(" Missing API_KEY or BOT_TOKEN in environment")\n'
    '            return',
    
    '        # Verificar BOT_TOKEN (requerido)\n'
    '        if not BOT_TOKEN:\n'
    '            logger.error("Missing BOT_TOKEN in environment - cannot send alerts")\n'
    '            return\n'
    '        \n'
    '        # API_KEY es opcional (se usarán datos de muestra si no está)\n'
    '        if not API_KEY:\n'
    '            logger.warning("No API_KEY - using sample data")'
)

# 2. Asegurar que no quedan emojis
content = re.sub(r'[^\x00-\x7F]+', '', content)

# Guardar
with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("main.py corregido exitosamente")
