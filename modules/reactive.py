"""
Sistema reactivo ultramínimal para personaje_global.
Dispara callbacks cuando ciertos campos cambian.

Patrón Observer simplificado: dict que emite eventos.
Uso:
    personaje = Personaje({"vida": 10, "pociones": 5})
    personaje.observe("pociones", lambda num: actualizar_ui(num))
    personaje.activo = True  # Activar tras inicializar Vista
    personaje["pociones"] = 6  # Triggeriza callback automáticamente
"""


class Personaje(dict):
    """Dict que emite eventos cuando sus valores cambian.
    
    Extiende dict, por lo que es 100% compatible:
    - personaje["vida"] = 10 → acceso normal
    - personaje.observe("vida", callback) → registra observador
    - personaje.activo = True → activa reactividad
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._watchers = {}  # {field: callable}
        self.activo = False
    
    def observe(self, field, callback):
        """Registra un callback para cuando 'field' cambia.
        
        Args:
            field (str): Nombre del campo a observar (ej: "pociones")
            callback (callable): Función que recibe el nuevo valor
        """
        self._watchers[field] = callback
    
    def __setitem__(self, key, value):
        """Override: dispara callback si el valor cambió y está observado."""
        if self.get(key) != value:
            super().__setitem__(key, value)
            # Solo dispara si:
            # 1. La reactividad está activada
            # 2. Hay un observador registrado para este campo
            if self.activo and key in self._watchers:
                self._watchers[key](value)
