"""
Módulos del Juego TLDRDC (v1.0)

Contiene módulos de configuración e UI para producción.

NOTA: Los módulos de debugging (logging_manager, performance_monitor) han sido
aislados en debug_modules/ para mantener v1.0 limpio y evitar generación
automática de carpetas en producción.
"""

# Importaciones principales para facilitar acceso (módulos de producción)
from .ui_config import (
    COLORES,
    RUTAS_IMAGENES_PANELES,
    UI_RENDER_MODE,
    CANVAS_LAYER_TAGS,
    CANVAS_LAYER_ORDER,
)
from .ui_imagen_manager import imagen_manager
from .ui_canvas_panel import CanvasPanel
from .ui_estructura import estructura_ui

__all__ = [
    'COLORES', 'RUTAS_IMAGENES_PANELES', 'UI_RENDER_MODE',
    'CANVAS_LAYER_TAGS', 'CANVAS_LAYER_ORDER',
    'imagen_manager',
    'CanvasPanel',
    'estructura_ui',
]

# DEBUG MODULES: Aislados en debug_modules/ (importación manual si es necesario)
# from debug_modules.logging_manager import DEBUG_MODE, _log_debug, limpiar_log
# from debug_modules.performance_monitor import PERF_MODE, _medir_tiempo, mostrar_estadisticas_perf
