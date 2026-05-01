# ARQUITECTURA - UI Tester TLDRDC

## Descripción General

El UI Tester es una herramienta de testing interactiva que **carga Vista (la UI original) sin modificaciones** e inyecta globals de prueba para permitir testing visual de sprites y mecánicas sin ejecutar el juego completo.

**Separación de responsabilidades:**
- `mocks.py` - Estado global + funciones mock
- `parser.py` - Parser de comandos interactivo
- `main.py` - Punto de entrada + carga dinámica de Vista

---

## Flujo de Ejecución

```
main() [main.py]
  │
  ├─ Create Tkinter root
  │
  ├─ cargar_vista_dinamicamente()
  │   │
  │   ├─ Locate TLDRDC_Prueba1.py
  │   ├─ Import module spec (NO EXECUTE YET)
  │   │
  │   ├─ INJECT GLOBALS INTO NAMESPACE:
  │   │   ├─ personaje_global (MockPersonajeReactivo)
  │   │   ├─ estado (dict)
  │   │   ├─ _IMG_BTN (dict, emptied)
  │   │   └─ narraciones mock (narrar, alerta, etc)
  │   │
  │   └─ Execute module (ahora tiene todos los globals)
  │       → TLDRDC_Prueba1 runs with OUR globals
  │       → Vista.__init__() executes
  │       → Vista._cargar_imgs_btns() executes (uses personaje_global)
  │       → Vista._registrar_observadores() executes
  │
  ├─ Vista(root) instantiate
  │   → UI fully initialized with 4 panels
  │   → All image buttons loaded into _IMG_BTN
  │   → Observers registered
  │
  ├─ TesterParser(vista, tldrdc_modulo) instantiate
  │   → Bind parser.procesar_comando() to vista.on_input
  │   → Print welcome + help
  │
  └─ root.mainloop()
     → User inputs commands
     → vista.on_input fires → parser.procesar_comando()
     → Commands modify personaje_global
     → Observers fire → Vista callbacks → UI updates
```

---

## Reactive System: Observer Pattern

**Problema original:** 
- `Vista._on_armas_cambio()` is a callback that updates weapon button sprites
- But it's only called when `personaje_global["armas"]` **changes**
- If we don't trigger the change, the observer never fires

**Solución en mocks.py:**

```python
class MockPersonajeReactivo(dict):
    """Custom dict subclass with observer pattern."""
    
    def observe(self, key, callback):
        """Register callback for when key changes."""
        if key not in self._observers:
            self._observers[key] = []
        self._observers[key].append(callback)
    
    def __setitem__(self, key, value):
        """Trigger observers when item is set."""
        super().__setitem__(key, value)
        if key in self._observers:
            for callback in self._observers[key]:
                callback()  # ← Execute callback

personaje_global = MockPersonajeReactivo({...})
```

**Flujo de cambios:**

```
CMD: "arma daga"
  │
  ├─ parser.cmd_arma("daga")
  │
  ├─ Validate weapon name
  │
  ├─ Call ORIGINAL: tldrdc_modulo.añadir_arma(personaje_global, "daga")
  │   (This function is from TLDRDC_Prueba1.py - UNMODIFIED)
  │
  ├─ Inside _original_ function:
  │   ├─ estado["armas_jugador"]["daga"] = {stats}
  │   └─ personaje_global["armas"] = estado["armas_jugador"].copy()
  │       ↓↓↓ TRIGGER __setitem__ ↓↓↓
  │
  ├─ MockPersonajeReactivo.__setitem__("armas", {...})
  │   │
  │   ├─ Set internal dict value
  │   │
  │   └─ Fire all observers for key="armas"
  │       └─ Vista._on_armas_cambio()  ← Callback registered earlier
  │           ├─ Read personaje_global["armas"]
  │           └─ Update weapon button sprites in real-time
  │
  └─ UI UPDATED ✓
```

---

## Inyección de Globals

**¿Por qué importlib.util?**

Necesitamos:
1. Cargar el módulo TLDRDC_Prueba1 del disco
2. Pero ANTES de ejecutar su código, inyectar nuestras variables globales
3. Para que cuando Vista.__init__() ejecute, use NUESTROS personaje_global, estado, etc.

**Sin importlib.util:** `import TLDRDC_Prueba1` usaría variables globales originales (no testing)

**Con importlib.util:**
```python
spec = importlib.util.spec_from_file_location("TLDRDC_Prueba1", path)
modulo = importlib.util.module_from_spec(spec)

# ← HERE we inject BEFORE execution
modulo.personaje_global = personaje_global
modulo.estado = estado
modulo._IMG_BTN = _IMG_BTN

# NOW execute (with our injected globals)
spec.loader.exec_module(modulo)
```

---

## Arquitectura de Archivos

```
ui_tester/
├── __init__.py              # Module initialization + imports
├── mocks.py                 # Globals + MockPersonajeReactivo class
├── parser.py                # TesterParser class + commands
├── main.py                  # Entry point + dynamic import
├── docs/
│   ├── ARQUITECTURA_TESTER.md       # This file
│   └── FASE2_COMBATE_PLAN.md        # (upcoming)
└── COMMANDS_REFERENCE.md    # User-facing command documentation
```

---

## Responsabilidades de Cada Módulo

### `mocks.py`
- **GlobalState:** `personaje_global`, `estado` initialized and ready
- **MockPersonajeReactivo:** Observer pattern dict
- **Metadata:** ARMAS_NOMBRES, ENEMIGOS_ESPECIALES, etc.
- **Mock Functions:** narrar(), alerta(), sistema() (no-ops)
- **Purpose:** Standalone - can be imported without UI

### `parser.py`
- **TesterParser Class:** Command dispatcher
- **Commands:** arma, pociones, status, inventory, help, clear, exit
- **Validation:** Against ARMAS_NOMBRES, ENEMIGOS_NOMBRES
- **Binding:** Connects Vista.on_input → procesar_comando()
- **Purpose:** Interactive command interface

### `main.py`
- **Orchestration:** Ties everything together
- **Dynamic Import:** cargar_vista_dinamicamente()
- **Global Injection:** Injects mocks.py globals BEFORE Vista runs
- **UI Setup:** Creates root, Vista, parser, runs mainloop
- **Purpose:** Entry point - `python ui_tester/main.py`

### `__init__.py`
- **Module Exports:** Exposes TesterParser, personaje_global, estado
- **Imports:** Aggregates from mocks, parser, main
- **Metadata:** Phase indicator, documentation
- **Purpose:** Makes ui_tester a proper Python package

---

## Flujo Típico de Testing

### Test 1: Agregar Arma
```
User Input: "arma espada"
    ↓
parser.procesar_comando("arma espada")
    ↓
cmd_arma("espada")
    ├─ Validate: "espada" in ARMAS_NOMBRES ✓
    ├─ Call: tldrdc_modulo.añadir_arma(personaje_global, "espada")
    │   (ORIGINAL game function - UNMODIFIED)
    │   → personaje_global["armas"] = {...}
    │   → triggers __setitem__
    │   → Vista._on_armas_cambio() executes
    │   → Button sprites update in real-time
    └─ Print: "[✓] Arma 'espada' procesada"
    
Vista User Sees: Weapon button sprite changes immediately ✓
```

### Test 2: Cambiar Pociones
```
User Input: "pociones 5"
    ↓
parser.procesar_comando("pociones 5")
    ↓
cmd_pociones("5")
    ├─ Validate: 0 <= 5 <= 10 ✓
    ├─ Set: personaje_global["pociones"] = 5
    │   → triggers __setitem__
    │   → Vista._on_pociones_cambio(5) executes
    │   → Button sprite updates to "5pociones.png"
    └─ Print: "[✓] Pociones: 5"

Vista User Sees: Potion counter sprite changes to "5pociones.png" ✓
```

### Test 3: Ver Estado
```
User Input: "status"
    ↓
parser.procesar_comando("status")
    ↓
cmd_status()
    ├─ Read: personaje_global.get("vida"), personaje_global.get("pociones"), etc.
    └─ Print: Formatted status table

Vista User Sees: Terminal output with current state ✓
```

---

## Diferencias vs Original TLDRDC_Prueba1

| Aspecto | Original | Tester |
|---------|----------|--------|
| **Punto de Entrada** | `if __name__ == "__main__": play()` | Inyectado via importlib |
| **personaje_global** | Creado en línea 4700+ | Inyectado ANTES de cargar |
| **estado dict** | Creado localmente | Inyectado como global |
| **Funciones narración** | Reales (tk.messagebox, etc) | Mocks (print) |
| **Imagen loading** | Loading full game images | Testing solo sprites necesarios |
| **Combate** | Full game loop con multithreading | (Phase 2 TODO) |

---

## Sincronización de Imágenes

**¿Cómo se cargan los sprites?**

`Vista._cargar_imgs_btns()` (línea ~5050 TLDRDC_Prueba1.py):
```python
def _cargar_imgs_btns(self):
    # Esta función SIEMPRE ejecuta al crear Vista
    # Carga almacenadas en _IMG_BTN global dict
    from modules.ui_imagen_manager import cargar_imagen
    
    # Load weapon buttons
    for arma in ARMAS_NOMBRES:
        _IMG_BTN[f"arma_{arma}"] = cargar_imagen(f"Botones/arma_{arma}.png")
    
    # Load potion sprite (0-10)
    for i in range(11):
        _IMG_BTN[f"{i}pociones"] = cargar_imagen(f"Botones/{i}pociones.png")
    
    # Launch image loading observable
    self._registrar_observadores_personaje()
```

**Inyección de _IMG_BTN:**

Como inyectamos `_IMG_BTN = {}` antes de Vista ejecución:
1. Vista.__init__() runs in TLDRDC_Prueba1
2. Calls self._cargar_imgs_btns()
3. Esto LLENA el `_IMG_BTN` global inyectado
4. Imágenes están listas en memoria

---

## Puntos de Extensión (Phases 2-3)

### Phase 2: Combate con Queue
**Archivo:** `../Phase 2 añadirá combate.py`

```python
class CombateQueue:
    """Thread-safe input queue for combate interaction."""
    
    def procesar_comando_combate(self, entrada):
        # Parse: "atacar", "defender", "huir"
        # Send to game thread
        # Receive game response
        # Update UI
```

### Phase 3: Eventos Acumulativos
**Archivo:** `../Phase 3 añadirá eventos.py`

```python
# Trigger Carcelero at eventos_superados >= 13
evento_13_trigger = estado["eventos_superados"] >= 13

if evento_13_trigger:
    cmd_combate("Carcelero")  # Jefe special
    estado["eventos_superados"] = 0  # Reset counter
```

---

## Debugging

**Para debuggear qué callbacks se registran:**
```python
# En parser.py, después de crear Vista:
print(personaje_global._observers)
# Output:
# {'armas': [<bound method Vista._on_armas_cambio>],
#  'pociones': [<bound method Vista._on_pociones_cambio>],
#  ...}
```

**Para debuggear cambios de state:**
```python
# En mocks.py MockPersonajeReactivo.__setitem__:
print(f"[OBSERVER] {key} changed to {value}")
```

**Para debuggear imports:**
```python
# En main.py cargar_vista_dinamicamente():
print(f"[DEBUG] Vista class: {Vista}")
print(f"[DEBUG] Module attributes: {dir(modulo)}")
```

---

## Archivos Originales (SIN TOCAR)

Todos estos archivos permanecen **100% intactos**:
- ✅ TLDRDC_Prueba1.py (cargado dinámicamente, no importado directo)
- ✅ modules/ (solo leídos, importados)
- ✅ code/images/ (solo images, no code)

El tester **es completamente aislado** en su carpeta `ui_tester/`.

