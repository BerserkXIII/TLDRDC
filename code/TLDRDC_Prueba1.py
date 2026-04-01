"""
TLDRDC - The Lost Dire Realm: Dungeon Crawler
===============================================

Game loop, UI orchestration, and game state management for a terminal-based
dungeon crawler with Tkinter GUI. Threading model separates game logic (worker
thread) from UI event loop (main thread) via _Bridge synchronization.

Modules:
    - modules.ui_config: UI constants (colors, shapes, dimensions)
    - modules.ui_imagen_manager: Image loading and caching
    - modules.ui_estructura: UI layout templates
    - modules.events: Event system and narrative content

Architecture:
    Game Logic Thread: Blocking I/O (waits at pedir_input) 
    Main Thread:       Tkinter event loop (never blocks)
    Via _Bridge:       threading.Event allows synchronized communication

See docs/ARQUITECTURA.md for complete threading architecture.
"""

import json
import math
import os
import random
import sys
import threading
import tkinter as tk
from tkinter import font as tkfont
from collections import deque
from enum import Enum

# ==============================================================================
# INITIALIZATION: Module Paths & Dependencies
# ==============================================================================

# Setup sys.path to find local modules. TLDRDC_Prueba1.py is in code/,
# but all modules (ui_config, events, etc) are at project root.
_proyecto_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _proyecto_root)

# Load UI configuration module (colors, button shapes, image paths).
# PIL is optional; without it, only PNG images load natively.
try:
    from modules.ui_config import COLORES, RUTAS_IMAGENES_PANELES
    from modules.ui_imagen_manager import imagen_manager
    from modules.ui_estructura import estructura_ui
    from modules.reactive import Personaje
    MODULOS_DISPONIBLES = True
except ImportError as e:
    print(f"Error: UI modules not found: {e}")
    MODULOS_DISPONIBLES = False

# PIL enables JPEG and RGBA image support. PNG always available via Tkinter.
try:
    from PIL import Image, ImageTk
    PIL_DISPONIBLE = True
except ImportError:
    PIL_DISPONIBLE = False

# Event system with 20 procedurally generated encounter events.
try:
    import modules.events as events_module
    from modules.events import (
        evento_aleatorio, rellenar_bolsa_eventos, obtener_evento_de_bolsa,
        rellenar_bolsa_exploracion, obtener_texto_exploracion_de_bolsa
    )
    MODULOS_EVENTOS_DISPONIBLES = True
except ImportError as e:
    print(f"Warning: Event module not found: {e}")
    MODULOS_EVENTOS_DISPONIBLES = False

# ==============================================================================
# Type Definitions: Enumerations for Type-Safe Game State
# ==============================================================================

class Condicion(Enum):
    """Trigger conditions for automated ability use during combat."""
    SIEMPRE = "siempre"
    VIDA_BAJA = "vida_baja"
    VIDA_MEDIA = "vida_media"


class TipoHabilidad(Enum):
    """Ability classification: active (consumes turn) or passive (modifies roll)."""
    ACTIVA = "activa"
    PASIVA = "pasiva"


class EfectoHabilidad(Enum):
    """Effect types that abilities can apply to alter combat."""
    # Damage & Defense
    SANGRADO = "sangrado"
    DAMAGE_BOOST = "damage_boost"
    STUN = "stun"
    ARMOR_REDUCTION = "armor_reduction"
    HEAL = "heal"
    
    # Special Ability Effects
    RECUPERACION_IMPIA = "recuperacion_impia"
    ACUCHILLAMIENTO = "acuchillamiento"
    ESQUIVA_TEMPORAL = "esquiva_temporal"
    GOLPES_FURIOSOS = "golpes_furiosos"
    FRENSI_DEMONIACO = "frensi_demoniaco"
    DRENAJE_ALMAS = "drenaje_almas"
    ARREBATO_APOCALIPTICO = "arrebato_apocaliptico"
    INYECCION_QUIRURGICA = "inyeccion_quirurgica"
    INCISION_MORTAL = "incision_mortal"
    AZOTAZO_DEMONICO = "azotazo_demonico"
    REDUCIR_ARMADURA = "reducir_armadura"


class Stance(Enum):
    """Player combat stance that modifies defensive behavior."""
    NINGUNO = None
    BLOQUEAR = "bloquear"
    ESQUIVAR = "esquivar"


class Accion(Enum):
    """Available player actions during encounters."""
    ATAQUE = "ataque"
    HUIDA = "huida"
    POCION = "pocion"
    STANCE_BLOQUEAR = "bloquear"
    STANCE_ESQUIVAR = "esquivar"

# ==============================================================================
# Thread Synchronization: Game <-> UI Bridge
# ==============================================================================
# Architecture: Game logic runs in a worker thread and blocks on pedir_input().
# The main thread runs Tkinter event loop (never blocks). _Bridge enables
# synchronized communication between threads via threading.Event().
#
# Flow: Game calls pedir_input() -> blocks until Vista calls _bridge.recibir()
#       -> Vista UI remains responsive to mouse/keyboard in main thread.
#
# See docs/ARQUITECTURA.md#Doble Hilo for detailed threading architecture.

class _Bridge:
    """
    Synchronization channel between game logic thread and Tkinter main thread.
    
    Uses threading.Event to block worker thread until UI delivers user input.
    Tkinter event loop remains free to handle user interactions.
    
    Attributes:
        _evento (threading.Event): Cross-thread signaling mechanism
        _valor (str): Input text passed from Vista to game logic
    """

    def __init__(self):
        """Initialize synchronization primitives."""
        self._evento = threading.Event()
        self._valor = ""

    def esperar(self):
        """
        Block calling thread until input is available.
        
        Worker thread calls this during normal game flow. Blocks until
        Vista calls recibir(). Clears event after unblocking to reset
        for next input cycle.
        
        Returns:
            str: Input text from Vista (user command/response)
        """
        self._evento.wait()
        self._evento.clear()
        return self._valor

    def recibir(self, texto):
        """
        Unblock waiting thread and deliver input.
        
        Called by Vista when user submits text via UI. Sets event flag to
        wake worker thread, which continues from esperar() call.
        
        Args:
            texto (str): User input to pass to game logic
        """
        self._valor = texto
        self._evento.set()


_bridge = _Bridge()


def pedir_input(prompt=""):
    """
    Request player input without blocking UI thread.
    
    Replaces builtin input() throughout game logic. Shows prompt in main
    text area, enables input field, then blocks calling (worker) thread
    until Vista delivers response. Tkinter event loop remains active.
    
    Args:
        prompt (str, optional): Text to display before input field. Defaults to "".
    
    Returns:
        str: Player's input from Vista
    
    Implementation:
        1. Emit prompt to text panel if provided
        2. Signal Vista to enable input field
        3. Block worker thread at _bridge.esperar()
        4. Vista detects Enter, calls _bridge.recibir(text)
        5. Worker thread unblocks and returns input
    """
    if prompt:
        emitir("preguntar", prompt)
    emitir("habilitar_input")
    return _bridge.esperar()


# ==============================================================================
# Message Queue: Model -> View Communication
# ==============================================================================
# Game logic never prints directly. Instead, it emits messages to cola_mensajes
# which Vista consumes and renders according to message type. This decouples
# game logic from presentation layer.
#
# Message Types:
#     "narrar"           : Narrative text in italic gray
#     "alerta"           : Danger/warning in red
#     "exito"            : Achievement/reward in yellow
#     "sistema"          : System events (save/load) in cyan
#     "titulo"           : Section separator with title
#     "separador"        : Horizontal rule
#     "preguntar"        : Player prompt (command request)
#     "dialogo"          : NPC dialogue in white
#     "susurros"         : Whispers in dark red, centered
#     "panel"            : Framed box (endings, intro)
#     "stats"            : Character statistics dict
#     "hud_combate"      : Combat stats (player/enemy HP)
#     "opciones_combate" : Available weapons and potions
#     "menu_principal"   : Game title screen signal
#     "titulo_juego"     : Game title display
#
# Usage: emitir("tipo", contenido) deposits message. Vista retrieves and renders.

cola_mensajes = deque()


def emitir(tipo, contenido=""):
    """
    Deposit message for Vista to consume and render.
    
    All game output flows through this function. Enables decoupling of
    game logic from UI presentation layer. Thread-safe via deque.
    
    Args:
        tipo (str): Message type (see queue documentation above)
        contenido (str or dict, optional): Message payload. Defaults to "".
    """
    cola_mensajes.append({"tipo": tipo, "contenido": contenido})


def panel(texto, titulo="", estilo="red"):
    """
    Emit a framed message panel (shorthand).
    
    Convenience wrapper for common panel emissions (game endings, intro, etc).
    
    Args:
        texto (str): Main panel content
        titulo (str, optional): Panel title. Defaults to "".
        estilo (str, optional): Panel style/color. Defaults to "red".
    """
    emitir("panel", {"texto": texto, "titulo": titulo, "estilo": estilo})


# ==============================================================================
# Global State: Single Mutable Container for Session Data
# ==============================================================================
# All session-mutable variables collected in one dict. No function requires
# 'global' keyword to mutate estado fields. Simplifies debugging and state
# inspection. Initialize with sensible defaults.

estado: dict = {
    "armas_jugador": {},
    "ruta_jugador": [],
    "pasos_nivel2": [],
    "pasos_secretos": [],
    "eventos_superados": 0,
    "veces_guardado": 0,
    "_c01": 0,
    "bolsa_eventos": [],
    "bolsa_exploracion": [],
}

# ==============================================================================
# Debug Logging: Non-Intrusive Performance & Logic Tracing
# ==============================================================================
# Optional logging infrastructure for development. Set DEBUG_MODE = True
# to enable file-based logs without impacting game UI. Logs written to
# adjacent debug folder (/0.7/Documentos Debug Performance).

DEBUG_MODE = False  # Set True to enable debug logging

DEBUG_FOLDER = os.path.expanduser(
    "~/Desktop/codigos/TLDRDC/0.7/Documentos Debug Performance"
)
os.makedirs(DEBUG_FOLDER, exist_ok=True)

LOG_FILE = os.path.join(DEBUG_FOLDER, "debug.log")
PERF_FILE = os.path.join(DEBUG_FOLDER, "performance.log")


def _log_debug(seccion, mensaje):
    """
    Write debug message to log file (if enabled).
    
    Non-intrusive logging: writes to disk, never interferes with real-time
    game UI. Useful for tracing condition evaluation, damage calculations,
    effect application, etc. Disable DEBUG_MODE for production.
    
    Args:
        seccion (str): Log category (e.g., "CONDITION", "DAMAGE", "EFFECT")
        mensaje (str): Message to log
    """
    if not DEBUG_MODE:
        return

    timestamp = "•"
    log_msg = f"[{timestamp}] {seccion}: {mensaje}"

    if LOG_FILE:
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(log_msg + "\n")
        except Exception as e:
            print(f"Error writing log: {e}")
    else:
        print(log_msg)  # Fallback to stdout


# ==============================================================================
# Validation Layer: Data Integrity Checks
# ==============================================================================
# Functions to validate game state consistency. Used during deserialization,
# NPC initialization, combat state transitions, etc. Prevents invalid state
# from propagating through game logic.

def validar_habilidad(habilidad):
    """
    Validate ability structure and values for consistency.
    
    Checks type safety and range constraints. Called during enemy spawning,
    ability loading, stat modification, etc.
    
    Args:
        habilidad (dict): Ability object to validate
    
    Returns:
        tuple: (is_valid: bool, error_message: str)
            Returns (True, "") if valid. Returns (False, message) on error.
    
    Validates:
        - Required fields: nombre, tipo, prob
        - Type constraints: nombre is non-empty str, prob ∈ [0,1], etc
        - Conditional fields: if condicion="vida_baja" → threshold ∈ [0,1]
        - Effect types: efecto must be valid EfectoHabilidad enum
    """
    if not isinstance(habilidad, dict):
        return False, "Ability must be dict"

    # Required fields check
    requeridos = ["nombre", "tipo", "prob"]
    for campo in requeridos:
        if campo not in habilidad:
            return False, f"Missing required field: {campo}"

    # Type validations
    if not isinstance(habilidad["nombre"], str) or not habilidad["nombre"]:
        return False, "nombre: must be non-empty string"
    if habilidad["tipo"] not in ("activa", "pasiva"):
        return False, f"tipo: must be 'activa' or 'pasiva', not '{habilidad['tipo']}'"
    if not isinstance(habilidad["prob"], (int, float)) or not (0 <= habilidad["prob"] <= 1):
        return False, f"prob: must be float ∈ [0,1], not {habilidad['prob']}"

    # Conditional validation: trigger conditions
    condicion = habilidad.get("condicion", "siempre")
    if condicion not in ("siempre", "vida_baja", "vida_media"):
        return False, f"condicion: invalid value '{condicion}'"

    if condicion in ("vida_baja", "vida_media"):
        threshold = habilidad.get("threshold", 0.5)
        if not isinstance(threshold, (int, float)) or not (0 <= threshold <= 1):
            return False, f"threshold: must be float ∈ [0,1], not {threshold}"

    # Effect type validation
    efecto = habilidad.get("efecto")
    efectos_validos = (
        "sangrado", "damage_boost", "stun", "armor_reduction", "heal",
        "drenaje", "recuperacion_impia", "acuchillamiento", "esquiva_temporal",
        "inyeccion_quirurgica", "incision_mortal", "golpes_furiosos",
        "frensi_demoniaco", "azotazo_demonico", "reductor_armadura", "nada"
    )
    if efecto and efecto not in efectos_validos:
        return False, f"efecto: unknown effect '{efecto}'"

    # Numeric parameter validation
    valor = habilidad.get("valor")
    if valor is not None and not isinstance(valor, (int, float)):
        return False, f"valor: must be number, not {type(valor).__name__}"

    return True, ""


def validar_enemigo(enemigo):
    """
    Validate enemy stat consistency.
    
    Ensures enemy objects have valid numeric ranges and required fields.
    Called during NPC initialization, save/load, and combat state setup.
    
    Args:
        enemigo (dict): Enemy object to validate
    
    Returns:
        tuple: (is_valid: bool, error_message: str)
    
    Validates:
        - Required fields: nombre, vida, vida_max, daño, armadura, habilidades
        - Numeric ranges: life ≥ 0, armor ≥ 0, vida ≤ vida_max
        - Damage tuple: [min, max] where min ≥ 0 and max ≥ min
        - Abilities: each is valid via validar_habilidad()
    """
    if not isinstance(enemigo, dict):
        return False, "Enemy must be dict"

    # Required fields
    requeridos = ["nombre", "vida", "vida_max", "daño", "armadura", "habilidades"]
    for campo in requeridos:
        if campo not in enemigo:
            return False, f"Missing required field: {campo}"

    # Numeric range validation
    if enemigo["vida"] < 0:
        return False, f"vida: cannot be negative ({enemigo['vida']})"
    if enemigo["vida"] > enemigo["vida_max"]:
        return False, f"vida: exceeds vida_max ({enemigo['vida']} > {enemigo['vida_max']})"
    if enemigo["vida_max"] <= 0:
        return False, f"vida_max: must be > 0, not {enemigo['vida_max']}"
    if enemigo["armadura"] < 0:
        return False, f"armadura: cannot be negative ({enemigo['armadura']})"

    # Damage range validation
    daño = enemigo["daño"]
    if isinstance(daño, (list, tuple)) and len(daño) == 2:
        if daño[0] < 0 or daño[1] < daño[0]:
            return False, f"daño: invalid range {daño} (must be [min≥0, max≥min])"
    else:
        return False, f"daño: must be [min, max] tuple, not {daño}"

    # Abilities validation
    if not isinstance(enemigo["habilidades"], list):
        return False, "habilidades: must be list"
    for hab in enemigo["habilidades"]:
        valida, msg = validar_habilidad(hab)
        if not valida:
            return False, f"Habilidad '{hab.get('nombre', '?')}' inválida: {msg}"
    
    return True, ""

def validar_personaje(personaje):
    """
    Valida que el personaje tenga stats válidos.
    Retorna (es_valido, mensaje_error).
    """
    if not isinstance(personaje, dict):
        return False, "Personaje debe ser dict"
    
    requeridos = ["vida", "vida_max", "armadura", "fuerza", "destreza", "inteligencia"]
    for campo in requeridos:
        if campo not in personaje:
            return False, f"Falta campo: {campo}"
    
    # Rango checks
    if personaje["vida"] < 0:
        return False, f"vida no puede ser negativa"
    if personaje["vida"] > personaje["vida_max"]:
        return False, f"vida > vida_max"
    if personaje["vida_max"] <= 0:
        return False, f"vida_max debe ser > 0"
    if personaje["armadura"] < 0:
        return False, f"armadura no puede ser negativa"
    
    # Stats deben estar en rango razonable (1-20 típico D&D)
    for stat in ("fuerza", "destreza", "inteligencia"):
        if not (1 <= personaje[stat] <= 20):
            return False, f"{stat} fuera de rango [1, 20]: {personaje[stat]}"
    
    return True, ""

def _verificar_integridad_turno(personaje, enemigo):
    """
    Verifica estado antes de resolver un turno.
    Retorna (es_valido, mensaje_detalle).
    Usado internamente por turno_enemigo/turno_jugador.
    """
    # Ambos deben estar vivos
    if personaje["vida"] <= 0:
        return False, "Personaje KO"
    if enemigo["vida"] <= 0:
        return False, "Enemigo KO"
    
    # _efectos_temporales debe existir en enemigo (verificación defensive)
    if "_efectos_temporales" not in enemigo:
        _log_debug("VALIDATION", f"FIX: {enemigo['nombre']} sin _efectos_temporales, inicializando")
        enemigo["_efectos_temporales"] = {}
    
    # igual para personaje
    if "_efectos_temporales" not in personaje:
        enemigo["_efectos_temporales"] = {}
    
    return True, "OK"

# ================== PERFORMANCE MONITORING (PASO 10) ==================
# Sistema para medir y monitorear performance de funciones clave.
import time
from contextlib import contextmanager

PERF_MODE = True  # Cambiar a True para activar monitoring
PERF_STATS = {
    # Estructura: "funcion": {"llamadas": 0, "tiempo_total": 0.0, "min": float('inf'), "max": 0.0}
}

@contextmanager
def _medir_tiempo(seccion):
    """
    Context manager para medir tiempo de ejecución.
    Uso: with _medir_tiempo("TURNO"):
             # código a medir
    
    Acumula estadísticas en PERF_STATS solo si PERF_MODE=True.
    """
    if not PERF_MODE:
        yield
        return
    
    inicio = time.perf_counter()
    try:
        yield
    finally:
        fin = time.perf_counter()
        duracion = fin - inicio
        
        if seccion not in PERF_STATS:
            PERF_STATS[seccion] = {
                "llamadas": 0,
                "tiempo_total": 0.0,
                "min": float('inf'),
                "max": 0.0
            }
        
        stats = PERF_STATS[seccion]
        stats["llamadas"] += 1
        stats["tiempo_total"] += duracion
        stats["min"] = min(stats["min"], duracion)
        stats["max"] = max(stats["max"], duracion)
        
        # Log si duracion es inusual (> 1 segundo)
        if duracion > 1.0:
            _log_debug("PERF_WARN", f"{seccion}: {duracion:.3f}s (lento)")

def mostrar_estadisticas_perf():
    """
    Imprime estadísticas de performance acumuladas.
    Guarda en performance.log y también muestra en consola.
    """
    if not PERF_STATS:
        mensaje = "Sin datos de performance."
        print(mensaje)
        return mensaje
    
    lineas = ["=== ESTADÍSTICAS DE PERFORMANCE ==="]
    lineas.append("")
    
    for seccion in sorted(PERF_STATS.keys()):
        stats = PERF_STATS[seccion]
        promedio = stats["tiempo_total"] / stats["llamadas"] if stats["llamadas"] > 0 else 0
        
        linea = (f"{seccion:20} | "
                f"Llamadas: {stats['llamadas']:4} | "
                f"Total: {stats['tiempo_total']:7.3f}s | "
                f"Promedio: {promedio*1000:6.2f}ms | "
                f"Min: {stats['min']*1000:6.2f}ms | "
                f"Max: {stats['max']*1000:6.2f}ms")
        lineas.append(linea)
    
    lineas.append("")
    resultado = "\n".join(lineas)
    
    # Escribir en archivo y consola
    print(resultado)
    try:
        with open(PERF_FILE, "w", encoding="utf-8") as f:
            f.write(resultado)
    except Exception as e:
        print(f"Error escribiendo performance.log: {e}")
    
    return resultado

# ================== CONFIGURACIÓN DE SAVE ==================
# El save se guarda en AppData\TLDRDC para que no sea visible junto al ejecutable
CARPETA_SAVE = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "TLDRDC")
os.makedirs(CARPETA_SAVE, exist_ok=True)       # Crea la carpeta si no existe
RUTA_SAVE = os.path.join(CARPETA_SAVE, "guardado.json")

# ================== FUNCIONES DE GUARDADO/CARGA ==================
def guardar_partida(personaje):
    """
    Guarda la partida en AppData\\TLDRDC\\guardado.json de forma segura.
    Usa JSON en vez de pickle para evitar ejecución de código arbitrario
    si el archivo fuera manipulado.
    """
    try:
        tmp_path = os.path.join(CARPETA_SAVE, "guardado_tmp.json")
        datos = {
            "personaje": personaje,
            "armas_jugador": estado["armas_jugador"],
            "ruta_jugador": estado["ruta_jugador"],
            "eventos_superados": estado["eventos_superados"],
            "bolsa_eventos": estado["bolsa_eventos"],
            "bolsa_exploracion": estado["bolsa_exploracion"],
            "pasos_nivel2": estado["pasos_nivel2"],
            "pasos_secretos": estado["pasos_secretos"],
            "veces_guardado": estado["veces_guardado"],
            "_c01": estado["_c01"],
        }
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, RUTA_SAVE)
    except Exception as e:
        alerta(f"✘ Error al guardar: {e}")


def cargar_partida():
    """
    Carga la partida desde AppData\\TLDRDC\\guardado.json.
    Devuelve el personaje y restaura las variables globales.
    """
    if not os.path.exists(RUTA_SAVE):
        alerta("✘ No hay partida guardada.")
        return None
    try:
        with open(RUTA_SAVE, "r", encoding="utf-8") as f:
            data = json.load(f)
        estado["armas_jugador"] = data.get("armas_jugador", {})
        estado["ruta_jugador"] = data.get("ruta_jugador", [])
        estado["eventos_superados"] = data.get("eventos_superados", 0)
        # Compatibilidad: si el guardado es antiguo (lista en vez de int), corregir
        if isinstance(estado["eventos_superados"], list):
            estado["eventos_superados"] = 0
        estado["bolsa_eventos"] = data.get("bolsa_eventos", [])
        estado["bolsa_exploracion"] = data.get("bolsa_exploracion", [])
        estado["pasos_nivel2"] = data.get("pasos_nivel2", [])
        estado["pasos_secretos"] = data.get("pasos_secretos", [])
        estado["veces_guardado"] = data.get("veces_guardado", 0)
        estado["_c01"] = data.get("_c01", 0)
        personaje = data.get("personaje", {})
        campos_req = {"nombre", "vida", "fuerza", "destreza", "pociones", "nivel"}
        if not campos_req.issubset(personaje.keys()):
            alerta("✘ El guardado está incompleto o dañado.")
            return None
        
        # CRÍTICO: Sincronizar armas en personaje (se guardan en estado pero no en personaje)
        # Esto asegura que personaje_global.get("armas") tenga los datos correctos al cargar
        personaje["armas"] = data.get("armas_jugador", {})
        
        return personaje
    except json.JSONDecodeError as e:
        alerta(f"✘ El archivo de guardado está corrupto: {e}")
        return None
    except Exception as e:
        alerta(f"✘ Error al cargar: {e}")
        return None


def intentar_guardar(personaje):
    """
    Intenta guardar la partida con riesgo creciente de combate.
    estado["veces_guardado"] sube siempre +1 al inicio, independientemente del resultado:
    cada búsqueda de escondite delata tu posición. Solo guarda si sobrevives sin huir.
    """

    narrar("Buscas un hueco entre las sombras donde refugiarte un momento...")
    narrar("Pero estos pasillos nunca están realmente vacíos. Alguien podría encontrarte.")

    estado["veces_guardado"] += 1                                  # Cada intento consume un escondite
    probabilidad = min(1.0, estado["veces_guardado"] * 0.2)

    if random.random() < probabilidad:
        # --- Combate pre-guardado ---
        alerta("Unos pasos se acercan. No estás solo, te han encontrado.")
        combate(personaje, enemigo_aleatorio())

        if personaje.get("_huyo_combate"):
            alerta("Huiste, pero te buscan, y encontrar refugio ya no es tan seguro...")
            return

        narrar("Acabas con la amenaza. Ahora sí tienes un momento de calma.")

    # --- Guardado efectivo ---
    dialogo("Has conseguido encontrar un lugar tranquilo para descansar.")
    sistema("✔ Consigues guardar con exito.")
    guardar_partida(personaje)


personaje_global = None
# Callback inyectado para sincronizar UI después de cambios en armas durante exploración
_callback_ui_armas = None
vista_global = None  # Referencia a Vista para registro de observadores desde main()

# ================== PROGRESO NIVEL 2 ====================

# Rutas predefinidas del juego
ruta_correcta_nivel2 = ["d", "i", "i", "d", "d", "i"]
ruta_secreta = ["d", "i", "d", "d", "i", "d", "i", "d", "i", "d"]



def rellenar_bolsa_eventos():
    """Rellena la bolsa con todos los eventos disponibles"""
    estado["bolsa_eventos"] = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]
    random.shuffle(estado["bolsa_eventos"])  # Mezclamos para mayor aleatoriedad

def rellenar_bolsa_exploracion():
    """Rellena la bolsa con todos los textos de exploración disponibles"""
    estado["bolsa_exploracion"] = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
    random.shuffle(estado["bolsa_exploracion"])  # Mezclamos para mayor aleatoriedad

def obtener_evento_de_bolsa():
    """Obtiene un evento de la bolsa, rellenándola si está vacía"""
    if not estado["bolsa_eventos"]:  # Si está vacía
        rellenar_bolsa_eventos()
    return estado["bolsa_eventos"].pop()  # Sacamos el último elemento

def obtener_texto_exploracion_de_bolsa():
    """Obtiene un texto de exploración de la bolsa, rellenándola si está vacía"""
    if not estado["bolsa_exploracion"]:  # Si está vacía
        rellenar_bolsa_exploracion()
    return estado["bolsa_exploracion"].pop()  # Sacamos el último elemento
# ================== PERSONAJE ==================

def crear_personaje():
    narrar("\nTe duele la cabeza, pero no es dolor, es una presión aguda en tu cabeza,"
           "como si algo hubiese anidado entre tus pensamientos y reptara tras tus ojos."
           "Te despiertas entumecido, con el frío de la piedra en los huesos, y descubres con horror que no puedes moverte.")
    narrar("Algo te sujeta, unas correas de cuero endurecido y grapas oxidadas que se hunden en tu carne. Bajo tu espalda sientes una losa húmeda; sobre ti, una bóveda que supura gotas oscuras que caen con una cadencia funeraria.")
    narrar("No recuerdas cómo llegaste aquí. No recuerdas dónde estabas. La memoria es una herida cauterizada a la fuerza, una cicatriz sin historia.")
    preguntar("Recuerdas cual era tu nombre?")
    while True:
        nombre_jugador = pedir_input().strip()
        if nombre_jugador:
            break
        alerta("Debes escribir un nombre.")
    nombre_jugador = nombre_jugador.lower()
    personaje = {
        "nombre": nombre_jugador,
        "vida": 10,
        "pociones": 6,
        "moscas": 0,
        "brazos": 0,
        "sombra": 0,
        "sangre": 0,
        "_pw": 0,
        "nivel": 1,
        "tiene_llave": False,
        "rencor":                              False,
        "hitos_brazos_reclamados":           [],
        "evento_brazos_final_completado":     False,
        "evento_brazos_segundo_completado":   False,
        "bolsa_acecho":                       [1, 2, 3],
        "_x9f": False,
        "armas": {},  # NUEVA PARTIDA: inventario de armas vacío al inicio
    }
    preguntar("\n¿Eras fuerte o ágil? No puedes ser fuerte y ágil al mismo tiempo..."
              "La carne solo tolera una bendición antes de desgarrarse bajo el peso de otra. ¿Qué parte de ti ha sobrevivido?")
    while True:
        entrada = pedir_input().strip()
        if not entrada.isdigit():
            alerta("Debes escribir un número.")
            continue
        fuerza = int(entrada)
        if 1 <= fuerza <= 9:
            break
        else:
            alerta("Solo valores entre 1 y 9.")
    destreza = 10 - fuerza
    # Límites máximos del personaje
    MAX_FUERZA_DESTREZA = 20
    MAX_VIDA = 25
    MAX_POCIONES = 10
    MAX_ARMADURA = 5
    # Aplicar límites a los atributos
    personaje["fuerza"] = min(fuerza, MAX_FUERZA_DESTREZA)
    personaje["destreza"] = min(destreza, MAX_FUERZA_DESTREZA)
    personaje["vida_max"] = MAX_VIDA
    personaje["pociones_max"] = MAX_POCIONES
    personaje["armadura_max"] = MAX_ARMADURA
    # Cálculo de armadura basado en destreza
    if destreza >= 9:
        personaje["armadura"] = 4
    elif destreza >= 6:
        personaje["armadura"] = 2
    elif destreza >= 3:
        personaje["armadura"] = 1
    else:
        personaje["armadura"] = 0
    return personaje

# ================== ARMAS ==================

# Mapeo de nombres de armas display → nombres de archivo sprite
# Usado para cargar PNG de sprites dinámicamente
_ARMAS_DISPLAY_A_SPRITE = {
    "daga": "daga",
    "espada": "espada",
    "martillo": "martillo",
    "porra": "porra",
    "maza": "maza",
    "lanza": "lanza",
    "estoque": "estoque",
    "cimitarra": "cimitarra",
    "Mano de Dios": "mano_dios",
    "Hoz de Sangre": "hoz_sangre",
    "Hoja de la Noche": "hoja_noche",
    "Hacha Maldita": "hacha_maldita",
}

# Base de datos de todas las armas disponibles
armas_global = {
    # Armas básicas
    "daga": {"daño": 2, "golpe": 95, "sangrado": 1, "tipo": "sutil"},
    "espada": {"daño": 3, "golpe": 85, "tipo": "pesada"},
    "martillo": {"daño": 5, "golpe": 75, "stun": 3, "tipo": "pesada"},
    "porra": {"daño": 3, "golpe": 80, "sangrado": 1, "stun": 2},
    "maza": {"daño": 7, "golpe": 70, "stun": 4, "tipo": "pesada"},
    "lanza": {"daño": 5, "golpe": 80, "sangrado": 1, "tipo": "sutil"},
    "estoque": {"daño": 4, "golpe": 80, "sangrado": 2, "tipo": "sutil"},
    "cimitarra": {"daño": 5, "golpe": 75, "tipo": "mixta"},
    # Armas épicas
    "Mano de Dios": {"daño": 2, "golpe": 75, "vida": 1, "sangrado": 2, "stun": 3,  "tipo": "mixta"},
    "Hoz de Sangre": {"daño": 5, "golpe": 85, "vida": 1, "sangrado": 1, "tipo": "mixta"},
    "Hoja de la Noche": {"daño": 8, "golpe": 75, "vida": 2, "stun": 1, "tipo": "mixta"},
    # Armas únicas de evento
    "Hacha Maldita": {"daño": 7, "golpe": 75, "tipo": "pesada", "auto_daño": 1}
}


def calcular_daño(arma, personaje):
    """Calcula el daño total considerando tipo de arma y atributos del personaje."""
    daño = arma["daño"]
    tipo = arma.get("tipo")
    
    # Bonus según tipo de arma y atributos
    if tipo == "sutil":
        daño += personaje["destreza"] // 2
    elif tipo == "pesada":
        daño += personaje["fuerza"] // 2
    elif tipo == "mixta":
        daño += (personaje["fuerza"] + personaje["destreza"]) // 3
    return daño


# ================== GESTIÓN DE ARMAS ==================

# Abreviaturas de armas aceptadas en input del jugador. Constante de módulo
# para evitar duplicación con turno_jugador.
_ABREVIATURAS_ARMAS: dict = {
    "por": "porra",
    "dag": "daga",
    "esp": "espada",
    "mar": "martillo",
    "maz": "maza",
    "lan": "lanza",
    "est": "estoque",
    "cim": "cimitarra",
    "man": "Mano de Dios",
    "hoz": "Hoz de Sangre",
    "hoj": "Hoja de la Noche",
    "hac": "Hacha Maldita",
}


def añadir_arma(personaje, nueva_arma):
    abreviaturas = _ABREVIATURAS_ARMAS
    nombre_real = abreviaturas.get(nueva_arma.lower(), nueva_arma)
    if nombre_real not in armas_global:
        alerta("¡Arma desconocida!")
        return
    if len(estado["armas_jugador"]) >= 3:
        preguntar(f"Tienes 3 armas, debes descartar una para recoger {nueva_arma}.\nArmas actuales: {list(estado["armas_jugador"].keys())}")
        while True:
            preguntar("Cual quieres descartar? (cancelar: /no)")
            descartar = pedir_input().lower()
            if descartar in ["/no", "no", "n"]:
                narrar("Cancelas la recogida del arma.")
                return
            descartar_real = abreviaturas.get(descartar, descartar)
            if descartar_real in estado["armas_jugador"]:
                del estado["armas_jugador"][descartar_real]
                personaje["armas"] = estado["armas_jugador"].copy()  # SYNC: Actualizar UI reactivamente
                sistema(f"Has descartado {descartar_real}.")
                break
            else:
                alerta("No tienes esa arma. Intenta de nuevo.")
    estado["armas_jugador"][nombre_real] = armas_global[nombre_real].copy()
    personaje["armas"] = estado["armas_jugador"].copy()  # SYNC: Actualizar UI reactivamente
    exito(f"Has conseguido {nombre_real}.")
    sistema(f"Armas disponibles: {list(estado["armas_jugador"].keys())}")

# ================== EVENTOS Y EXPLORACIÓN ==================
# Sistema de eventos modularizado en modules/events.py
# evento_aleatorio() es importado desde allí (línea ~38)

# ================== INTRODUCCIÓN ==================

def celda_inicial(personaje):
    separador()
    narrar(".")
    narrar("..")
    narrar("...")
    separador()
    panel(
        f"'Ásí que {personaje['nombre'].capitalize()}. No sé cómo llegaste aquí,"
        " pero debes salir, ¡y rápido! Si no, acabarás como yo...'",
        titulo="",
        estilo="dim red"
    )
    narrar("Levantas la vista sorprendido y ves un hombre decrépito, encadenado en el suelo.")
    narrar("No te habías dado cuenta de él, ni tampoco de haber dicho tu nombre en voz alta.")
    narrar(
        "Levantando la cabeza todo lo que le permiten las cadenas y con un hilo de voz,\n"
        "el prisionero te dice:"
    )
    panel(
        "'No dejes que te atrapen...'\n\n"
        "Sus ojos amarillentos y el brillo de las cadenas donde debería estar su cuerpo\n"
        "son lo único que ves. Sus ojos se le desorbitan, y se desvanece,\n"
        "chocando su cabeza contra el suelo.",
        titulo="",
        estilo="dim red"
    )
    narrar("El eco del cráneo roto resuena por tu celda, y seguramente por los pasillos...")
    narrar("No tienes ni idea de qué ocurre, pero tu instinto te grita que salgas de allí.")
    titulo_seccion("Bienvenido al principio de tu fin")
    narrar("Estás en una celda mugrienta. El cadáver del prisionero está a tu lado.")
    narrar("No sabes lo que te espera, pero podrías necesitar cualquier recurso que encuentres.")
    narrar(
        "Nada más levantarte notas tu vieja daga en la bota.\n"
        "No recuerdas dónde estabas antes de llegar aquí,\n"
        "pero la daga te dice que solías estar preparado para la pelea.\n"
        "Pero debiste perder la última..."
    )
    estado["armas_jugador"]["daga"] = armas_global["daga"].copy()
    # CRÍTICO: Sincronizar armas iniciales con UI para que se muestren los sprites
    personaje["armas"] = estado["armas_jugador"].copy()
    
    while True:
        preguntar("¿Rebuscas en el cadáver? (s/n)")
        resp = leer_input("> ", personaje)
        if resp in ["s", "si"]:
            narrar("Encuentras una espada oxidada y una poción entre los harapos del prisionero.")
            personaje["pociones"] += 1
            estado["armas_jugador"]["espada"] = armas_global["espada"].copy()
            # CRÍTICO: Sincronizar nueva arma con UI para que se muestre el sprite
            personaje["armas"] = estado["armas_jugador"].copy()
            break
        elif resp in ["n", "no"]:
            narrar("Decides no rebuscar en el cadáver.")
            break
        else:
            alerta("Respuesta no válida.")
    separador()
    narrar("Aquí no hay nada más que hacer. Debes buscar la salida.")
    narrar("Sacas la cabeza de la celda y estás en un corredor lleno de celdas.")
    narrar("Oyes ruidos, gemidos, llantos y gritos, pero no ves a nadie.")
    narrar("La oscuridad lo engulle todo. Apenas ves las paredes, pero debes avanzar.")
    explorar(personaje)

# ================== CURACIÓN ==================

def curacion(personaje):
    if personaje["vida"] <= 7:
        while True:
            preguntar(f"\n\u2665 Tu vida es baja ({personaje['vida']}). ¿Usar poción? (s/n)")
            resp = leer_input("> ", personaje)
            if resp in ["s","si"]:
                if personaje["pociones"] > 0:
                    personaje["pociones"] -= 1
                    personaje["vida"] = min(personaje["vida_max"], personaje["vida"] + 4)
                    exito(f"Bebes una poción. Recuperas 4 de vida → {personaje['vida']} / {personaje['vida_max']}")
                    sistema(f"Pociones restantes: {personaje['pociones']}")
                else:
                    alerta("No tienes pociones.")
                break

            elif resp in ["n","no"]:
                narrar("Sigues adelante sin curarte.")
                break

            else:
                alerta("Respuesta no válida.")


# ================== EXPLORACIÓN ==================

def racha(lista, ruta_ref):
    """Devuelve cuántos pasos finales de 'lista' coinciden con el prefijo de 'ruta_ref'.
    Usado para medir el progreso del jugador en las rutas secretas de nivel 2."""
    for n in range(min(len(lista), len(ruta_ref)), 0, -1):
        if lista[-n:] == ruta_ref[:n]:
            return n
    return 0


def explorar(personaje):
    """Bucle de exploración. Avanza paso a paso hasta derrota o final de juego."""
    while _explorar_paso(personaje):
        pass

def _explorar_paso(personaje):
    """Ejecuta un único paso de exploración. Devuelve True para continuar, None/False para parar."""
    if personaje["vida"] <= 0:
        alerta("Has muerto.")
        resultado_derrota = fin_derrota(personaje)
        if personaje.get("_flg1"):
            personaje.pop("_flg1", None)
            narrar("Lentamente, vuelves en sí.")
            return True
        return
    if personaje["vida"] <= 6 and personaje["pociones"] > 0:
        curacion(personaje)
    narrar("\nTe adentras en la mazmorra...")
    
    # Sistema de bolsa para textos de exploración
    textos_exploracion = obtener_texto_exploracion_de_bolsa()
    
    # Verificar condición especial de Hoz de Sangre
    if textos_exploracion == 2 and "Hoz de Sangre" in estado["armas_jugador"]:
        # Si sacamos el texto 2 y tenemos Hoz de Sangre, intentamos otro
        textos_exploracion = obtener_texto_exploracion_de_bolsa()
    #------------- TEXTOS EXPLORACIÓN ---------------------
    if textos_exploracion == 1:
        narrar("Dos pasillos se extienden ante ti, con paredes cubiertas de musgo y humedad. El silencio es abrumador, solo roto por el eco de tus pasos.")
        narrar("El aire huele a óxido y agua estancada. Tienes la sensación de que elegir mal no será fácil de corregir.")
        narrar("Ninguno de los dos pasillos te ofrece algo a lo que aferrarte. Solo la oscuridad y el sonido de tu propio pulso.")
    elif textos_exploracion == 2:
        narrar("A lo lejos, a tu izquierda, ves una sombra moverse rápidamente por el pasillo. No puedes distinguir qué es, pero sientes que te observa.")
        narrar("Durante un segundo, jurarías haber oído tu nombre susurrado entre las piedras.")
        narrar("La sombra no vuelve a aparecer. Pero la sensación de que algo te ha localizado, sí.")
    elif textos_exploracion == 3:
        narrar("El aire se vuelve más denso y frío a medida que avanzas. Sientes un escalofrío recorrer tu espalda.")
        narrar("Tu respiración forma una leve neblina frente a ti, y cada paso resuena más de lo normal.")
        narrar("Por la sangre escarchada del suelo dirías que el frío proviene de la izquierda...")
        narrar("No es el frío de la piedra. Es otro tipo de frío. El que no viene del ambiente.")
    elif textos_exploracion == 4:
        narrar("De repente, escuchas un ruido detrás de ti. Te das la vuelta rápidamente, pero solo ves oscuridad...")
        narrar("El silencio que sigue es aún peor, como si algo estuviera conteniendo el aliento.")
        narrar("Esperas. Nada se mueve. Eso no te tranquiliza en absoluto.")
    elif textos_exploracion == 5:
        narrar("Todos los pasillos parecen iguales, y te sientes perdido. No sabes si estás dando vueltas o avanzas hacia algún lado.")
        narrar("Las marcas en las paredes podrían ser antiguas... o nuevas. No estás seguro con toda la sangre y humedad que hay.")
        narrar("Empiezas a dudar si has pasado ya por aquí. No lo sabes. Eso es lo peor.")
    elif textos_exploracion == 6:
        narrar("A lo lejos, ves una figura encorvada arrastrándose por las paredes. Sus movimientos son torpes, pero al verte sale corriendo hacia la derecha.")
        narrar("El sonido húmedo que deja tras de sí tarda demasiado en desaparecer.")
        narrar("Lo que sea que era, ha ido hacia la derecha. Y lo ha hecho con prisa.")
    elif textos_exploracion == 7:
        narrar("El suelo cruje bajo tus pies, y de pronto te hundes un poco. No puedes ver nada, pero sientes que se te mojan los pies...")
        narrar("Algo se mueve bajo la superficie, rozándote los tobillos antes de desaparecer.")
        narrar("No hay agua visible. El suelo está seco. Lo que sea que te rozó no venía de un charco.")
    elif textos_exploracion == 8:
        narrar("Este pasillo está cubierto de insectos. Se alimentan de los desperdicios y la sangre, y su zumbido es insoportable...")
        narrar("Algunos se apartan de tu camino, otros parecen acercarse con curiosidad.")
        narrar("El zumbido no baja aunque los dejas atrás. Como si el pasillo entero vibrara a la misma frecuencia.")
    elif textos_exploracion == 9:
        narrar("A la derecha, a lo lejos en el pasillo, ves una luz tenue que parpadea. No sabes si es una señal de esperanza o una trampa...")
        narrar("Cada vez que parpadea, proyecta sombras que no siempre coinciden con las paredes.")
        narrar("No sabes si acercarte al fuego es más peligroso que ignorarlo. Aquí abajo, la luz tiene un precio.")
    elif textos_exploracion == 10:
        narrar("Oyes unos aullidos inhumanos. El eco inunda el pasillo, y no sabes de dónde vienen, pero parecen estar cerca...")
        narrar("Los aullidos se solapan entre sí, como si varias gargantas compartieran el mismo aliento.")
        narrar("No se acercan. Tampoco se alejan. Solo llenan el espacio como si fueran parte de la arquitectura.")
    elif textos_exploracion == 11:
        narrar("Al llegar al cruce, sientes una oleada de tristeza... '¡Qué hago aquí? ¿Cómo he llegado a este sitio?'")
        narrar("Durante un instante, te cuesta recordar qué te empujó a seguir adelante.")
        narrar("La tristeza pasa pronto. Demasiado pronto. Como si algo la hubiera retirado en lugar de disolverse sola.")
    elif textos_exploracion == 12:
        narrar("Cuando el camino se bifurca, notas un olor dulzón en el aire, más agradable que el hedor constante a humedad y sangre. Viene por la izquierda...")
        narrar("Ese aroma te resulta inquietantemente familiar, aunque no recuerdas por qué.")
        narrar("Lo que huele bien aquí abajo no lo hace por accidente.")
    elif textos_exploracion == 13:
        narrar("Oyes un tumulto a tu derecha. El pasillo está tenuemente iluminado, y ves un bulto en medio...")
        narrar("El bulto parece moverse de forma irregular, como si creciera por momentos.")
        narrar("El sonido que emite no es un quejido ni un gruñido. Es algo entre las dos cosas que no tiene nombre.")
    elif textos_exploracion == 14:
        narrar("No has comido ni bebido nada, pero no sientes cansancio. Sabes que es raro, pero no te preocupa.")
        narrar("De hecho, cuanto más avanzas, más ligera sientes la mente.")
        narrar("No es natural. No hay nada que te quite el hambre y el sueño aquí abajo lo es. Pero de momento, funciona.")
    elif textos_exploracion == 15:
        narrar("El pasillo está lleno de símbolos y pintadas color sangre. Continúan hacia la derecha...")
        narrar("Algunas marcas parecen moverse, y cuando te fijas, las ves solo en la izquierda. No te gusta...")
        narrar("No son decoración. Alguien las hizo con un proposito. Lo que no sabes es si para guiar o para advertir.")

# ================== BUCLE IZQUIERDA/DERECHA ==================
    while True:
        preguntar("Izquierda o derecha? (i/d) - g para guardar")
        valor = pedir_input().strip().lower()
        separador()

        if valor in ["stats", "st", "stat"]:
            mostrar_stats(personaje)
            continue

        if valor == "g":
            intentar_guardar(personaje)
            continue

        # [SECRETO 3] Rezar si textos_exploracion == 14
        if valor == "rezar" and textos_exploracion == 14:
            narrar("Cierras los ojos. El aire en el templo subterráneo se vuelve denso, casi sólido.")
            narrar("Ves figuras en la oscuridad: no son personas. Son cosas que fueron personas una vez, hace siglos.")
            narrar("La plaga los hizo así. La plaga que durmió, que esperó, que ahora se despierta.")
            narrar("Comprendes que los demonios del templo no son criaturas sino síntomas. Manifestaciones de algo más antiguo.")
            personaje["conocimiento_plaga"] = True  # Flag para diálogo futuro
            preguntar("Izquierda o derecha? (i/d) - g para guardar")
            valor = pedir_input().strip().lower()
            separador()
            # Reintentar validación i/d
            if valor in ["i", "izquierda"]:
                resp = "i"
                break
            elif valor in ["d", "derecha"]:
                resp = "d"
                break
            elif valor in ["stats", "st", "stat"]:
                mostrar_stats(personaje)
                continue
            else:
                alerta("Respuesta no válida. Elige i/d o g para guardar.")
                continue

        if valor in ["i", "izquierda"]:
            resp = "i"
            break
        elif valor in ["d", "derecha"]:
            resp = "d"
            break

        alerta("Respuesta no válida. Elige i/d o g para guardar.")


# ================== TEXTOS + NAVEGACIÓN ==================    

    if resp == "i" and textos_exploracion == 1:
        narrar("Decides tomar el pasillo de la izquierda, aunque nada te asegura que sea el camino correcto.")
        narrar("El eco de tus pasos cambia al entrar. El techo es más bajo aquí, o eso te parece.")
        tirada = random.random()
        if tirada < 0.5:
            narrar("Parece un pasillo cualquiera, lleno de mugre, sangre y desperdicios.")
            narrar("Las paredes están húmedas y rezuman algo que no es solo agua.")
            narrar("Pisas sin querer un montón de huesos pequeños. Ruedan con un sonido seco que se propaga demasiado lejos.")
            narrar("Te quedas quieto un momento. Nada responde.")
            narrar("Hay marcas en la piedra a la altura de la cadera, paralelas, como si alguien hubiera arrastrado algo pesado durante mucho tiempo.")
            narrar("O como si algo se hubiera arrastrado solo.")
            narrar("Sigues adelante. No hay nada que hacer con esa información salvo tenerla en cuenta.")
        else:
            narrar("Llevas apenas diez pasos cuando el sonido llega. Pasos. Rápidos. Directos.")
            narrar("No hay tiempo de prepararse del todo, pero es suficiente para no recibirlo de frente.")
            combate(personaje, enemigo_aleatorio())
            narrar("Cuando termina, el pasillo vuelve al silencio habitual.")
            narrar("Continúas. No queda otra.")

    elif resp == "d" and textos_exploracion == 1:
        narrar("No hay razón para elegir este y no el otro. Pero algo en ti se inclina hacia la derecha.")
        narrar("Giras y enfilas el camino. No miras atrás.")
        tirada = random.random()
        if tirada < 0.5:
            narrar("El pasillo es exactamente lo que prometía: mugre, piedra y silencio.")
            narrar("El suelo cruje bajo tus botas. Huesos pequeños. No preguntas de que o de quién.")
            narrar("Las paredes sudan humedad. El techo es más bajo de lo que esperabas.")
            narrar("No hay nada aquí. Solo el eco de tus pasos yendo más lejos de lo que querrías.")
            narrar("Avanzas.")
        else:
            narrar("Según avanzas, el suelo desaparece bajo el barro.")
            narrar("El agua es negra, densa, y huele a algo muerto que lleva tiempo haciéndolo.")
            narrar("El musgo lo cubre todo: las paredes, el techo, lo que queda de piedra entre el lodazal.")
            narrar("Cada paso se hunde más. El fango te abraza los tobillos con familiaridad.")
            chequeo_destreza = random.randint(1, 25)
            if chequeo_destreza <= personaje["destreza"]:
                narrar("Cubierto de desperdicios hasta las rodillas, avanzas pesadamente.")
                narrar("El barro tira de ti con cada paso, como si la mazmorra quisiera retenerte.")
                narrar("Pero tu determinacion es fuerte, y gracias a tu destreza consigues cruzar sin problemas.")
            elif chequeo_destreza > personaje["destreza"]:
                alerta("El lodo cede bajo tu pie de golpe. Te agarras a la pared, pero la piedra cede.")
                alerta("Caes de bruces. El barro frío y la mugre te llenan la boca antes de que puedas cerrarla.")
                narrar("Te incorporas escupiéndola, jadeando, y asqueado por el sabor ferroso del cieno.")
                evento = {"vida": -1}
                aplicar_evento(evento, personaje)

    elif resp == "i" and textos_exploracion == 2:
        narrar("Algo en la sombra te resulta familiar. No sé si es la forma, el movimiento, o algo que no puedes nombrar.")
        narrar("Pero no parece huir de ti. Parece guiarte, o eso es lo que quiere que pienses.")
        narrar("La sigues de todas formas. En este lugar, cualquier indicio es mejor que ninguno.")
        tirada = random.random()
        if tirada < 0.5:
            narrar("Doblas el mismo recodo que tomó la sombra. No hay nada al otro lado.")
            narrar("Solo el pasillo vacío, el silencio, y un frasco en el centro del suelo.")
            narrar("Demasiado centrado. Demasiado solo. Pero un recurso es un recurso.")
            narrar("Lo coges de todas formas. Aquí dentro no te puedes permitir desdeñar nada.")
            narrar("El pinchazo llega antes de que puedas reaccionar. Un dardo, muslo izquierdo.")
            dialogo("'¿De verdad creías que era un regalo? Me gustan los que tienen esperanza...'")
            narrar("La voz viene de arriba, suave, casi divertida.")
            susurros_aleatorios()
            narrar("Oyes una risita que se aleja entre las piedras, y un olor denso a sangre fresca cruza el pasillo de lado a lado.")
            evento = {"vida": -1, "pociones": 1}
            aplicar_evento(evento, personaje)
        else:
            narrar("La sombra no se detiene. Acelera.")
            narrar("Y tú también. No sabes por qué, pero no puedes dejar de seguirla.")
            narrar("Como si hubiera algo al otro lado que necesitas ver.")
            narrar("Doblas la esquina. La sombra se para. Se da la vuelta.")
            narrar("Ya no parece estar guiándote a ningún sitio.")
            if personaje["vida"] >= 5:
                alerta("Los filos emergen de la oscuridad. Era una trampa desde el principio.")
                combate(personaje, enemigo_aleatorio("Sombra tenebrosa"))
            else:
                narrar("Se queda inmóvil un instante, como estudiándote.")
                susurros_aleatorios()
                narrar("Luego, sin hacer ruido, se disuelve en la pared.")
                narrar("No ha atacado. No sabes si por misericordia o porque no le interesas así.")

    elif resp == "d" and textos_exploracion == 2:
        narrar("Te alejas de donde viste la sombra. Aquí abajo, lo que se mueve con esa fluidez no persigue buenas intenciones.")
        narrar("El pasillo de la derecha se estrecha. El aire pesa. Huele a hierro y a sudor rancio.")
        narrar("Acelereas el paso. Pero a los pocos segundos lo oyes: respiración rota, pasos caóticos, algo que rebota contra las paredes.")
        narrar("Un Rabioso dobla el recodo a toda velocidad, babeando sangre, con los ojos en blanco.")
        narrar("No te ha visto. Te busca por el olor.")
        tirada = random.random()
        if tirada < 0.5:
            narrar("Su paso errático lo traiciona. Tropieza y cae de morros contra el suelo con un golpe sordo.")
            narrar("Se retuerce intentando levantarse, convulsionando, incapaz de coordinar los miembros.")
            narrar("Aprovechas el momento y corres. No miras atrás.")
            narrar("Oyes como chilla de frustración, o dolor. No te detienes a averiguarlo, pero ya no te sigue...")
        else:
            narrar("Se lanza contra ti aullando. Estás preparado para el combate, pero el ataque no llega.")
            narrar("Una sombra cae del techo tras el Rabioso, sin hacer ruido.")
            narrar("El Rabioso ni la ve. Un filo cruza su garganta de lado a lado antes de que pueda parpadear.")
            narrar("El cuerpo se desploma como un saco. La sangre cubre el suelo en un segundo.")
            narrar("La sombra se yergue despacio, con los filos todavía goteando, y te mira sin ojos...")
            dialogo("'Tú no eras para él.'")
            susurros_aleatorios()
            alerta("Os separaban metros, y de pronto, no os separa nada.")
            combate(personaje, enemigo_aleatorio("Sombra tenebrosa"))

    # TEXTO 3: Frío y densidad
    elif resp == "i" and textos_exploracion == 3:
        narrar("El pasillo de la izquierda exhala frío. No como el de la piedra húmeda al que ya te has acostumbrado.")
        narrar("Este muerde. Te detienes un segundo en el umbral, sin saber muy bien por qué.")
        narrar("No tiene sentido que haga tanto frío aquí abajo. No debería.")
        narrar("Pero la sangre del suelo lleva tiempo congelada, y las paredes están cubiertas de escarcha.")
        narrar("Avanzas. El primer crujido bajo tu bota te pone el estómago del revés.")
        tirada = random.randint(1, 25)
        if tirada > personaje["fuerza"]:
            narrar("El frío te va debilitando. Primero los dedos, luego las manos, luego los brazos al completo.")
            narrar("Los charcos de sangre helada se fragmentan bajo cada paso como si la mazmorra te avisara de algo.")
            narrar("Las esquirlas saltan y te abren cortes en los tobillos, en las espinillas.")
            alerta("Pequeñas heridas. Pero aquí abajo, las pequeñas heridas se acumulan.")
            aplicar_evento({"vida": -1}, personaje)
        else:
            narrar("Llevas unos veinte pasos cuando el crujido cambia de tono.")
            narrar("No eres tú. Viene de delante. Y se acerca.")
            narrar("Algo se mueve a toda velocidad por el pasillo helado, levantando esquirlas a su paso.")
            narrar("No entiendes como se puede mover asi sobre el hielo.")
            alerta("Cuando la forma toma cuerpo, ya no hay distancia entre vosotros.")
            enemigo = random.choice(["Rabioso", "Perturbado", "Maniaco Mutilado"])
            combate(personaje, enemigo_aleatorio(enemigo))
    elif resp == "d" and textos_exploracion == 3:
        narrar("No. El frío no es para ti.")
        narrar("Giras a la derecha antes de que tu cuerpo te convenza de lo contrario.")
        narrar("Pero el calor no llega. Solo desaparece el frío seco y llega la humedad, que es distinto.")
        narrar("El pasillo rezuma agua por todas partes. El suelo está negro y brillante.")
        narrar("Cada paso suena demasiado. Aquí no hay forma de moverse en silencio.")
        tirada = random.randint(1, 25)
        if tirada > personaje["destreza"]:
            narrar("El suelo parece firme. No lo es.")
            narrar("Tu pie cede hacia un lado y el cuerpo va detrás antes de que puedas hacer nada.")
            alerta("Caes de lado contra la piedra. El golpe en tu cadera y codo resuena por todo tu cuerpo y por todo el pasillo.")
            narrar("Te quedas quieto un momento, escuchando si algo ha oído la caída.")
            narrar("Nada. Por ahora....")
            aplicar_evento({"vida": -1}, personaje)
        else:
            narrar("Oyes la respiración antes de verlo. Rota, convulsa, como si los pulmones no funcionaran bien.")
            narrar("Los pasos vienen de todas partes a la vez, rebotando en las paredes mojadas.")
            alerta("Un Rabioso dobla el recodo a ciegas, babeando sangre, con los brazos abiertos.")
            enemigo = random.choice(["Rabioso", "Perturbado", "Maniaco Mutilado"])
            combate(personaje, enemigo_aleatorio(enemigo))

    # TEXTO 4: Ruido
    elif resp == "i" and textos_exploracion == 4:
        narrar("Vas hacia el sonido. No sabes por qué. Pero parar aquí, sin saber qué es, se siente peor.")
        narrar("Los pasos son irregulares. Rápidos. Como si algo estuviera buscando, no moviéndose.")
        susurros_aleatorios()
        narrar("Te detienes en el recodo. El ruido también.")
        narrar("Un segundo de silencio total. Ni tu propia respiración.")
        tirada = random.random()
        if tirada < 0.33:
            narrar("Nada. El pasillo está vacío.")
            narrar("Pero en la pared, al fondo, hay marcas nuevas. Arañazos profundos en la piedra, a la altura de los ojos.")
            narrar("Paralelas. Cuatro. Como dedos.")
            susurros_aleatorios()
            narrar("Sigues adelante sin tocarlas.")
        elif tirada < 0.66:
            narrar("El primer filo aparece antes que la forma. Un brillo largo y curvo que sale de la oscuridad.")
            narrar("Luego la risa. Baja, casi íntima, como si te conociera.")
            alerta("La sombra se despliega desde las paredes como si fuera parte de ellas.")
            combate(personaje, enemigo_aleatorio("Sombra tenebrosa"))
        else:
            narrar("Lo que sea que hacía ese ruido ya no está.")
            narrar("Queda un rastro oscuro en el suelo, viscoso, que va de pared a pared.")
            narrar("No es sangre. Huele diferente. Más dulce. Más frío.")
            susurros_aleatorios()
            narrar("Cruzas el rastro sin pisarlo y sigues adelante.")
            narrar("Durante unos minutos, tienes la sensación de que algo te sigue a la misma distancia exacta.")
            narrar("Luego desaparece. O deja de dejarse notar.")
    elif resp == "d" and textos_exploracion == 4:
        narrar("No. Lo que sea que hace ese ruido, no quieres saber qué es.")
        narrar("Giras a la derecha y aceleras sin correr. Correr llama la atención.")
        narrar("Pero el silencio que queda detrás de ti no es el mismo silencio de antes.")
        narrar("Este respira.")
        chequeo_destreza = random.randint(1, 25)
        if chequeo_destreza > personaje["destreza"]:
            narrar("Lo oyes antes de que llegue: el roce de algo deslizándose por la piedra.")
            narrar("No son pasos. No tiene pies.")
            alerta("Te giras en el último momento. Los filos ya están a centímetros de tu cara.")
            combate(personaje, enemigo_aleatorio("Sombra tenebrosa"))
        else:
            tirada_escape = random.random()
            if tirada_escape < 0.5:
                narrar("No hay nadie detrás de ti. El pasillo está vacío.")
                narrar("Pero llevas veinte metros mirando atrás a cada paso, y eso tiene un precio.")
                narrar("Cuando por fin te paras a respirar, no reconoces el trozo de pasillo donde estás.")
                susurros_aleatorios()
                narrar("Da igual. Hay que seguir.")
            else:
                narrar("Sigues caminando y el silencio aguanta.")
                narrar("Veinte pasos. Treinta. Nada.")
                narrar("Pero justo cuando empiezas a relajarte, algo cae del techo frente a ti.")
                narrar("Un cuerpo. Reciente. Sin marcas visibles.")
                narrar("Lo rodeas sin mirarlo demasiado. Aquí no toca preguntar quién era.")
                susurros_aleatorios()

    # TEXTO 5: Pérdida
    elif resp == "i" and textos_exploracion == 5:
        chequeo_fuerza = random.randint(1, 25)
        if chequeo_fuerza > personaje["fuerza"]:
            narrar("Das vueltas durante lo que te parecen días.")
            narrar("Estás exhausto, el corredor es estrecho y no puedes descansar.")
            alerta("Tras una eternidad, pareces encontrar el camino, pero sientes que has perdido la cordura. Pierdes 1 punto de vida.")
            aplicar_evento({"vida": -1}, personaje)
    elif resp == "d" and textos_exploracion == 5:
        narrar("El pasillo parece no acabar nunca.")
        narrar("Las marcas de las paredes cambian, se retuercen y parecen escribir cosas.")
        chequeo_destreza = random.randint(1, 25)
        if chequeo_destreza > personaje["destreza"]:
            narrar("Te quedas absorto viendo la danza de las marcas.")
            alerta("Pierdes la noción del tiempo, hasta que te percatas de que algo trepa por tu pierna.")
            combate(personaje, enemigo_aleatorio("Larvas de Sangre"))
            narrar("Cuando consigues quitarte la larva de encima, te das cuenta del peligro.")
            narrar("Sigues avanzando, forzando tu atención fuera de la danza de las marcas.")
        else:
            narrar("Te quedas absorto viendo la danza de las marcas.")
            narrar("Parece que comienzas a entender algo en ellas, que quieren que sepas...")
            chequeo_fuerza = random.randint(1, 25)
            if chequeo_fuerza > personaje["fuerza"]:
                alerta("Intentas comprender su lenguaje, pero al forzar la vista sientes una gran punzada en tu cerebro.")
                alerta("Caes apretándote las sienes. Cuando te recuperas, avanzas casi a ciegas para evitar las marcas.")
                aplicar_evento({"vida": -1}, personaje)
            else:
                narrar("Con gran esfuerzo, consigues entender lo que dicen.")
                susurros_aleatorios()
                narrar("No tienes claro qué significa, pero sientes que hablan de ti.")
                aplicar_evento({"destreza": 1}, personaje)

    # TEXTO 6: Figura encorvada
    elif resp == "i" and textos_exploracion == 6:
        narrar("No la sigues. Sea lo que sea, no parece que quiera que vayas detrás de él.")
        narrar("Avanzas en la dirección contraria. El sonido húmedo tarda en desaparecer, pegado al silencio como una sombra.")
        narrar("Varios metros más adelante, el pasillo se dilata en un recodo donde la piedra ha cedido.")
        if random.random() < 0.55:
            # 30% — la figura dejó algo al huir
            narrar("En el hueco, entre fragmentos de pared y algo que fue tela, hay un frasco.")
            narrar("Caído, no abandonado. Como si lo hubiera soltado alguien que corrió sin mirar atrás.")
            narrar("El cristal está intacto. No te preguntas de quién era.")
            aplicar_evento({"pociones": 1}, personaje)
        else:
            # 25% — el rastro sonoro deja sus efectos
            narrar("No hay nada en el saliente. Solo el eco del arrastre, que sigue ahí aunque ya no tiene fuente.")
            susurros_aleatorios()
            narrar("Los susurros no duran, pero el instante en que flotan absorbe más tiempo del que debería.")
            narrar("Cuando sacudes la cabeza, te duele. Como si algo hubiera estado apretando desde dentro.")
            narrar("Ese sonido húmedo te ha hecho algo. No sabes exactamente qué...")
            aplicar_evento({"vida": -1}, personaje)

    elif resp == "d" and textos_exploracion == 6:
        narrar("Sigues el rastro hacia la derecha.")
        narrar("La humedad en el suelo guía tus botas mejor que cualquier antorcha.")
        narrar("El pasillo se estrecha. El sonido húmedo se ha apagado, pero las marcas en la pared son cada vez más recientes.")
        narrar("Carne. Hueso. La figura ha dejado un rastro macabro por las paredes.")
        if random.random() < 0.55:
            # 25% — la figura está acorralada
            narrar("Al doblar el recodo, la encuentras.")
            narrar("Acorralada contra una pared derrumbada, con los brazos caídos y los huesos visibles donde debería haber carne.")
            narrar("Te mira con lo que le queda de ojos. Ya no tiene adónde ir.")
            preguntar("¿Qué haces? (r)ematarla / (d)ejarla escapar")
            resp2 = leer_input("> ", personaje)
            # [SECRETO 1] Hablar si sombra > 1
            if resp2 == "hablar" and personaje["sombra"] > 1:
                narrar("Abres la boca, pero lo que sale no es tu voz.")
                narrar("Es un susurro que resuena en las paredes: antiguo, inhumano, que describe lo que ella es.")
                narrar("La criatura levanta la cabeza lentamente. Por un instante, algo que no es humano mira a través de sus ojos.")
                narrar("Comprende. Y en su comprensión, ve que tú también comprendes.")
                personaje["sombra"] += 1
                narrar("La sombra nunca abandona a los suyos.")
                preguntar("¿Qué haces? (r)ematarla / (d)ejarla escapar")
                resp2 = leer_input("> ", personaje)
            while resp2 not in ["r", "remate", "rematarla", "d", "dejar", "dejarla"]:
                alerta("Respuesta no válida. (r) para rematarla, (d) para dejarla escapar.")
                resp2 = leer_input("> ", personaje)
            if resp2 in ["r", "remate", "rematarla"]:
                narrar("No hay vacilación en el gesto. Solo el sonido de tu arma desenvainando y un tajo húmedo.")
                narrar("La figura resbala por la pared hasta el suelo.")
                narrar("Entre los jirones que le cuelgan del torso, algo pesa más de lo que debería.")
                narrar("Placas de metal, cosidas a la ropa con hilo basto. Alguien las puso ahí para que no cayeran.")
                narrar("Las arrancas. El pasillo queda en silencio.")
                aplicar_evento({"armadura": 1}, personaje)
            else:
                narrar("Un paso atrás. Otro.")
                narrar("La figura te sigue con los ojos mientras retrocedes, sin moverse, sin hacer nada.")
                narrar("Cuando doblas el recodo, oyes el arrastre que se reanuda. Esta vez alejándose.")
                narrar("No te sigue. Ya consiguió lo que quería: seguir en pie.")
                narrar("Tú también.")
                susurros_aleatorios()
        else:
            # 20% — era un señuelo
            narrar("El rastro termina en un recodo cerrado. No hay figura.")
            narrar("Solo el suelo más oscuro, más pegajoso que el resto. Y el olor dulzón que se intensifica aquí dentro.")
            narrar("Entonces lo ves: el suelo respira.")
            alerta("No era una figura. Era un señuelo.")
            alerta("Un maniaco emerge de las sombras del fondo, rápido, directo, sin ningún aviso previo.")
            combate(personaje, enemigo_aleatorio("Maniaco Mutilado"))


    # TEXTO 7: Agua
    elif resp == "i" and textos_exploracion == 7:
        narrar("Te pegas a la pared y avanzas sin pisar el centro del pasillo.")
        narrar("El suelo junto al muro está cubierto de limo, pero al menos es sólido.")
        narrar("Lo que te rozó los tobillos no estaba en el suelo. Estaba en el suelo.")
        if random.random() < 0.45:
            # 20% — la pared tampoco es segura
            narrar("Llevas pocos pasos cuando el frío punzante en la nuca no es ya una sensación.")
            narrar("Te tocas la parte de atrás de la cabeza y sientes tu propia sangre.")
            narrar("Te giras mientras desenfundas, y ves sombras donde no debería haberlas.")
            narrar("La sombra no viene del suelo. Lleva un rato en la pared, exactamente a tu altura, siguiéndote.")
            alerta("Cuando enfocas en ella, los filos ya están en movimiento.")
            combate(personaje, enemigo_aleatorio("Sombra tenebrosa"))
        else:
            # 25% — escape limpio
            narrar("Cruzas despacio, sin pisar el centro, sin apartar los ojos del suelo.")
            narrar("Nada vuelve a rozarte. Nada emerge.")
            narrar("No sabes si has tenido suerte o si lo que había ahí abajo decidió ignorarte.")
            narrar("Prefieres no averiguarlo.")

    elif resp == "d" and textos_exploracion == 7:
        narrar("Cruzas hacia el centro del pasillo. El suelo cede ligeramente bajo tu peso, esponjoso, tibio.")
        narrar("No hay agua visible. Pero cuando levantas el pie, algo transparente se estira entre la suela y la piedra.")
        narrar("No es agua.")
        if random.random() < 0.45:
            # 25% — escape pero con daño por el frío
            narrar("Cruzas rápido, pero el contacto es suficiente.")
            narrar("Sea lo que sea, penetra a través de las botas. El frío no viene de fuera: sube desde dentro.")
            narrar("Para cuando llegas al otro lado, los pies no los sientes y las piernas responden tarde.")
            narrar("Caminas un rato con los puños apretados esperando que pase.")
            narrar("Pasa. Pero deja rastro.")
            aplicar_evento({"vida": -1}, personaje)
        else:
            # 30% — chequeo destreza
            narrar("Llevas tres pasos cuando el suelo se mueve. La piedra bajo el liquido se resquebraja.")
            narrar("El suelo se desplaza, como si algo enorme respirara justo debajo, palpitando.")
            narrar("La superficie se vuelve resbaladiza en un instante. Agua, linfa, algo que no tiene nombre, todo a la vez.")
            chequeo_destreza = random.randint(1, 25)
            if chequeo_destreza <= personaje["destreza"]:
                narrar("Tu cuerpo reacciona antes que tu cabeza. Cambias el peso, ajustas los pasos y mantienes el equilibrio.")
                narrar("Cruzas el tramo movedizo sin perder caer, pisando rápido y sin dudar.")
                narrar("Al otro lado, el suelo vuelve a ser piedra. Sólida. Fría. Miras atras y el pasillo es idéntico...")
            else:
                narrar("El pie derecho se te resbala. Intentas corregir y mantener el equilibrio, pero no hay agarres.")
                narrar("Caes de rodillas sobre la superficie y las manos se hunden varios centímetros en algo blando.")
                chequeo_fuerza = random.randint(1, 25)
                if chequeo_fuerza <= personaje["fuerza"]:
                    narrar("Te impulsas hacia arriba con los brazos antes de que lo que hay debajo decida cerrarse.")
                    narrar("Tu instinto te grita que huyas. Sacas todas tus fuerzas y consigues despegarte y salir corriendo.")
                    narrar("Llegas al otro lado de pie, empapado hasta los codos, con algo oscuro pegado a los antebrazos.")
                    narrar("Notas que el icor es acido, y te limpias todo el que puedes. Algo te dice que te iban a devorar...")
                else:
                    narrar("Tardas demasiado en levantarte. El frío sube por tus brazos y se asienta en el pecho.")
                    susurros_aleatorios()
                    narrar("Notas mordicos frios por toda tu carne. El horror te invade igual que el frio.")
                    susurros_aleatorios()
                    narrar("A pesar del dolor, tu voluntad te impulsa mas alla de tu fisico, y consigues despegar las manos del suelo.")
                    narrar("Sin saber como, y a pesar del dolor, tu cuerpo se mueve hacia adelante, hacia el otro lado del pasillo.")
                    narrar("Cuando por fin cruzas, tienes heridas por todo el cuerpo y los músculos agarrotados.")
                    narrar("El daño es grave, pero notas todavia mas dolor en tu alma...")
                    aplicar_evento({"vida": -3}, personaje)


    # TEXTO 8: Insectos
    elif resp == "i" and textos_exploracion == 8:
        narrar("Decides cruzar el pasillo de frente, sin rodeos.")
        narrar("El zumbido se vuelve ensordecedor en cuanto entras. El aire está negro de cuerpos.")
        narrar("Son pequeños, del tamaño de una uña, con mandíbulas desproporcionadas para lo que son.")
        narrar("Los que llevan más tiempo aquí abajo no se parecen a ningún insecto que hayas visto fuera.")
        narrar("Tienen algo de larva, algo de araña, y algo que no tiene nombre.")
        narrar("Te cubres la cara con el brazo y avanzas.")
        tirada_i = random.random()
        if tirada_i < 0.25:
            # 25% — escape limpio
            narrar("El enjambre se separa a tu paso como si algo en ti lo repeliera.")
            narrar("No sabes si es el olor de tu sangre, el metal del arma, o pura suerte.")
            narrar("Cruzas el tramo sin recibir nada. Los insectos se reagrupan a tu espalda.")
            narrar("El zumbido queda atrás. El asco, no.")
        elif tirada_i < 0.55:
            # 30% — vida -1
            narrar("Los insectos no se apartan. Se multiplican.")
            alerta("Se te meten bajo la ropa, en la boca y en los ojos. Sientes decenas de pequeñas mordeduras ardiendo a la vez.")
            narrar("Algunos llevan sangre de otro huésped. Noto el sabor ferroso en los labios.")
            narrar("Cruzas escupiendo y rascándote. El ardor tarda en calmarse.")
            narrar("Dentro de cada picadura, algo que no es veneno pero tampoco es solo saliva.")
            aplicar_evento({"vida": -1}, personaje)
        else:
            # 45% — armadura -1
            narrar("El enjambre se concentra en tu equipo.")
            narrar("No muerden carne, muerden correas, remaches, tela endurecida.")
            narrar("Hay algo en sus mandíbulas que disuelve el cuero. Lo has visto antes en los cadáveres de aquí abajo.")
            alerta("Cuando cruzas al otro lado y te sacudes el último, el daño ya está hecho.")
            narrar("Una placa se ha soltado. Una correa, rota. La protección ya no es la misma.")
            aplicar_evento({"armadura": -1}, personaje)

    elif resp == "d" and textos_exploracion == 8:
        narrar("Giras a la derecha y el zumbido cambia de tono.")
        narrar("No es el mismo rumor sordo de antes. Este es agudo, rítmico, casi intencional.")
        narrar("El enjambre lleva aquí mucho tiempo. Las paredes están recubiertas de una capa orgánica oscura, como cera mezclada con sangre seca.")
        narrar("Hay restos humanos integrados en esa capa. Huesos, ropa, lo que fue una mano.")
        narrar("Los insectos no son carroñeros oportunistas. Son criadores. Están cultivando algo.")
        narrar("La masa de insectos se agita violentamente frente a ti.")
        tirada = random.random()
        if tirada < 0.4:
            narrar("El zumbido se interrumpe de golpe. Un silencio de medio segundo.")
            narrar("Luego el aire se corta con un batir de alas mojadas.")
            narrar("Una Mosca de Sangre emerge de la masa, más grande que sus crías, con las alas cubiertas de coágulos negros.")
            narrar("Sus ojos compuestos te descomponen en mil fragmentos. Todos dicen lo mismo: presa.")
            alerta("No espera. Las Moscas de Sangre nunca esperan.")
            combate(personaje, enemigo_aleatorio("Mosca de Sangre"))
        elif tirada < 0.7:
            narrar("El suelo se mueve. No tiembla: respira.")
            narrar("La capa orgánica se agrieta y de las fisuras emerge una masa palpitante, blanca y húmeda.")
            narrar("Larvas de Sangre. Docenas. Cada una del tamaño de un antebrazo.")
            alerta("Se arrastran hacia ti dejando un rastro viscoso y corrosivo que funde la piedra a su paso.")
            narrar("No son crías. Son la siguiente fase. Las Moscas no nacen de huevos: nacen de esto.")
            combate(personaje, enemigo_aleatorio("Larvas de Sangre"))
        else:
            narrar("El enjambre se fragmenta de pronto. Una parte del pasillo queda libre un segundo.")
            narrar("No sabes por qué se abren. Tampoco te importa.")
            narrar("Te cubres el rostro con el antebrazo y avanzas sin mirar atrás, respirando solo por la nariz.")
            narrar("El zumbido queda atrás poco a poco.")
            narrar("El asco, no. Y la sensación de que algo te ha estado observando desde dentro de esa masa, tampoco.")


    # TEXTO 9: Luz
    elif resp == "i" and textos_exploracion == 9:
        narrar("Le das la espalda a la luz. Lo que parpadea con esa cadencia no llama a nada bueno.")
        narrar("El pasillo de la izquierda está en penumbra total. Sin fuente visible, sin reflejo, sin nada.")
        narrar("Solo la oscuridad densa que se acumula aquí abajo cuando nada la rompe.")
        narrar("Avanzas pocos metros antes de tropezar con algo.")
        narrar("Un cuerpo reciente, aún caliente, aunque el suelo bajo él sea gélida piedra.")
        narrar("Lo que llama la atención no es el cuerpo en sí, sino que todavía tiene cosas encima.")
        narrar("Aquí abajo, los cadáveres no duran tanto. Algo los interrumpió antes de terminar.")
        tirada = random.random()
        if tirada < 0.33:
            narrar("Al moverlo para registrarlo, el brazo cae en un ángulo que no es posible.")
            narrar("Luego el cuello. Los dedos.")
            narrar("El cuerpo se dobla hacia dentro, hacia ti, sin lógica, sin aviso.")
            alerta("La boca se abre y su aullido te hiela. Esto ya no es una persona.")
            combate(personaje, enemigo_aleatorio("Perturbado"))
        elif tirada < 0.66:
            narrar("Rebuscas rápido, con una mano libre y los ojos encima del pasillo.")
            narrar("Lo que buscabas está ahí: un frasco atado al cinturón, tapado con cera, sin romper.")
            narrar("Guardado por alguien que pensaba usarlo y ya no puede.")
            narrar("No piensas en eso más de un segundo.")
            aplicar_evento({"pociones": 1}, personaje)
        else:
            narrar("El cuerpo lleva protecciones improvisadas encima. Cuero endurecido, fragmentos de quitina cosidos con nervio.")
            narrar("Tosco, pero hecho con cuidado. Alguien sabía lo que hacía cuando lo construyó.")
            narrar("Lo desmontas en silencio y lo integras sobre tu propio equipo donde más falta hace.")
            narrar("Hay algo casi ritual en aprovecharlo. Una forma de no desperdiciar lo que otro ya no puede usar.")
            aplicar_evento({"armadura": 1}, personaje)
    elif resp == "d" and textos_exploracion == 9:
        narrar("Te acercas a la luz.")
        narrar("De cerca, el parpadeo tiene un patrón. No es el viento, no es una mecha.")
        narrar("Algo pulsa dentro de ella.")
        narrar("No es una antorcha, ni un cristal. Es un brillo húmedo que late débilmente, como si respirara.")
        narrar("El reflejo se proyecta en las paredes cubiertas de sangre seca, y las sombras que lanza no coinciden con nada que tengas delante.")
        narrar("Lo que proyecta una sombra diferente a su fuente no debería existir. Aquí, existe.")
        tirada = random.random()
        if tirada < 0.33:
            narrar("Cuando estás a dos metros, la luz se apaga, se corta de repente.")
            narrar("El pasillo queda completamente negro, como si algo te hubiera cerrado los ojos.")
            narrar("Oyes el primer paso a tu izquierda. Luego a tu derecha.")
            alerta("La luz era el cebo para que te adentraras en la oscuridad.")
            combate(personaje, enemigo_aleatorio("Maniaco Mutilado"))
        elif tirada < 0.66:
            narrar("Al acercarte lo suficiente, el brillo cambia de color: se torna violaceo, azul, rosado...")
            narrar("Se vuelve más cálido, casi anaranjado, y empieza a deshacerse en una niebla baja que huele a hierro.")
            narrar("La niebla iridiscente te rodea, y sin pensarlo, respiras hondo, dejando que entre.")
            narrar("Al exhalar, tienes sensacion de mareo y la cabeza ligera. Podrias llegar a decir que te sientes 'bien'.")
            narrar("Tu instinsto te grita que te mantengas afilado, alerta, pero prosigues con una sonrisa boba en la cara.")
            aplicar_evento({"vida": 1}, personaje)
        else:
            narrar("La luz proviene del suelo, no de las paredes.")
            narrar("Hay un charco de sangre bajo tus botas, profundo, más de lo que debería poder acumularse en una mazmorra.")
            narrar("En el fondo, a través de la sangre, algo refleja.")
            narrar("Lo sacas con la mano, despacio. Un pequeño escudo metálico, completo, sin ninguna marca de combate.")
            narrar("No tiene dueño visible. No tienes forma de saber quién lo dejó caer aquí.")
            narrar("Lo secas contra la ropa y lo ajustas sobre tu equipo. La luz del charco se apaga en cuanto lo sacas.")
            aplicar_evento({"armadura": 1}, personaje)

    # TEXTO 10: Aullidos
    elif resp == "i" and textos_exploracion == 10:
        narrar("Giras a la izquierda y los aullidos estallan de repente, rebotando por el pasillo como cuchillas.")
        narrar("No hay un punto de origen. Vienen de las paredes, del techo, del suelo.")
        narrar("El sonido te rodea. No sabes cuántos son… ni desde dónde vienen.")
        narrar("Aquí abajo los que aullan no lo hacen por dolor, algo te dice que es su idioma...")
        tirada = random.random()
        if tirada < 0.4:
            narrar("Los aullidos se solapan entre sí hasta confundirse en un solo ruido sin forma.")
            narrar("Eso te da una ventana. Mientras no distinguen dónde están unos de otros, tampoco distinguen dónde estás tú.")
            narrar("Aprovechas la confusión y corres sin mirar atrás.")
            narrar("Los aullidos se pierden poco a poco entre los ecos de la mazmorra.")
            narrar("Desde lo lejos, te estar escuchado un coro cantar, pero en un idioma horrible.")
        elif tirada < 0.7:
            narrar("De pronto, uno de los aullidos cambia de tono. Se vuelve cercano. Dirigido.")
            narrar("Ya no suena a algo que grita en general. Suena a algo que te ha encontrado.")
            alerta("Un Rabioso emerge de la oscuridad, babeando sangre y aullando sin control.")
            alerta("Corre hacia ti golpeándose contra las paredes, dejando rastros carmesí.")
            narrar("Sus aullidos no son gritos de rabia o dolor. Son el único lenguaje que le queda.")
            combate(personaje, enemigo_aleatorio("Rabioso"))
        else:
            narrar("Los aullidos se apagan de golpe.")
            narrar("El silencio que les sigue es peor que el ruido. Demasiado limpio. Demasiado repentino.")
            narrar("Algo ha callado al resto, pero la espesa sombra no te permite ver nada.")
            alerta("Una figura se balancea frente a ti, murmurando incoherencias.")
            narrar("No aúlla. Solo murmura, bajo, constante, como si recitara algo que no termina nunca.")
            alerta("El Maníaco ríe mientras se acerca arrastrando sus muñones.")
            combate(personaje, enemigo_aleatorio("Maniaco Mutilado"))
    elif resp == "d" and textos_exploracion == 10:
        narrar("Tomas la derecha y los aullidos no se quedan atrás.")
        narrar("Los sonidos se multiplican y rebotan por los pasillos.")
        narrar("No sabes cuántos son… ni desde dónde vienen.")
        narrar("La piedra los duplica y los tuerce. Lo que suena como uno podría ser cinco. O al revés.")
        tirada = random.random()
        if tirada < 0.66:
            narrar("El pasillo se estrecha y eso ayuda. Menos superficie donde rebotar, menos confusión.")
            narrar("Contienes la respiración y te pegas a la pared.")
            susurros_aleatorios()
            narrar("Los aullidos se alejan poco a poco. Te quedas aturdido.")
            narrar("Lo que has oído parecía un coro, o una maldición, no lo sabes, pero dirías que has tenido suerte.")
            narrar("No los oyes más. Pero durante un rato largo, el silencio sigue teniendo su ritmo.")
        else:
            narrar("Un sonido diferente corta el resto. Más bajo, más irregular.")
            narrar("No es un aullido. Es algo que arrastra.")
            alerta("Una figura mutilada aparece arrastrándose por el suelo.")
            narrar("No tiene suficientes miembros para correr, pero no los necesita para alcanzarte.")
            alerta("Balbucea palabras sin sentido mientras se levanta con dificultad.")
            narrar("Lo que dice no es ningún idioma. Pero tiene cadencia, como si lo hubiera repetido miles de veces.")
            combate(personaje, enemigo_aleatorio("Maniaco Mutilado"))

    elif resp == "i" and textos_exploracion == 11:
        narrar("Giras a la izquierda, pero la oleada de tristeza no desaparece con el avance.")
        narrar("Este pasillo es diferente. Las paredes no tienen marcas de arañazos ni rastros de combate.")
        narrar("Solo humedad, piedra, y algo que se parece al silencio pero no lo es del todo.")
        narrar("Hay una frecuencia muy baja que no oyes, la sientes en el pecho. Pulsando.")
        narrar("Esta mazmorra lleva aquí mucho más tiempo que los que la habitan ahora.")
        narrar("Y a veces, en ciertos pasillos, eso se nota.")
        tirada = random.random()
        if tirada < 0.5:
            narrar("El silencio del pasillo te aplasta.")
            narrar("Un peso invisible cae sobre tu pecho y te cuesta respirar.")
            narrar("Recuerdos que no reconoces te atraviesan la mente, como si no fueran tuyos.")
            narrar("Una infancia que no es la tuya. Un nombre que no es el tuyo. Una pérdida que no viviste.")
            narrar("Rompes a llorar sin entender por qué, y eso es lo más perturbador de todo.")
            susurros_aleatorios()
            narrar("La mazmorra no genera estas emociones. Las extrae. Las acumula.")
            narrar("Lo que sientes ahora es el residuo de alguien que murió aquí sintiendo exactamente esto.")
            susurros_aleatorios()
            narrar("Cuando pasa, el pasillo está exactamente igual. Tú no.")
        else:
            narrar("El sentimiento se vuelve dulce y desagradable al mismo tiempo.")
            narrar("Sientes una tristeza profunda, antigua, como si este lugar llorara a través de ti.")
            narrar("No es tu tristeza. Es demasiado vieja para serlo. Demasiado fría.")
            narrar("Pero se mezcla con un humor negro, que te pide seguir riendo entre rios de sangre, estés donde estés.")
            narrar("Durante un instante te preguntas si salir de aquí tiene sentido alguno...")
            susurros_aleatorios()
            narrar("Los susurros no dicen palabras. Dicen nombres. Muchos nombres.")
            narrar("Uno de ellos podría ser el tuyo. No puedes estar seguro.")
            susurros_aleatorios()
            narrar("La sensación de que algo te ha reconocido, de que llevas aquí más tiempo del que recuerdas, no te abandona.")
        narrar("Tras unos momentos, consigues dominar tus emociones.")
        narrar("A pesar del vacío que sientes, debes seguir avanzando...")

    elif resp == "d" and textos_exploracion == 11:
        narrar("Tomas la derecha. La tristeza te sigue, como una pesada capa que te aprieta la nuez.")
        narrar("Cada paso te arranca algo por dentro, como si el pasillo se alimentara de tu pena.")
        narrar("No hay criaturas visibles. Pero aquí abajo lo invisible es lo que puede hacerte mas daño.")
        narrar("El dolor se intensifica hasta volverse casi insoportable. Caes de rodillas, luchando por recuperar el aliento.")
        narrar("Algo en este pasillo es perceptivo. Toma lo que tienes y lo amplifica.")
        tirada = random.random()
        if tirada < 0.6:
            alerta("Una figura emerge lentamente entre la penumbra, atraída por tu debilidad.")
            narrar("No corre. Sabe que no necesita hacerlo. Lo que sientes ahora te hace más lento, más torpe.")
            narrar("El combate es real, pero el verdadero daño ya estaba hecho antes de que empezara.")
            combate(personaje, enemigo_aleatorio())
            narrar("A pesar de la intensidad del combate, sientes un vacío en tu pecho...")
            narrar("Pero sabes que así eres presa fácil, así que tienes que seguir adelante.")
        else:
            narrar("La figura no llega. La tristeza llega a su pico y luego, de golpe, se rompe.")
            narrar("Como un cristal que cede. Como un peso que alguien ha retirado sin avisar.")
            susurros_aleatorios()
            narrar("El pasillo queda en silencio. Un silencio distinto, limpio.")
            narrar("En el suelo, donde el dolor era más intenso, hay algo.")
            narrar("Dos frascos. Intactos. Como si alguien los hubiera dejado aquí a propósito, sabiendo que llegarías.")
            narrar("O como si la propia mazmorra, por una vez, devolviera algo de lo que lleva tomando.")
            narrar("O quizas no quiere matar tu esperanza, para poder seguir alimentandose...")
            narrar("No buscas más explicación. Los guardas y sigues.")
            aplicar_evento({"pociones": 2}, personaje)
    
    elif resp == "i" and textos_exploracion == 12:
        narrar("Sigues el olor por la izquierda, que se hace cada vez más intenso.")
        narrar("Es dulzón, orgánico, con algo de madera húmeda y especias que no deberían existir aquí abajo.")
        narrar("Te recuerda vagamente a algo que te daba calma… o eso crees.")
        narrar("No puedes precisar qué. Solo que en algún momento de tu vida, ese olor significaba que estabas a salvo.")
        narrar("Por unos instantes, te sientes tranquilo. Si pudieras recordar cómo era, dirías que sientes felicidad...")
        narrar("El pasillo deja de parecer una mazmorra. Las paredes dejan de sangrar. El suelo no cruje.")
        narrar("Por un instante bajas la guardia, convencido de que aquí no hay peligro.")
        tirada = random.random()
        if tirada < 0.7:
            narrar("Ves algo al fondo del pasillo. Una silueta.")
            narrar("Por un momento, tu cabeza la convierte en alguien que conoces.")
            narrar("Alguien que llevabas tiempo sin ver. Alguien que te falta.")
            narrar("Abres la boca. Casi dices su nombre.")
            narrar("El olor se corta de golpe.")
            narrar("La silueta no está. Nunca estuvo.")
            narrar("Cuando el olor se desvanece, te das cuenta de que estas sentado junto a un cadaver.")
            narrar("Sacudes la cabeza con rabia. No puedes permitirte esto. Aquí no.")
        else:
            narrar("El olor te lleva hasta una figura al fondo del pasillo.")
            narrar("Está de espaldas. Pequeña. Con una postura que reconoces antes de ver la cara.")
            narrar("Une las piezas despacio: la forma de los hombros, la inclinación de la cabeza.")
            narrar("El aroma lo completa todo. Tu cuerpo lo cree antes de que tu mente pueda negarlo.")
            narrar("Abres la boca para llamarla, lleno de esperanza por un instante... Y se gira.")
            narrar("Ves un destrozo de cicatrices donde imaginabas un rostro amable.")
            narrar("El efecto del aroma te abandona en el peor momento posible.")
            narrar("Lo que tienes delante no tiene nada que ver con lo que viste en tu cabeza.")
            narrar("El maníaco sacude el cuello entre chasquidos, como despertando él también de algo.")
            alerta("Te mira con ojos vacíos y carga sin transición, sin aviso, sin lógica.")
            combate(personaje, enemigo_aleatorio("Maniaco Mutilado"))
    elif resp == "d" and textos_exploracion == 12:
        narrar("Tomas la derecha. El olor dulzón te envuelve por completo antes de dar diez pasos.")
        narrar("Es cálido, casi reconfortante. Te hace pensar en hogar… en seguridad.")
        narrar("En alguien esperándote. En una puerta abierta. En luz natural.")
        narrar("Aquí abajo no hay nada de eso, pero el aroma convence al cuerpo antes que a la mente.")
        narrar("Te mueves casi automáticamente, siguiendo el dulce rastro sin decidirlo.")
        tirada = random.random()
        if tirada < 0.4:
            narrar("El pasillo desemboca en una sala pequeña. Vacía, o eso parece al principio.")
            narrar("En el centro hay una figura encorvada, inmóvil, con la cabeza gacha.")
            narrar("El olor viene de ella. De su ropa, de su piel, de algo que segrega sin saberlo.")
            narrar("Cuando levanta la cabeza, tu mente intenta construir una cara familiar con los retazos que tiene.")
            narrar("No puede. Lo que hay debajo del aroma no se parece a nada que hayas querido.")
            alerta("El maníaco te mira con ojos vacíos y carga sin transición, sin aviso, sin lógica.")
            combate(personaje, enemigo_aleatorio("Maniaco Mutilado"))
            narrar("Cuando termina, tienes ese olor pegado en la ropa y en el pelo.")
            narrar("Ya no te parece tan reconfortante. Es el olor de algo que te usó.")
            narrar("Continúas tu marcha, asqueado, intentando no respirar por la nariz.")
        else:
            narrar("El rastro se diluye antes de llegar a ningún sitio.")
            narrar("El pasillo queda vacío. El olor, apagado. La ilusión, rota.")
            narrar("Te detienes un momento en medio de la nada, esperando algo que no llega.")
            narrar("Solo hay silencio y la sensación de haber sido engañado por tu propio cerebro.")
            narrar("Sacudes la cabeza. Sigues. No puede haber nada aquí que despierte lo que acababas de sentir.")

    elif resp == "i" and textos_exploracion == 13:
        narrar("Le das la espalda al tumulto y tomas la izquierda.")
        narrar("El sonido queda atrás, pero no del todo. Sigue llegando en oleadas, amortiguado por la distancia y la piedra.")
        narrar("Ese ruido no es de combate. No hay gritos formados ni golpes secos de arma.")
        narrar("Es algo que se mueve contra sí mismo. Que crece y se reordena.")
        narrar("Llevas unos veinte pasos cuando el eco desaparece. El silencio que lo sustituye es más pesado.")
        tirada_i = random.random()
        if tirada_i < 0.4:
            narrar("El pasillo se dobla en un recodo estrecho. Ahí, en el hueco entre dos afloramientos de piedra, hay algo.")
            narrar("Un frasco. Tapado con cera. Sin romper.")
            narrar("No hay cadáver cerca, no hay bolsa, no hay rastro de quién lo dejó.")
            narrar("Solo el frasco, solo, como si alguien hubiera decidido en ese punto exacto que ya no lo necesitaba.")
            narrar("No piensas en eso más de un segundo. Lo guardas y sigues.")
            aplicar_evento({"pociones": 1}, personaje)
        else:
            narrar("El pasillo no da señales de vida. Solo humedad, piedra y el olor denso de algo orgánico que se descompone en algún lugar cercano.")
            narrar("Llegas al otro lado sin encontrar nada ni nadie.")
            narrar("El tumulto que dejaste atrás sigue rumiando en algún punto del pasillo.")
            narrar("Lo que sea que lo formaba, ya no te persigue. De momento.")
    elif resp == "d" and textos_exploracion == 13:
        narrar("Te acercas al tumulto y el ruido cambia de naturaleza.")
        narrar("Ya no es solo movimiento. Es algo húmedo, visceral, como carne que trabaja.")
        narrar("El bulto en el centro del pasillo late. No tiembla: late, con su propio ritmo, como si tuviera un corazón.")
        narrar("La superficie que lo forma es oscura y palpitante, recubierta de una mucosidad brillante.")
        narrar("No parece un enemigo esperando. Parece algo haciéndose.")
        alerta("Cuando das un paso más, la masa se sacude, se hiende por el centro y algo sale de dentro.")
        tirada_d = random.random()
        if tirada_d < 0.55:
            narrar("Lo que emerge  es grande, es rápido. Demasiado rápido para su tamaño.")
            narrar("Un cuerpo que fue humano en algún momento, retorcido hacia dentro, con los huesos reordenados.")
            alerta("El Perturbado no corre, se lanza, arrojándose hacia ti en línea recta, sin instinto de conservación.")
            combate(personaje, enemigo_aleatorio("Perturbado"))
            narrar("Cuando cae, el bulto original ya no está. Solo queda el suelo manchado y ese olor a carne viva.")
        else:
            narrar("No tienes tiempo de retroceder.")
            alerta("La pústula estalla con un chasquido húmedo y sordo, sin aviso, sin transición.")
            narrar("El icor te cubre de golpe. Cálido, denso, con ese olor ácido que pica en la garganta y en los ojos.")
            narrar("Completamente asqueado, te limpias todo lo posible, pero el daño ya está hecho.")
            narrar("El líquido se filtra entre las juntas, entre las correas, entre las capas del equipo.")
            narrar("El cuero se ablanda. El metal pierde el brillo en segundos, como si se oxidara desde dentro.")
            alerta("Tu armadura ha sido corroída por el icor de las larvas.")
            aplicar_evento({"armadura": -1}, personaje)
        narrar("El pasillo vuelve a quedar en silencio, salvo por tu respiración agitada.")

    elif resp == "i" and textos_exploracion == 14:
        narrar("Giras a la izquierda. La ligereza que sientes en la cabeza no cede, sino que se asienta más.")
        narrar("Los pasos se vuelven automáticos. No hay señales de alarma en ningún rincón de tu mente.")
        narrar("Eso debería preocuparte, pero no te preocupa.")
        susurros_aleatorios()
        narrar("El pasillo desemboca en una capilla deformada, llena de humedad, sangre y perversos ídolos.")
        narrar("Antiguos símbolos religiosos han sido raspados y reemplazados por marcas rituales, trazadas con algo oscuro y reciente.")
        narrar("Lo registras. No reaccionas. La mente ligera no te lo permite.")
        susurros_aleatorios()
        alerta("Unas manos te atrapan antes de que tu cuerpo decida hacer algo. Te arrastran al centro de la capilla.")
        tirada = random.random()
        if tirada < 0.2:
            narrar("Un puñado de mutilados te sostienen y empujan con sus muñones y bocas.")
            alerta("Te sientes atrapado, sin poder moverte, cuando de pronto una mole de carne aullante surge del fondo.")
            alerta("Un maníaco rabioso babea y se lanza contra ti.")
            narrar("Al advertir el peligro, sacas fuerzas para sacudirte a los cultistas y prepararte para el combate.")
            combate(personaje, enemigo_aleatorio("Rabioso"))
        elif tirada < 0.4:
            narrar("Un puñado de mutilados te sostienen y empujan con sus muñones y bocas.")
            alerta("Te sientes atrapado, sin poder moverte, cuando de pronto una mole de carne aullante surge del fondo.")
            narrar("Al advertir el peligro, sacas fuerzas para sacudirte a los cultistas y prepararte para el combate.")
            narrar("Pero de pronto, la cabeza del rabioso estalla llenándolo todo de sangre.")
            narrar("La sangre hierve en el aire… el ambiente se vuelve turbio.")
            narrar("Los cultistas aullan de miedo sin cesar, hasta desvanecerse sangrando por todas partes.")
            narrar("De pronto sientes que te elevas, y te das cuenta de que estás en medio de una grotesca fuente humana de sangre.")
            narrar("Oyes una risa perversa por todas partes. Las velas se encienden, pero todo está negro.")
            susurros_aleatorios()
            narrar("Te encuentras hundido en un mar de sangre, luchando y pataleando por salir a flote.")
            narrar("Notas garras y golpes por todo tu cuerpo, y algo presiona con fuerza tratando de meterse en tu cabeza.")
            susurros_aleatorios()
            narrar("Cuando recobras el sentido, estás en medio de la sala, con tu arma en la mano y una masacre bajo tus pies.")
            narrar("Has matado a casi todos los cultistas mientras luchabas por salir de ese grotesco mar de sangre.")
            narrar("Los pocos vivos siguen rezando, golpeando sus frentes contra el suelo con ese sonido horrible.")
            narrar("Será mejor que salgas de aquí antes de que ocurra algo peor...")
        elif tirada < 0.6:
            narrar("Un puñado de mutilados te sostienen y empujan con sus muñones y bocas.")
            alerta("Las velas negras se apagan de golpe y una sombra se descuelga del techo.")
            susurros_aleatorios()
            alerta("Todos los cultistas caen al suelo con el cuello seccionado.")
            narrar("Te encuentras en medio de una grotesca fuente humana de sangre.")
            susurros_aleatorios()
            narrar("Oyes una risa perversa por todas partes. Las velas se encienden, pero todo está negro.")
            alerta("Menos unos filos brillantes que aparecen entre las sombras más oscuras...")
            if personaje["sombra"] < 3:
                combate(personaje, enemigo_aleatorio("Sombra tenebrosa"))
        elif tirada < 0.8:
            narrar("Un puñado de mutilados te sostienen y empujan con sus muñones y bocas.")
            narrar("Te sientes atrapado, pero sacas fuerza de flaqueza para sacudirte a los cultistas.")
            tirada = random.randint(1, 25)
            if tirada < personaje["destreza"] or tirada < personaje["fuerza"]:
                narrar("Consigues zafarte de la mayoría, atravesándolos con tu arma o inutilizando sus pocos miembros buenos.")
                alerta("Pero uno de ellos se levanta y te ataca por la espalda.")
                combate(personaje, enemigo_aleatorio("Maniaco Mutilado"))
            else:
                narrar("No consigues herirlos a todos, pero sí liberarte de ellos y salir corriendo.")
                alerta("Te zafas a duras penas, sintiendo mientras huyes cómo clavan sus dientes y garras en tu carne.")
                alerta("Carecen de miembros para correr, pero consiguen hacerte heridas profundas. -3 de vida.")
                aplicar_evento({"vida": -3}, personaje)
        else:
            narrar("Un puñado de mutilados te sostienen y empujan con sus muñones y bocas.")
            narrar("Los mutilados se detienen de pronto. Te sueltan y se paran en círculo a tu alrededor.")
            if personaje["sombra"] > 0:
                narrar("Los cultistas desmembrados se postran ante ti.")
                narrar("Se inclinan violentamente golpeando sus cabezas contra el suelo, salpicando sangre por todos lados.")
                preguntar("Parece que eres el centro de su ritual. Quieres dejar que terminen? s/n")
                resp_ritual = pedir_input().strip().lower()
                if resp_ritual in ["s", "si"]:
                    narrar("Esperas a que los cultistas realicen el ritual.")
                    narrar("Se pasan un buen rato machacando rítmicamente sus cabezas contra el suelo, sin dejar de rezar.")
                    narrar("No parece que sientan nada, están en una especie de trance autodestructivo.")
                    narrar("¿O quizás es que algo los controla?")
                    susurros_aleatorios()
                    narrar("Tras unos minutos de golpes incesantes, las runas del suelo se llenan con la sangre de los cultistas.")
                    susurros_aleatorios()
                    narrar("Cuando la sangre llena los símbolos por completo, los cultistas dan un último grito desgarrador.")
                    alerta("Sin tiempo a reaccionar, un brillo mortecino recorre el círculo de cultistas a la altura del cuello.")
                    susurros_aleatorios()
                    narrar("Los cultistas se desangran a chorros, bañando toda la sala.")
                    alerta("La sangre acumulada toma forma. Una sombra sangrienta se alza y se dirige hacia ti blandiendo filos ocultos.")
                    combate(personaje, enemigo_aleatorio("Sombra tenebrosa"))
                else:
                    narrar("A pesar de no querer enfadarlos, prefieres no quedarte a ver qué pasa.")
                    narrar("Lleno de nervios, te mueves rápidamente fuera de la sala.")
                    narrar("Desde la puerta ves cómo los mutilados continúan con su ritual. No quieres ver el final.")
            else:
                narrar("Estás tenso, mirando a los mutilados que clavan sus ojos enfermos en ti.")
                hambre = random.random()
                if hambre < 0.5:
                    narrar("Su aspecto es horrible, apenas dirías que son humanos, pero intuyes curiosidad en sus ojos.")
                    alerta("Sin previo aviso, los mutilados babeando se avalanzan sobre ti como si fueras un banquete.")
                    chequeo_fuerza = random.randint(1, 25)
                    if personaje["fuerza"] > chequeo_fuerza or personaje["destreza"] > chequeo_fuerza:
                        narrar("Consigues zafarte de la mayoría, atravesándolos con tu arma o inutilizando sus pocos miembros buenos.")
                        alerta("Casi todos quedan inútiles, menos uno que te ataca por la espalda.")
                        combate(personaje, enemigo_aleatorio("Maniaco Mutilado"))
                    else:
                        alerta("No consigues esquivar todos sus dientes. Te hacen heridas profundas.")
                        aplicar_evento({"vida": -3}, personaje)
                        narrar("A duras penas acabas con todos y respiras de alivio.")
                        alerta("Pero cuando crees estar a salvo, uno de ellos te ataca por la espalda.")
                        combate(personaje, enemigo_aleatorio("Maniaco Mutilado"))
                else:
                    narrar("Los mutilados te miran con sus ojos enfermos y el horror te invade.")
                    narrar("Trozos de hueso, uñas de más, cuernos y bultos con pelo... no ves más que eso.")
                    narrar("Sin embargo, uno de ellos te ofrece una ristra de pociones atadas con piel.")
                    narrar("Reticente pero sin ganas de enfadarlos, coges las pociones y asientes.")
                    aplicar_evento({"pociones": 2}, personaje)
                    narrar("Los mutilados se arrodillan y permanecen en silencio.")
                    narrar("Tras unos minutos sin saber qué hacer, decides que es mejor salir de ahí.")
                    narrar("Antes de abandonar la capilla, echas la vista atrás. Los cultistas siguen en la misma posición.")
                    narrar("Te sientes aturdido, afortunado, y totalmente vulnerable a esta mazmorra.")

    elif resp == "d" and textos_exploracion == 14:
        narrar("Giras a la derecha. La ligereza en la cabeza se vuelve casi dulce, casi cálida.")
        narrar("El pasillo de la derecha desemboca en una nave lateral de la capilla.")
        narrar("Las paredes están cubiertas de frescos profanados y restos humanos cosidos a la piedra.")
        narrar("Deberías pararte. No te paras.")
        susurros_aleatorios()
        narrar("Los mutilados te rodean antes de que termines de procesar dónde estás. Algo cambia en sus miradas.")
        narrar("No es agresión. Es reconocimiento.")
        susurros_aleatorios()
        narrar("Ves un altar central con una cruz de piedra. Te llevan hacia allí, y tú no ofreces resistencia.")
        tirada = random.random()
        if tirada < 0.1:
            narrar("Te lanzan contra el altar central. Te atan toscamente con cuerdas de pelo y piel a una cruz.")
            alerta("Uno de ellos grita y carga contra ti sin dudarlo. Te clava un hueso largo y afilado en las costillas.")
            narrar("Sientes un dolor enorme, pero no dejas de fijarte cómo se amontonan más y más maníacos delante de ti.")
            narrar("Todos gritan, se convulsionan y saltan en medio de la sala. Ves peleas y algunos que se devoran entre sí.")
            alerta("Te lanzan heces, piedras, huesos. Sientes todos los golpes, pero el miedo es más grande que el dolor.")
            narrar("Cuando la escena no puede ir a peor, uno de ellos trepa por la cruz donde estás.")
            alerta("Comienza a morderte y arrancarte la carne. Más se unen a él. Te están devorando.")
            narrar("De todos los finales que preveías, este es peor que cualquiera.")
            fin_derrota(personaje)
        elif tirada < 0.66:
            narrar("Ves una extraña gema oscura en el altar. A pesar de tu situación, sientes la urgencia de tomarla.")
            alerta("Uno de los que tiene un brazo funcional agarra la oscura gema y te la estampa en la cabeza.")
            narrar("El dolor es enorme, inmediato, pero placentero... Eso es lo que no tiene sentido.")
            narrar("De la gema surge una niebla oscura que te envuelve los hombros, el cuello, la cara.")
            narrar("Los cultistas gritan de éxtasis mientras la niebla se enrosca y penetra en tu cuerpo.")
            susurros_aleatorios()
            narrar(".\n..\n...\nTe levantas sin saber que ha pasado, pero te sientes diferente.")
            narrar("No sabes durante cuánto rato has estado aqui. Cuando miras, los mutilados están desplomados.")
            narrar("La ligereza que sentías en la cabeza ya no está. A vuelto la familiar sensacion de peligro constante.")
            narrar("Ninguno de los mutilados respira. No sabes si los has matado tú.")
            susurros_aleatorios()
            narrar("Caminas hacia la salida. El pasillo es el mismo, tú no.")
            if random.random() < 0.5:
                narrar("Intentas pensar en tu siguiente combate, intentando recuperar la concentración.")
                narrar("Te imaginas, los golpes, lo tajos, la sangre... Eso te hace sentir mejor.")
                narrar("Te resulta raro, pero funciona. Y eso, aquí dentro, es lo único que importa.")
                aplicar_evento({"fuerza": 1}, personaje)
            else:
                narrar("Intentas pensar en los susurros, intentando recuperar la concentración.")
                susurros_aleatorios()
                narrar("Te resulta raro, pero eso te hace sentir algo mejor.")
                aplicar_evento({"destreza": 1}, personaje)
        else:
            narrar("Los mutilados se detienen todos a la vez. En mitad de un gesto, en mitad de un paso.")
            narrar("Luego caen.")
            narrar("No convulsionan, no gritan. Solo caen, como si algo los hubiera apagado desde dentro.")
            susurros_aleatorios()
            narrar("No entiendes qué ha pasado. Quizás el ritual necesitaba a alguien que no llegó.")
            narrar("Quizás tú eras demasiado poco para lo que invocaban, o demasiado.")
            narrar("No esperas a saberlo. Sales antes de que la capilla decida terminar contigo lo que han dejado a medias.")

    
    elif resp == "i" and textos_exploracion == 15:
        narrar("Sigues los símbolos hacia la izquierda. No sabes si te guían o te confunden.")
        narrar("El pasillo se ensancha. La piedra cede paso a una bóveda circular con un foso en el centro.")
        narrar("Hay varios cultistas rabiosos dentro del foso. Están luchando entre ellos, rodeados por restos de los anteriores combates.")
        narrar("Por turnos. Con una lógica mínima que no esperabas encontrar aquí abajo.")
        narrar("El que gana, permanece. El que pierde, no. Ninguno dura mucho tiempo...")
        narrar("En el borde superior, un maniaco más alto que los demás permanece quieto. Te observa.")
        narrar("Este es un templo de algo que no tiene nombre pero reconoce la violencia como liturgia.")
        narrar("El jefe te mira sin expresión, sin emoción. Te está evaluando.")
        preguntar("¿Qué haces? (c)ombatir en el foso / (m)archarte")
        resp2 = leer_input("> ", personaje)
        while resp2 not in ["c", "combatir", "m", "marcharte", "marchar"]:
            alerta("Elige: (c)ombatir o (m)archarte")
            resp2 = leer_input("> ", personaje)
        if resp2 in ["m", "marcharte", "marchar"]:
            narrar("Asientes una sola vez en dirección al Rabioso jefe, intentando mostrar seguridad.")
            narrar("No sabes si lo entiende. Pero te sigue con la mirada mientras abandonas su ritual.")
            narrar("Sales sin querer saber más. Los gritos y los golpes resuenan un buen rato.")
        else:
            narrar("Lo entiendes instintivamente. Cuando termina el combate en curso, desenvainas tu arma.")
            narrar("Saltas al foso. El jefe te mira e inclina la cabeza un milímetro. Señal o gesto vacío, no lo sabes.")
            narrar("El primer combatiente se vuelve hacia ti. Las reglas son claras: matar o morir.")
            en_foso = True
            # — Combate 1 —
            combate(personaje, enemigo_aleatorio("Rabioso"))
            if personaje.get("_huyo_combate"):
                en_foso = False
            # — Flee check antes del combate 2 —
            if en_foso:
                narrar("El primer cultista cae. El foso guarda silencio un momento.")
                narrar("Al fondo, el jefe te observa con el hacha en la mano. Gesticula a otro guerrero para que baje.")
                preguntar("¿Quieres seguir luchando contra los maniacos?")
                preguntar("¿O intentas salir del foso? (s)eguir / (h)uir")
                resp3 = leer_input("> ", personaje)
                # [SECRETO 2a] Hablar si sangre > 1
                if resp3 == "hablar" and personaje["sangre"] > 1:
                    narrar("Cierras los ojos. La sangre en tus manos grita más fuerte que los maniacos.")
                    narrar("Cuando hablas, es con una voz que no reconoces: antigua, sangrienta, que llama a los cuerpos.")
                    narrar("Los maniacos se detienen. Uno de ellos mira al jefe, confundido, como si esperara órdenes de una autoridad que ya no está ahí.")
                    narrar("Entienden lo que eres. Y lo que pueden ser.")
                    personaje["sangre"] += 1
                    narrar("La sangre siempre reconoce a los suyos.")
                    preguntar("¿O intentas salir del foso? (s)eguir / (h)uir")
                    resp3 = leer_input("> ", personaje)
                while resp3 not in ["s", "seguir", "h", "huir"]:
                    alerta("Elige: (s)eguir o (h)uir")
                    resp3 = leer_input("> ", personaje)
                if resp3 in ["h", "huir"]:
                    chequeo_escape = random.randint(1, 25)
                    if chequeo_escape < personaje["fuerza"] or chequeo_escape < personaje["destreza"]:
                        narrar("Sabes que no sobreviviras si te quedas, pero a pesar del miedo, sales corriendo del foso.")
                        narrar("Trepas el borde antes de que reaccionen. El jefe los pone en alerta, y comienzan a perseguirte.")
                        narrar("Te dejas las unas en salir, pero consigues ganar algo de distancia y dejarlos atras. Sabes que te buscaran...") 
                        en_foso = False
                    else:
                        alerta("Intentas trepar por el borde, pero una pedrada te derriba.")
                        narrar("Tu oponente ya listo te arrastra al centro. El foso no ha terminado contigo.")
            # — Combate 2 —
            if en_foso:
                narrar("Salta sin pernsarlo. Es un maniaco más grande que los anteriores, con cicatrices que lo recorren de arriba abajo.")
                alerta("Levanta su garrote oxidado y ruge como una bestia. No hay descanso...")
                combate(personaje, enemigo_aleatorio("Rabioso"))
                if personaje.get("_huyo_combate"):
                    en_foso = False
            # — Flee check antes del combate 3 (jefe) —
            if en_foso:
                narrar("Dos abajo. El foso esta encharcado de sangre.")
                narrar("El lider maniaco baja al foso blandiendo su hacha casi tan grande como él.")
                narrar("Se para al fondo del foso, y te mira con una locura fria, calculadora, distinta a la de los anteriores.")
                preguntar("¿Intentas salir del foso? (s)eguir / (h)uir")
                resp4 = leer_input("> ", personaje)
                while resp4 not in ["s", "seguir", "h", "huir"]:
                    alerta("Elige: (s)eguir o (h)uir")
                    resp4 = leer_input("> ", personaje)
                if resp4 in ["h", "huir"]:
                    chequeo_escape = random.randint(1, 25)
                    narrar("Sabes que no sobreviviras si te quedas, pero a pesar del miedo, sales corriendo del foso.")
                    narrar("Trepas el borde antes de que reaccionen. El jefe los pone en alerta, y comienzan a perseguirte.")
                    narrar("Te dejas las unas en salir, pero consigues ganar algo de distancia y dejarlos atras. Sabes que te buscaran...") 
                    en_foso = False
                else:
                    alerta("Intentas trepar por el borde, pero una pedrada te derriba.")
                    narrar("Tu oponente ya listo te arrastra al centro. El foso no ha terminado contigo.")
            # — Combate 3: el jefe —
            if en_foso:                
                narrar("Con solo el peso de sus pasos contra la piedra hace retumbar el foso.")
                narrar("Los pocos cultistas que quedan vivos se ponen freneticos al ver a su jefe entrar.")
                alerta("El gigante profiere un rugido ensordecedor.")
                dialogo("'¡KA-BANDA KHAR-DUM!¡¡KA-BANDA SANGUOR REX!!'")
                combate(personaje, enemigo_aleatorio("Rabioso"))
                if not personaje.get("_huyo_combate"):
                    narrar("El combate ha sido brutal. El Rabioso sigue vivo a pesar de haberle cortado la garganta.")
                    narrar("Aplastas su cabeza con tu bota. Varias veces para estar seguro.")
                    narrar("Miras a tu alrededor. El foso está lleno de cadáveres, mas que antes.")
                    narrar("Todos los cultistas que observaban se han quitado la vida al ver caer a su líder.")
                    narrar("No sientes pena, no sientes nada. Solo la urgencia de tomar esa hacha y usarla.")
                    narrar("El hacha tiene el mango dentado, hecho por un artesano loco, fanatico del dolor.")
                    narrar("Al sentir como el hacha hiere tus manos, te sientes mas fuerte. No sientes dolor, solo ira.")
                    alerta("El Hacha Maldita inflige daño brutal, pero cada golpe certero también te desgarra a ti.")
                    añadir_arma(personaje, "Hacha Maldita")

    elif resp == "d" and textos_exploracion == 15:
        narrar("Giras a la izquierda.")
        narrar("Llevas unos pasos cuando lo recuerdas: las marcas solo estaban en la izquierda.")
        narrar("Deberías ir hacia la derecha. Hacia donde guían.")
        narrar("Tus pensamientos son confusos. Quieres volver atrás, pero sigues avanzando...")
        susurros_aleatorios()
        narrar("El pasillo gira. Luego otra vez. Bajas sin recordar haber bajado.")
        narrar("Llegas a un borde. Hay un foso abajo. Hay Rabiosos en el foso.")
        narrar("No tienes tiempo de procesar más. Sientes la adrenalina pulsando en tu cerebro.")
        preguntar("¿Qué haces? (h)uir / (l)uchar")
        resp2 = leer_input("> ", personaje)
        while resp2 not in ["h", "huir", "l", "luchar"]:
            alerta("Elige: (h)uir o (l)uchar")
            resp2 = leer_input("> ", personaje)
        en_foso = True
        if resp2 in ["h", "huir"]:
            chequeo_escape = random.randint(1, 25)
            if chequeo_escape < personaje["fuerza"] or chequeo_escape < personaje["destreza"]:
                narrar("Das media vuelta. El cuerpo, por una vez, te obedece.")
                narrar("Oyes los Rabiosos abajo. Nadie sube.")
                narrar("No sabes si te han dejado ir o simplemente no les interesas todavía.")
                en_foso = False
            else:
                alerta("Intentas girar. El suelo cede bajo tu pie. Caes al foso.")
        else:
            narrar("Te preparas para el salto.")
        # — Combate 1 —
            combate(personaje, enemigo_aleatorio("Rabioso"))
            if personaje.get("_huyo_combate"):
                en_foso = False
            # — Flee check antes del combate 2 —
            if en_foso:
                narrar("El primer cultista cae. El foso guarda silencio un momento.")
                narrar("Al fondo, el jefe te observa con el hacha en la mano. Gesticula a otro guerrero para que baje.")
                preguntar("¿Quieres seguir luchando contra los maniacos?")
                preguntar("¿O intentas salir del foso? (s)eguir / (h)uir")
                resp3 = leer_input("> ", personaje)
                # [SECRETO 2b] Hablar si sangre > 1
                if resp3 == "hablar" and personaje["sangre"] > 1:
                    narrar("Cierras los ojos. La sangre en tus manos grita más fuerte que los maniacos.")
                    narrar("Cuando hablas, es con una voz que no reconoces: antigua, sangrienta, que llama a los cuerpos.")
                    narrar("Los maniacos se detienen. Uno de ellos mira al jefe, confundido, como si esperara órdenes de una autoridad que ya no está ahí.")
                    narrar("Entienden lo que eres. Y lo que pueden ser.")
                    personaje["sangre"] += 1
                    narrar("La sangre siempre reconoce a los suyos.")
                    preguntar("¿O intentas salir del foso? (s)eguir / (h)uir")
                    resp3 = leer_input("> ", personaje)
                while resp3 not in ["s", "seguir", "h", "huir"]:
                    alerta("Elige: (s)eguir o (h)uir")
                    resp3 = leer_input("> ", personaje)
                if resp3 in ["h", "huir"]:
                    chequeo_escape = random.randint(1, 25)
                    if chequeo_escape < personaje["fuerza"] or chequeo_escape < personaje["destreza"]:
                        narrar("Sabes que no sobreviviras si te quedas, pero a pesar del miedo, sales corriendo del foso.")
                        narrar("Trepas el borde antes de que reaccionen. El jefe los pone en alerta, y comienzan a perseguirte.")
                        narrar("Te dejas las unas en salir, pero consigues ganar algo de distancia y dejarlos atras. Sabes que te buscaran...") 
                        en_foso = False
                    else:
                        alerta("Intentas trepar por el borde, pero una pedrada te derriba.")
                        narrar("Tu oponente ya listo te arrastra al centro. El foso no ha terminado contigo.")
            # — Combate 2 —
            if en_foso:
                narrar("Salta sin pernsarlo. Es un maniaco más grande que los anteriores, con cicatrices que lo recorren de arriba abajo.")
                alerta("Levanta su garrote oxidado y ruge como una bestia. No hay descanso...")
                combate(personaje, enemigo_aleatorio("Rabioso"))
                if personaje.get("_huyo_combate"):
                    en_foso = False
            # — Flee check antes del combate 3 (jefe) —
            if en_foso:
                narrar("Dos abajo. El foso esta encharcado de sangre.")
                narrar("El lider maniaco baja al foso blandiendo su hacha casi tan grande como él.")
                narrar("Se para al fondo del foso, y te mira con una locura fria, calculadora, distinta a la de los anteriores.")
                preguntar("¿Intentas salir del foso? (s)eguir / (h)uir")
                resp4 = leer_input("> ", personaje)
                while resp4 not in ["s", "seguir", "h", "huir"]:
                    alerta("Elige: (s)eguir o (h)uir")
                    resp4 = leer_input("> ", personaje)
                if resp4 in ["h", "huir"]:
                    chequeo_escape = random.randint(1, 25)
                    narrar("Sabes que no sobreviviras si te quedas, pero a pesar del miedo, sales corriendo del foso.")
                    narrar("Trepas el borde antes de que reaccionen. El jefe los pone en alerta, y comienzan a perseguirte.")
                    narrar("Te dejas las unas en salir, pero consigues ganar algo de distancia y dejarlos atras. Sabes que te buscaran...") 
                    en_foso = False
                else:
                    alerta("Intentas trepar por el borde, pero una pedrada te derriba.")
                    narrar("Tu oponente ya listo te arrastra al centro. El foso no ha terminado contigo.")
            # — Combate 3: el jefe —
            if en_foso:
                narrar("Con solo el peso de sus pasos contra la piedra hace retumbar el foso.")
                narrar("Los pocos cultistas que quedan vivos se ponen freneticos al ver a su jefe entrar.")
                alerta("El gigante profiere un rugido ensordecedor.")
                dialogo("'¡KA-BANDA KHAR-DUM!¡¡KA-BANDA SANGUOR REX!!'")
                combate(personaje, enemigo_aleatorio("Rabioso"))
                if not personaje.get("_huyo_combate"):
                    narrar("El combate ha sido brutal. El Rabioso sigue vivo a pesar de haberle cortado la garganta.")
                    narrar("Aplastas su cabeza con tu bota. Varias veces para estar seguro.")
                    narrar("Miras a tu alrededor. El foso está lleno de cadáveres, mas que antes.")
                    narrar("Todos los cultistas que observaban se han quitado la vida al ver caer a su líder.")
                    narrar("No sientes pena, no sientes nada. Solo la urgencia de tomar esa hacha y usarla.")
                    narrar("El hacha tiene el mango dentado, hecho por un artesano loco, fanatico del dolor.")
                    narrar("Al sentir como el hacha hiere tus manos, te sientes mas fuerte. No sientes dolor, solo ira.")
                    alerta("El Hacha Maldita inflige daño brutal, pero cada golpe certero también te desgarra a ti.")
                    añadir_arma(personaje, "Hacha Maldita")

    if personaje.get("_huyo_combate", False):
        reiniciar_camino_por_huida(personaje)
        return True

    # ================== CHECKEO NIVEL 2 ==================
    if personaje["nivel"] == 2 and resp in ["i", "d"]:
        estado["ruta_jugador"].append(resp)

        progreso_n2 = racha(estado["ruta_jugador"], ruta_correcta_nivel2)
        progreso_s  = racha(estado["ruta_jugador"], ruta_secreta)

        # Progreso del paso ANTERIOR (sin el último paso) para detectar caídas
        prev = estado["ruta_jugador"][:-1]
        prev_n2 = racha(prev, ruta_correcta_nivel2) if prev else 0
        prev_s  = racha(prev, ruta_secreta)         if prev else 0
        # "perdido": estaba siguiendo una ruta (max previo >= 2) y ahora ha retrocedido
        perdio_ruta = (len(estado["ruta_jugador"]) >= 3
                       and max(prev_n2, prev_s) >= 2
                       and max(progreso_n2, progreso_s) < max(prev_n2, prev_s))

        # Sincronizar las listas de seguimiento con el progreso real
        estado["pasos_nivel2"][:]  = ruta_correcta_nivel2[:progreso_n2]
        estado["pasos_secretos"][:] = ruta_secreta[:progreso_s]

        # ── PERDIDO: bajó el progreso tras haber avanzado (prioridad máxima) ──────
        if perdio_ruta:
            narrar("Sigues el hedor de la sangre, pero lo notas diferente.")
            narrar("No reconoces el pasillo, dirías que has perdido el rastro del camino principal...")
            if "Hoja de la Noche" in estado["armas_jugador"]:
                narrar("Las llamas de la Hoja de la Noche se apagan. Te invade una desesperación momentánea.")

        # ── RUTA SECRETA: pista con Hoja de la Noche ────────────────────────────
        elif progreso_s >= 3 and "Hoja de la Noche" in estado["armas_jugador"] and personaje.get("_pw", 0) != 1:
            textos = [
                "Las llamas negras se intensifican y se pierden en la oscuridad sin iluminar nada. Te estas acercando...",
                "La espada tiembla en tu mano, ansiosa, hambrienta. Dirías que tira de ti, pero, hacia donde?",
                "El aire se enfría alrededor de las llamas. Notas la presencia de algo antiguo...",
                "Las sombras escapan en la dirección contraria a la que avanzas. Como si huyeran del camino que has elegido...",
                "La hoja emite un sonido bajo, casi inaudible. No es metal contra metal. Es algo que reconoce el camino."]
            narrar(random.choice(textos))

        # ── PASO 2: pista inicial ruta normal ─────────────────────────────
        elif progreso_n2 == 2:
            if "Hoja de la Noche" in estado["armas_jugador"] and personaje.get("_pw", 0) != 1:
                narrar("Parece que hacia la izquierda sigue un corredor más amplio.")
                narrar("Aunque la penumbra y los restos no facilitan el camino, notas una leve corriente y distingues el hedor a sangre que lleva...")
                narrar("De pronto, la 'Hoja de la Noche' vibra y se inmola en llamas negras que se desprenden con rabia.")
                narrar("A pesar de la corriente, las llamas van hacia la derecha, como atraídas por algo...")
                preguntar("Presientes que el final está cerca, pero ¿cuál?")
            else:
                narrar("Parece que hacia la izquierda sigue un corredor más amplio.")
                narrar("Aunque la penumbra y los restos no facilitan el camino, notas una leve corriente y distingues el hedor a sangre que lleva...")

        # ── PASO 3+: siguiendo ruta normal ────────────────────────────────
        elif progreso_n2 >= 3:
            textos = [
                "El ambiente se vuelve denso y húmedo. El olor a sangre afirma que es el camino correcto.",
                "Los gritos se oyen más intensos y el hedor se intensifica. Debe ser por aquí...",
                "En el suelo, ves el reflejo de pequeños riachuelos y charcos de sangre. Debes estar cerca.",
                "Un vaho de sangre caliente invade el pasillo, enroscándose a tu alrededor. Parace como si quisiera guiarte..."]
            narrar(random.choice(textos))

        # ── EVENTOS FINALES ───────────────────────────────────────────────
        if estado["pasos_nivel2"] == ruta_correcta_nivel2:
            narrar("La puerta del fondo exhala aire caliente entre sus grietas.")
            enemigo = crear_amo_mazmorra(personaje)
            combate(personaje, enemigo)
            # Si el jugador escapa del jefe, continuar el juego
            if personaje.get("_huyo_combate", False):
                reiniciar_camino_por_huida(personaje)
                return True
            if enemigo.get("final_secreto"):
                _fate_02(personaje)
            return

        if estado["pasos_secretos"] == ruta_secreta:
            narrar("La oscuridad se condensa a tu alrededor.")
            alerta("Algo emerge desde las sombras para recibirte.")
            combate(personaje, crear_demonio_final())
            # Continuar el juego independientemente del resultado
            if personaje.get("_huyo_combate", False):
                reiniciar_camino_por_huida(personaje)
            else:
                # Limpiar la ruta secreta para que el combate no se retrigere
                estado["pasos_secretos"].clear()
            return True

# Eventos normales (ejecuta siempre a menos que sea un final especial)

    evento = evento_aleatorio(personaje)
    if personaje.get("_huyo_combate", False):
        reiniciar_camino_por_huida(personaje)
        return True
    aplicar_evento(evento, personaje)
    return True
# ================== INTERFAZ Y UTILIDADES ==================

# ================== HELPERS DE DISPLAY (UI) ==================
# Centralizando el output aquí se facilita la migración futura a Pygame:
# solo hay que sustituir estas funciones por llamadas a la interfaz gráfica.

def narrar(texto):
    """Texto narrativo. La Vista lo muestra en itálica tenue."""
    emitir("narrar", texto)

def alerta(texto):
    """Advertencia o peligro inminente."""
    emitir("alerta", texto)

def exito(texto):
    """Recompensa, objeto conseguido, logro."""
    emitir("exito", texto)

def sistema(texto):
    """Mensajes del sistema: guardado, cargado, errores."""
    emitir("sistema", texto)

def titulo_seccion(texto):
    """Separador visual con título."""
    emitir("titulo", texto)

def preguntar(texto):
    """Pregunta o prompt al jugador."""
    emitir("preguntar", texto)

def separador():
    """Línea divisoria entre bloques de texto."""
    emitir("separador", "")

def dialogo(texto):
    """Diálogo de personaje: voz directa, destacada."""
    emitir("dialogo", texto)


def mostrar_stats(personaje):
    """Emite un dict con las estadísticas para que la Vista las renderice."""
    vida_max = personaje.get("vida_max", 25)
    armas_str = ", ".join(estado["armas_jugador"].keys()) if estado["armas_jugador"] else "ninguna"
    emitir("stats", {
        "vida":        personaje["vida"],
        "vida_max":    vida_max,
        "fuerza":      personaje["fuerza"],
        "destreza":    personaje["destreza"],
        "armadura":    personaje["armadura"],
        "armadura_max": personaje.get("armadura_max", 5),
        "pociones":    personaje["pociones"],
        "pociones_max": personaje.get("pociones_max", 10),
        "armas":       armas_str,
        "num_armas":   len(estado["armas_jugador"]),
    })

# ================== SUSURROS ALEATORIOS ==================
def susurros_aleatorios():
    susurros = [
        "'dolor... poder... sangre... herida... abierta...'",
        "'nido... manos... sostienen... abajo... abajo...'",
        "'rey... oculto... pronunciado... no pronuncia...'",
        "'costura... carne... torre... invertida...'",
        "'llave... vientre... no debía... latir...'",
        "'sombra... bebe... sombra... inclina... copa...'",
        "'amo... falso... ejército... cultivado...'",
        "'piedra... aprende... respira... espera...'",
        "'sedimento... voluntad... grietas...'",
        "'Sanakht... grieta... cálculo... silencio...'",
        "'Ka-Banda... exceso... peso... manifestación... sangre...'"
    ]
    for _ in range(random.randint(1, 3)):
        emitir("susurros", random.choice(susurros))

# ================== LECTURA DE INPUT ==================

def leer_input(prompt, personaje):
    while True:
        valor = pedir_input().strip().lower()
        if valor in ["stats", "st", "stat"]:
            mostrar_stats(personaje)
            continue
        separador()
        return valor

# ================== FINALES ==================

def fin_derrota(personaje):
    panel(
        "Caes al suelo mientras la mazmorra te traga en su oscuridad.\n"
        "No hay salida, no hay redención, solo dolor y silencio.\n"
        "Has muerto en las profundidades.",
        titulo="FINAL: DERROTA",
        estilo="red"
    )
    # [SECRETO 6] Posibilidad de revivir (una sola vez)
    preguntar("(Presiona enter para terminar)")
    respuesta_final = pedir_input().strip().lower()
    if respuesta_final == "lo que esta muerto no puede morir" and not personaje.get("_x9f"):
        narrar("\n========================================\n")
        narrar("Pero la muerte aquí no es el final.")
        narrar("La mazmorra es un lugar donde los muertos siguen sirviendo.")
        narrar("Y algo en ti aún tiene hambre. Aún tiene propósito.")
        narrar("Los ojos se abren. El cuerpo se recompone.")
        narrar("========================================\n")
        narrar("Horas después... o quizás minutos. No lo sabes. Despiertas en un cruce desconocido.")
        narrar("Tu cuerpo duele. Tu mente está confusa. Pero estás vivo.")
        # Restaurar vida
        personaje["_x9f"] = True
        personaje["vida"] = max(1, personaje.get("vida_max", 10) // 2)
        personaje["_flg1"] = True
        return False
    else:
        sys.exit()

def _fate_05():
    panel(
        "Cuando cruzas el umbral hacia la luz, ya no eres lo que eras.\n"
        "La mazmorra tiene designios que van más allá de matar. Ella elige sus vasallos.\n"
        "Sentiste un demonio meterse en tu cuerpo cuando moriste. Lo sentiste todo.\n"
        "Pero tu voluntad era suficientemente fuerte para mantener el control... apenas.\n"
        "El precio fue alto: la mazmorra te reclama incluso en victoria.\n"
        "\n"
        "Sales a la luz del mundo exterior. El castigo comienza de inmediato.\n"
        "La carne se te empieza a desprender del hueso. Poco a poco al principio, después todo a la vez.\n"
        "El aire que respiras aquí, fuera de tu hogar subterráneo, es un veneno para lo que has llegado a ser.\n"
        "Te desecas. Tu cuerpo se convierte en polvo, en nada.\n"
        "Pero tu mente sigue despierta. Atrapada. Enloquecida.\n"
        "\n"
        "Has escapado de la mazmorra. Pero nunca escaparás de lo que ella planta en ti.\n"
        "El demonio no puede morir aquí arriba. Tú tampoco. Solo puedes sufrir eternamente.",
        titulo="FINAL: HERENCIA MALDITA",
        estilo="red"
    )
    pedir_input()
    sys.exit()

def _fate_01(personaje):                                            # MATAR AL AMO
    if personaje.get("_x9f"):
        return _fate_05()
    
    panel(
        "Sales de la sala del Amo de la Mazmorra tambaleándote, cubierto de sangre ajena y propia.\n"
        "No hay gloria, ni revelaciones, solo pasillos que por fin dejan de cerrarse sobre ti.\n"
        "La oscuridad sigue ahí, pero ya no te traga: esta vez te deja pasar.\n"
        "Respiras hondo por primera vez en mucho tiempo.\n"
        "Has sobrevivido a la mazmorra.",
        titulo="FINAL: SUPERVIVIENTE",
        estilo="yellow"
    )
    # TODO: tkinter — pantalla de final con creditos
    pedir_input()
    sys.exit()
# FINAL SECRETO
def _fate_02(personaje):                                        # MATAR AMO + PODER +1
    if personaje.get("_x9f"):
        return _fate_05()
    
    panel(
        "Atraviesas el último umbral con la Hoz de Sangre aún latiendo entre tus manos.\n"
        "Cada gota derramada en la mazmorra parece seguirte, como si te hubiera reclamado.\n"
        "Has escapado del Amo... pero no de aquello que despertaste.\n"
        "Sientes hambre, furia y un poder oscuro que ya no distingue enemigo de presa.\n"
        "Sabes que has salido vivo. No sabes si has salido humano.",
        titulo="FINAL: HEREDERO DE LA SANGRE",
        estilo="red"
    )
    # TODO: tkinter — pantalla de final secreto
    pedir_input()
    sys.exit()

def _fate_03(personaje):
    if personaje.get("_x9f"):
        return _fate_05()
    
    panel(
        "La Hoja de la Noche vibra en silencio cuando cae el Amo de la Mazmorra.\n"
        "No celebras la victoria: entiendes el precio de todo lo que has visto.\n"
        "Las sombras no te devoran. Te reconocen.\n"
        "Abandonas la mazmorra con una calma extraña, como quien cierra una deuda antigua.\n"
        "No eres el mismo que entró... pero tampoco te has perdido del todo.",
        titulo="FINAL: PORTADOR DE LA NOCHE",
        estilo="white"
    )
    # TODO: tkinter — pantalla de final hoja noche
    pedir_input()
    sys.exit()

def ejecutar_final_normal_por_arma(personaje):
    if "Hoja de la Noche" in estado["armas_jugador"]:
        _fate_03(personaje)
    elif "Hoz de Sangre" in estado["armas_jugador"]:
        _fate_02(personaje)
    else:
        _fate_01(personaje)

def _fate_04(personaje):                                       #   100 kills
    if personaje.get("_x9f"):
        return _fate_05()
    
    panel(
        "...no te sientes bien...\n"
        "El último combate ha roto algo en ti. Te das cuenta que no sabes cuánto llevas aquí dentro.\n"
        "Miras tus manos y tu ropa ensangrentada, y te das cuenta de que no eres un prisionero.\n"
        "Llegaste aquí como eso, pero te parece que fue hace una eternidad.\n"
        "Sigues vagando sin rumbo y destripando lo que te cruzas.\n"
        "Te conviertes en otra bestia enaje nada de la mazmorra.",
        titulo="FINAL SUPER SECRETO",
        estilo="red"
    )
    # TODO: tkinter — pantalla de final super secreto
    pedir_input()
    sys.exit()

def _fate_06(personaje):                                       # 66 kills + poder 1
    if personaje.get("_x9f"):
        return _fate_05()
    
    panel(
        "El suelo tiembla bajo tus pies.\n"
        "La mazmorra entera parece contener la respiración.\n"
        "Has derramado demasiada sangre. Ya no eres un prisionero.\n"
        "Una grieta enorme se abre en el suelo, de donde brota sangre.\n\n"
        "Has trascendido al dolor. Has dominado la sangre.\n"
        "Una puerta como la boca de un demonio emerge del suelo lentamente...\n\n"
        "'Nunca te dejaré, nunca te decepcionaré,\n"
        "nunca saldré corriendo y te abandonaré,\n"
        "nunca te haré llorar, nunca te diré adiós,\n"
        "nunca te diré una mentira y te lastimaré.'",
        titulo="FINAL SUPER HIPER SECRETO",
        estilo="red"
    )
    # TODO: tkinter — pantalla de final super hiper secreto
    pedir_input()
    sys.exit()
# ================== APLICACIÓN DE EVENTOS ==================
_KEYS_VALIDAS: frozenset = frozenset({
    "vida", "pociones", "fuerza", "destreza", "armadura", "armas",
    "moscas", "brazos", "sombra", "sangre", "_pw", "nivel",
    "tiene_llave", "rencor", "hitos_brazos_reclamados",
    "evento_brazos_final_completado", "evento_brazos_segundo_completado",
    "bolsa_acecho",
})

def aplicar_evento(evento, personaje):
    """Aplica cambios de evento a un personaje.
    
    Soporta los siguientes campos (claves en el diccionario 'evento'):
    - vida, armadura, fuerza, destreza: incrementadores de stats
    - pociones: número de pociones a sumar
    - armas: dict {nombre: stats_dict} de armas a obtener
    
    CRITICO: Después de cambios en armas, sincroniza la UI adjuntando un callback.
    """
    # Aplica los cambios del evento al personaje
    for key, valor in evento.items():
        # ---------------- VIDA ----------------
        if key == "vida":
            personaje["vida"] += valor
            # Limitar a vida máxima si existe
            if "vida_max" in personaje:
                if personaje["vida"] > personaje["vida_max"]:
                    personaje["vida"] = personaje["vida_max"]
                    sistema("Vida al máximo.")
            if personaje["vida"] < 0:
                personaje["vida"] = 0
            if valor < 0:
                alerta(f"Recibes {abs(valor)} de daño. Vida: {personaje['vida']}")
            else:
                exito(f"+{valor} de vida. Vida: {personaje['vida']}")
            if personaje["vida"] == 0:
                fin_derrota(personaje)
                return
        # ---------------- POCIONES ----------------
        elif key == "pociones":
            personaje["pociones"] += valor
            # Limitar a pociones máximas si existe
            if "pociones_max" in personaje and personaje["pociones"] > personaje["pociones_max"]:
                personaje["pociones"] = personaje["pociones_max"]
                sistema(f"Pociones al máximo ({personaje['pociones']}).")
            else:
                exito(f"Consigues {valor} poción(es). Ahora tienes {personaje['pociones']}.")
        # ---------------- FUERZA ----------------
        elif key == "fuerza":
            personaje["fuerza"] += valor
            # Limitar a fuerza máxima si existe
            if "fuerza_max" in personaje:
                if personaje["fuerza"] > personaje["fuerza_max"]:
                    personaje["fuerza"] = personaje["fuerza_max"]
                    sistema(f"Fuerza al máximo ({personaje['fuerza']}).")
            exito(f"Fuerza aumenta. Ahora es: {personaje['fuerza']}")
        # ---------------- DESTREZA ----------------
        elif key == "destreza":
            personaje["destreza"] += valor
            # Limitar a destreza máxima si existe
            if "destreza_max" in personaje:
                if personaje["destreza"] > personaje["destreza_max"]:
                    personaje["destreza"] = personaje["destreza_max"]
                    sistema(f"Destreza al máximo ({personaje['destreza']}).")
            exito(f"Destreza aumenta. Ahora es: {personaje['destreza']}")
        # ---------------- ARMADURA ----------------
        elif key == "armadura":
            personaje["armadura"] += valor
            if "armadura_max" in personaje and personaje["armadura"] > personaje["armadura_max"]:
                personaje["armadura"] = personaje["armadura_max"]
                sistema(f"Armadura al máximo ({personaje['armadura_max']}).")
            if personaje["armadura"] < 0:
                personaje["armadura"] = 0
            if valor > 0:
                exito(f"Armadura +{valor}. Armadura actual: {personaje['armadura']}")
            elif valor < 0:
                alerta(f"Armadura -{abs(valor)}. Armadura actual: {personaje['armadura']}")

        # ---------------- ARMAS ----------------
        elif key == "armas":
            for arma, stats in valor.items():
                añadir_arma(personaje, arma)
            # CRITICO: Sincronizar UI después de cambiar armas
            # Esto asegura que los sprites se actualicen inmediatamente
            if _callback_ui_armas is not None:
                _callback_ui_armas()
        # ---------------- OTROS ----------------
        else:
            if key not in _KEYS_VALIDAS:
                alerta(f"[DEV] aplicar_evento: key desconocida '{key}'")
            if key not in personaje:
                personaje[key] = valor
            else:
                personaje[key] += valor


# ── Bonus de Fibonacci ────────────────────────────────────────────────────────
# Hitos de combate donde se revela lore al jugador.
# La secuencia empieza en 2, cubre hasta el combate 89 (techo ~100 combates).
_FIB_SET: frozenset = frozenset({2, 3, 5, 8, 13, 21, 34, 55, 89})

# Cada entrada es una tupla de fragmentos narrados secuencialmente.
# El último elemento puede ser una tupla (texto, tag) para cambiar el estilo.
# Por defecto todos usan el tag "narrar"; los susurros usan ("texto", "susurros").
_LORE_FIBONACCI: dict = {
    2: (
        "Te arrodillas sobre algo que dejó de moverse y no sientes lo que esperabas "
        "sentir. Quizá porque no recuerdas qué se supone que debes sentir. No recuerdas "
        "nada antes de este corredor húmedo, estas manos llenas de sangre, este latido "
        "que sigue como si supiera algo que tú no.",
        "Cuando el eco del combate se apaga, las cadenas colgadas de los muros aún vibran "
        "levemente. Durante un instante juras que el suelo respira bajo tus rodillas. No "
        "es aire. Es un movimiento lento, profundo, como algo arrastrándose bajo toneladas "
        "de piedra. Entre los latidos de tu sien aparece un susurro que desaparece en "
        "cuanto intentas retenerlo.",
        ("nido.", "susurros"),
    ),
    3: (
        "Tu cuerpo aprende más rápido que tu mente. Tu mente sigue intentando entender "
        "qué es este lugar. Tu cuerpo ya lo sabe: es un sitio donde nada dura lo "
        "suficiente para tener nombre.",
        "Ves marcas en la piedra. No son cortes de herramientas ni arañazos de bestia. "
        "Son repeticiones. Símbolos tallados una y otra vez hasta quebrar la superficie "
        "del muro. Al principio parecen simples surcos, pero cuando los observas demasiado "
        "tiempo tu mente intenta cerrarlos, unirlos, completarlos como si fueran palabras "
        "incompletas. Como si fueran nombres olvidados.",
        "Cada vez que estás cerca de entenderlos, el pensamiento se corrompe y se deshace, "
        "como carne que empieza a pudrirse.",
    ),
    5: (
        "Uno de ellos tardó demasiado en morir. Sus labios seguían moviéndose cuando ya "
        "no había razón para que lo hicieran.",
        "La criatura no rezaba. Enumeraba. Palabras fragmentadas salían entre dientes rotos: "
        "rey… falso… sombra… sangre… Las repetía como si fueran cuentas de un rosario "
        "enfermo. Lo peor ocurrió después: dentro de tu propia cabeza esas mismas palabras "
        "empezaron a reorganizarse solas, como si alguien intentara reconstruir un recuerdo "
        "usando tu mente como herramienta. Cada combinación parece acercarse a algo "
        "importante, pero cuando estás a punto de comprenderlo el significado se descompone "
        "y desaparece.",
    ),
    8: (
        "Llevas suficientes muertes encima para empezar a escuchar lo que hay debajo del "
        "ruido. No es un don. Es una herida que todavía no sabes que tienes.",
        "Hay un nombre sepultado entre los gritos de tus enemigos. No lo gritan: lo exhalan. "
        "Solo cuando están muriendo, cuando el último aliento escapa hacia el suelo, ese "
        "nombre los precede. Lo escupen hacia abajo. Hacia las piedras. Como ofrenda, o "
        "como reconocimiento de algo que lleva más tiempo aquí que ellos.",
        ("Sanakrt.", "susurros"),
        "Nadie aquí parece rendirle culto. Pero nadie se mueve en estas profundidades sin "
        "orientarse en torno a ese nombre, como agujas que apuntan a un norte que ningún "
        "mapa conoce.",
    ),
    13: (
        "El siguiente enemigo que abates se abre como una fruta podrida cuando cae. De su "
        "interior no salen vísceras normales, sino un zumbido oscuro. Moscas. Demasiadas. "
        "Se arremolinan sobre el cadáver con una avidez que parece casi consciente.",
        "Entonces recuerdas fragmentos de historias escuchadas en algún lugar que ya no "
        "logras situar. Las moscas llegaron primero. No como insectos comunes, sino como "
        "hambre con alas. Los primeros cadáveres de esta prisión se abrieron ante ellas y "
        "de esa carne surgieron enjambres que aprendieron a devorar cuerpos vivos. Los "
        "supervivientes comenzaron a llamarlo la Plaga. Pero el nombre duró poco, porque "
        "pronto dejaron de hablar.",
        "La plaga no solo consume carne: también devora voces, recuerdos, palabras enteras.",
    ),
    21: (
        "Hay más de un modo de sobrevivir aquí y ninguno merece ese nombre. Lo entiendes "
        "viendo cómo se matan entre ellos con más convicción de la que tú traes.",
        "Unos mutilaron sus propios cuerpos para volverse invisibles al enjambre: "
        "aprendieron a existir en el silencio de las grietas, a moverse como sombras que "
        "ya no necesitan cuerpo. Otros eligieron lo contrario: la furia constante como "
        "escudo, el movimiento perpetuo como armadura, la violencia como el único dios "
        "al que todavía rezan.",
        "Se cazan entre sí cuando el hambre aprieta. Se odian con la ferocidad de quienes "
        "comparten una herida que nunca cerrará. Pero cuando mueren —los silenciosos y los "
        "furiosos por igual— pronuncian el mismo nombre.",
        ("Ka'banda.", "susurros"),
        "No como plegaria. No como maldición. Como si ningún otro idioma pudiera nombrar "
        "lo que alguna vez los gobernó.",
    ),
    34: (
        "Lo peor no son las criaturas que no razonan. Lo peor es lo que hay detrás de ellas.",
        "Hay seres en esta prisión que ni siquiera los otros monstruos se atreven a tocar. "
        "No nacieron aquí. Fueron traídos. Demonios menores, herramientas vivientes que "
        "obedecen órdenes que nadie ha escuchado en siglos. Entre los delirios de los "
        "prisioneros moribundos aparece un nombre humano mezclado con los de esas criaturas.",
        ("Fabius.", "susurros"),
        "No suena como el nombre de quien llegó aquí encadenado. Este lugar fue levantado "
        "para contener lo que no puede destruirse. Su obra no es diferente.",
    ),
    55: (
        "Las mazmorras no caen. Se llenan. Esta tiene capas como una cicatriz que tardó "
        "demasiado en cerrarse, cada era depositando su propia podredumbre encima de la anterior.",
        "Primero fue un bastión levantado para la guerra. Después un presidio donde encerrar "
        "a los enemigos de algún reino olvidado. Más tarde se convirtió en un lugar donde "
        "ocultar cosas que nadie debía recordar: rituales fallidos, experimentos prohibidos, "
        "horrores que no podían destruirse pero tampoco liberarse. Con el tiempo, los muros "
        "absorbieron todo ese sufrimiento como una esponja negra. Cuando la plaga llegó, y "
        "los demonios la siguieron, la prisión ya estaba preparada para recibirlos.",
        "Era un recipiente esperando llenarse. Pero debajo de todas esas capas, más profundo "
        "que el primer fundamento, algo lleva aquí más tiempo que la propia prisión. Anterior "
        "a la guerra, anterior a los reyes, anterior a los nombres mismos.",
        ("Sanakrt.", "susurros"),
    ),
    89: (
        "Los fragmentos que llevas recogiendo —nombres, palabras sueltas, imágenes sin "
        "contexto— dejan de ser ruido y empiezan a tener forma.",
        "Fabius, el hombre cuya obra solo este lugar podía contener. Ka'banda, el eco de un "
        "rey sangriento cuyo recuerdo aún corrompe estas piedras. Sanakrt, algo que espera "
        "en lo profundo donde ni siquiera los ejércitos han nacido todavía. Y por encima de "
        "todos, Be'lakor, una sombra tan vasta que no necesita cuerpo para dominar este lugar.",
        "Entonces comprendes algo que te hiela la sangre: la mazmorra no es una ruina "
        "abandonada ni un accidente. Es un semillero. Un lugar donde se cultivan monstruos, "
        "plagas y demonios a lo largo de generaciones.",
        "Y mientras desciendes un nuevo tramo de escaleras cubiertas de sangre seca, una "
        "sospecha se clava en tu mente. Quizá todos los horrores que has matado eran solo "
        "intentos fallidos. Prototipos. Experimentos incompletos.",
        "Y tú… tú podrías ser el último resultado que este lugar llevaba siglos intentando crear.",
    ),
}


def _mostrar_lore_fibonacci(combate: int) -> None:
    """Muestra los fragmentos de lore correspondientes al hito de combate dado."""
    fragmentos = _LORE_FIBONACCI.get(combate)
    if not fragmentos:
        return
    separador()
    for fragmento in fragmentos:
        if isinstance(fragmento, tuple):
            texto, tag = fragmento
            emitir(tag, texto)
        else:
            narrar(fragmento)
    separador()


def revisar_bonus_fibonacci(personaje):
    """Dispara lore narrativo en los hitos de combate de la secuencia de Fibonacci."""
    if estado["_c01"] not in _FIB_SET:
        return
    _mostrar_lore_fibonacci(estado["_c01"])

# ================== ENEMIGOS ==================

# Bolsas de presentación por enemigo (bag con reset)
_bolsas_presentacion: dict = {}

def sacar_presentacion(nombre: str, total: int) -> int:
    """Devuelve un índice de presentación usando sistema de bolsa con reset."""
    if nombre not in _bolsas_presentacion or not _bolsas_presentacion[nombre]:
        indices = list(range(total))
        random.shuffle(indices)
        _bolsas_presentacion[nombre] = indices
    return _bolsas_presentacion[nombre].pop()

def enemigo_aleatorio(nombre=None):

    enemigos = {
        "Larvas de Sangre": {
            "nombre": "Larvas de Sangre", "vida": 10, "vida_max": 10, "daño": (1,2), "esquiva": 17, "jefe": False, "armadura": 0,
            "habilidades": [
                {"nombre": "Ícor de Larva", "tipo": "activa", "prob": 0.25, "condicion": "siempre", "efecto": "reducir_armadura", "valor": 1}
            ],
            "_efectos_temporales": {}
        },
        "Mosca de Sangre": {
            "nombre": "Mosca de Sangre", "vida": 15, "vida_max": 15, "daño": (1,2), "esquiva": 15, "jefe": False, "armadura": 0,
            "habilidades": [
                {"nombre": "Ícor de Mosca", "tipo": "activa", "prob": 0.25, "condicion": "siempre", "efecto": "reducir_armadura", "valor": 1}
            ],
            "_efectos_temporales": {}
        },
        "Maniaco Mutilado": {
            "nombre": "Maniaco Mutilado", "vida": 14, "vida_max": 14, "daño": (1,3), "esquiva": 10, "jefe": False, "armadura": 0,
            "habilidades": [
                {"nombre": "Huesos Punzantes", "tipo": "pasiva", "prob": 0.25, "condicion": "siempre", "efecto": "sangrado", "valor": 1}
            ],
            "_efectos_temporales": {}
        },
        "Perturbado": {
            "nombre": "Perturbado", "vida": 18, "vida_max": 18, "daño": (2,3), "esquiva": 12, "jefe": False, "armadura": 0,
            "habilidades": [
                {"nombre": "Arrebato de Locura", "tipo": "activa", "prob": 0.25, "condicion": "siempre", "efecto": "damage_boost", "valor": 0.3}
            ],
            "_efectos_temporales": {}
        },
        "Rabioso": {
            "nombre": "Rabioso", "vida": 22, "vida_max": 22, "daño": (2,4), "esquiva": 5, "jefe": False, "armadura": 0,
            "habilidades": [
                {"nombre": "Golpe Brutal", "tipo": "activa", "prob": 0.20, "condicion": "siempre", "efecto": "damage_boost", "valor": 0},
                {"nombre": "Arrebato de Ira", "tipo": "pasiva", "prob": 0.30, "condicion": "vida_baja", "threshold": 0.6, "efecto": "damage_boost", "valor": 0.30}
            ],
            "_efectos_temporales": {}
        },
        "Sombra tenebrosa": {
            "nombre": "Sombra tenebrosa", "vida": 15, "vida_max": 15, "daño": (3,5), "esquiva": 15, "jefe": False, "armadura": 0,
            "habilidades": [
                {"nombre": "Colmillos de Sombra", "tipo": "pasiva", "prob": 0.15, "condicion": "siempre", "efecto": "sangrado", "valor": 1}
            ],
            "_efectos_temporales": {}
        },
    }

    # --- elegir enemigo ---
    if nombre and nombre in enemigos:
        enemigo = enemigos[nombre].copy()
    else:
        enemigo = random.choice(list(enemigos.values())).copy()

    # --- textos de presentación (bolsa con reset, 4 variantes por enemigo) ---
    if enemigo["nombre"] == "Maniaco Mutilado":
        v = sacar_presentacion("Maniaco Mutilado", 4)
        if v == 0:
            narrar("Te encuentras con una figura encorvada arrastrándose por las paredes.")
            narrar("Le faltan trozos de carne en brazos y rostro, y deja una baba rojiza al abalanzarse.")
        elif v == 1:
            narrar("Un cuerpo cosido con grapas oxidadas se descuelga del techo frente a ti.")
            narrar("Camina a tirones, enseñando hueso y tendón, mientras mastica algo que no quieres identificar.")
        elif v == 2:
            narrar("Una silueta sin dedos golpea el suelo con muñones sangrantes para impulsarse.")
            narrar("Su mandíbula torcida cuelga abierta y lanza un chillido húmedo antes de saltarte encima.")
        else:
            narrar("Oyes un gemido que sube de tono hasta convertirse en algo que no es humano.")
            narrar("Está colgado del techo por sus propias tripas, meciéndose. Cae cuando te ve. Se retuerce. Te mira.")

    elif enemigo["nombre"] == "Perturbado":
        v = sacar_presentacion("Perturbado", 4)
        if v == 0:
            narrar("Un hombre con la mirada perdida corre hacia ti gritando.")
            narrar("Tiene la piel del cuello arrancada a tiras y se ríe mientras la sangre le cae por el pecho.")
        elif v == 1:
            narrar("Una figura desnuda y deforme se avanza tambaleándose entre espasmos.")
            narrar("Sus uñas están arrancadas y, aun así, rasca las paredes dejando líneas de carne.")
        elif v == 2:
            narrar("Un desquiciado se golpea la frente contra el muro hasta abrirse una grieta.")
            narrar("Cuando te ve, te señala con dedos rotos y corre hacia ti chillando de alegría.")
        else:
            narrar("Se está arrancando la piel del antebrazo en tiras finas, sin dejar de reírse.")
            narrar("Cuando te ve, no para. Solo te señala con el brazo en carne viva y reanuda el grito.")

    elif enemigo["nombre"] == "Rabioso":
        v = sacar_presentacion("Rabioso", 4)
        if v == 0:
            narrar("Un demente cubierto de sangre aulla y se lanza a por ti.")
            dialogo("'¡SANGRE PARA EL DIOS DE LA SANGRE!', grita mientras se apuñala el pecho...")
        elif v == 1:
            narrar("Una bestia humana babea espuma roja y se rompe los dientes apretandolos de rabia.")
            narrar("Se le desorbitan los ojos, arquea la espalda y carga como un perro enloquecido.")
        elif v == 2:
            narrar("El rabioso se golpea el pecho con fuerza hasta abrirse la carne a puñetazos.")
            narrar("Entre gárgaras de sangre, pronuncia una oración podrida y se lanza directo a tu cuello.")
        else:
            narrar("El pasillo huele a sangre quemada antes de que lo veas. Tiene marcas a fuego por todo el cuerpo.")
            narrar("Abre los brazos hacia ti con las palmas arriba, rezando algo incoherente con una convicción absoluta.")

    elif enemigo["nombre"] == "Sombra tenebrosa":
        v = sacar_presentacion("Sombra tenebrosa", 4)
        if v == 0:
            narrar("Oyes una risita maliciosa, en varios sitios al mismo tiempo...")
            narrar("Ves destellos de filos entre una figura sombría que se detiene frente a ti.")
        elif v == 1:
            narrar("La luz de las antorchas se apaga por tramos y el pasillo se llena de cuchicheos.")
            narrar("Una sombra espesa, con hojas en lugar de dedos se despega del muro.")
        elif v == 2:
            narrar("Un charco negro se estira por el suelo hasta tomar forma humanoide frente a ti.")
            narrar("Dentro de su negrura asoman sangrientas cuchillas que palpitan como órganos vivos.")
        else:
            narrar("El silencio se concentra hasta que duele. Una figura plana, sin forma fija, pegada a la pared como una mancha.")
            narrar("Cuando se despega, los filos que la componen suenan como tijeras abriéndose y cerrándose sin parar.")

    elif enemigo["nombre"] == "Larvas de Sangre":
        v = sacar_presentacion("Larvas de Sangre", 4)
        if v == 0:
            narrar("Una repugnante larva palpitante llena de sangre se arrastra hacia ti.")
            narrar("Despliega su afilada probóscide y la sacude como un látigo viscoso.")
        elif v == 1:
            narrar("Del techo cae un gusano hinchado del tamaño de un brazo humano.")
            narrar("Su piel translúcida deja ver coágulos moviéndose dentro, y su mandíbula te apunta.")
        elif v == 2:
            narrar("Una masa segmentada revienta de un saco de carne y se retuerce a tus pies.")
            narrar("Abre una boca circular llena de dientes blandos y salta dejando rastro de pus roja.")
        else:
            narrar("Un gruñido húmedo vibra desde las paredes. La larva emerge de detrás de un cadáver.")
            narrar("Estaba usando el cuerpo como madriguera. Lo abre desde dentro para salir a por ti.")

    elif enemigo["nombre"] == "Mosca de Sangre":
        v = sacar_presentacion("Mosca de Sangre", 4)
        if v == 0:
            narrar("Un insecto hinchado y abotargado zumba sobre ti.")
            narrar("Sus obscenas bocas chasquean al verte, salpicando asquerosos coagulos.")
        elif v == 1:
            narrar("Una mosca del tamaño de un perro emerge del humo, con el abdomen reventado en llagas.")
            narrar("Cada obsceno aleteo desprende gotas calientes de sangre podrida.")
        elif v == 2:
            narrar("El asqueroso zumbido crece hasta dolerte en los dientes y una sombra te tapa la cara.")
            narrar("El insecto abre sus mandíbulas serradas y gotea un líquido negro sobre tus hombros.")
        else:
            narrar("El aire se espesa de pronto, como si algo grande lo desplazara.")
            narrar("La Mosca de Sangre planea desde las sombras del techo, tan lenta que parece que te está eligiendo.")

    sistema(f"Aparece: {enemigo['nombre']}")
    return enemigo

# ================== ENEMIGOS ESPECIALES ==================

def crear_carcelero():
    narrar("Intentas escapar, pero el sonido parece venir de todas partes. No sabes a donde ir...")
    narrar("Escuchas el tintineo antes de verlo, y no consigues identificarlo del todo.")
    narrar("No es solo una mole de carne y metal: es un cuerpo rehecho de suturas, clavos y ganchos.")
    narrar("Su piel está abierta en decenas de cicatrices mal cerradas.")
    narrar("Algunas supuran pus espeso que resbala entre placas oxidadas.")
    narrar("Otras dejan ver carne negruzca, infectada, palpitando.")
    narrar("Clavos gruesos atraviesan sus pectorales.")
    narrar("Ganchos se balancean bajo sus costillas, incrustados sin cuidado.")
    narrar("Cada movimiento desgarra un poco más lo que ya estaba roto.")
    narrar("Su vientre es lo peor.")
    narrar("La carne está cosida con hilo basto, tensado al límite.")
    narrar("Entre los puntos inflamados, clavada hasta la empuñadura, late una llave oxidada.")
    narrar("La herida nunca cerró. No debía haber cerrado nunca.")
    narrar("Sus ojos, pequeños en aquel rostro hinchado, brillan con rabia domesticada.")
    narrar("No es libre, pero parece disfrutar de sus cadenas. Literalmente...")
    narrar("Lo miras a los ojos, y ves un rostro abotargado, deformado por la tortura y la enfermedad.")
    narrar("Forrix levanta uno de sus deformes brazos y te señala.")
    narrar("Su mano temblorosa con las uñas partidas y negras. Su voz es un rugido roto, cargado de baba y sangre:")
    dialogo(
    f"{'¡Te vi merodear! ¡Te vi oler las puertas!\n¡Este sitio es mío… ¡¡MÍO!!\n'
    '¡El amo dijo que nadie baja… nadie toma la llave…\n¡¡Y yo obedezco!! ¡¡¡Yo siempre obedezco!!!'.upper()}"
    )
    
    # Transición clara hacia el combate
    narrar("La bestia de carne y metal ruge como un animal y se avalanza sobre ti, blandiendo sus ganchos.")
    alerta("¡FORRIX, EL CARCELERO, TE ATACA!")
    enemigo = {"nombre": "Forrix, el Carcelero","vida": 30,"vida_max": 30,"daño": (4, 6),"jefe": True,"esquiva": 3,"armadura": 0,
            "habilidades": [
                {"nombre": "Gancho de Carnicero", "tipo": "pasiva", "prob": 0.25, "condicion": "siempre", "efecto": "sangrado", "valor": 1},
                {"nombre": "Recuperacion Impia", "tipo": "activa", "prob": 1.0, "condicion": "vida_baja", "threshold": 0.6, "efecto": "recuperacion_impia"}
            ],
            "_efectos_temporales": {}}
    return enemigo

def crear_amo_mazmorra(personaje):
    if "Hoz de Sangre" in estado["armas_jugador"]:
        narrar("Entras a una sala enorme, llena de utensilios de tortura, cadenas y ganchos.")
        narrar("Una figura retorcida te observa tras una mesa de cirugía, con una máscara de hierro.")
        narrar("Ves trozos de piel y huesos en la máscara, como perversos adornos.")
        dialogo("'Vaya… uno de mis juguetes ha escapado. Y veo que tú también has estado jugando con los demás...'")
        dialogo("'Pero no me importa, ¡esos cultistas de las sombras no son nadie a mi lado!'")
        dialogo("'¡Aunque tengas su poder, no eres rival para mí!'")
        narrar("Ves cómo el Amo de la Mazmorra saca una gema violácea de su bolsillo y la estampa contra su frente, rompiéndola en mil pedazos.")
        narrar("La niebla violeta de la gema se introduce por los orificios de la máscara, y Fabius se sacude violentamente.")
        dialogo("'¡Aquí el dolor es poder, Y YO CONTROLO EL DOLOR!'")
        return {"nombre": "Fabius, Amo de la Mazmorra", "vida": 45, "vida_max": 45, "daño": (6,7), "jefe": True, "esquiva": 14, "armadura": 0,
                "habilidades": [
                    {"nombre": "Sutura de Dolor", "tipo": "pasiva", "prob": 0.30, "condicion": "siempre", "efecto": "sangrado", "valor": 2},
                    {"nombre": "Inyección Quirúrgica", "tipo": "activa", "prob": 1.0, "condicion": "vida_media", "efecto": "inyeccion_quirurgica"}
                ],
                "_efectos_temporales": {}}
    elif "Hoja de la Noche" in estado["armas_jugador"] and (personaje["_pw"]) == 1:
        narrar("Entras a una sala enorme. Esta llena de utensilios de tortura, cadenas y ganchos.")
        narrar("Una figura retorcida te observa tras una mesa de cirugia, con una máscara de hierro.")
        dialogo("'Vaya… uno de mis juguetes ha escapado... pero que llevas ahi?'")
        narrar("El Amo de la Mazmorra te mira con una mirada desagradable.")
        dialogo("'¡Como has conseguido esa hoja!?'")
        narrar("Al mirarte fijamente, ves como se el Amo de la mazmorra se sorprende")
        dialogo("'No puede ser...'")
        narrar("Con una velocidad inusitada, Fabius avanza frente a ti y se para en medio de la sala.")
        narrar("Puedes ver su horrible figura, totalmente retorcida y contrahecha. Notas su poder, pero tambien sus deformidades y afecciones.")
        narrar("Te preparas para enfrentarlo, pero Fabius de repente se postra ante ti y comienza a reverenciarte con adoracion.")
        dialogo("'¡OH ALABADO! Khar-dum! Khar-dum! Sanguor Rex!'")
        narrar("El Amo de la Mazmorra comienza a rezarte, mientras se da cabezazos con fuerza con cada salmo.")
        dialogo("'Vor-nakh! Vor-nakh! Thrakk ul-Khor!'")
        narrar("Parece totalmente abstraido, en un estado catartico.")
        dialogo("'¡TU ELEGIDO!¡Zhur-dakka! Zhur-dakka! Mor-eth kha!'")
        narrar("Te mira fijamente tras esa oracion, y comienza a llorar sangre.")
        dialogo("'CRUX SANGUIS — CRUX FERRUS — CRUX BELLUM!'")
        narrar("Tras esas palabras, su cabeza estalla y su cuerpo se desploma.")
        return {"nombre": "Fabius, Amo de la Mazmorra", "vida": 0, "vida_max": 0, "daño": (0,0), "jefe": True, "final_secreto": True, "esquiva": 0, "armadura": 0,
                "habilidades": [],
                "_efectos_temporales": {}}
    elif "Hoja de la Noche" in estado["armas_jugador"]:
        narrar("Entras a una sala enorme. Esta llena de utensilios de tortura, cadenas y ganchos.")
        narrar("Una figura retorcida te observa tras una mesa de cirujia, con una máscara de hierro.")
        dialogo("'Vaya… uno de mis juguetes ha escapado... pero que llevas ahi?'")
        narrar("El Amo de la Mazmorra te mira con una mirada desagradable.")
        dialogo("'¡Como has conseguido esa hoja!?'")
        dialogo("'Da igual, conozco cada secreto de esta mazmorra, y tu no! No eres nadie a mi lado!'")
        narrar("Ves como el Amo de la Mazmorra saca una gema violacea de su bolsillo, y levanta su mascara...")
        dialogo("'Solo yo conozco todos los misterios de las gemas, y como aprovechar todo su poder.'")
        narrar("Solo alcanzas a ver una masa de carne rosa y supurante bajo su mascara, y ves con asco como Fabius introduce la gema en lo que deberia ser su boca.")
        narrar("La gema desaparece en la masa de carne de su cara, y el Amo de la Mazmorra se sacude violentamente y se desploma.")
        dialogo("'¡CREES EN ESE ESTUPIDO DEMONIO?¡SOLO YO CONTROLO EL DOLOR!'")
        narrar("Depues del grito, Fabius se levanta espasmodicamente, y notas como su cuerpo ha crecido y sus ojos sobresalen de la mascara.")
        dialogo("'¡AHORA CONOCERAS EL MIEDO!'")
        return {"nombre": "Fabius, Amo de la Mazmorra", "vida": 60, "daño": (8,9), "jefe": True, "esquiva": 21,
                "habilidades": [
                    {"nombre": "Sutura de Dolor", "tipo": "pasiva", "prob": 0.30, "condicion": "siempre", "efecto": "sangrado", "valor": 2},
                    {"nombre": "Inyección Quirúrgica", "tipo": "activa", "prob": 1.0, "condicion": "vida_media", "efecto": "inyeccion_quirurgica"},
                    {"nombre": "Incisión Mortal", "tipo": "activa", "prob": 0.5, "condicion": "siempre", "efecto": "incision_mortal"}
                ],
                "_efectos_temporales": {}}
    else:
        narrar("Entras a una sala enorme, llena de utensilios de tortura, cadenas y ganchos.")
        narrar("Una figura retorcida te observa tras una mesa de cirugía, con una máscara de hierro.")
        narrar("Ves trozos de piel y huesos en la máscara, como perversos adornos.")
        dialogo("'Vaya… uno de mis juguetes ha escapado.'")
        narrar("El Amo de la Mazmorra te mira con ojos de cordero.")
        dialogo("'Seguro que lo has pasado muy mal ahí abajo, ven deja que te consuele.'")
        narrar("El Amo de la Mazmorra esgrime un afilado estilete hacia ti.")
        dialogo("'Yo te curaré las heridas...'")
        return {"nombre": "Fabius, Amo de la Mazmorra", "vida": 30, "daño": (6,7), "jefe": True, "esquiva": 7,
                "habilidades": [
                    {"nombre": "Sutura de Dolor", "tipo": "pasiva", "prob": 0.30, "condicion": "siempre", "efecto": "sangrado", "valor": 2}
                ],
                "_efectos_temporales": {}}

def crear_sombra_sangrienta():
    narrar("Esta vez la sombra te atrapa a ti y te arrastra a un mar de sangre sin orillas.")
    susurros_aleatorios()
    alerta("Sientes un terror primitivo, pataleas en vacío y cada movimiento te hunde más.")
    narrar("No hay suelo. No hay techo. Solo la sangre, cálida y densa, subiendo hasta la cintura.")
    susurros_aleatorios()
    narrar("La oscuridad tiene textura aquí. La notas en los pulmones con cada respiración.")
    narrar("Hay figuras en el fondo, o crees que las hay. No se mueven. Solo observan.")
    susurros_aleatorios()
    dialogo("'No eres nadie para pararnos...'")
    narrar("La voz no tiene dirección. Viene de dentro, no de fuera.")
    narrar("El mar de sangre se aquieta de golpe. Eso es peor que el movimiento.")
    susurros_aleatorios()
    alerta("Una sombra serpentina repta como un rayo hacia ti, blandiendo unas extrañas hoces por brazos.")
    narrar("No tiene cara. No la necesita. Ya sabes quién es...")
    return {"nombre": "Sanakht, la Sombra Sangrienta", "vida": 20, "vida_max": 20, "daño": (6,7), "jefe": True, "esquiva": 15, "armadura": 0,
            "habilidades": [
                {"nombre": "Acuchillamiento", "tipo": "activa", "prob": 1.0, "condicion": "vida_baja", "threshold": 0.7, "efecto": "acuchillamiento"},
                {"nombre": "Sombra oculta", "tipo": "activa", "prob": 1.0, "condicion": "vida_baja", "threshold": 0.3, "efecto": "esquiva_temporal"}
            ],
            "_efectos_temporales": {}}

def crear_demonio_final():
    narrar("La oscuridad se comprime y luego revienta en una marea de ceniza y sangre.")
    narrar("Desde el fondo del pasillo emerge Bel'akhor, Devorador de Almas.")
    narrar("Su silueta recuerda a un toro deforme erguido sobre dos patas, con una musculatura imposible y antinatural.")
    narrar("Unas alas de murciélago descomunales se abren a su espalda, cubriendo las paredes como un eclipse vivo.")
    narrar("Blande una hacha pesada de bronce, del mismo metal maldito que su armadura agrietada.")
    narrar("Cráneos de formas humanas e inhumanas cuelgan de placas y correajes, tintineando con cada paso.")
    narrar("Por cada grieta de la armadura supura sangre espesa, como si el demonio sangrara un ejército entero.")
    narrar("No oyes su voz, pero su presencia te atraviesa la mente: hambre, guerra y condena.")
    return {
        "nombre": "Bel'akhor, Principe Demonio",
        "vida": 150,
        "vida_max": 150,
        "daño": (10,12),
        "jefe": True,
        "_grant_pw": 1,
        "esquiva": 5,
        "armadura": 0,
        "habilidades": [
            {"nombre": "Rugido Infernal", "tipo": "pasiva", "prob": 0.25, "condicion": "siempre", "efecto": "damage_boost", "valor": 0.3},
            {"nombre": "Azotazo Demoníaco", "tipo": "activa", "prob": 1.0, "condicion": "vida_media", "efecto": "azotazo_demonico"},
            {"nombre": "Drenaje de Almas", "tipo": "activa", "prob": 1.0, "condicion": "vida_baja", "threshold": 0.6, "efecto": "drenaje_almas"},
            {"nombre": "Arrebato Apocalíptico", "tipo": "activa", "prob": 1.0, "condicion": "vida_baja", "threshold": 0.4, "efecto": "arrebato_apocaliptico"}
        ],
        "_efectos_temporales": {}
    }

def crear_mano_demoniaca():
    narrar("El aire se vuelve espeso y un olor agrio a sangre vieja te golpea la cara.")
    narrar("Desde la penumbra aparece el enano deforme, arrastrándose entre risas ahogadas por la rabia.")
    dialogo("'¡TE DIJE QUE ME LOS TRAJERAS! ¡AHORA VERAS LO QUE HE HECHO CONTIGO!'")
    narrar("A sus pies se retuerce una masa de carne cosida con tendones, brazos y huesos mal encajados.")
    narrar("La criatura se alza sobre ti como una torre enferma, palpitando con espasmos violentos.")
    narrar("Donde debería haber rostro, solo hay una hendidura llena de dientes y respiración caliente.")
    narrar("Sus manos son muñones gigantescos rematados en uñas negras, como cuchillas de carnicería.")
    narrar("El enano golpea su espalda con una varilla de hierro y la bestia ruge, obediente y furiosa.")
    dialogo("'¡MI OBRA! ¡MI VENGANZA!' grita mientras la criatura se lanza a por ti.")
    return {"nombre": "Mano Demoniaca", "vida": 30, "vida_max": 30, "daño": (8,9), "jefe": True, "esquiva": 8, "armadura": 0,
            "habilidades": [
                {"nombre": "Regeneracion grotesca", "tipo": "pasiva", "prob": 0.30, "condicion": "siempre", "efecto": "heal", "valor": 3},
                {"nombre": "Golpes furiosos", "tipo": "activa", "prob": 0.5, "condicion": "siempre", "efecto": "golpes_furiosos"}
            ],
            "_efectos_temporales": {}}

def crear_demonio_sombrio():
    narrar("La sangre cubre toda la sala, y el cuerpo sin cabeza del Rabioso comienza a convulsionar.")
    narrar("Su carne se retuerce, se regira y se transforma.")
    narrar("Ves como su cuerpo se hincha, le aparecen cuernos y protuberancias por todo su ser.")
    narrar("El ser que tienes delante no puede ser humano, ni producto de la magia...")
    narrar("La Hoz de Sangre vibra con fuerza cuando el ser termina de formarse ante tí.")
    dialogo("'Vor-nakh! Vor-nakh! Thrakk ul-Khor!'")
    dialogo("'Al final has conseguido atraer mi atención, maldito humano.")
    narrar("La voz de la criatura resuena en tu mente, pues no la ves mover ninguna de sus multiples bocas.")
    dialogo("'CRUX SANGUIS — CRUX FERRUS — CRUX BELLUM!'")
    dialogo("'Crees que por poseer la Hoz de Sangre eres digno de mi atencion?'")
    narrar("Aun estas aturdido por la escena, y todo lo que has vivido, pero a tu mente rota llegan recuerdos.")
    dialogo("'Demonio...', te dice la voz de tu cabeza.'Ka-Banda...','Poder...'")
    dialogo("'Crees que te dejare acumular sangre de mis seguidores sin consecuencias?'")
    narrar("Sin previo aviso hay una explosion de sangre a la espalda del demonio.")
    narrar("Le surjen unas deformes alas esqueleteicas de sus hombros, y se eleva imponente en medio de la sala.")
    dialogo("'¡KA-BANDA KHAR-DUM!¡¡KA-BANDA SANGUOR REX!!'")
    narrar("Esta vez si profiere un grito ensordecedor, que te estremece el alma.")
    narrar("Pero la Hoz en tu mano y tus instintos te preparan para la batalla.")
    return {"nombre": "Ka-Banda, Demonio Sombrio", "vida": 50, "vida_max": 50, "daño": (6,7), "jefe": True, "esquiva": 12, "armadura": 0,
            "habilidades": [
                {"nombre": "Hoja sombria", "tipo": "pasiva", "prob": 0.15, "condicion": "siempre", "efecto": "stun", "valor": 1},
                {"nombre": "Frensi demoniaco", "tipo": "activa", "prob": 1.0, "condicion": "vida_baja", "threshold": 0.5, "efecto": "frensi_demoniaco"}
            ],
            "_efectos_temporales": {}}

# ================== HABILIDADES DE ENEMIGOS ==================

def decrementar_efectos_temporales(enemigo):
    """Decrementa los efectos temporales del enemigo al final de su turno."""
    efectos = enemigo["_efectos_temporales"]
    efectos_a_remover = []
    
    for efecto, datos in efectos.items():
        datos["turnos_restantes"] -= 1
        if datos["turnos_restantes"] <= 0:
            efectos_a_remover.append(efecto)
    
    for efecto in efectos_a_remover:
        del efectos[efecto]

def decrementar_efectos_temporales_jugador(personaje):
    """Decrementa los efectos temporales del jugador (reducción de armadura, etc)."""
    if "_efectos_temporales" not in personaje:
        return
    
    efectos = personaje["_efectos_temporales"]
    efectos_a_remover = []
    
    for efecto, datos in efectos.items():
        datos["turnos_restantes"] -= 1
        if datos["turnos_restantes"] <= 0:
            efectos_a_remover.append(efecto)
            if efecto == "armor_reduction":
                # Informar al jugador que se recuperó la armadura
                sistema(f"🛡 Tu armadura se ha recuperado de la reducción temporal.")
    
    for efecto in efectos_a_remover:
        del efectos[efecto]

def _normalizar_enum(valor):
    """Convierte Enum a .value si es necesario, preserva strings."""
    if isinstance(valor, Enum):
        return valor.value
    return valor


def evaluar_condicion_habilidad(enemigo, condicion, prob=1.0, threshold=0.5):
    """
    Centraliza la evaluación de condiciones para habilidades.
    Compatible con strings y Enums.Condicion.
    Retorna True si la condición se cumple, False en caso contrario.
    """
    # VALIDATION (PASO 9)
    assert isinstance(prob, (int, float)) and 0 <= prob <= 1, f"prob debe estar en [0,1], no {prob}"
    assert isinstance(threshold, (int, float)) and 0 <= threshold <= 1, f"threshold debe estar en [0,1], no {threshold}"
    assert "vida" in enemigo and "vida_max" in enemigo, "enemigo debe tener vida y vida_max"
    
    # Convertir Enum a string si es necesario
    cond_str = _normalizar_enum(condicion)
    
    if cond_str == "siempre":
        resultado = random.random() < prob
        _log_debug("CONDITION", f"{enemigo['nombre']} siempre (prob={prob}): {resultado}")
        return resultado
    elif cond_str == "vida_baja":
        vida_pct = enemigo["vida"] / max(1, enemigo.get("vida_max", enemigo["vida"]))
        resultado = vida_pct < threshold and random.random() < prob
        _log_debug("CONDITION", f"{enemigo['nombre']} vida_baja (vida={vida_pct:.2f}%, umbral={threshold}): {resultado}")
        return resultado
    elif cond_str == "vida_media":
        vida_pct = enemigo["vida"] / max(1, enemigo.get("vida_max", enemigo["vida"]))
        resultado = 0.3 < vida_pct < 0.7 and random.random() < prob
        _log_debug("CONDITION", f"{enemigo['nombre']} vida_media (vida={vida_pct:.2f}%): {resultado}")
        return resultado
    return False

def aplicar_habilidades_pasivas(enemigo, personaje):
    """Aplica modificadores y efectos de habilidades pasivas al ataque. Devuelve dict con modificadores."""
    modificadores = {"daño": 0, "sangrado": 0, "stun_prob": 0, "armor_reduction": 0}
    habilidades_pasivas = [h for h in enemigo.get("habilidades", []) if _normalizar_enum(h.get("tipo")) == "pasiva"]
    
    for hab in habilidades_pasivas:
        condicion = hab.get("condicion", "siempre")
        efecto = hab.get("efecto", "nada")
        valor = hab.get("valor", 0)
        prob = hab.get("prob", 1.0)
        threshold = hab.get("threshold", 0.5)
        
        # Evaluar condición usando función centralizada
        if evaluar_condicion_habilidad(enemigo, condicion, prob, threshold):
            # Narrar la habilidad si existe narrativa
            nombre_hab = hab.get("nombre", "")
            if nombre_hab in NARRATIVAS_HABILIDADES:
                narrar(NARRATIVAS_HABILIDADES[nombre_hab])
            
            if efecto == "sangrado":
                modificadores["sangrado"] += valor
            elif efecto == "damage_boost":
                modificadores["daño"] += valor
            elif efecto == "stun":
                modificadores["stun_prob"] += valor
            elif efecto == "armor_reduction":
                modificadores["armor_reduction"] += valor
            elif efecto == "heal":
                # Aplicar healing directamente al enemigo
                enemigo["vida"] = min(enemigo.get("vida_max", enemigo["vida"]), enemigo["vida"] + valor)
                sistema(f"💚 {enemigo['nombre']} está regenerando. (+{valor} HP)")
    
    return modificadores

def ejecutar_habilidad_activa(enemigo, personaje):
    """Ejecuta una habilidad activa que consume el turno. Devuelve dict con info del efecto o None si no hay."""
    habilidades_activas = [h for h in enemigo.get("habilidades", []) if _normalizar_enum(h.get("tipo")) == "activa"]
    if not habilidades_activas:
        return None
    
    for hab in habilidades_activas:
        prob = hab.get("prob", 0)
        condicion = hab.get("condicion", "siempre")
        nombre_hab = hab.get("nombre", "Habilidad")
        threshold = hab.get("threshold", 0.5)
        
        # Evaluar condición usando función centralizada
        if evaluar_condicion_habilidad(enemigo, condicion, prob, threshold):
            efecto = hab.get("efecto", "nada")
            resultado = {"nombre_hab": nombre_hab, "debe_atacar": False, "efectos": {}}
            
            # Narrar la habilidad si existe narrativa
            if nombre_hab in NARRATIVAS_HABILIDADES:
                narrar(NARRATIVAS_HABILIDADES[nombre_hab])
            
            if efecto == "reducir_armadura":
                valor = hab.get("valor", 1)
                personaje["armadura"] = max(0, personaje.get("armadura", 0) - valor)
                sistema(f"🛡 {enemigo['nombre']} usa {nombre_hab}: Tu armadura se reduce en {valor}.")
                return resultado
            
            elif efecto == "damage_boost":
                enemigo["_damage_boost"] = hab.get("valor", 0.5)
                alerta(f"⚡ {enemigo['nombre']} usa {nombre_hab}: Se prepara para un ataque potenciado.")
                return resultado
            
            elif efecto == "recuperacion_impia":
                # Forrix: se cura 4 HP y prepara damage_boost 20%
                enemigo["vida"] = min(enemigo.get("vida_max", enemigo["vida"]), enemigo["vida"] + 4)
                enemigo["_damage_boost"] = 0.2
                alerta(f"💚⚡ {enemigo['nombre']} usa {nombre_hab}: Se cura y se prepara para un golpe devastador.")
                resultado["debe_atacar"] = True
                return resultado
            
            elif efecto == "acuchillamiento":
                # Sanakht: ejecuta ataque normal que causa 2 sangrado extra
                alerta(f"🩸 {enemigo['nombre']} usa {nombre_hab}: Se posiciona para un ataque devastador.")
                resultado["debe_atacar"] = True
                resultado["efectos"]["sangrado_extra"] = 2
                return resultado
            
            elif efecto == "esquiva_temporal":
                # Sanakht: reduce la precisión del jugador durante 2 turnos
                enemigo["_efectos_temporales"]["precision_reducida"] = {"valor": 10, "turnos_restantes": 2}
                alerta(f"👻 {enemigo['nombre']} usa {nombre_hab}: Se sumerge en las sombras, eliminándote del plano de la realidad.")
                return resultado
            
            elif efecto == "golpes_furiosos":
                # Mano: ejecuta ataque con +30% daño y 10% stun
                alerta(f"💥 {enemigo['nombre']} usa {nombre_hab}: ¡Golpes furiosos desde todos lados!")
                resultado["debe_atacar"] = True
                resultado["efectos"]["damage_boost"] = 0.3
                resultado["efectos"]["stun_chance"] = 0.1
                return resultado
            
            elif efecto == "frensi_demoniaco":
                # Ka-Banda: ejecuta ataque con +25% daño + 30% damage_boost para 2 turnos
                alerta(f"🔥 {enemigo['nombre']} usa {nombre_hab}: ¡ENTRA EN UN FRENESÍ DEMONIACO!")
                enemigo["_damage_boost"] = 0.25  # +25% para este ataque
                enemigo["_efectos_temporales"]["damage_boost"] = {"valor": 0.3, "turnos_restantes": 2}
                resultado["debe_atacar"] = True
                return resultado
            
            elif efecto == "drenaje_almas":
                # Bel'akhor: ataque que se cura con el daño hecho
                alerta(f"💀 {enemigo['nombre']} usa {nombre_hab}: ¡Tu esencia es suya!")
                resultado["debe_atacar"] = True
                resultado["efectos"]["drenaje"] = True
                resultado["efectos"]["drenaje_porcentaje"] = 0.5  # 50% del daño se cura
                # También reduce armadura
                personaje["armadura"] = max(0, personaje.get("armadura", 0) - 1)
                alerta(f"🛡 Tu defensa falla. Tu armadura se debilita.")
                return resultado
            
            elif efecto == "arrebato_apocaliptico":
                # Bel'akhor: ataque brutal con -2 armadura temporal
                alerta(f"⚔️ {enemigo['nombre']} usa {nombre_hab}: ¡La ruina te alcanza!")
                resultado["debe_atacar"] = True
                resultado["efectos"]["damage_boost"] = 0.6
                resultado["efectos"]["armor_reduction"] = 2
                resultado["efectos"]["armor_duration"] = 3
                return resultado
            
            elif efecto == "inyeccion_quirurgica":
                # Fabius: se cura 3 HP y prepara ataque potenciado
                enemigo["vida"] = min(enemigo.get("vida_max", enemigo["vida"]), enemigo["vida"] + 3)
                alerta(f"💚⚡ {enemigo['nombre']} usa {nombre_hab}: Se inyecta algo. Sonríe con complacencia.")
                resultado["debe_atacar"] = True
                resultado["efectos"]["damage_boost"] = 0.25
                return resultado
            
            elif efecto == "incision_mortal":
                # Fabius: ataque brutal +40% daño + 3 sangrado
                alerta(f"⚔️ {enemigo['nombre']} usa {nombre_hab}: ¡Tu cuerpo será su obra maestra!")
                resultado["debe_atacar"] = True
                resultado["efectos"]["damage_boost"] = 0.4
                resultado["efectos"]["sangrado_extra"] = 3
                return resultado
            
            elif efecto == "azotazo_demonico":
                # Bel'akhor: ataque +35% daño + 2 sangrado
                alerta(f"💥 {enemigo['nombre']} usa {nombre_hab}: ¡EL FIN DEL MUNDO!")
                resultado["debe_atacar"] = True
                resultado["efectos"]["damage_boost"] = 0.35
                resultado["efectos"]["sangrado_extra"] = 2
                return resultado
    
    return None

# ================== COMBATE ==================

# Diccionario de narrativas para habilidades específicas
NARRATIVAS_HABILIDADES = {
    # PASIVAS
    "Huesos Punzantes": "Los fragmentos filosos que sobresalen de su cuerpo te raspan, dejando heridas profundas.",
    "Gancho de Carnicero": "El gancho oxidado rasgura tu piel. La herida arde.",
    "Colmillos de Sombra": "Los colmillos invisibles dejan rastros de sangre en el aire.",
    "Sutura de Dolor": "Las líneas de sutura brillan rojo. Sientes el dolor antes de ver la herida.",
    "Arrebato de Ira": "Un gruñido salvaje. Su cuerpo se desata, enloquecido.",
    "Rugido Infernal": "Un aullido que resuena en tus huesos. El demonio se potencia.",
    "Regeneracion grotesca": "Los muñones milagrosamente se regeneran, humeando. La criatura se sana a sí misma.",
    "Hoja sombria": "Algo invisible te golpear. Tu cuerpo no responde.",
    # ACTIVAS
    "Ícor de Larva": "La probóscide dispara un ácido viscoso. Tu armadura se corroe.",
    "Ícor de Mosca": "Un goteo de icor negro cae sobre ti. Tu defensa se debilita.",
    "Arrebato de Locura": "Su cuerpo se tensa. Los ojos se abren anómalamente. ¡Se prepara para golpear con toda su fuerza!",
    "Golpe Brutal": "Hace una pausa. Reúne toda su furia. El siguiente ataque será devastador.",
    "Recuperacion Impia": "Forrix invoca un poder antiguo. Sus heridas se cierran mientras habla en lengua demoniaca.",
    "Inyección Quirúrgica": "Una aguja microscópica te atraviesa. El cirujano susurra un diagnóstico de muerte.",
    "Incisión Mortal": "El bisturí brilla. Esta vez, el corte es la música más bella que jamás ha oído.",
    "Acuchillamiento": "La sombra se vuelve filo. Una lluvia de cuchillas emerge de la oscuridad.",
    "Sombra oculta": "Sanakht desaparece en una penumbra imposible. Ya no sabes dónde atacar.",
    "Azotazo Demoníaco": "El demonio desata su ira primordial. Los aires mismos tiemblan.",
    "Drenaje de Almas": "Una conexión visceral entre ambos. Sientes tu esencia siendo succionada.",
    "Arrebato Apocalíptico": "Bel'akhor pronuncia palabras de ruina. Tu defensa colapsa.",
    "Golpes furiosos": "Los muñones golpean sin orden ni concierto. Es pura violencia sin control.",
    "Frensi demoniaco": "Ka-Banda se convierte en pura furia. Ataca desde todos lados a la vez.",
}

# Diccionario de narrativas de ataque para cada enemigo
NARRATIVAS_ENEMIGOS = {
    "Maniaco Mutilado": [
        "El maníaco se abalanza a trompicones, babeando, intentando hundirte los dientes en el cuello.",
        "Se lanza contra ti con sus muñones por delante, golpeando sin control con todos sus apendices.",
        "Usa los huesos afilados que sobresalen de su torso y brazos para atacarte.",
    ],
    "Perturbado": [
        "Ríe histéricamente mientras se lanza sobre ti, con manos convertidas en garras de carne viva.",
        "Su cuerpo convulsiona violentamente, grita y se retuerce, pero no detiene su ataque.",
        "Muerde sus brazos, arrancando trozos y escupiendotelos mientras avanza.",
    ],
    "Rabioso": [
        "El rabioso se abalanza contra ti escupiendo espuma roja, con su cuerpo al límite de lo que puede aguantar.",
        "Grita algo ininteligible y carga de cabeza, sin cubrir nada, sin importarle nada.",
        "Se abre una herida nueva en le pecho antes de atacar. El dolor parece alimentarlo.",
    ],
    "Sombra tenebrosa": [
        "Los filos surgen de la nada, disparados desde la oscuridad antes de que puedas reaccionar.",
        "La sombra se fragmenta y se recompone a tu lado. Las cuchillas llegan desde ángulos imposibles de defender.",
        "Un siseo frío. Los filos te rozan antes de que los veas. El corte llega un instante después.",
    ],
    "Larvas de Sangre": [
        "La larva lanza su probóscide como un látigo, clavándola antes de que te apartes.",
        "Se enrolla sobre sí misma y salta con su asqueroso aguijon por delante.",
        "Se retuerce sobre sí misma. Pareciera que baila, y de repente te dispara un chorro de icor purulento.",
    ],
    "Mosca de Sangre": [
        "Las mandíbulas serradas se cierran con un chasquido seco mientras zumba hacia ti.",
        "Bate las alas con violencia y el golpe de aire caliente y fetido te desestabiliza antes del ataque.",
        "Gotea un líquido negro sobre ti al pasar. Sientes nauseas. El dolor llega un segundo después.",
    ],
    "Forrix, el Carcelero": [
        "El puño de Forrix desciende con la fuerza de una roca. Oyes los tintineos del metal en su carne antes de ver el golpe.",
        "Arranca un gancho de su espalda con un chasquido horrible. Sin inmutarse por el dolor, lo blande contra ti.",
        "Se aprieta las suturas de su cabeza con ambas manos, y entonces te embiste como un toro de metal.",
    ],
    "Fabius, Amo de la Mazmorra": [
        ("El Cirujano tiene una fuerza increible para su tamaño. Sus puños se sienten como martillos.", "La carne siempre miente. Yo solo la obligo a decir la verdad."),
        ("Su cuerpo viola sus propias leyes anatómicas y te golpea con apendices no humanos.", "¿Ves? El cuerpo es una hipótesis. Yo la reviso constantemente."),
        ("Una risa suave, casi íntima, acompaña el corte. No celebra el daño. Lo cataloga.", "No te matare... te convertire en mi obra maestra!"),
    ],
    "Sanakht, la Sombra Sangrienta": [
        ("Las hoces se abren en un arco que la geometría no debería permitir. La sangre que dejan en el aire no te parece humana.", "susurros"),
        ("Se disuelve en la oscuridad como tinta en agua y reaparece cosida a tu sombra. El filo llega antes que la forma.", "susurros"),
        ("Un susurro que no es voz erosiona el instante antes del golpe. El cuerpo lo entiende aunque la mente no quiera.", "susurros"),
    ],
    "Mano Demoniaca": [
        ("Los muñones caen sobre ti con la inercia de algo que no conoce la fatiga ni el límite. La criatura os observa:", "Más brazos... más amigos... todos juntos... todos míos..."),
        ("La criatura barre el espacio que ocupas con indiferencia, como si no te viera. Su maestro la anima:", "Vaaayaa, no pense que esta me hubiera salido tan bien!."),
        ("Cada 'pisada' del monstruo hace temblar la piedra. Tú intento de amigo sigue hablandote:", "Si te quedas quieto... también puedo arreglarte."),
    ],
    "Ka-Banda, Demonio Sombrio": [
        ("Ka-Banda pronuncia una sílaba y el aire entre ambos explota en una fracción de segundo.", "¡¡KA'BANDA MAK NOR!! ¡KA'BANDA THRAKK UL-KHOR!!"),
        ("Ves como sus bocas se abren en cascada, desfasadas unas de otras. Sientes sus mordiscos tras los ojos.", "El demonio se lanza sobre ti con una velocidad inhumana, blandiendo sus hoces como si fueran parte de su cuerpo."),
        ("No hay movimiento previo. Solo lo notas. El golpe simplemente ocurre, se manifiesta en ti.", "¡¡KHRON-ETH, KHRON-ETH!! - Por el sonido gorgoteante, jurarias que rie."),
    ],
    "Bel'akhor, Principe Demonio": [
        ("El hacha de bronce cae como si la propia gravedad hubiera tomado partido. El impacto no resuena en el metal: resuena en tus dientes.", "Hubo un tiempo en que los reyes me obedecían."),
        ("El ala se despliega un milisegundo antes que el arma. Te golpea. Luego llega lo demás.", "Ahora solo quedan ruinas... y mi paciencia."),
        ("Bel'akhor no mira el arma mientras ataca. Te mira a ti. El hacha sabe sola a dónde ir.", "Inclínate. Todos terminan aprendiendo."),
    ],
}

def _narrar_ataque_enemigo(nombre):
    """Narra el ataque de un enemigo seleccionando aleatoriamente de NARRATIVAS_ENEMIGOS."""
    if nombre not in NARRATIVAS_ENEMIGOS:
        return  # Si el enemigo no tiene narrativa personalizada, no narrar
    
    narrativa = random.choice(NARRATIVAS_ENEMIGOS[nombre])
    
    # Manejar narrativas con diálogo (tuplas)
    if isinstance(narrativa, tuple):
        for parte in narrativa:
            if parte == "susurros":
                susurros_aleatorios()
            else:
                narrar(parte) if len(parte) > 30 else dialogo(parte)
    else:
        narrar(narrativa)

def _calcular_damage_total(daño_bruto, enemigo, efectos_especiales, mods_pasivos):
    """
    Centraliza el cálculo de daño bruto considerando todas las fuentes de boosts:
    - Boost anterior (_damage_boost)
    - Boost temporal (_efectos_temporales)
    - Boost especial de habilidad activa
    - Boost pasivo de habilidades pasivas
    """
    # VALIDATION (PASO 9)
    assert isinstance(daño_bruto, (int, float)) and daño_bruto >= 0, f"daño_bruto debe ser >= 0, no {daño_bruto}"
    assert isinstance(efectos_especiales, dict), f"efectos_especiales debe ser dict"
    assert isinstance(mods_pasivos, dict), f"mods_pasivos debe ser dict"
    
    with _medir_tiempo("_calcular_damage_total()"):
        daño_original = daño_bruto
        _log_debug("DAMAGE", f"Inicio cálculo: daño_origen={daño_bruto}")
        
        # Aplicar boost de habilidad anterior
        if "_damage_boost" in enemigo:
            boost_anterior = enemigo["_damage_boost"]
            daño_bruto = math.ceil(daño_bruto * (1 + boost_anterior))
            _log_debug("DAMAGE", f"  - Boost anterior ({boost_anterior:.1%}): {daño_original} → {daño_bruto}")
            del enemigo["_damage_boost"]
        
        # Aplicar boost temporal
        if "_efectos_temporales" in enemigo and "damage_boost" in enemigo["_efectos_temporales"]:
            boost = enemigo["_efectos_temporales"]["damage_boost"]["valor"]
            daño_prev = daño_bruto
            daño_bruto = math.ceil(daño_bruto * (1 + boost))
            _log_debug("DAMAGE", f"  - Boost temporal ({boost:.1%}): {daño_prev} → {daño_bruto}")
        
        # Aplicar boost especial de habilidad activa
        if "damage_boost" in efectos_especiales:
            boost_esp = efectos_especiales["damage_boost"]
            daño_prev = daño_bruto
            daño_bruto = math.ceil(daño_bruto * (1 + boost_esp))
            _log_debug("DAMAGE", f"  - Boost especial ({boost_esp:.1%}): {daño_prev} → {daño_bruto}")
        
        # Aplicar boost pasivo de habilidades pasivas
        bonus_pasivo = mods_pasivos.get("daño", 0)
        if bonus_pasivo != 0:
            daño_prev = daño_bruto
            daño_bruto += bonus_pasivo
            _log_debug("DAMAGE", f"  - Bonus pasivo (+{bonus_pasivo}): {daño_prev} → {daño_bruto}")
        
        # Asegurar que el daño es entero
        daño_bruto = math.ceil(daño_bruto)
        _log_debug("DAMAGE", f"Final: {daño_bruto}")
        return daño_bruto

def _planificar_efectos(personaje, enemigo, daño_final, efectos_especiales, mods_pasivos, stance):
    """
    **FASE 1: PLANIFICACIÓN** - Determina qué efectos se aplicarán sin modificar estado.
    Compatible con strings y Enums.Stance.
    Retorna dict con plan de ejecución de efectos.
    """
    # VALIDATION (PASO 9)
    assert isinstance(daño_final, (int, float)) and daño_final >= 0, f"daño_final debe ser >= 0"
    assert "vida" in personaje and "armadura" in personaje, "personaje debe tener vida y armadura"
    assert "fuerza" in personaje and "destreza" in personaje, "personaje debe tener stats"
    
    # Convertir Enum a string si es necesario
    stance_str = _normalizar_enum(stance)
    
    plan = {
        "daño": daño_final,
        "daño_bruto": daño_final,
        "daño_tras_reduccion": daño_final,
        "sangrado": 0,
        "stun": False,
        "armor_reduction": None,
        "drenaje": None,
    }
    
    # Calcular daño tras stance (bloquear/esquivar)
    if stance_str == "bloquear":
        tirada = random.randint(1, 20) + personaje["fuerza"]
        margen = max(0, tirada - 12)
        reduccion = min(0.60, margen * 0.06)
        plan["daño_tras_reduccion"] = int(daño_final * (1 - reduccion))
        plan["stance_info"] = ("bloquear", tirada, reduccion)
    elif stance_str == "esquivar":
        tirada = random.randint(1, 20) + personaje["destreza"]
        if tirada > 12:
            plan["esquiva_exitosa"] = True
            plan["stance_info"] = ("esquivar", tirada, True)
        else:
            plan["esquiva_exitosa"] = False
            plan["stance_info"] = ("esquivar", tirada, False)
            plan["daño_tras_reduccion"] = daño_final
    else:
        plan["daño_tras_reduccion"] = daño_final
    
    # Calcular reducción de armadura
    armadura = personaje.get("armadura", 0)
    if "_efectos_temporales" in personaje and "armor_reduction" in personaje["_efectos_temporales"]:
        armadura = max(0, armadura - personaje["_efectos_temporales"]["armor_reduction"]["valor"])
    
    plan["armadura_efectiva"] = armadura
    plan["daño"] = max(1, math.ceil(plan["daño_tras_reduccion"] - armadura))
    
    # Sangrado (de pasivas y especiales)
    sangrado_total = mods_pasivos.get("sangrado", 0)
    if "sangrado_extra" in efectos_especiales:
        sangrado_total += efectos_especiales["sangrado_extra"]
    plan["sangrado"] = sangrado_total
    
    # Stun (de pasivas)
    if mods_pasivos.get("stun_prob", 0) > 0 and random.random() < mods_pasivos["stun_prob"]:
        plan["stun"] = True
    
    # Reducción de armadura temporal (de activas)
    if "armor_duration" in efectos_especiales and "armor_reduction" in efectos_especiales:
        plan["armor_reduction"] = {
            "valor": efectos_especiales.get("armor_reduction", 0),
            "duracion": efectos_especiales.get("armor_duration", 1)
        }
    
    # Drenaje de almas (de activas)
    if "drenaje" in efectos_especiales and efectos_especiales.get("drenaje", False):
        plan["drenaje"] = {
            "porcentaje": efectos_especiales.get("drenaje_porcentaje", 0.5),
            "cura_directa_armadura": 1  # Se reduce armadura al activar
        }
    
    _log_debug("EFFECT_PLAN", f"{enemigo['nombre']} → Plan: daño={plan['daño']}, sangrado={plan['sangrado']}, stun={plan['stun']}")
    return plan

def _ejecutar_efectos(personaje, enemigo, plan):
    """
    **FASE 2: EJECUCIÓN** - Aplica todos los efectos del plan al estado del juego.
    """
    # Esquiva exitosa: terminar aquí
    if plan.get("esquiva_exitosa"):
        exito(f"💨 Esquivas el ataque. (tirada {plan['stance_info'][1]})")
        return
    
    # Reportar stance
    if "stance_info" in plan:
        tipo_stance, tirada, resultado = plan["stance_info"]
        if tipo_stance == "bloquear":
            reduccion = resultado
            if reduccion > 0:
                sistema(f"🛡 Bloqueas parte del golpe. (tirada {tirada}, -{int(reduccion*100)}% daño)")
            else:
                sistema(f"Intentas bloquear pero no cubres el golpe. (tirada {tirada})")
    
    # Aplicar daño
    daño = plan["daño"]
    armadura = plan["armadura_efectiva"]
    daño_bruto = plan["daño_tras_reduccion"]
    
    _log_debug("EFFECT_EXEC", f"Aplicando daño: {daño} (bruto={daño_bruto}, arm={armadura})")
    if armadura > 0 and daño < daño_bruto:
        alerta(f"Recibes {daño} de daño.  ({daño_bruto} − {armadura} armadura)")
    else:
        alerta(f"Recibes {daño} de daño.")
    personaje["vida"] -= daño
    
    # Drenaje de almas
    if plan.get("drenaje"):
        drenaje = plan["drenaje"]
        cura = int(daño * drenaje["porcentaje"])
        enemigo["vida"] = min(enemigo.get("vida_max", enemigo["vida"]), enemigo["vida"] + cura)
        _log_debug("EFFECT_EXEC", f"Drenaje: {enemigo['nombre']} cura {cura} HP")
        exito(f"💀 {enemigo['nombre']} absorbe tu vida: +{cura} HP.")
        # También reduce armadura al aplicar drenaje
        personaje["armadura"] = max(0, personaje.get("armadura", 0) - drenaje["cura_directa_armadura"])
    
    # Reducción de armadura temporal
    if plan.get("armor_reduction"):
        ar = plan["armor_reduction"]
        if "_efectos_temporales" not in personaje:
            personaje["_efectos_temporales"] = {}
        personaje["_efectos_temporales"]["armor_reduction"] = {
            "valor": ar["valor"],
            "turnos_restantes": ar["duracion"]
        }
        _log_debug("EFFECT_EXEC", f"Armadura temporal: -{ar['valor']} por {ar['duracion']} turnos")
        alerta(f"🛡 Tu armadura se reduce en {ar['valor']} durante {ar['duracion']} turno(s).")
    
    # Sangrado
    if plan.get("sangrado", 0) > 0:
        enemigo["sangrado"] = enemigo.get("sangrado", 0) + plan["sangrado"]
        _log_debug("EFFECT_EXEC", f"Sangrado: +{plan['sangrado']} (total={enemigo['sangrado']})")
        alerta(f"🩸 Te causa sangrado de {plan['sangrado']}.")
    
    # Reducción de armadura pasiva
    if plan.get("armor_reduction_pasiva", 0) > 0:
        personaje["armadura"] = max(0, personaje.get("armadura", 0) - plan["armor_reduction_pasiva"])
        _log_debug("EFFECT_EXEC", f"Armadura reducida pasivamente: -{plan['armor_reduction_pasiva']}")
        alerta(f"🛡 Tu armadura se reduce en {plan['armor_reduction_pasiva']}.")
    
    # Stun
    if plan.get("stun"):
        personaje["stun"] = personaje.get("stun", 0) + 1
        _log_debug("EFFECT_EXEC", f"Stun aplicado (total={personaje.get('stun', 0)})")
        alerta(f"⚡ ¡Te quedas aturdido!")

def turno_enemigo(personaje, enemigo, stance=None):
    """Resuelve el turno del enemigo aplicando la stance declarada por el jugador."""
    # VALIDATION (PASO 9)
    es_valido, msg = _verificar_integridad_turno(personaje, enemigo)
    if not es_valido:
        _log_debug("VALIDATION", f"turno_enemigo: {msg}")
        alerta(f"⚠️ Error de validación: {msg}")
        return
    
    with _medir_tiempo("turno_enemigo()"): 
        nombre = enemigo["nombre"]
        _log_debug("TURN", f"=== Turno de {nombre} (vida={enemigo['vida']}/{enemigo.get('vida_max', enemigo['vida'])}) ===")

        if enemigo.get("stun", 0) > 0:
            _log_debug("TURN", f"  {nombre} está aturdido")
            alerta(f"⚡ {nombre} está aturdido y pierde el turno.")
            enemigo["stun"] = max(0, enemigo["stun"] - 1)
            decrementar_efectos_temporales(enemigo)
            return

        # --- Verificar si ejecuta una habilidad activa ---
        hab_activa_info = ejecutar_habilidad_activa(enemigo, personaje)
        if hab_activa_info and not hab_activa_info.get("debe_atacar", False):
            # Habilidad ejecutada sin ataque (gastó el turno)
            _log_debug("TURN", f"  {nombre} usó habilidad activa sin ataque")
            decrementar_efectos_temporales(enemigo)
            return
        
        # Si hay habilidad activa que debe atacar, marcar los efectos especiales
        efectos_especiales = hab_activa_info.get("efectos", {}) if hab_activa_info else {}

        # Narración del ataque (selecciona aleatoriamente de narrativas predefinidas)
        _narrar_ataque_enemigo(nombre)
        
        narrar(f"{nombre} te ataca.")

        daño_bruto = random.randint(*enemigo["daño"])
        
        # Aplicar habilidades pasivas
        mods = aplicar_habilidades_pasivas(enemigo, personaje)
        
        # Centralizar cálculo de daño con todos los boosts
        daño_bruto = _calcular_damage_total(daño_bruto, enemigo, efectos_especiales, mods)
        
        # FASE 1: PLANIFICAR todos los efectos sin aplicarlos
        plan = _planificar_efectos(personaje, enemigo, daño_bruto, efectos_especiales, mods, stance)
        
        # FASE 2: EJECUTAR todos los efectos del plan
        _ejecutar_efectos(personaje, enemigo, plan)
        
        # Aplicar modificación de armadura pasiva (de habilidades pasivas)
        if mods.get("armor_reduction", 0) > 0:
            personaje["armadura"] = max(0, personaje.get("armadura", 0) - mods["armor_reduction"])
            alerta(f"🛡 Tu armadura se reduce en {mods['armor_reduction']}.")
        
        # Aplicar stun_chance de habilidades especiales
        if "stun_chance" in efectos_especiales and random.random() < efectos_especiales["stun_chance"]:
            personaje["stun"] = personaje.get("stun", 0) + 1
            alerta(f"⚡ ¡Quedas aturdido/a!")
        
        # Decrementar efectos temporales al final del turno del enemigo
        decrementar_efectos_temporales(enemigo)

# ================== TURNO DEL JUGADOR ==================

def _aplicar_modificadores_stance(stance, daño, prob, stance_anterior, repeticiones_consecutivas):
    """
    **O(1) STANCE LOGIC** - Calcula modificadores de daño y precisión basados en stance.
    Retorna: (daño_modificado, prob_modificada, penalizacion_str, nuevo_repeticiones)
    """
    penalizacion_str = ""
    nuevo_repeticiones = repeticiones_consecutivas
    
    if stance in ("bloquear", "esquivar"):
        # Actualizar contador de repeticiones
        if stance == stance_anterior:
            nuevo_repeticiones += 1
        else:
            nuevo_repeticiones = 1
        
        # Penalización acumulativa: -10% probabilidad por turno repitiendo
        penalizacion = nuevo_repeticiones * 10
        prob = max(0, prob - penalizacion)
        penalizacion_str = f"Penalización por repetir postura: -{penalizacion}% precisión (turnos consecutivos: {nuevo_repeticiones})"
    else:
        nuevo_repeticiones = 0
    
    # Aplicar multiplicadores de daño según stance
    if stance == "bloquear":
        daño = max(1, daño // 2)
    elif stance == "esquivar":
        daño = max(1, int(daño * 0.67))
        prob = int(prob * 0.67)
    
    return daño, prob, penalizacion_str, nuevo_repeticiones

def turno_jugador(personaje, enemigo):
    """Lee la acción del jugador y la resuelve: poción, huida, stance o ataque.
    Devuelve (resultado, stance): resultado es 'huida' o 'ataque'; stance es None|'bloquear'|'esquivar'.
    """
    abreviaturas = {**_ABREVIATURAS_ARMAS, "p": "pocion", "pot": "pocion", "h": "huir",
                    "bl": "bloquear", "blo": "bloquear", "esq": "esquivar"}

    huida_intentada    = False
    pocion_usada_turno = False
    stance             = None   # None | "bloquear" | "esquivar"
    stance_anterior    = None   # stance del turno anterior
    repeticiones_consecutivas = 0  # contador de repeticiones de misma stance

    while True:
        emitir("opciones_combate", {
            "armas":               list(estado["armas_jugador"].keys()),
            "pociones":            personaje["pociones"],
            "huida_bloqueada":     huida_intentada,
            "pocion_usada_turno":  pocion_usada_turno,
            "stance":              stance,
        })
        eleccion = leer_input("→ Acción: ", personaje).lower()  # TODO: tkinter callback
        accion = abreviaturas.get(eleccion, eleccion)

        # ---------- STANCE: BLOQUEAR (no consume turno, toggle) ----------
        if accion == _normalizar_enum(Accion.STANCE_BLOQUEAR) or accion == "bloquear":
            stance = None if stance == "bloquear" else "bloquear"
            if stance == "bloquear":
                sistema("🛡 Postura de bloqueo activa. Tu ataque hará la mitad de daño.")
            else:
                sistema("Postura de bloqueo desactivada.")
                stance_anterior = None
                repeticiones_consecutivas = 0
            continue

        # ---------- STANCE: ESQUIVAR (no consume turno, toggle) ----------
        if accion == _normalizar_enum(Accion.STANCE_ESQUIVAR) or accion == "esquivar":
            stance = None if stance == "esquivar" else "esquivar"
            if stance == "esquivar":
                sistema("💨 Postura de esquiva activa. Precisión y daño reducidos un 33%.")
            else:
                sistema("Postura de esquiva desactivada.")
                stance_anterior = None
                repeticiones_consecutivas = 0
            continue

        # ---------- USAR POCIÓN (no consume turno) ----------
        if accion == _normalizar_enum(Accion.POCION) or accion == "pocion":
            if pocion_usada_turno:
                alerta("Ya has usado una poción este turno.")
                continue
            if personaje["pociones"] <= 0:
                alerta("No te quedan pociones.")
                continue
            if personaje["vida"] >= personaje["vida_max"]:
                sistema("No necesitas usar una poción ahora.")
                continue

            personaje["pociones"] -= 1
            personaje["vida"] = min(personaje["vida_max"], personaje["vida"] + 4)
            pocion_usada_turno = True
            exito(
                f"Bebes una poción. ♥ Vida: {personaje['vida']} "
                f"| Pociones restantes: {personaje['pociones']}"
            )
            continue

        # ---------- HUIR (1 intento por turno, no consume turno) ----------
        if accion == _normalizar_enum(Accion.HUIDA) or accion == "huir":
            if huida_intentada:
                alerta("Ya has intentado huir este turno.")
                continue

            huida_intentada = True
            tirada = random.randint(1, 20) + personaje["destreza"]

            if tirada >= 15:
                exito("Encuentras una abertura y logras escapar.")
                return ("huida", None)
            else:
                alerta("Intentas huir, pero el enemigo te corta el paso.")
                continue

        # ---------- ATACAR (consume turno) ----------
        if accion not in estado["armas_jugador"]:
            alerta("No existe esa arma ni acción.")
            continue

        arma = estado["armas_jugador"][accion]
        daño = calcular_daño(arma, personaje)
        prob = arma["golpe"]   # precisión plana, sin modificador de stat
        # Aplicar esquiva del enemigo si existe
        esquiva_enemigo = enemigo.get("esquiva", 0)
        if esquiva_enemigo:
            prob = max(0, prob - esquiva_enemigo)
            sistema(f"El enemigo esquiva parte de tu ataque: -{esquiva_enemigo}% precisión.")
        
        # Aplicar reducción de precisión temporal (Sombra Oculta, etc)
        if "_efectos_temporales" in enemigo and "precision_reducida" in enemigo["_efectos_temporales"]:
            reduccion = enemigo["_efectos_temporales"]["precision_reducida"]["valor"]
            prob = max(0, prob - reduccion)
            sistema(f"El enemigo está envuelto en sombras: -{reduccion}% precisión.")

        # Modificadores de stance sobre el ataque del jugador (O(1) complexity)
        daño, prob, penalizacion_str, repeticiones_consecutivas = _aplicar_modificadores_stance(
            stance, daño, prob, stance_anterior, repeticiones_consecutivas
        )
        if penalizacion_str:
            sistema(penalizacion_str)
        
        # Actualizar stance anterior para el próximo turno
        if stance in ("bloquear", "esquivar"):
            stance_anterior = stance

        if random.randint(1, 100) <= prob:
            enemigo["vida"] -= daño
            exito(f"Golpeas por {daño}.")

            if "vida" in arma:
                personaje["vida"] += arma["vida"]
                exito(f"Tu arma absorbe {arma['vida']} de vida.")

            if "sangrado" in arma:
                enemigo["sangrado"] = enemigo.get("sangrado", 0) + arma["sangrado"]
                alerta(f"🩸 Provocas sangrado: {arma['sangrado']} por turno.")

            if "stun" in arma and random.randint(1, 6) <= arma["stun"]:
                enemigo["stun"] = 1
                alerta(f"⚡ ¡{enemigo['nombre']} queda aturdido!")
            if "auto_daño" in arma:
                personaje["vida"] -= arma["auto_daño"]
                alerta(f"La empuñadura del hacha te desgarra. -{arma['auto_daño']} de vida.")
        else:
            alerta("Fallas el golpe.")

        return ("ataque", stance)

# ================== SANGRADO ==================


def aplicar_sangrado(enemigo):
    """Aplica el daño de sangrado acumulado sobre el enemigo al final del ciclo."""
    daño = enemigo.get("sangrado", 0)
    if daño > 0:
        enemigo["vida"] -= daño
        alerta(f"🩸 {enemigo['nombre']} sangra: -{daño} de vida.")


# ================== BUCLE DE COMBATE ==================


def combate(personaje, enemigo=None):
    """Bucle principal de combate: HUD → turno jugador → turno enemigo → sangrado."""
    personaje["_huyo_combate"] = False
    victoria = False

    if enemigo is None:
        enemigo = enemigo_aleatorio()

    while enemigo["vida"] > 0 and personaje["vida"] > 0:

        # --- HUD ---
        emitir("hud_combate", {
            "vida":           personaje["vida"],
            "vida_max":       personaje.get("vida_max", 25),
            "fuerza":         personaje["fuerza"],
            "destreza":       personaje["destreza"],
            "armadura":       personaje.get("armadura", 0),
            "enemigo_nombre": enemigo["nombre"],
            "enemigo_vida":   enemigo["vida"],
        })

        # --- Turno del jugador ---
        resultado, stance = turno_jugador(personaje, enemigo)

        if resultado == "huida":
            alerta("Temiendo por tu vida, abandonas corriendo el combate.")
            narrar("Te alejas sin mirar atrás, guiándote solo por tu instinto.")
            personaje["_huyo_combate"] = True
            emitir("terminar_combate", {})
            return

        if enemigo["vida"] <= 0:
            exito("Has vencido a tu enemigo.")
            victoria = True
            emitir("terminar_combate", {})
            break

        # --- Turno del enemigo ---
        turno_enemigo(personaje, enemigo, stance)

        if personaje["vida"] <= 0:
            emitir("terminar_combate", {})
            break
        
        # --- Decrementar efectos temporales del jugador ---
        decrementar_efectos_temporales_jugador(personaje)

        # --- Sangrado (al final del ciclo) ---
        aplicar_sangrado(enemigo)

        if enemigo["vida"] <= 0:
            exito("Tu enemigo sucumbe a las heridas de sangrado.")
            victoria = True
            break

    if personaje["vida"] <= 0:
        alerta("Has sido derrotado.")
        resultado_derrota = fin_derrota(personaje)
        if personaje.get("_flg1"):
            personaje.pop("_flg1", None)
            return
        return

    evento_post_combate = resolver_eventos_post_combate(personaje, enemigo)
    if evento_post_combate:
        aplicar_evento(evento_post_combate, personaje)

    # Finalizar: bonus y finales secretos
    if victoria:
        estado["_c01"] += 1
    if estado["_c01"] >= 666 and personaje["_pw"] == 1:
        _fate_06(personaje)
        return
    elif estado["_c01"] >= 100:
        _fate_04(personaje)
        return
    revisar_bonus_fibonacci(personaje)

# ================== PROGRESO DE NIVEL ==================


def avanzar_nivel(personaje):
    """Reinicia el contador de eventos y aplica la transición al siguiente nivel."""
    narrar("Abres la puerta de hierro y asciendes al nivel superior...")
    estado["eventos_superados"] = 0
    estado["veces_guardado"] = 0          # Nuevos escondites: el riesgo de guardar se reinicia


def reiniciar_camino_por_huida(personaje):
    """Limpia la ruta del jugador tras huir de un combate."""
    personaje["_huyo_combate"] = False
    estado["ruta_jugador"].clear()
    estado["pasos_nivel2"].clear()
    estado["pasos_secretos"].clear()
    estado["eventos_superados"] -= 2  # Penalización por huir: pierdes parte del progreso hacia el siguiente nivel
    alerta("Escapas a ciegas entre pasillos idénticos, con el corazón desbocado.")
    narrar("Cuando te detienes, no reconoces nada: has perdido por completo el camino.")
    narrar("Tendrás que volver a encontrar tu rumbo...")


# ================== FLUJO PRINCIPAL ==================

# ================== POST-COMBATE ==================


def resolver_eventos_post_combate(personaje, enemigo):
    """Resuelve el texto y recompensas tras vencer a cada tipo de enemigo."""
    nombre = enemigo["nombre"]
    if nombre == "Forrix, el Carcelero":
        narrar("Tras propinarle el último tajo, Forrix retrocede un paso. La furia abandona su rostro y deja algo peor al descubierto.")
        narrar("La mandíbula le tiembla; los labios, gruesos y desgarrados, se pliegan en una mueca infantil que no encaja en aquel cráneo de bestia.")
        narrar("Sus ojos enrojecidos se enturbian, vidriosos, incapaces de comprender la grieta que se abre en su obediencia.")
        dialogo("'¡IDIOTA, ESTÚPIDO! ¡TE ODIO, LO HAS ARRUINADO TODO!'")
        narrar("Mira su vientre como quien contempla un altar profanado, donde la llave palpita entre los puntos inflamados.")
        narrar("La carne está lacerada, los tajos han reventado tejido surcado por infecciones antiguas.")
        narrar("Forrix se congestiona, y cada latido empuja hacia fuerala llave junto con un brillo húmedo y oscuro.")
        dialogo("'¡¡¡VETE DE AQUÍ, NO TE MERECES ESTAR AQUÍ!!!'")
        narrar("Clava sus asquerosas uñas en la herida sin vacilar.")
        narrar("La presión abre los bordes reblandecidos; los cortes ceden con un desgarro viscoso.")
        narrar("Tira de la llave varias veces, mientras brota pus y coagulos.")
        narrar("La resistencia dura un instante, como si algo desde dentro se aferrara a ella.")
        narrar("Luego se abre la carne en canal.")
        dialogo("'¡SOLO QUERÍAS ESTO, VERDAD?' — brama mientras se arranca el hierro del abdomen.")
        narrar("La cavidad se desborda.")
        narrar("Asoman nudos intestinales hinchados, cubiertos de un brillo lechoso.")
        narrar("La sangre no fluye: cae como miel negra, mezclada con pus y fragmentos de metal.")
        narrar("Forrix permanece erguido, sosteniendo torpemente sus propias tripas con sorpresa.")
        narrar("Cuando recuerda que estas allí, su rostro se contrae en una mueca deforme")
        narrar("Ruge como poseido e intenta lanzarte la llave con un gesto torpe y cargado de odio.")
        narrar("El brazo se alza apenas un palmo antes de perder toda fuerza.")
        narrar("El hierro resbala de sus dedos, la llave golpea el suelo y rueda por la sala.")
        narrar("Forrix se desploma hacia delante, cayendo sobre lo que queda de sí mismo.")
        narrar("El impacto retumba como un yunque y aplasta lo que quedaba dentro.")
        narrar("Su rostro queda torcido en una mueca de rencor puro, como si incluso en la muerte intentara negarte el paso.")
        narrar("El Carcelero no vuelve a moverse.")
        narrar("El Carcelero queda inmóvil, su cuerpo desparramado y la llave a tus pies.")
        narrar("Te quedas unos segundos paralizado, observando aquel monstruo destrozado.")
        narrar("Una criatura tan enferma y retorcida... a que le debia esa obediencia ciega y ese odio desmedido?")
        narrar("El horror se mezcla con la fascinación: ¿cómo alguien podía haber soportado tanto dolor?")
        narrar("¿Cómo sobrevivir tantos horrores, y aun así seguir existiendo en la carne y el metal?")
        narrar("Recoges la llave, la limpias de podredumbre en un jirón de ropa y te diriges hacia la salida.")
        narrar("Con un último vistazo a Forrix, empujas la puerta oxidada y te adentras en los niveles inferiores de la mazmorra.")
        personaje["tiene_llave"] = True
        personaje["nivel"] += 1
        avanzar_nivel(personaje)
        return None

    elif nombre == "Sanakht, la Sombra Sangrienta":
        narrar("Tras desgarrar el último jirón de sombra, se crea un remolino que absorbe el océano de sangre.")
        alerta("No puedes nadar más rápido y el remolino te engulle.")
        narrar("Apareces tirado en medio del corredor, cubierto de sangre y con la cabeza dando vueltas.")
        narrar("Vomitas chorros y coágulos de sangre, que frente a tus ojos se amontonan con vida propia.")
        narrar("Comienzan a tornarse negros y compactarse, tomando la forma de una extraña arma.")
        narrar("Te repugna, pero una pulsión interna te obliga a cogerla.")
        return {"armas": {"hoz": {}}}

    elif nombre == "Fabius, Amo de la Mazmorra":
        exito("Consigues salir.")
        ejecutar_final_normal_por_arma(personaje)
        return {}

    elif nombre == "Mano Demoniaca":
        narrar("La aberración se desploma entre espasmos, y su carne cosida se abre como un saco podrido.")
        narrar("El enano deforme se queda inmóvil un segundo... y luego rompe a llorar con una rabia infantil y enferma.")
        dialogo("'¡NO! ¡NO! ¡ERA PERFECTA! ¡ME LA HAS ROTO!'")
        narrar("Con los ojos enrojecidos y la cara empapada, se abalanza sobre ti agitando su varilla de hierro.")
        narrar("Lo esquivas sin esfuerzo.")
        narrar("De un solo golpe seco lo rajas, y al segundo queda inmóvil en el suelo de piedra.")
        narrar("El llanto se apaga, y la sala queda en silencio salvo por tu respiración.")
        return {}

    elif nombre == "Ka-Banda, Demonio Sombrio":
        narrar("El demonio cae de rodillas, pero no se desploma como una criatura mortal.")
        narrar("Su carne se abre en grietas ardientes y la sala entera late al ritmo de su sangre.")
        narrar("Cada latido te golpea en el pecho como un martillo, y la Hoz de Sangre comienza a vibrar en tu mano.")
        susurros_aleatorios()
        dialogo("'La sangre no se pierde... se transforma.'")
        narrar("Ka-Banda alza la cabeza por última vez y una carcajada imposible retumba en todos los muros.")
        narrar("La Hoz se agrieta, absorbe la marea roja del demonio y se retuerce como si estuviera viva.")
        narrar("Cuando la tormenta de sangre se disipa, tu vieja arma ya no existe.")
        narrar("En su lugar sostienes una hoja negra, afilada como un juramento.")
        if "Hoz de Sangre" in estado["armas_jugador"]:
            del estado["armas_jugador"]["Hoz de Sangre"]
        estado["armas_jugador"]["Hoja de la Noche"] = armas_global["Hoja de la Noche"].copy()
        exito("La Hoz de Sangre se ha transmutado en la Hoja de la Noche. Obtienes: Hoja de la Noche.")
        return {}

    elif nombre == "Bel'akhor, Principe Demonio":
        narrar("Clavas el arma en el pecho del demonio y notas cómo el metal rasga carne imposible, dura como piedra viva.")
        narrar("Bel'akhor ruge, y sus alas de murciélago golpean el aire con tanta fuerza que te arrancan la respiración.")
        narrar("Le cortas una pierna a la altura de la rodilla, luego la otra, y aun así intenta arrastrarse hacia ti.")
        narrar("Con un grito que no parece humano, alzas tu arma y le abres el cuello de lado a lado.")
        narrar("La sangre negra sale a presión por la herida y te cubre la cara, el pecho y las manos.")
        narrar("El demonio se convulsiona, su hacha de bronce cae al suelo y su armadura se resquebraja como una cáscara vacía.")
        narrar("Antes de deshacerse, Bel'akhor te mira fijamente y notas que algo de él se aferra a tu mente.")
        narrar("Una oleada de poder te invade por dentro, brutal y adictiva, como fuego helado bajo la piel.")
        narrar("Sabes que has ganado fuerza... pero también sientes una presencia ajena respirando detrás de tus pensamientos.")
        narrar("Has vencido al Devorador de Almas, pero sigues atrapado en la mazmorra.")
        narrar("Debes encontrar el pasillo principal de la salida antes de enloquecer del todo.")
        personaje["_pw"] = max(personaje.get("_pw", 0), enemigo.get("_grant_pw", 1))
        return {}

    elif nombre == "Perturbado":
        final_perturbado = random.choice([1, 2, 3])
        if final_perturbado == 1:
            narrar("El perturbado cae de rodillas, todavía murmurando palabras sin dueño.")
            narrar("Su risa histérica se corta en seco y solo queda un gorgoteo húmedo.")
            narrar("Cuando por fin cae, su mirada perdida sigue clavada en un miedo que no es el tuyo.")
        elif final_perturbado == 2:
            narrar("El cuerpo se desploma como un saco roto, dejando un rastro de uñas y sangre en la piedra.")
            narrar("Sus dedos arañan el suelo unos segundos, buscando una salida que no existe.")
            narrar("Al final, el silencio le gana la pelea.")
        else:
            narrar("Te mira con una súplica tardía, como si por un instante hubiera recordado quién era.")
            narrar("Abre la boca para decir algo, pero solo expulsa sangre.")
            narrar("Cae boca abajo y no vuelve a moverse.")
        return {}

    elif nombre == "Mosca de Sangre":
        final_mosca = random.choice([1, 2, 3])
        if final_mosca == 1:
            narrar("La mosca se estrella contra el suelo y sus alas revientan en una lluvia viscosa.")
            narrar("Su zumbido cae de tono hasta convertirse en un temblor casi humano.")
            narrar("La quitina se parte en silencio y queda inmóvil.")
        elif final_mosca == 2:
            narrar("Sus bocas chasquean por última vez antes de quedarse abiertas para siempre.")
            narrar("El abdomen hinchado se desinfla lentamente, derramando sangre oscura.")
            narrar("El hedor agrio te obliga a cubrirte la cara.")
        else:
            narrar("La criatura gira sobre sí misma, desorientada y rota.")
            narrar("Un golpe final le atraviesa el tórax y la deja clavada contra la piedra.")
            narrar("El zumbido se apaga de golpe.")
        personaje["moscas"] += 2
        if personaje["moscas"] >= 3:
            narrar("Has reunido suficientes quitinas duras de Mosca de Sangre para cubrirte con ellas.")
            personaje["moscas"] -= 3
            aplicar_evento({"armadura": 1}, personaje)
        return {}

    elif nombre == "Larvas de Sangre":
        final_larvas = random.choice([1, 2, 3])
        if final_larvas == 1:
            narrar("Las larvas se retuercen unas sobre otras, clavándose entre sí en una agonía ciega.")
            narrar("Una tras otra revientan bajo tus golpes, salpicando un líquido negro y espeso.")
            narrar("El montón palpitante se inmoviliza por fin.")
        elif final_larvas == 2:
            narrar("Los chillidos húmedos del nido se apagan hasta quedar en un burbujeo moribundo.")
            narrar("Las probóscides tiemblan un instante antes de quebrarse.")
            narrar("La masa de carne queda hecha jirones sobre el suelo.")
        else:
            narrar("Pisoteas los últimos cuerpos blandos hasta que dejan de reaccionar.")
            narrar("La sangre espesa te llega a las botas y el asco te sube a la garganta.")
            narrar("Cuando miras de nuevo, no queda ninguna viva.")
        personaje["moscas"] += 1
        if personaje["moscas"] >= 3:
            narrar("Has reunido suficientes quitinas de Larvas de Sangre para cubrirte con ellas.")
            personaje["moscas"] -= 3
            aplicar_evento({"armadura": 1}, personaje)
        return {}

    elif nombre == "Maniaco Mutilado":
        final_maniaco = random.choice([1, 2, 3])
        if final_maniaco == 1:
            narrar("El maníaco cae a trompicones, golpeando la piedra con un sonido hueco y final.")
            narrar("Sus dientes siguen castañeteando unos segundos, como si aún quisiera morderte.")
            narrar("Un último espasmo recorre su cuerpo y todo termina.")
        elif final_maniaco == 2:
            narrar("Se arrastra un palmo más, dejando un rastro oscuro y desigual.")
            narrar("Levanta la cabeza para lanzarse otra vez, pero el cuerpo ya no le responde.")
            narrar("Se desploma de lado y queda inmóvil.")
        else:
            narrar("Sus ojos enfermos se apagan poco a poco, sin comprender que ya perdió.")
            narrar("El cuerpo se pliega sobre sí mismo, vencido por su propio dolor.")
            narrar("La sala queda en calma, salvo tu respiración.")

        tiene_brazo = random.choice([1, 2])
        if tiene_brazo == 1 and personaje["brazos"] == 0:
            narrar("Cuando el cuerpo deja de moverse, algo en el techo emite un chasquido húmedo.")
            narrar("Una figura se descuelga del arco de piedra sin hacer el menor ruido, tocando el suelo con más de dos pies.")
            narrar("Es pequeña, deforme, con la columna torcida en un ángulo que no debería permitir el movimiento.")
            narrar("Sus ojos, demasiado grandes para su cara, se clavan en el brazo cercenado del maníaco con una fijación perturbadora.")
            dialogo("'Ohhh... este todavía conservaba uno...'")
            narrar("Levanta la vista hacia ti con una sonrisa entre costuras y cicatrices de su cara contrahecha.")
            dialogo("'¿Lo has notado ya? Algunos de estos desgraciados aún tienen brazos. No muchos brazos, ni muy 'brazo', pero los hay!'")
            narrar("Hace algo parecido a una asquerosa risa ahogada. Ladea la cabeza y te mira cuando ve que no te ries.")
            dialogo("'Bueno, yo no puedo quitárselos. No estaría bien, me parece a mí. Pero tú ya los matas de todas formas...'")
            dialogo("'¿Los querrías para algo? ¿No? Pues dámelos a mí. Te compensaré, te lo juro por lo poco que me queda.'")
            narrar("Vuelve a exhibir esa sonrisa torcida, como si estuviera haciendo un trato contigo.")
            preguntar("¿Aceptas el trato con el desconocido? s/n")
            resp = leer_input("> ", personaje)
            # [SECRETO 5] Hablar con el hombrecillo (siempre activo)
            if resp == "hablar":
                narrar("Abres la boca con una pregunta que no completas, pero la criatura escucha lo que no dijiste.")
                narrar("Se inclina más cerca, su cuello doblándose en un ángulo imposible.")
                dialogo("'¿Quieres saber qué soy?'")
                narrar("La voz que sale de él no es suya. Es múltiple, resonante, como si hablaran a través de él.")
                dialogo("'Soy lo que los dioses dejaron olvidado. Lo que los dioses no se atrevieron a destruir.'")
                dialogo("'Soy el que cose lo roto. El que acompaña a los que la piedra ha llamado.'")
                narrar("Por un instante, sus ojos brillan con una luz que no es natural.")
                dialogo("'Y tú... tú también escuchas cuando la piedra habla, ¿verdad?'")
                narrar("La pregunta cuelga en el aire como si fuera un hecho. Como si supiera la respuesta antes de que hables.")
                preguntar("¿Aceptas el trato con el desconocido? s/n")
                resp = leer_input("> ", personaje)
            if resp in ["s", "si"]:
                narrar("La criatura se queda quieta cuando asientes. Tan quieta que por un instante parece muerta.")
                narrar("Luego su cuello se inclina hacia un lado con un crujido blando, y sus labios se abren en una sonrisa demasiado amplia, como un enorme tajo.")
                dialogo("'¿Sí…?¿De verdad los traerás?'")
                dialogo("'No muchos… no todos… solo los que ya no estén siendo usados…'")
                narrar("Se acerca dando pequeños pasos laterales, como si temiera que fueras a cambiar de opinión.")
                narrar("Tiene los hombros cubiertos de costuras antiguas y grapas oxidadas. Algunas se han abierto y muestran una carne de tono desigual, remendada con paciencia obsesiva.")
                dialogo("'Aquí abajo nadie quiere los brazos cuando dejan de obedecer. Los arrancan. Los pisan. Los olvidan.'")
                dialogo("'Pero yo puedo arreglarlos.' Te cuenta mientras revolotea por el cadaver del mutilado.")
                narrar("Se lleva la mano al pecho. La piel allí no coincide con la de su cuello.")
                dialogo("'Él corta para mejorar.'")
                dialogo("'Yo coso para acompañar.' Baja la voz, de manera casi solemne.")
                dialogo("'No me gusta estar solo cuando la piedra empieza a respirar y decir cosas.'")
                narrar("Y por primera vez entiendes que no está hablando solo de sí mismo.")
                narrar("La criatura abre la boca más de lo que debería y deja escapar un gorjeo de satisfacción.")
                dialogo("'¡Sabía que eras listo! No te arrepentirás. Yo... noto estas cosas. Sabré cuándo tengas brazos para mí.'")
                narrar("Recoge el brazo con una delicadeza que resulta más perturbadora que su andar animalizado.")
                narrar("Se pierde entre las sombras del techo antes de que puedas preguntarle nada.")
                personaje["brazos"] += 1
            elif resp in ["n", "no"]:
                narrar("Cuando le dices que no, no reacciona de inmediato.")
                narrar("Parpadea lentamente.")
                narrar("Luego su rostro se afloja, como si algo dentro de él hubiese perdido tensión.")
                dialogo("'Ah… claro.'")
                dialogo("'Claro que no.'")
                narrar("Se rasca el antebrazo. Ves como se hace un corte y se rompen sus uñas.")
                dialogo("'Nadie quiere cargar con lo que sobra.'")
                dialogo("'Es más fácil dejarlo pudrirse en las esquinas.'")
                narrar("Se acerca, inclinando el torso hasta casi tocarte con la frente. Por reflejo echas la mano a tu arma...")
                dialogo("'Él decía lo mismo... Que cada corte era necesario.'")
                dialogo("'Que los restos no importaban.'")
                narrar("Su voz cambia, se vuelve más grave.")
                dialogo("'Siempre despreciando lo que no sirve...'")
                narrar("Se gira taciturno, y se aparta mascullando.")
                dialogo("'No te preocupes, la piedra siempre recoge lo que se deja atrás.'")
                dialogo("'No pasa nada. Ya los conseguiré. De un modo... u otro.'")
                narrar("Vuelve al techo con la misma fluidez inquietante con que bajó. El chasquido se aleja.")
                narrar("No sabes por qué, pero tienes la sensación de haber cometido un error.")
                personaje["rencor"] = True
                personaje["brazos"] += 1
            else:
                alerta("Respuesta no válida.")
        elif tiene_brazo == 2:
            narrar("Revisas el cuerpo por costumbre. No hay nada que merezca la pena.")
        elif tiene_brazo == 1:
            narrar("Al caer, notas que el maníaco aún conserva algo parecido a un brazo.")
            personaje["brazos"] += 1
            if personaje["rencor"]:
                narrar("Lo pisas con rabia hasta que deja de parecerse a nada reconocible.")
                narrar("Que la criatura no encuentre lo que busca.")
                if random.random() < 0.5:
                    if not personaje["bolsa_acecho"]:
                        personaje["bolsa_acecho"] = [1, 2, 3]
                    frase_acecho = random.choice(personaje["bolsa_acecho"])
                    personaje["bolsa_acecho"].remove(frase_acecho)
                    if frase_acecho == 1:
                        narrar("Desde algún punto del techo llega un chasquido único, breve.")
                        narrar("Luego nada. Pero la sensación de que algo contaba persiste más de lo que debería.")
                    elif frase_acecho == 2:
                        narrar("Entre los restos, uno de los dedos sigue moviéndose durante unos segundos.")
                        narrar("No es un espasmo. Es demasiado lento para ser un espasmo.")
                        narrar("Luego se detiene, de golpe, como si algo hubiera cortado el hilo.")
                    elif frase_acecho == 3:
                        narrar("Sientes los ojos antes de verlos: dos puntos fijos en la oscuridad del arco de entrada.")
                        narrar("Cuando levantas la vista, ya no hay nada.")
                        narrar("Solo el olor leve a hilo viejo y carne fría.")
            else:
                narrar("Lo separas sin demora y lo guardas. La criatura sabrá que lo tienes.")

        # Hitos de gema: 3 y 6 brazos (solo si no hay rencor y no se han reclamado ya)
        if personaje["brazos"] in [3, 6] and not personaje["rencor"] and personaje["brazos"] not in personaje["hitos_brazos_reclamados"]:
            narrar("Antes de que puedas guardarlo, un chasquido familiar resuena por encima de tu cabeza.")
            narrar("La criatura ya está allí, colgada del techo boca abajo, con los ojos fijos en lo que llevas.")
            dialogo("'Yaaaa lo noto... ya lo noto desde aquí.'")
            narrar("Se deja caer al suelo con un golpe sordo y recoge los brazos con manos temblorosas de anticipación.")
            if personaje["brazos"] == 3:
                narrar("Los tiene ordenados con un cuidado reverencial. Algunos aún conservan anillos, cicatrices de batalla, marcas de hierro candente.")
                narrar("Los acaricia como si fueran reliquias sagradas.")
                dialogo("'Mira este… todavía tiembla cuando lo sujeto.'")
                dialogo("'Eso significa que no se ha ido del todo.'")
                dialogo("'La mazmorra no se queda todo. Solo lo que grita más fuerte.'")
                narrar("Ha comenzado a coser un torso incompleto. Tres brazos distintos cuelgan de él, cada uno de diferente tamaño y color.")
                narrar("Las manos se contraen en espasmos involuntarios, como si recordaran gestos que el cuerpo ya no puede realizar.")
                dialogo("'¿Sabes lo que ocurre cuando reúnes suficientes manos?'")
                dialogo("'Empiezan a recordar cosas entre ellas.'")
                dialogo("'No recuerdos suyos… recuerdos de la piedra.'")
                narrar("Te mira con intensidad súbita.")
                dialogo("'Hay algo debajo. Más abajo que las puertas cerradas.'")
                dialogo("'Algo que no necesita ojos… pero agradece las manos.'")
                narrar("Sus dedos aprietan el hilo con más fuerza de la necesaria.")
                dialogo("'Él cree que está creando soldados.'")
                dialogo("'Pero solo está haciendo piezas.'")
                narrar("Sonríe.")
                dialogo("'Yo hago compañía.'")
                narrar("Vuelve a la realidad de golpe, como si se hubiese olvidado de que estás ahí.")
            elif personaje["brazos"] == 6:
                narrar("Está distinto. Más erguido. Más excitado. Su voz se superpone a sí misma por momentos, como si dos pensamientos lucharan por salir primero.")
                narrar("Detrás de él, algo cubierto con telas respira de forma irregular.")
                dialogo("'Ya casi pueden sostenerse…'")
                dialogo("'Ya casi pueden abrazar…'")
                dialogo("'Ya casi pueden sujetar lo que se mueve cuando nadie mira.'")
                narrar("Se aproxima demasiado a ti.")
                dialogo("'¿La has sentido?'")
                dialogo("'Esa presión cuando estás solo en un pasillo largo.'")
                dialogo("'Esa certeza de que alguien calcula cuánto vales.'")
                narrar("Se ríe en un susurro.")
                dialogo("'No es el amo.'")
                dialogo("'Él solo escucha lo que le conviene.'")
                dialogo("'Lo otro… lo otro escucha todo.'")
                narrar("Se vuelve hacia su creación.")
                dialogo("'Cuando esté completo, podrá tocar esa oscuridad sin romperse.'")
                dialogo("'Podrá ofrecerle algo que no sea miedo.'")
                narrar("Te observa otra vez.")
                dialogo("'Y tú ayudaste.'")
                dialogo("'Tú sí entiendes que los brazos sirven para algo más que empuñar armas.'")
                narrar("Se sacude, como saliendo de un estado. Te mira de nuevo con esa sonrisa de costuras.")
            dialogo("'Muchas gracias. Toma, esto es para ti. No sé qué hace exactamente, pero te irá bien.'")
            narrar("Te lanza algo oscuro y facetado que gira en el aire antes de que lo atrapes.")
            narrar("La gema es fría. Fría de verdad, no como la piedra. Fría como si tuviera temperatura propia, más baja que la tuya.")
            personaje["hitos_brazos_reclamados"].append(personaje["brazos"])
            gema = random.random()
            if gema > 0.5:
                narrar("Antes de que puedas examinarla, algo dentro de ti te dice que la rompas. No es un pensamiento, es más urgente que eso.")
                narrar("La estrellas contra tu esternón. El dolor es blanco y corto. Los fragmentos no caen: se absorben.")
                narrar("Sientes cada esquirla disolverse en algo que corre más rápido que la sangre.")
                narrar("Cuando el frío desaparece, te mueves diferente. Más ligero. Más preciso.")
                aplicar_evento({"destreza": 1}, personaje)
            else:
                narrar("Antes de que puedas examinarla, algo dentro de ti te dice que la rompas. No es un pensamiento, es más urgente que eso.")
                narrar("La estrellas contra tu esternón. El dolor es blanco y corto. Los fragmentos no caen: se absorben.")
                narrar("Algo se asienta en tus músculos, más profundo que el cansancio. Como una tensión nueva que no duele.")
                narrar("Cuando el frío desaparece, aprietas el puño. Diferente. Más.")
                aplicar_evento({"fuerza": 1}, personaje)
            narrar("Cuando levantas la vista, la criatura ya no está. Solo el eco húmedo de algo que se aleja por el techo.")

        # Hito 10: entrega del arma o combate por rencor
        if personaje["brazos"] >= 10 and not personaje["evento_brazos_final_completado"]:
            personaje["evento_brazos_final_completado"] = True
            if personaje["rencor"]:
                narrar("No lo ves llegar.")
                narrar("Pero el sonido es inconfundible: varias manos apoyándose en las paredes al mismo tiempo, varios dedos tensándose contra la piedra.")
                narrar("Su voz llega desde distintos puntos del corredor, como si no supiera ya dónde empieza su cuerpo.")
                dialogo("'Casi caminamos…'")
                dialogo("'Casi sostenemos…'")
                dialogo("'Casi tocamos lo que respira abajo…'")
                narrar("Una risa quebrada resuena entre las paredes.")
                dialogo("'No necesitábamos tu ayuda.'")
                dialogo("'Solo necesitábamos lo que dejabas caer.'")
                narrar("Silencio. Luego, más cerca.")
                dialogo("'Ven.'")
                dialogo("'Ven a conocerlos.'")
                narrar("Algo demasiado grande, con demasiadas articulaciones, empieza a moverse hacia ti.")
                alerta("El techo explota en un chillido que hace vibrar la piedra. La criatura cae frente a ti y esta vez su expresión no tiene nada de amistosa.")
                narrar("Te señala con algo que le crece de la muñeca, retorcido, pulsante, hecho de piezas que no deberían encajar.")
                dialogo("'Te dije que lo conseguiria de un modo u otro.'")
                narrar("Lo que suelta no parece tanto un ataque como una liberación.")
                combate(personaje, crear_mano_demoniaca())
            else:
                narrar("El chasquido del techo llega antes de que lo veas. Ya lo reconoces.")
                narrar("La criatura desciende lentamente, sujetando algo con las dos manos como si fuera frágil.")
                narrar("No lo es. Lo que carga está hecho de articulaciones ajenas, tendones trenzados y algo que todavía late en el centro.")
                narrar("Lo deposita en el suelo frente a ti con una delicadeza absurda dada su forma.")
                dialogo("'Diez. Ya son diez. Llevo mucho tiempo haciendo esto y nunca pensé que encontraría a alguien tan... colaborador.'")
                narrar("La criatura se inclina hacia ti más de lo que su columna debería permitir.")
                dialogo("'Úsalo. Te has ganado un nuevo amigo.'")
                aplicar_evento({"armas": {"man": {}}}, personaje)
                narrar("Cuando levantas la vista, ya ha desaparecido. El chasquido del techo se pierde pasillo arriba.")
                narrar("Solo queda el peso nuevo en tus manos y la sensación de que el trato no ha terminado del todo.")

        # Hito 13: segundo encuentro — con o sin rencor, la criatura vuelve con otra creación
        if personaje["brazos"] >= 13 and not personaje["evento_brazos_segundo_completado"]:
            personaje["evento_brazos_segundo_completado"] = True
            if personaje["rencor"]:
                narrar("Oyes el chasquido mucho antes de verla. Y esta vez no para.")
                alerta("La criatura lleva demasiado tiempo esperando esto.")
                narrar("Cuando cae frente a ti, su monstruo de carne ya está extendido, ya reconoce tu olor.")
                dialogo("'No te guardo rencor. Pero mentí.'")
                combate(personaje, crear_mano_demoniaca())
            else:
                narrar("El chasquido del techo. La silueta que se descuelga.")
                narrar("Ya no te sobresaltas cuando aparece.")
                narrar("Carga algo nuevo, distinto al anterior, construido con partes que no reconoces como humanas.")
                dialogo("'Trece es mi número favorito. Siempre lo ha sido, aunque no recuerdo por qué.'")
                narrar("Te lanza la creación sin ceremonia. Pero cuando la agarras, sientes que hay algo dentro que responde.")
                dialogo("'Cuídate. Este sitio no te querrá mucho más tiempo.'")
                narrar("Se pierde en el techo antes de que puedas preguntar qué significa eso.")
                aplicar_evento({"armas": {"man": {}}}, personaje)

        return {}

    elif nombre == "Rabioso":
        final_rabioso = random.choice([1, 2, 3])
        if final_rabioso == 1:
            narrar("El rabioso se revuelve en el suelo, pateando con furia ciega hasta que su cuerpo se rinde.")
            narrar("La espuma sangrienta de su boca se vuelve oscura y espesa.")
            narrar("Su último alarido se rompe en un susurro seco.")
        elif final_rabioso == 2:
            narrar("Golpea la piedra una vez más con la frente y queda inmóvil en un charco carmesí.")
            narrar("Sus dedos arañan el suelo con una fuerza que ya no tiene destino.")
            narrar("El fanatismo abandona sus ojos de golpe.")
        else:
            narrar("Cae de espaldas, escupiendo sangre y dientes entre gruñidos rotos.")
            narrar("Intenta incorporarse con un último impulso de odio.")
            narrar("No lo consigue. La furia lo abandona para siempre.")

        if "Hoz de Sangre" in estado["armas_jugador"]:
            personaje["sangre"] += 1
            narrar("La Hoz de Sangre palpita y absorbe la esencia de la criatura.")
            narrar("Notas cómo el metal late, se expande y se alimenta de su furia.")
            if personaje["sangre"] >= 4:
                narrar("De pronto, la sangre del rabioso se arremolina y estalla contra las paredes.")
                narrar("Una presencia demoníaca emerge de la masacre.")
                combate(personaje, crear_demonio_sombrio())
        else:
            narrar("A pesar de haberlo herido gravemente, el Rabioso sigue pataleando y luchando en el suelo, en un charco de su propia sangre. No te explicas que lo impulsa así...")
        return {}

    elif nombre == "Sombra tenebrosa":
        final_sombra = random.choice([1, 2, 3])
        if final_sombra == 1:
            narrar("La sombra se deshilacha en jirones negros que se disuelven como humo mojado.")
            narrar("Sus filos pierden brillo y caen al suelo convertidos en polvo oscuro.")
            narrar("Solo queda un frío punzante en la piel.")
        elif final_sombra == 2:
            narrar("Una risita lejana intenta nacer, pero se rompe en un susurro ahogado.")
            narrar("La figura tiembla, se abre por la mitad y desaparece dentro de su propia oscuridad.")
            narrar("Durante un segundo todo queda completamente en silencio.")
        else:
            narrar("La sombra retrocede un paso, como si dudara por primera vez.")
            narrar("Tu golpe la atraviesa y la forma negra implosiona en polvo helado.")
            narrar("La temperatura sube de golpe, como si nada hubiera pasado.")

        if personaje["sombra"] == 0:
            narrar("Al destripar el último jirón de sombra, los fragmentos que quedan se te adhieren al cuerpo.")
            narrar("Notas un frío que quema donde te rozan las sombras, pero es revitalizador, a su manera...")
            preguntar("¿Abrazas las sombras? (s/n)")
            resp = leer_input("> ", personaje)
            while resp not in ["s", "si", "n", "no"]:
                alerta("Respuesta no válida.")
                resp = leer_input("> ", personaje)
            if resp in ["s", "si"]:
                susurros_aleatorios()
                narrar("Dejas que te envuelvan, y sientes como si te sumergieras en un lago de sangre helada.")
                narrar("Sales del trance renovado, pero sientes que algo te ha marcado por dentro.")
                personaje["sombra"] += 1
            else:
                narrar("Sientes que no tienes nada que hacer con las sombras, así que decides evitarlas.")
                narrar("Te sacudes las más cercanas y echas a correr dejándolas atrás.")
                susurros_aleatorios()
        elif personaje["sombra"] >= 1:
            susurros_aleatorios()
            narrar("Al destripar el último jirón de sombra, los fragmentos se te adhieren al cuerpo de nuevo.")
            narrar("Notas el frío conocido. Cada vez es más intenso.")
            personaje["sombra"] += 1
            if personaje["sombra"] >= 4:
                narrar("Las sombras ya no huyen de ti, ni tú de ellas. De hecho, te reconocen.")
                susurros_aleatorios()
                alerta("La risa se convierte en un alarido y la forma sombría sangra oscuridad.")
                susurros_aleatorios()
                alerta("Las sombras se abalanzan sobre ti, te abrazan, y tú dejas que te lleven...")
                susurros_aleatorios()
                combate(personaje, crear_sombra_sangrienta())
        return {}

    return {}

# ================== VISTA (TKINTER) ==================
# La Vista no conoce la logica del juego.
# Solo sabe leer cola_mensajes y renderizar cada tipo de mensaje.
# Toda la presentacion visual vive aqui: colores, fuentes, layout.

# ════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN VISUAL CENTRALIZADA
# ════════════════════════════════════════════════════════════════════
# Las siguientes variables ahora viven en módulos separados:
# - COLORES, RUTAS_IMAGENES_PANELES: en ui_config.py
# - imagen_manager: en ui_imagen_manager.py (carga PNG con caché)
# - estructura_ui: en ui_estructura.py (crea paneles con Canvas + widgets)
#
# Este modelo modular permite:
# 1. Cambiar temas de color desde ui_config.py sin tocar el código
# 2. Agregar nuevas imágenes sin modificar la lógica
# 3. Mejorar el renderizado sin impactar la configuración
# ════════════════════════════════════════════════════════════════════

# Variables de compatibilidad para código legacy
_IMG_BTN = {}  # Diccionario de imágenes de botones (cargadas dinámicamente)
# Rutas de bordes eliminadas: sistema legacy nunca implementado
# Se usaba carga de PNG para bordes decorativos (deprecado)


class Vista:
    """
    Ventana principal del juego. Layout asimetrico:

        +---------------------------+---------------+
        |                           |               |
        |   TEXTO NARRATIVO         |    IMAGEN     |
        |      (~72% x ~63%)        |  (~28% x ~63%)|
        |                           |               |
        +---------------------------+---------------+
        |                           |  STATS STRIP  |
        |   PARSER (input)          +---------------+
        |      (~72% x ~37%)        |    BOTONES    |
        |                           |  (~28% x ~37%)|
        +---------------------------+---------------+

    Los porcentajes se ajustan con las constantes de clase.
    Todos los paneles tienen reborde decorativo.
    Los PNG de reborde se cargan con set_border_image() cuando esten listos.
    
    ══════════════════════════════════════════════════════════════════
    📌 ÁREA DE BOTONES - AJUSTE DE DIMENSIONES
    El área se controla mediante BOTONES_AREA_HEIGHT (píxeles fijos).
    Ancho de botones: BTN_W_ARMA, BTN_W_STANCE, BTN_W_ACCION
    
    ══════════════════════════════════════════════════════════════════
    """

    # --- Proporciones del layout (faciles de ajustar) ---
    PESO_COL_TEXTO   = 72
    PESO_COL_PANEL   = 28
    PESO_FILA_MAIN   = 70
    PESO_FILA_INPUT  = 30

    # --- Configuracion del HUD de stats ---
    ALTO_STATS  = 30        # px de altura de la franja de stats (25% más: 55 * 1.25)
    VIDA_LLENA  = "\u2665"  # simbolo corazon lleno
    VIDA_VACIA  = "\u25cb"  # simbolo corazon vacio

    # --- Configuracion de botones ---
    BTN_FONT       = ("Consolas", 10)
    BTN_PADX       = 10
    BTN_PADY       = 5
    BOTONES_AREA_HEIGHT = 340  # Altura FIJA del área de botones (px). Ajusta aquí, no cambia el panel.

    # --- Velocidad typewriter (ms por letra) ---
    VELOCIDAD_TYPEWRITER = {
        "narrar":     0,
        "dialogo":    0,   # mas lento: mas dramatico
        "susurros":   0,   # muy lento: inquietante
        "alerta":     0,   # instantaneo: urgencia
        "exito":      0,
        "sistema":    0,
        "preguntar":  0,
    }

    def __init__(self, root):
        self.root = root
        self.root.title("TL;DR:DC")
        self.root.configure(bg=COLORES["fondo"])
        self.root.attributes("-fullscreen", True)

        # Callback que el Controlador conectara: recibe string del parser
        self.on_input = None

        # Historial del parser (flecha arriba/abajo = comando anterior/siguiente)
        self._historial_parser = []
        self._historial_idx    = -1

        # Referencia a imagen cargada (evita garbage collection de PhotoImage)
        self._imagen_tk = None

        # Flag: True solo cuando el juego espera input del jugador.
        # La Entry queda bloqueada en cualquier otro momento.
        self._input_activo = False

        # Flag: True mientras un typewriter esta escribiendo.
        # El polling espera a que termine antes de sacar el siguiente mensaje.
        self._ocupado = False
        
        # Flag: True cuando estamos EN combate. Botones solo activos durante combate.
        self._en_combate = False

        self._construir_layout()
        self._configurar_tags()
        self._cargar_imgs_btns()
        # _cargar_bordes_imagen() eliminada: sistema legacy de bordes PNG nunca usado
        self._iniciar_polling()

    # ------------------------------------------------------------------
    # LAYOUT PRINCIPAL
    # ------------------------------------------------------------------

    def _construir_layout(self):
        """
        Grid raiz de 2 columnas x 2 filas.
        Los pesos de columnconfigure/rowconfigure son los que controlan
        las proporciones: cambiar PESO_COL_TEXTO etc. es suficiente.
        """
        self.root.columnconfigure(0, weight=self.PESO_COL_TEXTO)
        self.root.columnconfigure(1, weight=self.PESO_COL_PANEL)
        self.root.rowconfigure(0, weight=self.PESO_FILA_MAIN)
        self.root.rowconfigure(1, weight=self.PESO_FILA_INPUT)

        self._construir_panel_texto()
        self._construir_panel_parser()
        self._construir_panel_imagen()
        self._construir_panel_stats_y_botones()

    def _reborde(self, parent, ruta_fondo=None, **grid_kwargs):
        """
        Crea un panel con reborde usando estructura_ui.crear_panel_con_fondo().
        
        Args:
            parent: tk widget padre
            ruta_fondo: str - Ruta a imagen PNG de fondo (opcional)
            **grid_kwargs: grid parameters (row, column, padx, pady, etc)
        
        Devuelve el frame interior (content frame).
        El frame exterior (outer) se accede mediante inner._reborde_outer.
        """
        # Usar estructura_ui para crear el panel con 3 capas (borde > canvas > frame)
        frame_contenido, canvas_fondo, outer = estructura_ui.crear_panel_con_fondo(
            parent,
            ruta_fondo=ruta_fondo,  # Cargar imagen si se proporciona
            color_borde=COLORES["borde"],
            color_fondo=COLORES["fondo_panel"],
            **grid_kwargs
        )
        
        # Mantener compatibilidad: guardar referencia al frame exterior
        frame_contenido._reborde_outer = outer
        frame_contenido._canvas_fondo_interno = canvas_fondo
        
        return frame_contenido

    def _construir_panel_texto(self):
        panel = self._reborde(self.root, ruta_fondo=RUTAS_IMAGENES_PANELES["fondo_texto"], 
                             row=0, column=0, padx=(6, 3), pady=(6, 3))
        self._borde_texto = panel._reborde_outer  # Guardar referencia al Frame exterior
        panel.rowconfigure(0, weight=1)
        panel.columnconfigure(0, weight=1)

        self.texto = tk.Text(
            panel,
            bg=COLORES["fondo_panel"], fg=COLORES["narrar"],
            font=("Consolas", 11),
            wrap="word",
            state="disabled",
            relief="flat",
            padx=12, pady=8,
            cursor="arrow",
            spacing3=4,
            height=1,              # elimina el minimo natural; el grid controla el tamano
            yscrollcommand=lambda *a: None,
        )
        self.texto.grid(row=0, column=0, sticky="nsew")

    def _construir_panel_parser(self):
        """
        Panel inferior izquierdo: registro de historial (Text) + Entry de input.
        El registro muestra los comandos escritos y las respuestas del juego
        que sean ecos de accion (tag 'preguntar'). La Entry es donde se escribe.
        """
        panel = self._reborde(self.root, ruta_fondo=RUTAS_IMAGENES_PANELES["fondo_parser"],
                             row=1, column=0, padx=(6, 3), pady=(3, 6))
        self._borde_parser = panel._reborde_outer  # Guardar referencia al Frame exterior
        panel.rowconfigure(0, weight=1)   # registro ocupa el espacio sobrante
        panel.rowconfigure(1, weight=0)   # entry: altura fija
        panel.columnconfigure(0, weight=1)

        # --- Registro de historial ---
        self.parser_registro = tk.Text(
            panel,
            bg=COLORES["parser_bg"], fg=COLORES["parser_fg"],
            font=("Consolas", 10),
            wrap="word",
            state="disabled",
            relief="flat",
            padx=10, pady=6,
            cursor="arrow",
            spacing3=3,
            height=1,              # elimina el minimo natural; el grid controla el tamano
            yscrollcommand=lambda *a: None,
        )
        self.parser_registro.grid(row=0, column=0, sticky="nsew")
        # Tag para los comandos del jugador (en rojo claro, diferenciados)
        self.parser_registro.tag_configure(
            "cmd", foreground=COLORES["alerta"], font=("Consolas", 10, "bold")
        )
        self.parser_registro.tag_configure(
            "resp", foreground=COLORES["parser_fg"], font=("Consolas", 10)
        )

        # --- Separador visual (linea fina) ---
        tk.Frame(panel, bg=COLORES["borde"], height=1).grid(
            row=1, column=0, sticky="ew", pady=(0, 0)
        )

        # --- Frame de entrada con prompt > ---
        frame_entry = tk.Frame(panel, bg=COLORES["parser_bg"])
        frame_entry.grid(row=2, column=0, sticky="ew")
        frame_entry.columnconfigure(1, weight=1)

        tk.Label(
            frame_entry, text=">",
            bg=COLORES["parser_bg"], fg=COLORES["alerta"],
            font=("Consolas", 13, "bold"), padx=8, pady=6,
        ).grid(row=0, column=0)

        self.parser_entry = tk.Entry(
            frame_entry,
            bg=COLORES["parser_bg"], fg=COLORES["parser_fg"],
            disabledbackground=COLORES["parser_bg"],   # evita el blanco de Windows al bloquear
            disabledforeground=COLORES["separador"],   # texto tenue cuando esta bloqueado
            insertbackground=COLORES["parser_cursor"],
            font=("Consolas", 12),
            relief="flat", bd=0,
        )
        self.parser_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=4)
        self.parser_entry.configure(state="disabled")  # bloqueado hasta habilitar_input
        self.parser_entry.bind("<Return>", self._enviar_input)
        self.parser_entry.bind("<Up>",     self._historial_arriba)
        self.parser_entry.bind("<Down>",   self._historial_abajo)
        self.parser_entry.focus_set()

    def _construir_panel_imagen(self):
        panel = self._reborde(self.root, ruta_fondo=RUTAS_IMAGENES_PANELES["fondo_imagen"],
                             row=0, column=1, padx=(3, 6), pady=(6, 3))
        self._borde_imagen = panel._reborde_outer  # Guardar referencia al Frame exterior

        self.canvas_imagen = tk.Canvas(
            panel, bg=COLORES["fondo_panel"], highlightthickness=0,
        )
        self.canvas_imagen.pack(fill="both", expand=True)
        # Cada vez que el canvas cambia de tamaño (arranque, maximizar,
        # redimensionar ventana) recarga la imagen al tamaño exacto correcto.
        self.canvas_imagen.bind("<Configure>", lambda e: self._cargar_imagen())
        self._ruta_imagen_actual = None

    def _construir_panel_stats_y_botones(self):
        """Panel derecho inferior: franja stats arriba, botones FIJOS abajo.
        
        Layout SIMPLE:
        row 0: Stats strip (altura fija ALTO_STATS, weight=0)
        row 1: Botones (altura fija BOTONES_AREA_HEIGHT, weight=0) ← NO expande
        """
        panel = self._reborde(self.root, ruta_fondo=RUTAS_IMAGENES_PANELES["fondo_stats"],
                             row=1, column=1, padx=(3, 6), pady=(3, 6))
        self._borde_panel_derecho = panel._reborde_outer  # Guardar referencia al Frame exterior
        self._panel_derecho = panel  # Guardar referencia al panel interior (para fondo dinámico)
        
        panel.rowconfigure(0, weight=0)   # stats: fija
        panel.rowconfigure(1, weight=0, minsize=self.BOTONES_AREA_HEIGHT)  # botones: FIJA
        panel.columnconfigure(0, weight=1)

        self._construir_stats_strip(panel)
        self._construir_area_botones(panel)

    def _construir_stats_strip(self, parent):
        """
        Franja permanente con vida, armadura, fuerza y destreza.
        Se actualiza con actualizar_hud(). Nunca desaparece.
        Altura controlada por ALTO_STATS.
        """
        strip = tk.Frame(parent, bg=COLORES["fondo_panel"], height=self.ALTO_STATS)
        strip.grid(row=0, column=0, sticky="ew", padx=6, pady=(6, 2))
        strip.grid_propagate(False)   # respeta altura fija aunque esten vacios

        # Los labels se guardan en dict para actualizacion individual facil
        self._stats_labels = {}

        def _lbl(key, col, color=COLORES["stats_fg"]):
            lbl = tk.Label(
                strip, text="--",
                bg=COLORES["fondo_panel"], fg=color,
                font=("Consolas", 11),
            )
            lbl.grid(row=0, column=col, padx=8, pady=5, sticky="w")
            self._stats_labels[key] = lbl

        strip.columnconfigure(0, weight=2)   # vida (mas ancho, tiene corazones)
        strip.columnconfigure(1, weight=1)
        strip.columnconfigure(2, weight=1)
        strip.columnconfigure(3, weight=1)
        strip.columnconfigure(4, weight=0)   # boton X: ancho fijo

        _lbl("vida",      0, COLORES["stats_vida"])
        _lbl("armadura",  1, COLORES["stats_fg"])
        _lbl("fuerza",    2, COLORES["stats_fg"])
        _lbl("destreza",  3, COLORES["stats_fg"])

        btn_cerrar = tk.Label(
            strip, text="✕",
            bg=COLORES["fondo_panel"], fg="#5a3030",
            font=("Consolas", 11),
            cursor="hand2",
            padx=8, pady=3,
        )
        btn_cerrar.grid(row=0, column=4, sticky="ne", padx=(0, 4), pady=2)
        btn_cerrar.bind("<Button-1>", lambda e: self.root.destroy())
        btn_cerrar.bind("<Enter>",    lambda e: btn_cerrar.configure(fg="#cc4444"))
        btn_cerrar.bind("<Leave>",    lambda e: btn_cerrar.configure(fg="#5a3030"))

    def _construir_area_botones(self, parent):
        """
        Contenedor FIJO de botones que se auto-dimensionan responsivamente.
        Los botones se crean UNA VEZ y se auto-escalan al espacio disponible.
        Layout:
        row 0: Stances  (cols 1, 3)
        row 1: Armas    (cols 0, 2, 4)
        row 2: Acciones (cols 1, 3)
        
        Panel con altura FIJA (160px):
        - 3 filas distribuidas: ~53px c/u
        - Minsize: 50px (150px total < 160px disponibles)
        - weight=0 para no sobreexpandirse
        

        """
        # Crear Frame simple para elementos de botones
        self._area_botones = tk.Frame(
            parent, bg=COLORES["fondo_panel"], height=self.BOTONES_AREA_HEIGHT
        )
        
        # sticky="ew" = estira horizontalmente sin expandir verticalmente
        self._area_botones.grid(row=1, column=0, sticky="ew", padx=4, pady=(2, 4))
        self._area_botones.grid_propagate(False)  # Respetar altura fija
        
        # 5 columnas con weight=1 → equipartición horizontal
        for i in range(5):
            self._area_botones.columnconfigure(i, weight=1)
        
        # 3 filas con altura proporcional
        # Suma minsize: 50 + 55 + 50 = 155px < 160px (sobrante = 5px)
        # Fila 1 (armas) con weight=1 absorbe espacio sobrante → 60px final
        self._area_botones.rowconfigure(0, weight=0, minsize=80)   # Stances (compacto)
        self._area_botones.rowconfigure(1, weight=0, minsize=200)   # Armas (crece flexiblemente)
        self._area_botones.rowconfigure(2, weight=0, minsize=65)   # Acciones (compacto)
        
        self._botones_armas = {}
        self._botones_stances = {}
        self._botones_acciones = {}
        self._toggle_state = {}
        
        # --- FILA 0: STANCES (columnas 1, 3) ---
        cvs_bl = self._boton(
            self._area_botones, "", None,
            activo=False, row=0, col=1, forma="circulo", imagen="bloqueo"
        )
        self._botones_stances['bloquear'] = cvs_bl
        
        cvs_esq = self._boton(
            self._area_botones, "", None,
            activo=False, row=0, col=3, forma="circulo", imagen="esquiva"
        )
        self._botones_stances['esquivar'] = cvs_esq
        
        # Radio button stances (select one, deselect others)
        def _select_stance(cual):
            if not self._en_combate:
                return  # Ignorar clicks fuera de combate
            # ALTERNANCIA: igual que parser (evita doble procesamiento)
            if self._toggle_state.get('activa') == cual:
                self._toggle_state['activa'] = None
            else:
                self._toggle_state['activa'] = cual
            self._actualizar_stances_visual()
            # Notificar al juego SIN inyectar al parser (evita doble procesamiento)
            if self.on_input:
                self.on_input(cual)
        
        cvs_bl.bind("<Button-1>", lambda e: _select_stance("bl"))
        cvs_esq.bind("<Button-1>", lambda e: _select_stance("esq"))
        
        # --- FILA 1: 3 ARMAS (columnas 0, 2, 4) ---
        for slot_name, col in [('arma1', 0), ('arma2', 2), ('arma3', 4)]:
            cvs = self._boton(
                self._area_botones, "---", None,
                activo=False, row=1, col=col, forma="hexagono", imagen=None, imagen_fondo="fondo_armas"
            )
            self._botones_armas[slot_name] = cvs
        
        # --- FILA 2: ACCIONES (columnas 1, 3) ---
        cvs_pocion = self._boton(
            self._area_botones, "", lambda: self._enviar_comando("p"),
            activo=False, row=2, col=1, forma="circulo", imagen="0pociones"
        )
        self._botones_acciones['pocion'] = cvs_pocion
        
        cvs_huir = self._boton(
            self._area_botones, "Huir", lambda: self._enviar_comando("h"),
            activo=False, row=2, col=3, forma="circulo", imagen=None
        )
        self._botones_acciones['huir'] = cvs_huir
        
        # ═══ VALIDACION DE RENDERIZADO INICIAL (Opción D) ═══
        # Forzar cálculo de geometría y dibujo inicial de todos los Canvas
        # Previene botones vacíos al startup
        self._area_botones.update_idletasks()
        
        # Recopilar todos los Canvas y forzar redibujado inicial
        todos_los_canvas = list(self._botones_stances.values()) + \
                          list(self._botones_armas.values()) + \
                          list(self._botones_acciones.values())
        
        # CRITICAL: Ejecutar _dibujar() con root.after() para que el Canvas tenga geometría real
        def _forzar_redraw():
            for cvs in todos_los_canvas:
                if hasattr(cvs, '_dibujar'):
                    cvs._dibujar()
        
        self.root.after(10, _forzar_redraw)

    # ------------------------------------------------------------------
    # ACTUALIZACION DE STATS HUD
    # ------------------------------------------------------------------

    def _registrar_observadores_personaje(self):
        """Registra callbacks de reactividad para cambios en personaje_global.
        Se llama desde main() DESPUÉS de que personaje_global sea creado.
        Los callbacks se activan cuando personaje_global.activo = True.
        
        CRÍTICO: Todos los callbacks usan root.after() para ser thread-safe.
        El worker thread (que modifica personaje_global) no puede tocar widgets directamente.
        root.after() encola la actualización al main thread Tkinter.
        
        NOTA: Se ejecutan callbacks iniciales para sincronizar sprites al cargar partida.
        Los cambios en armas durante exploración se sincronizan directamente desde
        aplicar_evento() que inyecta el callback _callback_ui_armas.
        """
        # Observar cambios en stats - THREAD-SAFE con root.after()
        personaje_global.observe("vida", 
            lambda v: self.root.after(0, lambda: self.actualizar_hud(personaje_global)))
        personaje_global.observe("armadura", 
            lambda v: self.root.after(0, lambda: self.actualizar_hud(personaje_global)))
        personaje_global.observe("fuerza", 
            lambda v: self.root.after(0, lambda: self.actualizar_hud(personaje_global)))
        personaje_global.observe("destreza", 
            lambda v: self.root.after(0, lambda: self.actualizar_hud(personaje_global)))
        personaje_global.observe("vida_max", 
            lambda v: self.root.after(0, lambda: self.actualizar_hud(personaje_global)))
        
        # Observar cambios en pociones
        personaje_global.observe("pociones", 
            lambda v: self.root.after(0, lambda: self._on_pociones_cambio(v)))
        
        # Observar cambios en armas - THREAD-SAFE con root.after()
        # Esto se dispara cuando se asigna personaje["armas"] desde celda_inicial o exploración
        personaje_global.observe("armas", 
            lambda v: self.root.after(0, lambda: self._on_armas_cambio()))
        
        # ═══ SINCRONIZACIÓN INICIAL: Ejecutar callbacks con valores actuales ═══
        # Esto sincroniza los sprites con el estado actual al cargar partida guardada
        # Los cambios en armas durante exploración se sincronizan vía observer + callback inyectado
        self.actualizar_hud(personaje_global)
        self._on_pociones_cambio(personaje_global.get("pociones", 0))
        self._on_armas_cambio()

    def _on_pociones_cambio(self, num_pociones):
        """Callback reactivo: se ejecuta DESDE EL MAIN THREAD (via root.after).
        Actualiza el sprite del botón de pociones según la cantidad disponible.
        Muestra el sprite correspondiente a num_pociones (0-10).
        
        Nota: Este método ya está encolado en el main thread por root.after(),
        así que es safe modificar widgets aquí.
        """
        if "pocion" in self._botones_acciones:
            cvs = self._botones_acciones["pocion"]
            # Limitar a 0-10 (máximo disponible)
            num_pociones = min(max(num_pociones, 0), 10)
            # Cambiar la imagen dinámicamente según cantidad de pociones
            nombre_imagen = f"{num_pociones}pociones"
            cvs._btn_imagen = nombre_imagen
            # Marcar como activo si hay pociones disponibles
            cvs._btn_activo = (num_pociones > 0)
            # Forzar redibujado del canvas
            if hasattr(cvs, '_dibujar'):
                cvs._dibujar()
    
    def _on_armas_cambio(self):
        """Callback reactivo: se ejecuta DESDE EL MAIN THREAD (via root.after).
        Actualiza los botones de armas cuando el inventario cambia en exploración.
        IMPORTANTE: Solo muestra SPRITES, sin texto. El inventario se ve en la pantalla narrativa.
        """
        if personaje_global is None:
            return
        
        armas = personaje_global.get("armas", {})
        slots = (list(armas.keys()) + ["----"] * 3)[:3]
        
        for i, arma_nombre in enumerate(slots):
            slot_name = ['arma1', 'arma2', 'arma3'][i]
            if slot_name in self._botones_armas:
                cvs = self._botones_armas[slot_name]
                tiene = arma_nombre != "----"
                
                # Actualizar estado e imagen
                cvs._btn_texto = ""  # NO mostrar nombres en los botones
                cvs._btn_activo = tiene
                cvs._btn_forma = "hexagono"  # Mantener forma hexagonal siempre
                
                if tiene:
                    # Intentar asignar imagen del arma
                    # Primero intenta el nombre de display, luego el sprite name
                    if arma_nombre in _IMG_BTN:
                        cvs._btn_imagen = arma_nombre
                    else:
                        # Fallback: buscar en el mapeo inverso
                        sprite_name = _ARMAS_DISPLAY_A_SPRITE.get(arma_nombre)
                        if sprite_name and sprite_name in _IMG_BTN:
                            cvs._btn_imagen = sprite_name
                        else:
                            # Última opción: probar si existe como lowercase
                            lowercase_name = arma_nombre.lower()
                            if lowercase_name in _IMG_BTN:
                                cvs._btn_imagen = lowercase_name
                            else:
                                # No encontrada, dejar vacío
                                cvs._btn_imagen = None
                else:
                    cvs._btn_imagen = None
                
                # Forzar redibujado
                if hasattr(cvs, '_dibujar'):
                    cvs._dibujar()

    def actualizar_hud(self, d):
        """
        Actualiza los labels de la franja de stats.
        Acepta tanto el dict de hud_combate como el de stats.
        """
        vida     = d.get("vida", 0)
        vida_max = d.get("vida_max", 25)
        armadura = d.get("armadura", 0)
        fuerza   = d.get("fuerza", 0)
        destreza = d.get("destreza", 0)

        corazones  = self.VIDA_LLENA * vida + self.VIDA_VACIA * (vida_max - vida)
        vida_color = COLORES["alerta"] if vida / max(vida_max, 1) < 0.3 else COLORES["stats_vida"]

        self._stats_labels["vida"].configure(text=corazones, fg=vida_color)
        self._stats_labels["armadura"].configure(text=f"\u26e8 {armadura}")
        self._stats_labels["fuerza"].configure(text=f"F:{fuerza}")
        self._stats_labels["destreza"].configure(text=f"D:{destreza}")

    # ------------------------------------------------------------------
    # BOTONES CONTEXTUALES
    # Tres grupos intercambiables segun el estado del juego.
    # ------------------------------------------------------------------

    # _limpiar_botones() eliminada: botones ahora son estáticos, no dinámicos

    def _cargar_imgs_btns(self):
        """
        Intenta cargar los PNG de pixel art para los botones.
        Si un asset no existe simplemente no se carga y el botón
        muestra solo texto. Rutas relativas a assets/btns/.
        """
        import pathlib
        base = pathlib.Path(__file__).parent / "assets" / "btns"
        nombres = [
            "daga", "espada", "martillo", "porra", "maza", "lanza",
            "estoque", "cimitarra", "Mano de Dios", "Hoz de Sangre",
            "Hoja de la Noche", "Hacha Maldita",
            "bloquear", "esquivar", "huir",
            "izquierda", "derecha", "guardar",
        ]
        for nombre in nombres:
            ruta = base / f"{nombre}.png"
            img = imagen_manager.cargar_imagen(str(ruta))
            if img:
                _IMG_BTN[nombre] = img
        
        # Cargar sprites dinámicos de pociones (0-10)
        pociones_base = pathlib.Path(__file__).parent / "images" / "Botones" / "pociones"
        for i in range(11):
            nombre = f"{i}pociones"
            ruta = pociones_base / f"{nombre}.png"
            img = imagen_manager.cargar_imagen(str(ruta))
            if img:
                _IMG_BTN[nombre] = img
        
        # Cargar sprites de stances (bloqueo y esquiva)
        stances_base = pathlib.Path(__file__).parent / "images" / "Botones" / "stances"
        for nombre in ["bloqueo", "esquiva"]:
            ruta = stances_base / f"{nombre}.png"
            img = imagen_manager.cargar_imagen(str(ruta))
            if img:
                _IMG_BTN[nombre] = img
        
        # Cargar sprites de armas dinámicamente desde carpeta
        armas_base = pathlib.Path(__file__).parent / "images" / "Botones" / "armas"
        if armas_base.exists():
            for archivo_png in armas_base.glob("*.png"):
                nombre_sprite = archivo_png.stem
                img = imagen_manager.cargar_imagen(str(archivo_png))
                if img:
                    # Guardar bajo AMBOS nombres (sprite file y display name)
                    _IMG_BTN[nombre_sprite] = img
                    
                    for display_name, sprite_name in _ARMAS_DISPLAY_A_SPRITE.items():
                        if sprite_name == nombre_sprite:
                            _IMG_BTN[display_name] = img
                            break
        
        # Cargar imagen de fondo para botones de armas
        fondo_armas_path = pathlib.Path(__file__).parent / "images" / "Botones" / "fondo armas" / "FondoArmas.png"
        if fondo_armas_path.exists():
            img_fondo = imagen_manager.cargar_imagen(str(fondo_armas_path))
            if img_fondo:
                _IMG_BTN["fondo_armas"] = img_fondo
                print(f"[OK] FondoArmas.png cargado correctamente")
            else:
                print(f"[ERROR] No se pudo cargar FondoArmas.png desde {fondo_armas_path}")
        else:
            print(f"[ERROR] Archivo FondoArmas.png no encontrado en {fondo_armas_path}")
        
        # DEBUG: Mostrar resumen de carga
        armas_cargadas = [k for k in _IMG_BTN.keys() if any(
            nombre in k.lower() for nombre in 
            ["daga", "espada", "martillo", "porra", "maza", "lanza", 
             "estoque", "cimitarra", "mano", "hoz", "hoja", "hacha"]
        )]
        if armas_cargadas:
            print(f"[OK] Weapon sprites loaded: {sorted(armas_cargadas)}")

    # ELIMINADO: _cargar_bordes_imagen() y _aplicar_borde_imagen()
    # Sistema legacy de decoración PNG para bordes nunca fue implementado completamente.
    # Las variables _RUTA_BORDE_* siempre fueron None (sin asignar).

    def _boton(self, parent, texto, comando=None, activo=True,
               row=0, col=0, forma="rect", imagen=None, imagen_fondo=None):
        """
        Fabrica un botón Canvas RESPONSIVO que se auto-dimensiona al espacio.
        Se redibuja automáticamente al cambiar tamaño de ventana/grid.
        """
        # Establecer altura del Canvas según su fila (50, 60, 50 px)
        altura_por_fila = {0: 50, 1: 80, 2: 50}
        h = altura_por_fila.get(row, 50)
        
        cvs = tk.Canvas(
            parent, bg=COLORES["fondo_panel"], highlightthickness=0,
            cursor="hand2" if activo else "arrow", height=h
        )
        cvs.grid(row=row, column=col, padx=4, pady=3, sticky="nsew")

        # Almacenar estado en el canvas para redibujado dinámico
        cvs._btn_texto = texto
        cvs._btn_activo = activo
        cvs._btn_forma = forma
        cvs._btn_imagen = imagen
        cvs._btn_imagen_fondo = imagen_fondo
        cvs._btn_hover = False

        def _dibujar():
            w = cvs.winfo_width()
            h = cvs.winfo_height()
            if w < 5 or h < 5:
                return
            cvs.delete("all")
            
            # Determinar color de texto según estado activo
            fg = COLORES["boton_activo"] if cvs._btn_activo else COLORES["boton_inactivo"]
            
            # Cargar imágenes si existen
            bg_ref = _IMG_BTN.get(cvs._btn_imagen_fondo) if cvs._btn_imagen_fondo else None
            img_ref = _IMG_BTN.get(cvs._btn_imagen) if cvs._btn_imagen else None
            
            # Dibujar imagen de fondo si existe
            if bg_ref:
                cvs.create_image(w//2, h//2, image=bg_ref, anchor="center")
            
            # Dibujar imagen del arma si existe
            if img_ref:
                if cvs._btn_texto:
                    # Mostrar imagen encima y texto abajo
                    cvs.create_image(w//2, h//2-9, image=img_ref, anchor="center")
                    cvs.create_text(w//2, h-10, text=cvs._btn_texto, fill=fg, font=self.BTN_FONT, anchor="center")
                else:
                    # Centrar imagen completamente
                    cvs.create_image(w//2, h//2-3, image=img_ref, anchor="center")
            else:
                # Fallback: mostrar solo texto
                cvs.create_text(w//2, h//2, text=cvs._btn_texto, fill=fg, font=self.BTN_FONT, anchor="center")

        cvs._dibujar = _dibujar
        cvs.bind("<Configure>", lambda e: _dibujar())
        cvs.bind("<Enter>", lambda e: (setattr(cvs, '_btn_hover', True), _dibujar()))
        cvs.bind("<Leave>", lambda e: (setattr(cvs, '_btn_hover', False), _dibujar()))

        if activo and comando:
            cvs.bind("<Button-1>", lambda e: comando())

        return cvs
    
    def desactivar_botones_combate(self):
        """
        Desactiva TODOS los botones de combate cuando termina el combate.
        El HUD sigue actualizándose, pero los botones no son clickeables.
        Restaura los sprites de armas después de salir de la vista de combate.
        """
        self._en_combate = False
        
        # CRÍTICO: Restaurar sprites de armas después de salir del combate
        # En combate se mostró solo nombres (imagen=None), aquí hay que restaurar
        self._on_armas_cambio()
        
        # Forzar redibujado de todos los botones para que se vuelvan grises
        self._forzar_redraw_botones()
    
    def _redibujar_boton(self, cvs, texto, activo=True, forma="rect"):
        """
        Actualiza estado de un botón y lo redibuja responsivamente.
        SIN recrear el widget, solo cambia su contenido dinámicamente.
        """
        cvs._btn_texto = texto
        cvs._btn_activo = activo
        cvs._btn_forma = forma
        cvs.configure(cursor="hand2" if activo else "arrow")
        cvs._dibujar()
    
    def _forzar_redraw_botones(self):
        """
        Redibuja todos los botones de combate.
        Se usa cuando _en_combate cambia para actualizar colores/apariencia.
        """
        todos_los_botones = (list(self._botones_stances.values()) +
                            list(self._botones_armas.values()) +
                            list(self._botones_acciones.values()))
        for cvs in todos_los_botones:
            if hasattr(cvs, '_dibujar'):
                cvs._dibujar()
    
    def _actualizar_stances_visual(self):
        """
        Redibuja los botones de stance basado en estado interno (_toggle_state).
        Usada por toggle de stances.
        """
        activa = self._toggle_state.get('activa')
        
        bl_activo = (activa == 'bl')
        esq_activo = (activa == 'esq')
        
        self._redibujar_boton(
            self._botones_stances['bloquear'],
            "", bl_activo, "circulo",
        )
        self._redibujar_boton(
            self._botones_stances['esquivar'],
            "", esq_activo, "circulo",
        )
    
    def actualizar_botones_combate(self, armas, pociones, huida_bloqueada=False, pocion_usada_turno=False, stance=None):
        """
        REEMPLAZA a mostrar_botones_combate().
        Actualiza botones estáticos sin recrearlos.
        Se llama cada turno del combate para refrescar estado.
        
        ACTIVA automáticamente los botones de combate (los pone clickeables).
        """
        # Marcar que estamos EN combate (si no lo estábamos, forzar redraw)
        estaba_inactivo = not self._en_combate
        self._en_combate = True
        
        # SOLO inicializar _toggle_state la PRIMERA VEZ que entramos en combate
        # Luego, el usuario lo controla mediante clicks y parser
        if estaba_inactivo:
            self._toggle_state['activa'] = stance
        # NO sobrescribir en turnos posteriores
        
        # --- Actualizar ARMAS (fila 0) ---
        slots = (list(armas) + ["----"] * 3)[:3]
        for i, arma in enumerate(slots):
            slot_name = ['arma1', 'arma2', 'arma3'][i]
            cvs = self._botones_armas[slot_name]
            tiene = arma != "----"
            
            # En exploración se muestran SOLO sprites (sin texto)
            # En combate se muestran SPRITES (conservar imagen, sin texto)
            cvs._btn_texto = ""  # NO mostrar nombres/descripciones
            cvs._btn_activo = tiene
            cvs._btn_forma = "hexagono"  # Mantener forma hexagonal siempre
            
            # Mantener y asignar imagen del arma (no eliminar)
            if tiene:
                if arma in _IMG_BTN:
                    cvs._btn_imagen = arma
                else:
                    # Fallback: buscar en el mapeo
                    sprite_name = _ARMAS_DISPLAY_A_SPRITE.get(arma)
                    if sprite_name and sprite_name in _IMG_BTN:
                        cvs._btn_imagen = sprite_name
                    else:
                        lowercase_name = arma.lower()
                        if lowercase_name in _IMG_BTN:
                            cvs._btn_imagen = lowercase_name
                        else:
                            cvs._btn_imagen = None
            else:
                cvs._btn_imagen = None
            
            # Redibuja para aplicar cambio
            if hasattr(cvs, '_dibujar'):
                cvs._dibujar()
            
            # Re-asignar comando si cambió
            if tiene:
                cmd = (lambda a: lambda: self._enviar_comando(a) if self._en_combate else None)(arma)
                cvs.bind("<Button-1>", lambda e, c=cmd: c())
            else:
                cvs.bind("<Button-1>", lambda e: None)
        
        # --- Actualizar STANCES (fila 1) ---
        # El estado se mantiene en _toggle_state, actualizar visualmente
        # Normalizar formato: juego usa "bloquear"/"esquivar", UI usa "bl"/"esq"
        if stance is not None:
            # Convertir formato del juego al formato de UI
            stance_normalizado = {
                "bloquear": "bl",
                "esquivar": "esq"
            }.get(stance, stance)  # Si no está en el diccionario, usar tal cual
            self._toggle_state['activa'] = stance_normalizado
        else:
            # Si NO hay stance (fin de turno), apagar el botón
            self._toggle_state['activa'] = None
        self._actualizar_stances_visual()
        
        # --- Actualizar ACCIONES (fila 2) ---
        # Poción: desactivar si no hay pociones disponibles O ya se usó una en este turno
        cvs_pocion = self._botones_acciones['pocion']
        tiene_pocion = (pociones > 0) and not pocion_usada_turno
        self._redibujar_boton(
            cvs_pocion, "", tiene_pocion, "circulo",
        )
        if tiene_pocion:
            cvs_pocion.bind("<Button-1>", lambda e: self._enviar_comando("p") if self._en_combate else None)
        else:
            cvs_pocion.bind("<Button-1>", lambda e: None)
        
        # Huir
        cvs_huir = self._botones_acciones['huir']
        puede_huir = not huida_bloqueada
        self._redibujar_boton(cvs_huir, "Huir", puede_huir, "circulo")
        
        # Si acábamos de entrar en combate, forzar redraw para pasar de gris a activo
        if estaba_inactivo:
            self._forzar_redraw_botones()

    # mostrar_botones_explorar() y mostrar_botones_evento() eliminadas (funciones vacías deprecadas)

    # ------------------------------------------------------------------
    # IMAGEN SITUACIONAL
    # ------------------------------------------------------------------

    def set_imagen(self, ruta_png):
        """Registra la imagen activa y la carga en el canvas."""
        self._ruta_imagen_actual = ruta_png
        self._cargar_imagen()

    def _cargar_imagen(self):
        """
        Carga _ruta_imagen_actual escalada al tamanyo actual del canvas.
        Se llama automaticamente al cambiar el tamanyo (evento <Configure>)
        y desde set_imagen(). Si no hay imagen registrada no hace nada.
        """
        if not self._ruta_imagen_actual:
            return
        w = self.canvas_imagen.winfo_width()
        h = self.canvas_imagen.winfo_height()
        if w < 10 or h < 10:
            return  # canvas aun no tiene tamanyo real; <Configure> lo llamara
        try:
            if PIL_DISPONIBLE:
                img = Image.open(self._ruta_imagen_actual)
                img = img.resize((w, h), Image.LANCZOS)
                self._imagen_tk = ImageTk.PhotoImage(img)
            else:
                self._imagen_tk = tk.PhotoImage(file=self._ruta_imagen_actual)
            self.canvas_imagen.delete("all")
            self.canvas_imagen.create_image(0, 0, anchor="nw", image=self._imagen_tk)
        except Exception as e:
            sistema(f"No se pudo cargar imagen: {e}")

    # ELIMINADO: _cargar_fondo_panel_derecho() - Legacy system nunca implementado.
    # Variables _RUTA_FONDO_PANEL_DERECHO siempre fueron None.

    # ------------------------------------------------------------------
    # PARSER
    # ------------------------------------------------------------------

    def _habilitar_input(self):
        """Activa la Entry para que el jugador pueda escribir."""
        self._input_activo = True
        self.parser_entry.configure(state="normal")
        self.parser_entry.focus_set()

    def _log_parser(self, texto, tag="cmd"):
        """Escribe una linea en el registro del parser. Estilo terminal: texto + salto."""
        self.parser_registro.configure(state="normal")
        self.parser_registro.insert("end", texto + "\n", tag)
        self.parser_registro.see("end")
        self.parser_registro.configure(state="disabled")

    def _enviar_input(self, event=None):
        if not self._input_activo:
            return
        texto = self.parser_entry.get().strip()
        if not texto:
            return
        if texto.lower() in ("cerrar juego", "salir juego"):
            self.root.destroy()
            return
        
        # Sincronizar stances si se escriben "bl" o "esq" directamente en parser
        texto_lower = texto.lower()
        abrev_stance = {"bl": "bl", "blo": "bl", "bloquear": "bl",
                        "esq": "esq", "esquiva": "esq", "esquivar": "esq"}
        if texto_lower in abrev_stance and self._en_combate:
            stance_key = abrev_stance[texto_lower]
            # Alternar: si ya está activa, desactivar; si no, activar
            if self._toggle_state.get('activa') == stance_key:
                self._toggle_state['activa'] = None
            else:
                self._toggle_state['activa'] = stance_key
            self._actualizar_stances_visual()
        
        # Borrar y bloquear EN ESTE ORDEN: delete no funciona en state=disabled
        self.parser_entry.delete(0, "end")
        self._input_activo = False
        self.parser_entry.configure(state="disabled")
        self._historial_parser.append(texto)
        self._historial_idx = -1
        self._log_parser(f"> {texto}", tag="cmd")
        self.agregar_texto(f"Elegiste : {texto}", "elegiste", typewriter=False)
        if self.on_input:
            self.on_input(texto)

    def _enviar_comando(self, cmd):
        """Inyecta un comando como si el jugador lo hubiera escrito."""
        if not self._input_activo:
            return
        self.parser_entry.configure(state="normal")
        self.parser_entry.delete(0, "end")
        self.parser_entry.insert(0, cmd)
        self._enviar_input()

    def _historial_arriba(self, event):
        if not self._historial_parser:
            return
        if self._historial_idx < 0:
            self._historial_idx = len(self._historial_parser) - 1
        else:
            self._historial_idx = max(0, self._historial_idx - 1)
        self.parser_entry.delete(0, "end")
        self.parser_entry.insert(0, self._historial_parser[self._historial_idx])

    def _historial_abajo(self, event):
        if self._historial_idx < 0:
            return
        self._historial_idx += 1
        self.parser_entry.delete(0, "end")
        if self._historial_idx < len(self._historial_parser):
            self.parser_entry.insert(0, self._historial_parser[self._historial_idx])
        else:
            self._historial_idx = -1

    # ------------------------------------------------------------------
    # TAGS DE ESTILO
    # Cada tipo de mensaje tiene su tag en el widget Text.
    # Cambiar el estilo visual aqui afecta a todos los mensajes de ese tipo.
    # ------------------------------------------------------------------

    def _configurar_tags(self):
        self.texto.tag_configure(
            "narrar",    foreground=COLORES["narrar"],    font=("Consolas", 11, "italic"))
        self.texto.tag_configure(
            "alerta",    foreground=COLORES["alerta"],    font=("Consolas", 11, "bold"))
        self.texto.tag_configure(
            "exito",     foreground=COLORES["exito"],     font=("Consolas", 11, "bold"))
        self.texto.tag_configure(
            "sistema",   foreground=COLORES["sistema"],   font=("Consolas", 11))
        self.texto.tag_configure(
            "dialogo",   foreground=COLORES["dialogo"],   font=("Consolas", 12, "bold"))
        self.texto.tag_configure(
            "susurros",  foreground=COLORES["susurros"],  font=("Consolas", 10, "italic"))
        self.texto.tag_configure(
            "preguntar", foreground=COLORES["preguntar"], font=("Consolas", 11, "bold"))
        self.texto.tag_configure(
            "elegiste",  foreground=COLORES["preguntar"], font=("Consolas", 11, "italic"))
        self.texto.tag_configure(
            "titulo",    foreground=COLORES["titulo"],    font=("Consolas", 12, "bold"))
        self.texto.tag_configure(
            "separador", foreground=COLORES["separador"], font=("Consolas", 10))

    # ------------------------------------------------------------------
    # ESCRITURA DE TEXTO
    # ------------------------------------------------------------------

    def agregar_texto(self, texto, tag, typewriter=True):
        velocidad = self.VELOCIDAD_TYPEWRITER.get(tag, 0) if typewriter else 0
        if velocidad > 0:
            self._ocupado = True
            self._typewriter(texto + "\n", tag, 0, velocidad)
        else:
            self.texto.configure(state="normal")
            self.texto.insert("end", texto + "\n", tag)
            self.texto.see("end")
            self.texto.configure(state="disabled")

    def _typewriter(self, texto, tag, indice, velocidad):
        """
        Escribe una letra cada `velocidad` ms usando .after().
        Cuando termina libera _ocupado para que el polling continue.
        """
        if indice < len(texto):
            self.texto.configure(state="normal")
            self.texto.insert("end", texto[indice], tag)
            self.texto.see("end")
            self.texto.configure(state="disabled")
            self.root.after(velocidad, self._typewriter, texto, tag, indice + 1, velocidad)
        else:
            self._ocupado = False

    # ------------------------------------------------------------------
    # DISPATCHER: recibe un mensaje y llama al renderer correcto
    # ------------------------------------------------------------------

    def procesar_mensaje(self, msg):
        tipo      = msg["tipo"]
        contenido = msg["contenido"]

        if tipo in ("narrar", "alerta", "exito", "sistema", "dialogo", "preguntar"):
            self.agregar_texto(contenido, tipo)

        elif tipo == "susurros":
            self.agregar_texto(f"  {contenido}  ", "susurros")

        elif tipo == "separador":
            self.agregar_texto("-" * 52, "separador", typewriter=False)

        elif tipo == "titulo":
            self.agregar_texto(f"-- {contenido} --", "titulo", typewriter=False)

        elif tipo == "panel":
            if contenido.get("titulo"):
                self.agregar_texto(f"[ {contenido['titulo']} ]", "titulo", typewriter=False)
            self.agregar_texto(contenido["texto"], "narrar")

        elif tipo == "stats":
            self.actualizar_hud(contenido)
            self._mostrar_stats_texto(contenido)

        elif tipo == "hud_combate":
            self.actualizar_hud(contenido)

        elif tipo == "habilitar_input":
            self._habilitar_input()

        elif tipo == "hud":
            # Actualiza el HUD silenciosamente, sin texto en el area narrativa
            self.actualizar_hud(contenido)

        elif tipo == "opciones_combate":
            self.actualizar_botones_combate(
                contenido.get("armas", []),
                contenido.get("pociones", 0),
                contenido.get("huida_bloqueada", False),
                pocion_usada_turno=contenido.get("pocion_usada_turno", False),
                stance=contenido.get("stance"),
            )
        
        elif tipo == "terminar_combate":
            self.desactivar_botones_combate()

        elif tipo == "menu_principal":
            self._mostrar_menu_principal(contenido)

        elif tipo == "titulo_juego":
            self._mostrar_titulo_juego(contenido)

    # ------------------------------------------------------------------
    # RENDERERS ESPECIFICOS
    # ------------------------------------------------------------------

    def _mostrar_stats_texto(self, d):
        """
        Muestra stats en el area narrativa cuando el jugador escribe 'stats'.
        El HUD permanente ya los muestra siempre; esto es confirmacion verbal.
        """
        self.agregar_texto("-- ESTADISTICAS --", "titulo", typewriter=False)
        vida_tag = "alerta" if d["vida"] < d["vida_max"] * 0.3 else "sistema"
        self.agregar_texto(f"  Vida:      {d['vida']} / {d['vida_max']}", vida_tag,  typewriter=False)
        self.agregar_texto(f"  Fuerza:    {d['fuerza']}",                 "sistema", typewriter=False)
        self.agregar_texto(f"  Destreza:  {d['destreza']}",               "sistema", typewriter=False)
        self.agregar_texto(f"  Armadura:  {d['armadura']} / {d['armadura_max']}", "sistema", typewriter=False)
        self.agregar_texto(f"  Pociones:  {d['pociones']} / {d['pociones_max']}", "sistema", typewriter=False)
        self.agregar_texto(f"  Armas ({d['num_armas']}/3): {d['armas']}",  "sistema", typewriter=False)

    def _mostrar_menu_principal(self, opciones):
        """
        Menu de inicio: muestra las opciones en el texto principal.
        Sin botones: el jugador responde por el parser (1/2/3).
        """
        for op in opciones:
            self.agregar_texto(op, "preguntar", typewriter=False)

    def _mostrar_titulo_juego(self, d):
        # --- Canvas: imagen de portada ---
        _PORTADA = r"C:\Users\User\Desktop\codigos\TLDRDC\0.7\archivos 0.7_migracion\imagenes\PRUEBA_puerta_1.png"
        self.set_imagen(_PORTADA)

        # --- Texto principal: titulo centrado ---
        self.texto.tag_configure("titulo_centrado",
            foreground=COLORES["titulo"],
            font=("Consolas", 20, "bold"),
            justify="center",
        )
        self.texto.tag_configure("subtitulo_centrado",
            foreground=COLORES["sistema"],
            font=("Consolas", 11),
            justify="center",
        )
        self.texto.tag_configure("tagline_centrado",
            foreground=COLORES["narrar"],
            font=("Consolas", 10, "italic"),
            justify="center",
        )
        self.agregar_texto("", "separador", typewriter=False)
        self.agregar_texto(d["titulo"],    "titulo_centrado",    typewriter=False)
        self.agregar_texto(d["subtitulo"], "subtitulo_centrado", typewriter=False)
        self.agregar_texto(d["tagline"],   "tagline_centrado",   typewriter=False)
        self.agregar_texto("", "separador", typewriter=False)

    # ------------------------------------------------------------------
    # POLLING: vacia la cola cada 50ms sin bloquear la ventana
    # ------------------------------------------------------------------

    def _iniciar_polling(self):
        """
        Cada 50ms saca UN mensaje de cola_mensajes y lo procesa.
        Si hay un typewriter activo (_ocupado=True) no saca nada:
        espera a que termine para no intercalar caracteres.
        """
        if not self._ocupado and cola_mensajes:
            self.procesar_mensaje(cola_mensajes.popleft())
        self.root.after(50, self._iniciar_polling)

# ================== MAIN ==================
def main():
    global personaje_global
    # Inicializar las bolsas al inicio del juego
    rellenar_bolsa_eventos()
    rellenar_bolsa_exploracion()

    emitir("titulo_juego", {
        "titulo":    "TL;DR:DC",
        "subtitulo": "The Lost Dire Realm: Dungeon Crawler",
        "tagline":   "Sobrevive. O conviertete en parte de ella.",
    })

    while True:
        emitir("menu_principal", ["1) Nueva partida", "2) Cargar partida", "3) Salir"])
        opcion = pedir_input().strip()

        if opcion == "1":
            # Crear nuevo personaje
            personaje = crear_personaje()
            break

        elif opcion == "2":
            # Intentar cargar partida
            personaje = cargar_partida()
            if personaje:  # Si se cargó correctamente, salimos del bucle
                break
            else:
                alerta("No se pudo cargar la partida. Elige otra opción.")

        elif opcion == "3":
            sistema("Hasta luego...")
            pedir_input()
            sys.exit()

        else:
            alerta("Opción no válida. Elige 1, 2 o 3.")

    personaje_global = Personaje(personaje)
    personaje_global.activo = True  # Activar reactividad después de inicializar
    
    # CRÍTICO: Hacer que 'personaje' apunte al wrapper reactivo
    # Así todas las funciones que reciben 'personaje' como parámetro modificarán el wrapper
    # en lugar del dict original, permitiendo que los observadores detecten los cambios
    personaje = personaje_global
    
    # Registrar observadores de reactitividad EN VISTA (usar root.after para ejecutar en main thread)
    if vista_global is not None:
        # root será accesible como vista_global.root
        vista_global.root.after(0, vista_global._registrar_observadores_personaje)

    # ===== INYECCIÓN DE DEPENDENCIAS EN MÓDULO EVENTS =====
    # Después de que todas las funciones se han definido, inyectamos
    # las referencias al módulo events para que pueda accederlas.
    if MODULOS_EVENTOS_DISPONIBLES:
        try:
            # Inyectar funciones narrativas
            events_module.narrar = narrar
            events_module.alerta = alerta
            events_module.preguntar = preguntar
            events_module.leer_input = leer_input
            events_module.dialogo = dialogo
            events_module.exito = exito
            events_module.sistema = sistema
            events_module.emitir = emitir
            events_module.susurros_aleatorios = susurros_aleatorios
            
            # Inyectar funciones de combate
            events_module.combate = combate
            events_module.enemigo_aleatorio = enemigo_aleatorio
            events_module.crear_carcelero = crear_carcelero
            events_module.aplicar_evento = aplicar_evento
            
            # Inyectar variables globales de estado
            events_module.estado = estado
            events_module.armas_global = armas_global
            
            sistema("✓ Módulo de eventos correctamente inicializado")
        except Exception as e:
            alerta(f"Error al inyectar dependencias en eventos: {e}")
    
    # ===== INYECTAR CALLBACK DE UI PARA ARMAS =====
    # Esto permite que aplicar_evento() sincronice la UI cuando se obtiene un arma
    # El callback se encola al main thread para thread-safety
    global _callback_ui_armas
    if vista_global is not None:
        _callback_ui_armas = lambda: vista_global.root.after(0, vista_global._on_armas_cambio)

    mostrar_stats(personaje)
    sistema("Usa el comando 'stats/stat/st' para consultar tus estadísticas en cualquier momento.")
    separador()

    # Iniciar juego
    if opcion == "1":
        celda_inicial(personaje_global)
    else:
        explorar(personaje_global)
   


def _demo_vista():
    """
    Entrypoint de prueba: abre la ventana con datos ficticios sin
    iniciar el game loop. Permite comprobar layout, colores y botones.
    Cambiar _DEMO_ESTADO para ver cada grupo de botones.
    """

    # --- Datos falsos de personaje para el HUD ---
    _DEMO_PERSONAJE = {
        "vida": 18, "vida_max": 25,
        "fuerza": 7, "destreza": 3,
        "armadura": 2, "armadura_max": 5, 
        "pociones": 2, "pociones_max": 10,
    }
    # --- Estado a mostrar: "explorar" | "combate" | "combate_sin_pocion" | "evento" ---
    _DEMO_ESTADO = "combate"

    root = tk.Tk()
    vista = Vista(root)

    # Cargar HUD con datos falsos
    vista.actualizar_hud(_DEMO_PERSONAJE)

    # Texto de muestra para ver typewriter y colores
    emitir("titulo_juego", {
        "titulo":    "TL;DR:DC",
        "subtitulo": "The Lost Dire Realm: Dungeon Crawler",
        "tagline":   "Sobrevive. O conviertete en parte de ella.",
    })
    emitir("separador")
    emitir("narrar",   "La oscuridad lo engulle todo. Apenas ves las paredes, pero debes avanzar.")
    emitir("dialogo",  "'No dejes que te atrapen...'")
    emitir("susurros", "'dolor... poder... sangre... herida... abierta...'")
    emitir("alerta",   "El enemigo te ataca. Recibes 4 de dano.")
    emitir("exito",    "Golpeas por 7. El enemigo sangra.")
    emitir("sistema",  "Partida guardada correctamente.")
    emitir("separador")
    emitir("narrar",   "Te adentras en el pasillo. Oyes pasos detras de ti.")

    # Mostrar el grupo de botones segun el estado demo
    if _DEMO_ESTADO == "explorar":
        pass

    elif _DEMO_ESTADO == "combate":
        # 2 armas equipadas, 1 slot vacio, 2 pociones disponibles
        vista.actualizar_botones_combate(
            armas=["daga", "espada"],
            pociones=2,
        )

    elif _DEMO_ESTADO == "combate_sin_pocion":
        # Igual pero sin pociones: boton pocion aparece gris/bloqueado
        vista.actualizar_botones_combate(
            armas=["daga", "espada", "martillo"],
            pociones=0,
        )

    elif _DEMO_ESTADO == "evento":
        pass

    root.mainloop()


# ============================================================================
# INYECCIÓN DE DEPENDENCIAS PARA MÓDULO DE EVENTOS
# ============================================================================
# Asignar todas las funciones y variables globales que el módulo de eventos necesita
# (Hecho aquí para evitar referencies a funciones no definidas)
if MODULOS_EVENTOS_DISPONIBLES:
    events_module.narrar = narrar
    events_module.alerta = alerta
    events_module.preguntar = preguntar
    events_module.leer_input = leer_input
    events_module.dialogo = dialogo
    events_module.exito = exito
    events_module.sistema = sistema
    events_module.emitir = emitir
    events_module.susurros_aleatorios = susurros_aleatorios
    events_module.combate = combate
    events_module.enemigo_aleatorio = enemigo_aleatorio
    events_module.crear_carcelero = crear_carcelero
    events_module.aplicar_evento = aplicar_evento
    events_module.fin_derrota = fin_derrota
    events_module.añadir_arma = añadir_arma
    
    events_module.estado = estado
    events_module.armas_global = armas_global

# ============================================================================

def _iniciar_juego():
    """
    Entrypoint de produccion: crea la Vista, conecta el puente de input,
    lanza el game loop en un hilo daemon y arranca el mainloop de tkinter.
    El hilo del juego es daemon: si se cierra la ventana, muere solo.
    """
    global vista_global
    root = tk.Tk()
    vista = Vista(root)
    vista_global = vista  # Guardar referencia para que main() pueda registrar observadores
    vista.on_input = _bridge.recibir

    def _run_juego():
        try:
            main()
        except SystemExit:
            root.after(0, root.destroy)

    hilo = threading.Thread(target=_run_juego, daemon=True)
    hilo.start()
    root.mainloop()


if __name__ == "__main__":
    _iniciar_juego()
    # Para jugar: cambia _demo_vista() por _iniciar_juego()

