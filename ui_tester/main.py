"""
MAIN - UI Tester Entry Point
=============================

Dynamically loads TLDRDC_Prueba1.py and injects test globals.
Initializes Vista and TesterParser without modifying original files.

Execution:
    python -m ui_tester.main
    python ui_tester/main.py
"""

import sys
import os
import importlib.util
import tkinter as tk

# Add TLDRDC root to path
TLDRDC_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, TLDRDC_ROOT)

from . import mocks, parser
from .mocks import personaje_global, estado, _IMG_BTN


def cargar_vista_dinamicamente():
    """
    Load TLDRDC_Prueba1.py without modifying the original file.
    
    Process:
    1. Find TLDRDC_Prueba1.py module file
    2. Inject test globals into its namespace BEFORE executing
    3. Load module via importlib.util
    4. Return Vista class and game functions
    
    Returns:
        (Vista class, TLDRDC module)
    """
    
    # Path to TLDRDC_Prueba1.py
    modulo_path = os.path.join(TLDRDC_ROOT, "TLDRDC_Prueba1.py")
    
    if not os.path.exists(modulo_path):
        raise FileNotFoundError(f"No se encuentra: {modulo_path}")
    
    # Load module spec
    spec = importlib.util.spec_from_file_location("TLDRDC_Prueba1", modulo_path)
    modulo = importlib.util.module_from_spec(spec)
    
    # ===== INJECT TEST GLOBALS BEFORE EXECUTION =====
    # These will be available to the module when it runs
    modulo.personaje_global = personaje_global
    modulo.estado = estado
    modulo._IMG_BTN = _IMG_BTN
    
    # Inject mock functions so Tkinter doesn't fail on imports
    modulo.narrar = mocks.narrar
    modulo.alerta = mocks.alerta
    modulo.sistema = mocks.sistema
    modulo.exito = mocks.exito
    modulo.pedir_input = mocks.pedir_input
    
    # Execute module (this runs TLDRDC_Prueba1.py in modulo's namespace)
    spec.loader.exec_module(modulo)
    
    # ===== AFTER EXECUTION: Inject queue and emit function =====
    # These are available AFTER module runs and Vista is defined
    mocks.cola_mensajes = modulo.cola_mensajes
    mocks.emitir = modulo.emitir
    
    print(f"[✓] Inyección completada:")
    print(f"    mocks.cola_mensajes: {mocks.cola_mensajes}")
    print(f"    mocks.emitir: {mocks.emitir}")
    
    # Retrieve Vista class from executed module
    Vista = getattr(modulo, "Vista", None)
    if not Vista:
        raise RuntimeError("No se encontró clase Vista en TLDRDC_Prueba1.py")
    
    print("[✓] Módulo TLDRDC cargado dinámicamente")
    print(f"[✓] Globals inyectados: personaje_global, estado, _IMG_BTN")
    
    return Vista, modulo


def main():
    """
    Main entry point for UI Tester.
    
    1. Create Tkinter root
    2. Dynamically load Vista from TLDRDC_Prueba1
    3. Create Vista instance (this initializes all UI)
    4. Bind Vista to TesterParser
    5. Run event loop
    """
    
    print("\n" + "="*70)
    print("🚀 UI TESTER - INICIALIZANDO")
    print("="*70)
    print(f"[*] Raíz TLDRDC: {TLDRDC_ROOT}")
    
    # Create root window
    root = tk.Tk()
    root.title("UI Tester - TLDRDC Visual")
    root.geometry("1400x900")
    
    # Load Vista and TLDRDC module
    try:
        Vista, tldrdc_modulo = cargar_vista_dinamicamente()
    except Exception as e:
        print(f"[✗] Error cargando Vista: {e}")
        root.destroy()
        return
    
    # Create Vista instance (initializes entire UI)
    print("[*] Instanciando Vista...")
    vista = Vista(root)
    
    # Force UI to draw before starting message processing
    root.update()
    root.update_idletasks()
    
    # Unlock parser entry field (Vista initializes it as disabled by default)
    vista.parser_entry.config(state="normal")
    vista._input_activo = True
    vista.parser_entry.focus()
    
    # Create parser and bind to Vista
    print("[*] Inicializando parser de comandos...")
    cmd_parser = parser.TesterParser(vista, tldrdc_modulo)
    
    # Inject reference to parser in Vista for any callbacks
    vista.parser = cmd_parser
    
    print("\n[✓] TESTER LISTO")
    print("="*70 + "\n")
    
    # Start event loop
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\n[*] Tester cerrado por usuario")


if __name__ == "__main__":
    main()
