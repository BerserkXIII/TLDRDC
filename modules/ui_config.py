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
    "boton_fg":        "#cccccc",      # Texto botones
    "boton_bg":        "#1a1a1a",      # Fondo botones inactivos
    "boton_hover":     "#3a0a0a",      # Hover en botones
    "boton_activo":    "#cc4444",      # Botones disponibles
    "boton_inactivo":  "#333333",      # Botones bloqueados
    "stats_fg":        "#999999",      # Texto stats
    "stats_vida":      "#cc2222",      # Color vida
    "parser_bg":       "#080808",      # Fondo parser
    "parser_fg":       "#cccccc",      # Texto parser
    "parser_cursor":   "#cc2222",      # Cursor parser
}

# ════════════════════════════════════════════════════════════════════
# FORMAS DE BOTONES (polígonos normalizados 0-1)
# ════════════════════════════════════════════════════════════════════

FORMAS_BTN = {
    # Rombo / diamante — armas pesadas y esquivar
    "rombo":    [(0.50, 0.04), (0.97, 0.50), (0.50, 0.96), (0.03, 0.50)],
    
    # Hexágono vertical — armas sutiles
    "hexagono": [(0.25, 0.04), (0.75, 0.04), (0.97, 0.50),
                 (0.75, 0.96), (0.25, 0.96), (0.03, 0.50)],
    
    # Escudo — bloquear
    "escudo":   [(0.08, 0.04), (0.92, 0.04), (0.92, 0.58),
                 (0.50, 0.97), (0.08, 0.58)],
    
    # Octógono — armas mixtas
    "octagono": [(0.30, 0.04), (0.70, 0.04), (0.96, 0.30), (0.96, 0.70),
                 (0.70, 0.96), (0.30, 0.96), (0.04, 0.70), (0.04, 0.30)],
    
    "circulo":  None,   # usa create_oval
    "rect":     None,   # rectángulo plano (fallback)
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

RUTAS_IMAGENES_BOTONES = {
    "daga": str(_IMAGEN_ASSETS / "daga.png"),
    "espada": str(_IMAGEN_ASSETS / "espada.png"),
    "martillo": str(_IMAGEN_ASSETS / "martillo.png"),
    # ... agregar más según sea necesario
}

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
