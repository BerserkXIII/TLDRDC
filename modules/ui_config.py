# ════════════════════════════════════════════════════════════════════
# UI CONFIGURATION MODULE
# Centraliza toda la configuración visual: colores, rutas, dimensiones
# ════════════════════════════════════════════════════════════════════

import os
from pathlib import Path

# Rutas base relativas a este archivo
_BASE_DIR = Path(__file__).parent
_IMAGEN_ASSETS = _BASE_DIR / "imagenes" / "pruebas"

# ════════════════════════════════════════════════════════════════════
# PALETA DE COLORES GÓTICA
# ════════════════════════════════════════════════════════════════════

COLORES = {
    "fondo":           "#0a0a0a",      # Fondo principal
    "fondo_panel":     "#0e0e0e",      # Fondo de paneles
    "borde":           "#3a1a1a",      # Borde decorativo
    "narrar":          "#b0b0b0",      # Narrativa normal
    "alerta":          "#cc2222",      # Alertas/errores
    "exito":           "#ccaa00",      # Éxitos/logros
    "sistema":         "#22aacc",      # Mensajes del sistema
    "dialogo":         "#ffffff",      # Diálogos de NPCs
    "susurros":        "#661111",      # Susurros oscuros
    "preguntar":       "#dddddd",      # Preguntas/turnos
    "titulo":          "#cc2222",      # Títulos
    "separador":       "#333333",      # Líneas separadoras
    "boton_activo":    "#cc4444",      # Botones disponibles
    "boton_inactivo":  "#333333",      # Botones bloqueados
    "stats_fg":        "#999999",      # Texto stats
    "stats_vida":      "#cc2222",      # Color vida
    "parser_bg":       "#080808",      # Fondo parser
    "parser_fg":       "#cccccc",      # Texto parser
    "parser_cursor":   "#cc2222",      # Cursor parser
}


# ════════════════════════════════════════════════════════════════════
# RUTAS DE IMÁGENES PARA PANELES
# ════════════════════════════════════════════════════════════════════

RUTAS_IMAGENES_PANELES = {
    "fondo_texto": str(_IMAGEN_ASSETS / "prueba_panel_texto.png"),
    "fondo_imagen": str(_IMAGEN_ASSETS / "prueba_panel_imagen.png"),
    "fondo_parser": str(_IMAGEN_ASSETS / "prueba_panel_parser.png"),
    "fondo_stats": str(_IMAGEN_ASSETS / "prueba_panel_stats.png"),
}

# ════════════════════════════════════════════════════════════════════
# RUTAS DE IMÁGENES PARA BOTONES
# ════════════════════════════════════════════════════════════════════

# NOTA: Carga de imágenes ahora es DINÁMICA desde /code/images/Botones/
# Las imágenes se cargan automáticamente mediante globbing de carpetas
# Ver _cargar_imgs_btns() en TLDRDC_Prueba1.py para detalles

# ════════════════════════════════════════════════════════════════════
# CONSTANTES DE DIMENSIONES
# ════════════════════════════════════════════════════════════════════

PESO_COL_IZQ = 72      # Porcentaje ancho panel izquierdo
PESO_COL_DER = 28      # Porcentaje ancho panel derecho
PESO_ALTO_ARRIBA = 70  # Porcentaje alto paneles arriba
PESO_ALTO_ABAJO = 30   # Porcentaje alto paneles abajo

ALTO_STATS = 69        # Altura franja stats
BOTONES_AREA_HEIGHT = 160  # Altura área botones

# Dimensiones de textos Widget
ANCHO_PANEL_TXT = 100
ALTO_PANEL_TXT = 30
ANCHO_PARSER = 100
ALTO_PARSER = 15

# ════════════════════════════════════════════════════════════════════
# FUENTES
# ════════════════════════════════════════════════════════════════════

FUENTES = {
    "normal": ("Consolas", 11),
    "titulo": ("Consolas", 12, "bold"),
    "boton": ("Consolas", 10),
    "parser": ("Consolas", 10),
}

# ════════════════════════════════════════════════════════════════════
# VELOCIDADES DE ANIMACIÓN
# ════════════════════════════════════════════════════════════════════

VELOCIDAD_TYPEWRITER = 30  # ms entre caracteres al escribir
