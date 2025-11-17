"""
Gestión del estado de alertas (límite diario).
Reinicio a las 6 AM hora de América (Eastern Time).
"""
import json
import os
from datetime import datetime, timedelta, timezone


class AlertsState:
    """Rastrea cuántas alertas se han enviado hoy."""
    
    def __init__(self, filepath: str, daily_limit: int = 5, reset_hour: int = 6):
        self.filepath = filepath
        self.daily_limit = daily_limit
        self.reset_hour = reset_hour  # Hora de reinicio (6 AM por defecto)
        self.state = self._load_state()
    
    def _load_state(self) -> dict:
        """Carga el estado desde el archivo JSON."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error al cargar estado: {e}")
        return {"date": "", "count": 0}
    
    def _save_state(self):
        """Guarda el estado en el archivo JSON."""
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2)
    
    def _get_current_cycle(self) -> str:
        """Obtiene el ciclo actual (fecha-hora de reinicio)."""
        # Usar UTC-5 (aproximación de hora de América)
        now = datetime.now(timezone.utc) - timedelta(hours=5)
        
        # Si es antes de las 6 AM, usar el ciclo del día anterior
        if now.hour < self.reset_hour:
            cycle_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            cycle_date = now.strftime("%Y-%m-%d")
        
        return f"{cycle_date}-{self.reset_hour:02d}h"
    
    def _check_reset(self):
        """Reinicia el contador si es un nuevo ciclo (después de las 6 AM)."""
        current_cycle = self._get_current_cycle()
        if self.state.get("date") != current_cycle:
            self.state = {"date": current_cycle, "count": 0}
            self._save_state()
            print(f"🔄 Contador de alertas reiniciado. Nuevo ciclo: {current_cycle}")
    
    def can_send(self) -> bool:
        """Verifica si se pueden enviar más alertas hoy."""
        self._check_reset()
        return self.state["count"] < self.daily_limit
    
    def record_send(self):
        """Registra el envío de una alerta."""
        self._check_reset()
        self.state["count"] += 1
        self._save_state()
    
    def get_remaining(self) -> int:
        """Retorna cuántas alertas quedan disponibles hoy."""
        self._check_reset()
        return max(0, self.daily_limit - self.state["count"])