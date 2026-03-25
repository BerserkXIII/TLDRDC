# 🎮 Guía Completa: Sistema de Botones Tkinter

Esta guía te enseña **cómo modificar los botones** del juego sin romper nada. Nivel: Principiante en Tkinter.

---

## 📍 Tabla de Contenidos

1. [¿Dónde se definen los botones?](#1-dónde-se-definen-los-botones)
2. [Cambiar colores](#2-cambiar-colores)
3. [Cambiar formas](#3-cambiar-formas)
4. [Cambiar posición](#4-cambiar-posición)
5. [Cambiar tamaño](#5-cambiar-tamaño)
6. [Cambiar comportamiento (activo/inactivo)](#6-cambiar-comportamiento-activoinactivo)
7. [Agregar un nuevo botón](#7-agregar-un-nuevo-botón)
8. [Debugging: Qué hacer si algo sale mal](#8-debugging-qué-hacer-si-algo-sale-mal)

---

## 1. ¿Dónde se definen los botones?

### Archivos importantes:

| Archivo | Qué ContIENE | Líneas |
|---------|--------------|--------|
| `modules/ui_config.py` | Colores, formas, fuentes | 15-120 |
| `code/TLDRDC_Prueba1.py` | Clases Vista, creación de botones | 4400-5050 |

### Estructura visual:

```
TLDRDC/
├── modules/
│   └── ui_config.py         ← Configuración GLOBAL (colores, formas)
└── code/
    └── TLDRDC_Prueba1.py    ← Lógica de botones (posición, comportamiento)
```

---

## 2. Cambiar colores

### 📝 Abre: `modules/ui_config.py` (línea 15)

```python
COLORES = {
    "boton_fg":        "#cccccc",      # Texto de botones (gris claro)
    "boton_bg":        "#1a1a1a",      # Fondo INACTIVO (casi negro)
    "boton_hover":     "#3a0a0a",      # Hover: cuando pasas mouse (rojo oscuro)
    "boton_activo":    "#cc4444",      # ACTIVO disponible (rojo brillante)
    "boton_inactivo":  "#333333",      # Bloqueado (gris)
}
```

### Cómo cambiar:

**Ejemplo 1: Cambiar el color del fondo inactivo a azul**

```python
# ANTES:
"boton_bg":        "#1a1a1a",      # Negro

# DESPUÉS:
"boton_bg":        "#001a2e",      # Azul oscuro
```

**Ejemplo 2: Cambiar el color activo a verde**

```python
# ANTES:
"boton_activo":    "#cc4444",      # Rojo

# DESPUÉS:
"boton_activo":    "#44cc44",      # Verde
```

### 🎨 Referencia de colores hexadecimales:

| Color | Código | Aspecto |
|-------|--------|--------|
| Rojo brillante | `#ff0000` | Alerta, activo |
| Verde brillante | #00ff00` | Éxito, permitido |
| Azul brillante | `#0066ff` | Info, neutral |
| Amarillo brillante | `#ffff00` | Advertencia |
| Púrpura | `#9900ff` | Mágico, especial |
| Gris claro | `#cccccc` | Texto, normal |
| Gris oscuro | `#333333` | Inactivo, deshabilitado |

**Herramienta online:** Busca "color picker hex" en Google para ver colores interactivos.

---

## 3. Cambiar formas

### 📝 Abre: `modules/ui_config.py` (línea 41)

```python
FORMAS_BTN = {
    "rombo":    [(0.50, 0.04), (0.97, 0.50), (0.50, 0.96), (0.03, 0.50)],
    "hexagono": [(0.25, 0.04), (0.75, 0.04), (0.97, 0.50), 
                 (0.75, 0.96), (0.25, 0.96), (0.03, 0.50)],
    "escudo":   [(0.08, 0.04), (0.92, 0.04), (0.92, 0.58), 
                 (0.50, 0.97), (0.08, 0.58)],
    "octagono": [(0.30, 0.04), (0.70, 0.04), (0.96, 0.30), (0.96, 0.70),
                 (0.70, 0.96), (0.30, 0.96), (0.04, 0.70), (0.04, 0.30)],
    "circulo":  None,   # Especial: se dibuja como óvalo
    "rect":     None,   # Especial: se dibuja como rectángulo
}
```

### Las formas actuales disponibles:

- 🔶 **rombo** - Diamante (4 puntas)
- 🔷 **hexagono** - 6 lados (armas principales)
- 🛡️ **escudo** - Escudo (stances: bloquear)
- 🔷 **octagono** - 8 lados
- 🔵 **circulo** - Redondo (pociones, huir)
- ▭ **rect** - Rectángulo plano

### Cómo cambiar la forma de un botón:

**Ejemplo: Cambiar el botón de "Bloquear" de escudo a rombo**

Abre `code/TLDRDC_Prueba1.py` línea 4706 y busca:

```python
# ANTES:
cvs_bl = self._boton(
    self._area_botones, "🛡 Bloquear", None,
    activo=False, row=0, col=1, forma="escudo", imagen="bloquear"
)

# DESPUÉS:
cvs_bl = self._boton(
    self._area_botones, "🛡 Bloquear", None,
    activo=False, row=0, col=1, forma="rombo", imagen="bloquear"  # ← cambio aquí
)
```

---

## 4. Cambiar posición

### 🔍 Abre: `code/TLDRDC_Prueba1.py` (línea 4667)

El área de botones es una **grilla (grid) de 5 columnas x 3 filas**:

```
    COL 0    COL 1    COL 2    COL 3    COL 4
  ┌─────────┬─────────┬─────────┬─────────┬─────────┐
R │         │         │         │         │         │
O 0■ ---    │ 🛡 BL   │ ---     │ 💨 ESQ  │ ---     │  ← FILA 0 (Stances)
W │         │         │         │         │         │
  ├─────────┼─────────┼─────────┼─────────┼─────────┤
  │         │         │         │         │         │
1 │ ARMA1   │ ---     │ ARMA2   │ ---     │ ARMA3   │  ← FILA 1 (Armas)
  │         │         │         │         │         │
  ├─────────┼─────────┼─────────┼─────────┼─────────┤
  │         │         │         │         │         │
2 │ ---     │ POCIÓN  │ ---     │ HUIR    │ ---     │  ← FILA 2 (Acciones)
  │         │         │         │         │         │
  └─────────┴─────────┴─────────┴─────────┴─────────┘
```

### Parámetros de posición:

Cada botón tiene dos parámetros:
- `row=X` - Fila (0, 1, 2)
- `col=Y` - Columna (0, 1, 2, 3, 4)

### Ejemplos de cambio:

**Ejemplo 1: Mover el botón "Bloquear" de columna 1 a columna 0**

```python
# ANTES (línea 4706):
cvs_bl = self._boton(
    self._area_botones, "🛡 Bloquear", None,
    activo=False, row=0, col=1, forma="escudo", imagen="bloquear"
)

# DESPUÉS:
cvs_bl = self._boton(
    self._area_botones, "🛡 Bloquear", None,
    activo=False, row=0, col=0, forma="escudo", imagen="bloquear"  # ← col=1 → col=0
)
```

**Ejemplo 2: Intercambiar posiciones de Bloquear y Esquivar**

```python
# ANTES:
cvs_bl = self._boton(..., row=0, col=1, ...)      # Bloquear en col 1
cvs_esq = self._boton(..., row=0, col=3, ...)     # Esquivar en col 3

# DESPUÉS:
cvs_bl = self._boton(..., row=0, col=3, ...)      # Bloquear en col 3
cvs_esq = self._boton(..., row=0, col=1, ...)     # Esquivar en col 1
```

### ⚠️ Regla importante:

- **No puedes poner dos botones en la misma posición** (row=X, col=Y)
- Si haces eso, solo aparecer el último
- Las columnas pares (0, 2, 4) suelen estar vacías para dar espacio visual

---

## 5. Cambiar tamaño

### 🔍 Abre: `code/TLDRDC_Prueba1.py` (línea 4688)

Hay dos niveles de tamaño:

#### **Nivel 1: Altura del área de botones completa**

```python
# Línea 4688:
self._area_botones = tk.Frame(
    parent, bg=COLORES["fondo_panel"], height=self.BOTONES_AREA_HEIGHT
)

# El valor BOTONES_AREA_HEIGHT está en línea 4564:
BOTONES_AREA_HEIGHT = 160  # Pixel totales: 160px
```

**Cambiar altura total:**

```python
# ANTES: 160px
BOTONES_AREA_HEIGHT = 160

# DESPUÉS: 200px (más espacio)
BOTONES_AREA_HEIGHT = 200

# O: 120px (más compacto)
BOTONES_AREA_HEIGHT = 120
```

#### **Nivel 2: Altura de cada fila**

```python
# Líneas 4782:
self._area_botones.rowconfigure(0, weight=0, minsize=50)   # Fila 0: Stances (50px)
self._area_botones.rowconfigure(1, weight=1, minsize=55)   # Fila 1: Armas (55px, puede crecer)
self._area_botones.rowconfigure(2, weight=0, minsize=50)   # Fila 2: Acciones (50px)
```

**Parámetro `minsize`** = altura mínima en píxeles

**Cambiar:** Si quieres botones más grandes:

```python
# ANTES: 50, 55, 50
self._area_botones.rowconfigure(0, weight=0, minsize=50)   # Stances
self._area_botones.rowconfigure(1, weight=1, minsize=55)   # Armas
self._area_botones.rowconfigure(2, weight=0, minsize=50)   # Acciones

# DESPUÉS: Botones más grandes
self._area_botones.rowconfigure(0, weight=0, minsize=70)   # 50 → 70
self._area_botones.rowconfigure(1, weight=1, minsize=80)   # 55 → 80
self._area_botones.rowconfigure(2, weight=0, minsize=70)   # 50 → 70
```

#### **Nivel 3: Ancho de botones**

```python
# Líneas 4692-4697 (las 5 columnas):
for i in range(5):
    self._area_botones.columnconfigure(i, weight=1)
```

**Explicación:**
- `weight=1` significa que todas las columnas ocupan **igual espacio**
- Si quieres una columna más ancha que otra, aumenta su `weight`

**Ejemplo: Hacer la columna 1 el doble de ancha**

```python
# ANTES: Todas iguales (weight=1)
for i in range(5):
    self._area_botones.columnconfigure(i, weight=1)

# DESPUÉS: Columna 1 el doble
for i in range(5):
    if i == 1:
        self._area_botones.columnconfigure(i, weight=2)  # ← El doble
    else:
        self._area_botones.columnconfigure(i, weight=1)
```

---

## 6. Cambiar comportamiento (activo/inactivo)

### 🔍 Abre: `code/TLDRDC_Prueba1.py` (línea 4990)

El comportamiento de botones se controla con **dos lugares**:

#### **Lugar 1: Flag global - ¿Estamos en combate?**

```python
# Línea 4442
self._en_combate = False
```

Este flag controla TODO:
- **Si `_en_combate = False`**: Todos los botones están GRISES (inactivos)
- **Si `_en_combate = True`**: Los botones con armas/acciones se encienden (ROJO)

#### **Lugar 2: Crear un botón - ¿Es interactivo?**

Cuando creas un botón, tienes parámetro `activo`:

```python
# Línea 4706 - Botón Bloquear:
cvs_bl = self._boton(
    self._area_botones, "🛡 Bloquear", None,
    activo=False,  # ← Este parámetro
    row=0, col=1, forma="escudo", imagen="bloquear"
)
```

**`activo=False`** = Botón está deshabilitado incluso fuera de combate
**`activo=True`** = Botón está habilitado (si estamos en combate)

### Lógica visual (cómo se colorean):

```
┌─────────────────────────────────────────────┐
│ LÓGICA DE COLORES (línea 4905-4910)        │
├─────────────────────────────────────────────┤
│ IF _en_combate AND activo=True:            │
│    Color = "#cc4444" (ROJO) ← ACTIVO       │
│ ELSE:                                       │
│    Color = "#333333" (GRIS) ← INACTIVO     │
│                                             │
│ PLUS: Si pasa el mouse (hover):            │
│    Color = "#3a0a0a" (ROJO OSCURO)        │
└─────────────────────────────────────────────┘
```

### Cambiar comportamiento:

**Ejemplo 1: Hacer que el botón "Poción" esté siempre deshabilitado**

```python
# Línea 4751:
cvs_pocion = self._boton(
    self._area_botones, "Poción (0)", lambda: self._enviar_comando("p"),
    activo=False,  # ← Ya está False, perfecto
    row=2, col=1, forma="circulo", imagen="pocion"
)
```

**Ejemplo 2: Hacer que el botón "Bloquear" esté siempre ROJO (siempre activo)**

```python
# ANTES (línea 4706):
cvs_bl = self._boton(
    self._area_botones, "🛡 Bloquear", None,
    activo=False,
    row=0, col=1, forma="escudo", imagen="bloquear"
)

# DESPUÉS: activo=True
cvs_bl = self._boton(
    self._area_botones, "🛡 Bloquear", None,
    activo=True,  # ← Cambio
    row=0, col=1, forma="escudo", imagen="bloquear"
)
```

### Entender el ciclo de combate:

```
ANTES DE COMBATE:
  _en_combate = False
  ↓
  Todos los botones GRISES (sin importar activo=True/False)

INICIA COMBATE:
  actualizar_botones_combate() → _en_combate = True
  ↓
  Botones con activo=True se vuelven RJOS
  Botones con activo=False siguen GRISES

TERMINA COMBATE:
  _en_combate = False
  ↓
  Todos los botones GRISES de nuevo
```

---

## 7. Agregar un nuevo botón

### Paso 1: Definir propiedades en `ui_config.py`

Si necesitas una forma especial, agrégala:

```python
# En modules/ui_config.py, línea 56:
FORMAS_BTN = {
    # ... formas existentes ...
    "estrella": [(0.50, 0.04), (0.61, 0.35), (0.98, 0.35), (0.68, 0.57), 
                 (0.79, 0.91), (0.50, 0.70), (0.21, 0.91), (0.32, 0.57), 
                 (0.02, 0.35), (0.39, 0.35)],
}
```

### Paso 2: Crear el botón en `TLDRDC_Prueba1.py`

```python
# Línea 4760 (después de los botones existentes):
# Fila 2, Columna 4: Nuevo botón "Magia"
cvs_magia = self._boton(
    self._area_botones, "✨ Magia", lambda: self._enviar_comando("m"),
    activo=False, row=2, col=4, forma="estrella", imagen="magia"
)
self._botones_acciones['magia'] = cvs_magia
```

### Paso 3: Manejar el comando

En el método `_enviar_comando()` (busca línea ~5100), agrega:

```python
def _enviar_comando(self, cmd):
    if cmd == "m":  # Magia
        print("¡Usa magia!")
        # Aquí tu código
    elif cmd == "p":  # Poción
        # ... código existente ...
```

---

## 8. Debugging: Qué hacer si algo sale mal

### ❌ Error: "El botón no aparece"

**Causas comunes:**

1. **Posición incorrecta** - Dos botones en la misma (row, col)
   - **Solución:** Comprueba que no hay duplicados

2. **Row/col fuera de rango**
   - **Solución:** row debe ser 0-2, col debe ser 0-4

3. **Canvas muy pequeño**
   - **Solución:** Aumenta `BOTONES_AREA_HEIGHT` o el `minsize` de la fila

**Debugging:**
```python
# Agrega esto temporalmente para ver posiciones:
print(f"Botón Bloquear: row=0, col=1")
print(f"Area botones size: {self._area_botones.winfo_width()} x {self._area_botones.winfo_height()}")
```

### ❌ Error: "El botón tiene color raro"

**Causas comunes:**

1. **Color hexadecimal inválido**
   - Verifica que sea `#RRGGBB` (6 dígitos)
   - **Malo:** `#cc44` (solo 4)
   - **Bien:** `#cc4444` (6)

2. **Estamos fuera de combate**
   - Los botones siempre son GRISES si `_en_combate = False`
   - **Solución:** Inicia combate para ver los colores reales

### ❌ Error: "El botón no responde al click"

**Causas comunes:**

1. **`activo=False`** - El botón está deshabilitado
   - **Solución:** Cambia a `activo=True`

2. **No pasaste `lambda` como comando**
   - **Malo:** `self._boton(..., lambda print("Hola"))`
   - **Bien:** `self._boton(..., lambda: print("Hola"))`

3. **Estamos fuera de combate**
   - `_en_combate = False` desactiva TODOS los clicks
   - **Solución:** Inicia combate

### 📋 Checklist de debugging:

```
¿El botón aparece?
☐ row y col son 0-2 y 0-4
☐ No hay dos botones en la misma posición
☐ BOTONES_AREA_HEIGHT es suficiente

¿El botón tiene el color correcto?
☐ Color hexadecimal es #RRGGBB (6 dígitos)
☐ Estamos en combate (_en_combate = True)
☐ activo=True para que se vea ROJO

¿El botón responde al click?
☐ activo=True
☐ Comando es lambda: ... (con `:`)
☐ Estamos en combate
```

---

## 📚 Resumen rápido

| Qué quieres cambiar | Archivo | Línea | Qué editar |
|-------------------|---------|-------|-----------|
| Colores | `ui_config.py` | 15 | `COLORES = {...}` |
| Formas | `ui_config.py` | 41 | `FORMAS_BTN = {...}` |
| Posición | `TLDRDC_Prueba1.py` | 4706+ | `row=X, col=Y` |
| Tamaño fila | `TLDRDC_Prueba1.py` | 4692 | `rowconfigure(..., minsize=NNN)` |
| Tamaño total | `TLDRDC_Prueba1.py` | 4402 | `BOTONES_AREA_HEIGHT = NNN` |
| Activo/inactivo | `TLDRDC_Prueba1.py` | 4706+ | `activo=True/False` |
| Agregar botón | `TLDRDC_Prueba1.py` | 4760+ | Copiar + modificar template |

---

## 🎓 Conceptos clave aprendidos

**Tkinter es un puzzle:**
- **Canvas** = Lienzo donde dibujas formas
- **Frame** = Contenedor (como una caja)
- **Grid** = Sistema de posición (filas y columnas)
- **Bind** = Escuchar eventos (click, mouse, etc)

**Sistema de botones TLDRDC:**
- **Colores:** Definidos en `ui_config.py`, usados en lógica de renderizado
- **Formas:** Coordenadas normalizadas (0-1) que se escalan al tamaño real
- **Posición:** Grid (row, col) en área de botones 5x3
- **Comportamiento:** Controlado por `_en_combate` flag global

---

## 📞 Próximos pasos

- Le tengas dudas, documenta exactamente **qué quisiste hacer** y **qué salió mal**
- Usa el checklist de debugging
- Recuerda: **Cambia una cosa a la vez** para identificar qué rompió

¡Buen coding! 🎮

