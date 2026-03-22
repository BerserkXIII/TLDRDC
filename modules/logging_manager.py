"""
Módulo de Logging para TLDRDC.

Gestiona el sistema de logging no-intrusivo para debugging.
Activar/desactivar con la variable DEBUG_MODE.
"""

import os

# ================== CONFIGURACIÓN DE LOGGING ==================

DEBUG_MODE = False  # Cambiar a True para activar debugging -------------------------------------

# Crear carpeta para logs de debug y performance
# DEBUG_FOLDER apunta a: Version 0.7/debug_reports/
DEBUG_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "debug_reports")
os.makedirs(DEBUG_FOLDER, exist_ok=True)

LOG_FILE = os.path.join(DEBUG_FOLDER, "debug.log")


def _log_debug(seccion, mensaje):
    """
    Emite un mensaje de debug al log si DEBUG_MODE está activo.
    No interfiere con la UI del jugador.
    
    Args:
        seccion: str - categoría del log (ej: "CONDITION", "DAMAGE", "EFFECT")
        mensaje: str - mensaje a loguear
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
            print(f"Error escribiendo log: {e}")
    else:
        print(log_msg)  # Consola si no hay archivo


def limpiar_log():
    """Limpia el archivo de log (útil al iniciar debug)."""
    if LOG_FILE:
        try:
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.write("")
        except Exception as e:
            print(f"Error limpiando log: {e}")
