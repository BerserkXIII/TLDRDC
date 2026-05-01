"""
DEBUG_MODULES - Módulos de debugging y performance monitoring para TLDRDC (v1.0+)

Estos módulos están aislados en debug_modules/ para mantener v1.0 limpio.
En producción (v1.0) NO se importan automáticamente.

Para usar en desarrollo:
    from debug_modules.logging_manager import DEBUG_MODE, _log_debug
    from debug_modules.performance_monitor import PERF_MODE, _medir_tiempo

Activar:
    - Modificar DEBUG_MODE = True en logging_manager.py
    - Modificar PERF_MODE = True en performance_monitor.py
"""

# No exportar por defecto (uso explícito)
__all__ = []
