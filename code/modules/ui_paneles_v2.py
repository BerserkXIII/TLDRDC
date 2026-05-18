# ════════════════════════════════════════════════════════════════════
# UI PANELS V2 - CLEAN REWRITE
# ════════════════════════════════════════════════════════════════════
# Requisitos:
# - Panel texto: 1330x710px (imagen + Text widget)
# - Panel parser: 1330x300px (imagen + Text + Entry)
# - Panel imagen: 510x710px (imagen + Canvas dinámico)
# - Panel botones: 510x300px (imagen + Botones)
# 
# Arquitectura:
# - outer: Frame con borde (grid en parent)
# - canvas: imagen de fondo (grid 0,0 - FIRST)
# - frame_widgets: contenedor widgets (grid 0,0 - SECOND = ENCIMA)

import tkinter as tk
from .ui_config import COLORES, RUTAS_IMAGENES_PANELES, CANVAS_LAYER_TAGS
from .ui_imagen_manager import imagen_manager


class PanelConFondo:
    """Single panel: border + background image + widget container - GRID ONLY."""
    
    def __init__(self, parent, ruta_fondo=None, color_borde=COLORES["borde"],
                 color_fondo=COLORES["fondo_panel"], row=0, column=0, **grid_kwargs):
        """
        Create layered panel using ONLY grid() geometry manager.
        
        Args:
            parent: parent tk widget
            ruta_fondo: PNG path (optional)
            color_borde: border hex color
            color_fondo: background hex color
            row, column: grid position in parent
            **grid_kwargs: additional grid() params (padx, pady, etc)
        """
        # --- LAYER 1: Outer frame (border) - positioned via grid in parent ---
        self.outer = tk.Frame(parent, bg=color_borde, padx=2, pady=2)
        if "sticky" not in grid_kwargs:
            grid_kwargs["sticky"] = "nsew"
        self.outer.grid(row=row, column=column, **grid_kwargs)
        
        # Configure outer grid to make children expand
        self.outer.rowconfigure(0, weight=1)
        self.outer.columnconfigure(0, weight=1)
        
        # --- LAYER 2: Canvas (background image) - grid at (0,0) ---
        self.canvas = tk.Canvas(
            self.outer,
            bg=color_fondo,
            highlightthickness=0,
            relief="flat",
            bd=0
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        
        # Store image reference
        self.canvas._bg_image = None
        self.canvas._image_id = None
        
        # Load image when canvas size changes
        def _on_canvas_configure(event):
            if not ruta_fondo or event.width < 5 or event.height < 5:
                return
            try:
                img = imagen_manager.cargar_imagen(
                    ruta_fondo,
                    tamaño=(event.width, event.height)
                )
                if img:
                    self.canvas._bg_image = img
                    if self.canvas._image_id is None:
                        self.canvas._image_id = self.canvas.create_image(
                            0, 0,
                            image=img,
                            anchor="nw",
                            tags=("background", CANVAS_LAYER_TAGS["background"]),
                        )
                    else:
                        self.canvas.itemconfig(self.canvas._image_id, image=img)
                    self.canvas.tag_lower(CANVAS_LAYER_TAGS["background"])
            except Exception:
                pass
        
        self.canvas.bind("<Configure>", _on_canvas_configure)
        
        # --- LAYER 3: Frame for widgets - grid at (0,0) AFTER canvas = ON TOP ---
        self.frame_widgets = tk.Frame(self.outer)
        self.frame_widgets.grid(row=0, column=0, sticky="nsew")
        
        # Configure grid so widgets expand to fill
        self.frame_widgets.rowconfigure(0, weight=1)
        self.frame_widgets.columnconfigure(0, weight=1)
    
    def get_widget_frame(self):
        """Return the frame where to place widgets."""
        return self.frame_widgets


class GestorPaneles:
    """Orchestrate 4 panels (texto, parser, imagen, botones)."""
    
    def __init__(self, root):
        """
        Initialize panel manager.
        
        Args:
            root: tk.Tk() window
        """
        self.root = root
        
        # Configure root's main grid
        self.root.columnconfigure(0, weight=72)   # texto column
        self.root.columnconfigure(1, weight=28)   # panel column
        self.root.rowconfigure(0, weight=70)      # main row
        self.root.rowconfigure(1, weight=30)      # input row
        
        # Create 4 panels
        self.panel_texto = PanelConFondo(
            self.root,
            ruta_fondo=RUTAS_IMAGENES_PANELES["fondo_texto"],
            color_borde=COLORES["borde"],
            color_fondo=COLORES["fondo_panel"],
            row=0, column=0,
            padx=(6, 3), pady=(6, 3)
        )
        
        self.panel_parser = PanelConFondo(
            self.root,
            ruta_fondo=RUTAS_IMAGENES_PANELES["fondo_parser"],
            color_borde=COLORES["borde"],
            color_fondo=COLORES["fondo_panel"],
            row=1, column=0,
            padx=(6, 3), pady=(3, 6)
        )
        
        self.panel_imagen = PanelConFondo(
            self.root,
            ruta_fondo=RUTAS_IMAGENES_PANELES["fondo_imagen"],
            color_borde=COLORES["borde"],
            color_fondo=COLORES["fondo_panel"],
            row=0, column=1,
            padx=(3, 6), pady=(6, 3)
        )
        
        self.panel_botones = PanelConFondo(
            self.root,
            ruta_fondo=RUTAS_IMAGENES_PANELES["fondo_botones"],
            color_borde=COLORES["borde"],
            color_fondo=COLORES["fondo_panel"],
            row=1, column=1,
            padx=(3, 6), pady=(3, 6)
        )
        
        # Expose widget containers for game UI to populate
        self.frame_texto = self.panel_texto.get_widget_frame()
        self.frame_parser = self.panel_parser.get_widget_frame()
        self.frame_imagen = self.panel_imagen.get_widget_frame()
        self.frame_botones = self.panel_botones.get_widget_frame()
