# 🏗️ Arquitectura de TLDRDC

Documento técnico explicando decisiones de diseño, patrones, y estructura del proyecto.

---

## 📋 Contenido

- [Visión General](#visión-general)
- [Arquitectura 0.1.0 (Monolítica)](#arquitectura-010-monolítica)
- [Arquitectura 0.2.0 (Modularizada)](#arquitectura-020-modularizada)
- [Patrones de Diseño](#patrones-de-diseño)
- [Sistema de Eventos](#sistema-de-eventos)
- [Decisiones Clave](#decisiones-clave)
- [Cómo Extender](#cómo-extender)

---

## Visión General

TLDRDC es un **Roguelike Textual con GUI experimental**:
- Basado en **turnos**
- Generación **procedimental** de eventos
- Narrativa **emergente** (el jugador descubre la historia)
- Código **modular** desde v0.2.0

**Stack Técnico**:
```
┌─────────────────────────────────┐
│      TLDRDC_Prueba1.py          │  (Main: UI, Combat, Flow)
│         ~5,500 líneas           │
└──────────────┬──────────────────┘
               │
      ┌────────┴────────┐
      │                 │
┌─────▼──────┐   ┌─────▼──────────┐
│ modules/   │   │ modules/ui_*.py │
│ events.py  │   │                 │
│ 1,336 líneas   │ Layout, Config  │
└────────────┘   └─────────────────┘
```

---

## Arquitectura 0.1.0 (Monolítica)

### Descripción

**Archivo único**: `TLDRDC.py` (~6,800 líneas)

Todo en un solo archivo:
- ✅ Fácil empezar
- ✅ No hay imports complejos
- ❌ Difícil de mantener
- ❌ Difícil de debuggear
- ❌ Imposible encontrar código
- ❌ 1,338 líneas de eventos duplicados

### Estructura (Conceptual)

```
Imports (0-100)
│
Functions: UI Setup (100-500)
  - Crear ventanas
  - Configurar layout
  - Event bindings
│
Functions: Combat System (500-1,000)
  - Calcular daño
  - Checar muerte
│
Functions: Events (1,000-5,000)
  - evento_1()
  - evento_2()
  - ... evento_20()
  - _evento_1()  ← DUPLICADOS
  - _evento_2()
  - ... _evento_20()
│
Main Game Loop (5,000-6,800)
  - Inicializar personaje
  - Main loop
  - Evento aleatorio
```

### Problema: Duplicación

**20 eventos aparecían 2 veces cada uno**:

```python
# Línea ~1,000
def evento_1(personaje):
    personaje.hp -= 5
    return "¡Te duele!"

# Línea ~3,000 (DUPLICADO INNECESARIO)
def _evento_1(personaje):
    personaje.hp -= 5
    return "¡Te duele!"
```

**Por qué**: Probablemente refactorización parcial o versioning mal hecho.
**Impacto**: +1,338 líneas de código basura, confusión, mantenimiento imposible.

---

## Arquitectura 0.2.0 (Modularizada)

### Decisión: Externalizar Eventos

**Objetivo**: Separar lógica de eventos de la lógica principal.

**Beneficios**:
- ✅ Archivo principal enfocado (~5,500 líneas)
- ✅ Eventos como módulo dedicado (~1,336 líneas)
- ✅ Fácil agregar eventos nuevos
- ✅ Mantenimiento más sencillo

### Estructura Nueva

```
c:\Users\User\Desktop\codigos\TLDRDC\
│
├── TLDRDC_Prueba1.py           ← MAIN FILE (~5,500 líneas)
│   ├── Imports (líneas 1-40)
│   ├── UI Setup (líneas 41-500)
│   ├── Game Logic (líneas 500-5,300)
│   ├── Inyección Dependencias (línea 5,546) ← CLAVE
│   └── Main Loop (líneas 5,550-5,700)
│
├── modules/
│   ├── __init__.py              ← Marker de paquete
│   │
│   ├── events.py                ← EVENTS MODULE (~1,336 líneas)
│   │   ├── Imports (líneas 1-10)
│   │   ├── Dependencias inyectadas (líneas 11-30)
│   │   │   evento_aleatorio = None  ← Set por main file
│   │   │   aplicar_evento = None
│   │   │
│   │   ├── Core Functions (líneas 31-100)
│   │   │   rellenar_bolsa_eventos()
│   │   │   obtener_evento_de_bolsa()
│   │   │
│   │   ├── Eventos Actual (líneas 100-900)
│   │   │   _evento_1() through _evento_20()
│   │   │
│   │   └── Event Registry (línea 900-950)
│   │       _EVENTOS = {1: _evento_1, 2: _evento_2, ...}
│   │
│   ├── ui_config.py             ← UI CONFIGURATION
│   │   ├── Colores
│   │   ├── Dimensiones ventana
│   │   └── Fuentes
│   │
│   ├── ui_estructura.py         ← LAYOUT
│   │   ├── Crear widgets
│   │   └── Posicionar elementos
│   │
│   └── ui_imagen_manager.py     ← IMAGE LOADING
│       └── Cargar y cachear imágenes
│
├── TLDRDC_Prueba1_backup.py    ← BACKUP (v0.1.0 monolítica)
│
├── VERSION ESTABLE/            ← Versiones previas
│   └── TLDRDC_BUENA.py
│
├── .gitignore                  ← Git configuration
├── README.md                   ← Project intro
├── CHANGELOG.md                ← Version history
├── requirements.txt            ← Dependencies
├── LICENSE                     ← MIT License
│
└── docs/
    ├── CONTRIBUYIENDO.md       ← Contribution guide
    ├── ARQUITECTURA.md         ← THIS FILE
    ├── CREDITOS.md            ← Credits
    └── backups/               ← Future backup folder
```

### Ventajas de Estructura Modular

| Aspecto | v0.1.0 | v0.2.0 |
|--------|--------|--------|
| **Main file** | 6,800 líneas | 5,500 líneas |
| **Eventos** | Mezclados | Módulo dedicado |
| **Agregar evento** | Editar main | Editar events.py |
| **Debuggear evento** | Buscar en 6,800 líneas | Buscar en 1,336 líneas |
| **Entender flow** | Muy confuso | Claro |
| **Duplicación** | 1,338 líneas extra | ✅ Eliminada |

---

## Patrones de Diseño

### 1. Inyección de Dependencias (Dependency Injection)

**Problema en v0.1.0**:
```
eventos.py necesita usar evento_aleatorio()
pero evento_aleatorio() está en TLDRDC_Prueba1.py
TLDRDC_Prueba1.py importa eventos.py
↓
IMPORT CIRCULAR ❌
```

**Solución en v0.2.0: Late Binding**

```python
# modules/events.py (líneas 15-25)
evento_aleatorio = None  # Placeholder
aplicar_evento = None

# Luego, en línea 5,546 de TLDRDC_Prueba1.py:
from modules import events

# Inyectar funciones DESPUÉS de definirlas
events.evento_aleatorio = evento_aleatorio
events.aplicar_evento = aplicar_evento
```

**Beneficio**: Evita import circular, permite separación limpia.

**Cuando se hace**:
```
TLDRDC_Prueba1.py timeline:
1. Línea 1-40: Imports
2. Línea 41-5,500: Definir TODAS las funciones
3. Línea 5,546: ← AQUÍ se inyectan dependencias
4. Línea 5,550+: Main loop inicia
```

### 2. Fisher-Yates Shuffle (Bolsa de Eventos)

**Objetivo**: Cada evento toma turno, sin repeticiones hasta nuevo ciclo

```python
# modules/events.py - rellenar_bolsa_eventos()
def rellenar_bolsa_eventos():
    """Llenar bolsa con eventos 1-20 en orden aleatorio"""
    global _bolsa_eventos
    eventos = list(range(1, 21))
    random.shuffle(eventos)  # ← Fisher-Yates integrado
    _bolsa_eventos = eventos

# Obtener siguiente evento (auto-refill)
def obtener_evento_de_bolsa():
    global _bolsa_eventos
    if not _bolsa_eventos:
        rellenar_bolsa_eventos()
    return _bolsa_eventos.pop()
```

**Ventaja sobre `.choice()`**:
```
random.choice(range(1, 21))  ← Posible duplicado
vs
bolsa_eventos               ← Garantizado NO duplicado
```

### 3. Registry Pattern (Event Mapping)

```python
# modules/events.py - línea 900-950
_EVENTOS = {
    1:  _evento_1,
    2:  _evento_2,
    3:  _evento_3,
    # ...
    20: _evento_20,
}

# Uso:
numero_evento = 5
funcion_evento = _EVENTOS[numero_evento]
resultado = funcion_evento(personaje)
```

**Ventaja**: Fácil de ampliar, lookups rápidos.

---

## Sistema de Eventos

### Flujo de Eventos

```
┌──────────────────┐
│ Main Loop        │
│ (cada turno)     │
└────────┬─────────┘
         │
         ▼
   evento_aleatorio()  ← Obtiene número (1-20)
         │
         ▼
   obtener_evento_de_bolsa()  ← Popup bolsa
         │
         ▼
   _EVENTOS[numero]()  ← Llama función
         │
         ▼
   Modifica personaje  ← HP, stats, etc
         │
         ▼
   aplicar_evento()  ← Aplica cambios a UI
         │
         ▼
   Regresa a Main Loop
```

### Anatomía de un Evento

```python
# modules/events.py - ejemplo
def _evento_5(personaje):
    """
    Evento 5: Encuentras una poción dañada
    Probabilidad 50% de curación, 50% envenenamiento
    """
    if random.random() < 0.5:
        # Suerte
        healing = random.randint(10, 20)
        personaje.hp = min(personaje.hp + healing, personaje.max_hp)
        evento_aleatorio()  # Log o registrar
        return f"¡Poción efectiva! +{healing} HP"
    else:
        # Mala suerte
        damage = random.randint(5, 15)
        personaje.hp -= damage
        return f"¡Poción envenenada! -{damage} HP"
```

### Cómo Agregar Evento Nuevo

**Paso 1**: Editar `modules/events.py`

```python
# Agregar antes del diccionario _EVENTOS
def _evento_21(personaje):
    """Evento 21: Tu evento nuevo aquí"""
    # Tu lógica
    return "Tu mensaje"

# Paso 2: Registrar en diccionario
_EVENTOS = {
    1:  _evento_1,
    # ... todos los otros ...
    20: _evento_20,
    21: _evento_21,  ← NUEVO
}

# Paso 3: Actualizar rango de bolsa
def rellenar_bolsa_eventos():
    eventos = list(range(1, 22))  ← Cambiar 21 de 20
    random.shuffle(eventos)
    _bolsa_eventos = eventos
```

---

## Decisiones Clave

### ¿Por qué Tkinter?

**Pros**:
- ✅ Incluido en Python (sin dependencias)
- ✅ Multiplataforma
- ✅ Simple para UIs básicas

**Contras**:
- ❌ Styling limitado
- ❌ Moderno pero no espectacular

**Alternativas consideradas**:
- PyQt5 (demasiado pesado para prototipo)
- Pygame (más para juegos, menos para GUI)
- Web (Flask + HTML) fue descartado por simplicidad

### ¿Por qué Modularizar en v0.2.0?

**Triggers**:
1. ❌ Código llegó a 6,800 líneas (insostenible)
2. ❌ 1,338 líneas eran duplicadas (evento_X vs _evento_X)
3. ❌ Imposible encontrar código específico
4. ✅ Oportunidad de aprender arquitectura

**Proceso real**:
1. Extrayeron 20 funciones evento_X y _evento_X
2. Se creó `modules/events.py` con compilación limpia
3. Se movió inyección de dependencias (línea 735 → 5,546)
4. Se arreglaron 16 errores de imports
5. Se verificó que todo funcione

**Resultado**: Código más mantenible, 22% más pequeño, más profesional.

---

## Cómo Extender

### Agregar UI Nueva

1. **Crear archivo en `modules/`**:
```python
# modules/ui_nuevo.py
def crear_nuevo_panel(parent_window):
    panel = tk.Frame(parent_window)
    # Tu código aquí
    return panel
```

2. **Importar en main**:
```python
from modules.ui_nuevo import crear_nuevo_panel
```

3. **Usar en main**:
```python
mi_panel = crear_nuevo_panel(ventana_principal)
```

### Agregar Sistema Nuevo

**Opción 1: Módulo simple**
```
modules/sistema_nuevo.py ← Si es pequeño (<300 líneas)
```

**Opción 2: Paquete**
```
modules/
├── sistema/
│   ├── __init__.py
│   ├── core.py
│   └── utils.py
```

### Considerar Antes de Cambiar

- ❓ ¿Esto romperá imports existentes?
- ❓ ¿Necesita inyección de dependencias?
- ❓ ¿Hay imports circulares posibles?
- ❓ ¿Debo actualizar documentation?

---

## Evolución Futura

### Ideas para v0.3.0

- [ ] Persistencia (guardar progreso)
- [ ] Más eventos (actualmente 20)
- [ ] Sistema de items
- [ ] Mapa procedimental
- [ ] Enemigos diferentes

### Refactorización Técnica Deseada

- [ ] Type hints completos
- [ ] Unit tests
- [ ] Configuración externa (JSON/YAML)
- [ ] Logging structured
- [ ] Performance profiling

---

## Referencias

**Patrones Aplicados**:
- Dependency Injection: https://martinfowler.com/articles/injection.html
- Registry Pattern: https://refactoring.guru/design-patterns/prototype
- Fisher-Yates: https://en.wikipedia.org/wiki/Fisher%E2%80%93Yates_shuffle

**Python Best Practices**:
- PEP 8 Style Guide: https://pep8.org/
- The Twelve-Factor App: https://12factor.net/

---

<div align="center">

## 📚 ¿Preguntas sobre la arquitectura?

Consulta [CONTRIBUYIENDO.md](./CONTRIBUYIENDO.md) para reportar issues
o [README.md](../README.md) para el overview.

</div>

---

**Última actualización**: 18 de Marzo de 2026
**Estado**: Completa para v0.2.0
