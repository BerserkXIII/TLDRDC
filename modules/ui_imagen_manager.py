# ════════════════════════════════════════════════════════════════════
# IMAGE MANAGER MODULE
# Maneja carga de imágenes con caché y detección de PIL
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
    Administrador centralizado de imágenes.
    - Carga PNG y JPG con PIL si está disponible
    - Mantiene caché para evitar garbage collection
    - Fallback a tk.PhotoImage nativo para PNG sin PIL
    """
    
    def __init__(self):
        self._cache = {}       # {ruta: tk.PhotoImage}
        self.pil_disponible = PIL_DISPONIBLE
    
    def cargar_imagen(self, ruta, tamaño=None):
        """
        Carga imagen desde ruta (PNG o JPG).
        
        Args:
            ruta: str - Ruta absoluta al archivo de imagen
            tamaño: (ancho, alto) opcional - Redimensiona si es dado
        
        Returns:
            tk.PhotoImage o None si no se puede cargar
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
        Valida que todas las rutas en un diccionario existan.
        
        Args:
            dict_rutas: dict - {"nombre": "ruta/archivo"}
        
        Returns:
            dict - {"nombre": existe_booleano}
        """
        return {nom: os.path.exists(rut) for nom, rut in dict_rutas.items()}
    
    def limpiar_cache(self):
        """Limpia el caché de imágenes."""
        self._cache.clear()

# ════════════════════════════════════════════════════════════════════
# INSTANCIA GLOBAL
# ════════════════════════════════════════════════════════════════════

imagen_manager = ImagenManager()
