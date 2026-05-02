# ════════════════════════════════════════════════════════════════════
# IMAGE MANAGER
# ════════════════════════════════════════════════════════════════════

import tkinter as tk
import os
from pathlib import Path

# Detectar disponibilidad de PIL
try:
    from PIL import Image, ImageTk
    PIL_DISPONIBLE = True
except ImportError:
    PIL_DISPONIBLE = False

# ════════════════════════════════════════════════════════════════════
# GESTOR DE IMÁGENES CON CACHÉ
# ════════════════════════════════════════════════════════════════════

class ImagenManager:
    """
    Centralized image loader with caching.
    Supports PNG/JPG via PIL when available; fallback to native Tkinter.
    """
    
    def __init__(self):
        self._cache = {}       # {ruta: tk.PhotoImage}
        self.pil_disponible = PIL_DISPONIBLE
    
    def cargar_imagen(self, ruta, tamaño=None):
        """
        Load image from path (PNG or JPG).
        
        Args:
            ruta: absolute path to image file
            tamaño: (width, height) tuple for resizing (optional)
        
        Returns:
            tk.PhotoImage or None if loading fails
        """
        if not ruta or not os.path.exists(ruta):
            return None
        
        ruta = str(ruta)
        
        # Comprobar si ya está en caché
        cache_key = (ruta, tamaño)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            if tamaño and self.pil_disponible:
                # PIL: cargar, redimensionar, convertir a PhotoImage
                img = Image.open(ruta)
                img.thumbnail(tamaño, Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
            else:
                # Fallback: tk.PhotoImage nativo (PNG sin redimensión)
                photo = tk.PhotoImage(file=ruta)
            
            self._cache[cache_key] = photo
            return photo
        
        except Exception as e:
            print(f"Error cargando imagen {ruta}: {e}")
            return None
    
    def validar_rutas(self, dict_rutas):
        """
        Validate that all paths in dict exist.
        
        Args:
            dict_rutas: dict with {name: path} pairs
        
        Returns:
            dict with {name: bool} for each path
        """
        return {nom: os.path.exists(rut) for nom, rut in dict_rutas.items()}
    
    def limpiar_cache(self):
        """Clear image cache."""
        self._cache.clear()

# ════════════════════════════════════════════════════════════════════
# GLOBAL INSTANCE
# ════════════════════════════════════════════════════════════════════

imagen_manager = ImagenManager()
