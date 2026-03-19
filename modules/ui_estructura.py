# ════════════════════════════════════════════════════════════════════
# UI STRUCTURE MODULE
# Factory para crear paneles con Canvas (para imágenes) + Frame (widgets)
# ════════════════════════════════════════════════════════════════════

import tkinter as tk
from .ui_config import COLORES
from .ui_imagen_manager import imagen_manager

# ════════════════════════════════════════════════════════════════════
# FACTORY PARA CREAR PANELES CON FONDO DE IMAGEN
# ════════════════════════════════════════════════════════════════════

class EstructuraUI:
    """
    Factory para crear paneles UI con arquitectura multicapa:
    
    [outer_frame: borde decorativo]
        └─ [canvas_fondo: muestra imagen PNG de fondo]
            └─ [frame_contenido: contiene widgets (Text, Canvas, etc)]
    
    Esto permite:
    - Fondo PNG decorativo con z-order correcto
    - Widgets superpuestos en el Frame dentro del Canvas
    - Redimensionamiento responsivo
    """
    
    @staticmethod
    def crear_panel_con_fondo(
        parent,
        ruta_fondo=None,
        color_borde=COLORES["borde"],
        color_fondo=COLORES["fondo_panel"],
        row=0, column=0,
        **grid_kwargs
    ):
        """
        Crea un panel con 3 capas: borde > Canvas(fondo) > Frame(contenido)
        
        Args:
            parent: tk widget padre
            ruta_fondo: str - Ruta PNG para fondo (opcional)
            color_borde: str - Color hex del borde (#XXXXXX)
            color_fondo: str - Color hex del fondo si no hay PNG
            row, column: int - Posición en grid del padre
            **grid_kwargs: otros parámetros para grid()
        
        Returns:
            (frame_contenido, canvas_fondo, outer_frame)
        """
        # Capa 1: Frame exterior (borde decorativo)
        outer = tk.Frame(parent, bg=color_borde, padx=2, pady=2)
        
        # Aplicar grid al Frame exterior si se especificó row/column
        if "sticky" not in grid_kwargs:
            grid_kwargs["sticky"] = "nsew"
        outer.grid(row=row, column=column, **grid_kwargs)
        
        # Capa 2: Canvas (para imagen de fondo)
        canvas = tk.Canvas(outer, bg=color_fondo, highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        
        # Capa 3: Frame contenedor de widgets (dentro del Canvas)
        frame_contenido = tk.Frame(canvas, bg=color_fondo)
        
        # Posicionar el Frame en el Canvas de forma que se redimensione
        canvas.create_window(0, 0, window=frame_contenido, anchor="nw", tags="content")
        
        # Variable para guardar la imagen (evita garbage collection)
        _current_bg_image = None
        
        # Callback para redimensionar imagen cuando el canvas cambia de tamaño
        def _on_canvas_configure(event):
            nonlocal _current_bg_image
            
            # Ajustar tamaño del Frame de contenido
            canvas.itemconfig("content", width=event.width, height=event.height)
            frame_contenido.configure(width=event.width, height=event.height)
            
            # Redimensionar imagen de fondo si existe
            if ruta_fondo and event.width > 1 and event.height > 1:
                try:
                    # Cargar y redimensionar imagen al tamaño actual del canvas
                    img = imagen_manager.cargar_imagen(ruta_fondo, tamaño=(event.width, event.height))
                    if img:
                        _current_bg_image = img  # Guardar referencia para evitar GC
                        canvas.delete("background")
                        canvas.create_image(0, 0, image=img, anchor="nw", tags="background")
                        canvas.tag_lower("background")  # Enviar al fondo
                except Exception as e:
                    print(f"Error redimensionando fondo {ruta_fondo}: {e}")
        
        canvas.bind("<Configure>", _on_canvas_configure)
        
        # Guardar referencias útiles
        outer._canvas_fondo = canvas
        outer._frame_contenido = frame_contenido
        
        return (frame_contenido, canvas, outer)
    
    @staticmethod
    def crear_panel_imagen_dinamico(parent, row=0, column=0, **grid_kwargs):
        """
        Crea un panel simplificado solo para mostrar imágenes dinámicas.
        
        Returns:
            (canvas_imagen, outer_frame)
        """
        outer = tk.Frame(parent, bg=COLORES["borde"], padx=2, pady=2)
        if "sticky" not in grid_kwargs:
            grid_kwargs["sticky"] = "nsew"
        outer.grid(row=row, column=column, **grid_kwargs)
        
        canvas = tk.Canvas(outer, bg=COLORES["fondo_panel"], highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        
        return (canvas, outer)

# ════════════════════════════════════════════════════════════════════
# INSTANCIA GLOBAL
# ════════════════════════════════════════════════════════════════════

estructura_ui = EstructuraUI()
