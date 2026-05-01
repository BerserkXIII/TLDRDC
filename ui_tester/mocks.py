"""
MOCKS - Global State and Mock Functions for UI Tester
=====================================================

Provides:
    - personaje_global: Reactive character object
    - estado: Global game state
    - Mock functions: narrar, alerta, etc.
    - Weapon/Enemy references: ARMAS_NOMBRES, ENEMIGOS_NOMBRES
"""

import os
import sys

# ═════════════════════════════════════════════════════════════════════
# MODULE SETUP
# ═════════════════════════════════════════════════════════════════════

# Get project root for imports
_tester_dir = os.path.dirname(os.path.abspath(__file__))
_codigo_dir = os.path.dirname(_tester_dir)
_proyecto_root = os.path.dirname(_codigo_dir)
sys.path.insert(0, _proyecto_root)

# Import UI modules (used for rendering)
try:
    from modules.ui_config import COLORES, FORMAS_BTN, RUTAS_IMAGENES_PANELES
    from modules.ui_imagen_manager import imagen_manager
    from modules.ui_estructura import estructura_ui
    from modules.reactive import Personaje
    MODULOS_DISPONIBLES = True
except ImportError as e:
    print(f"[!] Warning: UI modules not available: {e}")
    MODULOS_DISPONIBLES = False

# ═════════════════════════════════════════════════════════════════════
# REACTIVE PERSONAJE (mimics Personaje class from modules)
# ═════════════════════════════════════════════════════════════════════

class MockPersonajeReactivo(dict):
    """
    Character object with observer pattern.
    When a key changes, all registered callbacks are triggered.
    Used to synchronize UI with state changes.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._observers = {}
        self.activo = True
    
    def observe(self, key, callback):
        """Register callback for key changes."""
        if key not in self._observers:
            self._observers[key] = []
        self._observers[key].append(callback)
    
    def __setitem__(self, key, value):
        """Update key and trigger observers."""
        super().__setitem__(key, value)
        if self.activo and key in self._observers:
            for callback in self._observers[key]:
                try:
                    callback(value)
                except Exception as e:
                    print(f"[ERROR] Callback error in '{key}': {e}")

# Create global instance
personaje_global = MockPersonajeReactivo({
    "nombre": "Tester",
    "vida": 15,
    "vida_max": 25,
    "pociones": 6,
    "pociones_max": 10,
    "armadura": 2,
    "armadura_max": 5,
    "fuerza": 5,
    "destreza": 5,
    "armas": {},
    "moscas": 0,
    "brazos": 0,
    "sombra": 0,
    "sangre": 0,
    "nivel": 1,
})

# ═════════════════════════════════════════════════════════════════════
# GLOBAL STATE (mimics estado dict from main game)
# ═════════════════════════════════════════════════════════════════════

estado = {
    "armas_jugador": {},
    "ruta_jugador": [],
    "eventos_superados": 0,        # ★ CONTADOR CRÍTICO: Cuando >= 13 → Carcelero
    "bolsa_eventos": list(range(1, 21)),
    "bolsa_exploracion": list(range(1, 16)),
    "pasos_nivel2": [],
    "pasos_secretos": [],
    "veces_guardado": 0,
    "_c01": 0,
}

# ═════════════════════════════════════════════════════════════════════
# MOCK FUNCTIONS (Narrative output - no operations in tester)
# ═════════════════════════════════════════════════════════════════════

def narrar(texto):
    """Mock: Narrative text (would be displayed in Vista.texto in real game)."""
    pass

def alerta(texto):
    """Mock: Alert message."""
    pass

def preguntar(texto):
    """Mock: Question prompt."""
    pass

def sistema(texto):
    """Mock: System message."""
    pass

def exito(texto):
    """Mock: Success message."""
    pass

def dialogo(texto):
    """Mock: Character dialogue."""
    pass

def susurros_aleatorios():
    """Mock: Random whispers."""
    pass

def pedir_input():
    """Mock: Input request (Phase 2 will use Queue)."""
    return ""

# ═════════════════════════════════════════════════════════════════════
# GLOBAL MESSAGE QUEUE (Inyectado por main.py)
# ═════════════════════════════════════════════════════════════════════

cola_mensajes = None  # Will be injected by main.py
emitir = None          # Will be injected by main.py

def leer_input(prompt, personaje):
    """Mock: Alternative input function."""
    return ""

# ═════════════════════════════════════════════════════════════════════
# WEAPON METADATA (for parser validation)
# ═════════════════════════════════════════════════════════════════════

ARMAS_NOMBRES = [
    "daga", "espada", "martillo", "porra", "maza", "lanza",
    "estoque", "cimitarra", "Mano de Dios", "Hoz de Sangre",
    "Hoja de la Noche", "Hacha Maldita"
]

ARMAS_ABREVIATURAS = {
    "dag": "daga",
    "esp": "espada",
    "mar": "martillo",
    "por": "porra",
    "maz": "maza",
    "lan": "lanza",
    "est": "estoque",
    "cim": "cimitarra",
    "man": "Mano de Dios",
    "hoz": "Hoz de Sangre",
    "hoj": "Hoja de la Noche",
    "hac": "Hacha Maldita",
}

# ═════════════════════════════════════════════════════════════════════
# ENEMY METADATA (for parser validation - Phase 2)
# ═════════════════════════════════════════════════════════════════════

ENEMIGOS_NOMBRES = [
    "Larvas de Sangre",
    "Mosca de Sangre",
    "Maniaco Mutilado",
    "Perturbado",
    "Rabioso",
    "Sombra tenebrosa",
]

ENEMIGOS_ESPECIALES = {
    "Forrix, el Carcelero": {
        "descripcion": "JEFE - Trigger: eventos_superados >= 13",
        "vida": 30,
        "daño": (4, 6),
        "esquiva": 3,
        "armadura": 0,
    },
    # Fabius - 3 FORMAS / VARIANTES
    "Fabius, Amo de la Mazmorra": {
        "descripcion": "JEFE FINAL - Forma Base (sin items especiales)",
        "vida": 30,
        "vida_max": 30,
        "daño": (6, 7),
        "esquiva": 7,
        "armadura": 0,
    },
    "Fabius, Amo de la Mazmorra (Potenciado)": {
        "descripcion": "JEFE FINAL - Forma Media (con Hoz de Sangre)",
        "vida": 45,
        "vida_max": 45,
        "daño": (6, 7),
        "esquiva": 14,
        "armadura": 0,
    },
    "Fabius, Amo de la Mazmorra (Transformado)": {
        "descripcion": "JEFE FINAL - Forma Enojada (con Hoja de la Noche + potencia máx)",
        "vida": 60,
        "vida_max": 60,
        "daño": (8, 9),
        "esquiva": 21,
        "armadura": 0,
    },
    # OTROS JEFES
    "Sanakht, la Sombra Sangrienta": {
        "descripcion": "JEFE - Demonio de la Sangre (del crear_sombra_sangrienta)",
        "vida": 20,
        "vida_max": 20,
        "daño": (6, 7),
        "esquiva": 15,
        "armadura": 0,
    },
    "Ka-Banda, Demonio Sombrio": {
        "descripcion": "JEFE - Demonio Antiguo (del crear_demonio_sombrio)",
        "vida": 50,
        "vida_max": 50,
        "daño": (6, 7),
        "esquiva": 12,
        "armadura": 0,
    },
    "Bel'akhor, Principe Demonio": {
        "descripcion": "JEFE FINAL - Devorador de Almas (del crear_demonio_final)",
        "vida": 150,
        "vida_max": 150,
        "daño": (10, 12),
        "esquiva": 5,
        "armadura": 0,
        "_grant_pw": 1,  # Otorga poder especial al ganar
    },
    "Mano Demoniaca": {
        "descripcion": "JEFE - Creación del Enano (del crear_mano_demoniaca)",
        "vida": 30,
        "vida_max": 30,
        "daño": (8, 9),
        "esquiva": 8,
        "armadura": 0,
    },
}

# ═════════════════════════════════════════════════════════════════════
# IMAGE CACHE (loaded by Vista._cargar_imgs_btns)
# ═════════════════════════════════════════════════════════════════════

_IMG_BTN = {}  # Will be populated by Vista during initialization
