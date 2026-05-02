"""
Reactive observer pattern for character stats.
Callback dispatch on field mutation.

Usage:
    personaje = Personaje({"vida": 10, "pociones": 5})
    personaje.observe("pociones", lambda num: actualizar_ui(num))
    personaje.activo = True  # Activate after UI init
    personaje["pociones"] = 6  # Triggers callback automatically
"""


class Personaje(dict):
    """Dict that emits callbacks when values change.
    
    Inherits dict—fully compatible with standard dict API.
    Register watchers via observe(field, callback).
    Callbacks fire when observed fields mutate (if activo=True).
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._watchers = {}  # {field: callable}
        self.activo = False
    
    def observe(self, field, callback):
        """Register callback for field mutations.
        
        Args:
            field: field name to observe (e.g. "pociones")
            callback: invoked with new value on change
        """
        self._watchers[field] = callback
    
    def __setitem__(self, key, value):
        """Override: fire callback if value changed and observed."""
        if self.get(key) != value:
            super().__setitem__(key, value)
            if self.activo and key in self._watchers:
                self._watchers[key](value)
