"""
Script para activar usuario como premium permanente
"""
import sys
import os
from pathlib import Path

# Añadir directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.users import get_users_manager

def set_user_premium(chat_id: str):
    """Activa un usuario como premium permanente"""
    manager = get_users_manager()
    user = manager.get_user(chat_id)
    
    if not user:
        print(f"❌ Usuario {chat_id} no encontrado. Creando...")
        user = manager.create_user(chat_id)
    
    # Activar premium permanente
    user.nivel = "premium"
    user.is_permanent_premium = True
    user.premium_expires_at = None  # Nunca expira
    
    # Guardar cambios
    manager.save()
    
    print(f"✅ Usuario {chat_id} activado como PREMIUM PERMANENTE")
    print(f"   - Nivel: {user.nivel}")
    print(f"   - Premium permanente: {user.is_permanent_premium}")
    print(f"   - Alertas máximas: 5/día")
    print(f"   - Bankroll: ${user.bankroll:.2f}")

if __name__ == "__main__":
    # Tu CHAT_ID
    CHAT_ID = "5901833301"
    set_user_premium(CHAT_ID)
