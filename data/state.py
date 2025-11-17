"""
Gestión del estado de alertas (límite diario).
"""
import json
import os
from datetime import datetime


class AlertsState:
    """Rastrea cuántas alertas se han enviado hoy."""
    
    def __init__(self, filepath: str, daily_limit: int = 5):
        self.filepath = filepath
        self.daily_limit = daily_limit
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
    
    def _check_reset(self):
        """Reinicia el contador si es un nuevo día."""
        today = datetime.now().strftime("%Y-%m-%d")
        if self.state.get("date") != today:
            self.state = {"date": today, "count": 0}
            self._save_state()
    
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
