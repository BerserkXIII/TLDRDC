"""
Módulo de Monitoreo de Performance para TLDRDC.

Sistema para medir y monitorear performance de funciones clave.
"""

import os
import time
from contextlib import contextmanager

# Importar _log_debug con manejo de errores (funciona tanto desde raíz como desde aquí)
try:
    from .logging_manager import _log_debug
except ImportError:
    try:
        from modules.logging_manager import _log_debug
    except ImportError:
        # Fallback si se importa directamente
        def _log_debug(seccion, mensaje):
            pass

# ================== CONFIGURACIÓN DE PERFORMANCE MONITORING ==================

PERF_MODE = True  # Cambiar a True para activar monitoring -------------------------------------

PERF_STATS = {
    # Estructura: "funcion": {"llamadas": 0, "tiempo_total": 0.0, "min": float('inf'), "max": 0.0}
}

# Ruta del archivo de performance
# DEBUG_FOLDER apunta a: Version 0.7/debug_reports/
DEBUG_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "debug_reports")
os.makedirs(DEBUG_FOLDER, exist_ok=True)
PERF_FILE = os.path.join(DEBUG_FOLDER, "performance.log")


@contextmanager
def _medir_tiempo(seccion):
    """
    Context manager para medir tiempo de ejecución.
    
    Uso:
        with _medir_tiempo("TURNO"):
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


def limpiar_estadisticas():
    """Limpia las estadísticas acumuladas."""
    global PERF_STATS
    PERF_STATS.clear()
