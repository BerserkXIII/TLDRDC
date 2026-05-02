# ════════════════════════════════════════════════════════════════════
# UI CONFIGURATION
# ════════════════════════════════════════════════════════════════════

import os
from pathlib import Path

# Rutas base relativas a este archivo
_BASE_DIR = Path(__file__).parent
_IMAGEN_ASSETS = _BASE_DIR / "imagenes" / "pruebas"

# ════════════════════════════════════════════════════════════════════
# GOTHIC COLOR PALETTE
# ════════════════════════════════════════════════════════════════════

COLORES = {
    "fondo":           "#0a0a0a",      # Main background
    "fondo_panel":     "#0e0e0e",      # Panel background
    "borde":           "#3a1a1a",      # Decorative border
    "narrar":          "#b0b0b0",      # Narrative text
    "alerta":          "#cc2222",      # Alerts/errors
    "exito":           "#ccaa00",      # Successes/rewards
    "sistema":         "#22aacc",      # System messages
    "dialogo":         "#ffffff",      # NPC dialogue
    "susurros":        "#661111",      # Dark whispers
    "preguntar":       "#dddddd",      # Prompts/turns
    "titulo":          "#cc2222",      # Titles
    "separador":       "#333333",      # Dividers
    "boton_activo":    "#cc4444",      # Active buttons
    "boton_inactivo":  "#333333",      # Inactive buttons
    "stats_fg":        "#999999",      # Stats text
    "stats_vida":      "#cc2222",      # Life color
    "parser_bg":       "#080808",      # Parser background
    "parser_fg":       "#cccccc",      # Parser text
    "parser_cursor":   "#cc2222",      # Parser cursor
}


# ════════════════════════════════════════════════════════════════════
# PANEL IMAGE PATHS
# ════════════════════════════════════════════════════════════════════

RUTAS_IMAGENES_PANELES = {
    "fondo_texto": str(_IMAGEN_ASSETS / "prueba_panel_texto.png"),
    "fondo_imagen": str(_IMAGEN_ASSETS / "prueba_panel_imagen.png"),
    "fondo_parser": str(_IMAGEN_ASSETS / "prueba_panel_parser.png"),
    "fondo_stats": str(_IMAGEN_ASSETS / "prueba_panel_stats.png"),
}

# ════════════════════════════════════════════════════════════════════
# BUTTON IMAGE PATHS
# ════════════════════════════════════════════════════════════════════

# Note: Images now load dynamically from /code/images/Botones/.
# See _cargar_imgs_btns() in TLDRDC_Prueba1.py.

# ════════════════════════════════════════════════════════════════════
# DIMENSIONS
# ════════════════════════════════════════════════════════════════════

PESO_COL_IZQ = 72      # Left panel width %
PESO_COL_DER = 28      # Right panel width %
PESO_ALTO_ARRIBA = 70  # Top panel height %
PESO_ALTO_ABAJO = 30   # Bottom panel height %

ALTO_STATS = 69        # Altura franja stats
BOTONES_AREA_HEIGHT = 160  # Altura área botones

# Dimensiones de textos Widget
ANCHO_PANEL_TXT = 100
ALTO_PANEL_TXT = 30
ANCHO_PARSER = 100
ALTO_PARSER = 15

# ════════════════════════════════════════════════════════════════════
# FONTS
# ════════════════════════════════════════════════════════════════════

FUENTES = {
    "normal": ("Consolas", 11),
    "titulo": ("Consolas", 12, "bold"),
    "boton": ("Consolas", 10),
    "parser": ("Consolas", 10),
}

# ════════════════════════════════════════════════════════════════════
# ANIMATION SPEEDS
# ════════════════════════════════════════════════════════════════════

VELOCIDAD_TYPEWRITER = 30  # ms between chars (typewriter effect)
