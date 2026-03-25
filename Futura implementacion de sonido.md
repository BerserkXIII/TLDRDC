# Plan de Implementación: Sistema de Audio (v0.3)

## 1. Resumen Ejecutivo

Integración de **pygame.mixer** para reproducción de:
- **Música ambiental** (temas, cambios con crossfade)
- **Efectos de sonido** (SFX: golpes, gritos, goteos, etc.)

**Scope:** Mínimo, no-invasivo, sin problemas de threading.

---

## 2. Arquitectura

### Punto Clave: Sin Threading Problems

```
Game Logic Thread        Main Thread (Tkinter)
  ↓                           ↓
emitir("narrar", {    →  procesar_mensaje()
  "texto": "...",     →    ↓
  "tema": "combate"   →    audio.reproducir_tema()
})                    →    pygame.mixer (main thread, seguro)
```

**Pygame mixer maneja dos canales independientes:**
- `pygame.mixer.music` → Música de fondo (apenas toca)
- `pygame.mixer.Sound` → Efectos (capa superior)

---

## 3. Archivos a Crear/Modificar

### 3.1 Crear: `modules/ui_sonido.py`

Módulo gestor de audio con:
- `GestorAudio` class
- `reproducir_tema(nombre_tema)` → Crossfade 1s
- `reproducir_sfx(nombre_sfx, volumen=1.0)` → Efecto inmediato
- `detener()` → Fade out 500ms

### 3.2 Modificar: `modules/ui_config.py`

Agregar diccionario de temas:

```python
TEMAS_AUDIO = {
    "exploración": "ambiente_mazmorra",
    "combate": "combate_generico",
    "boss_carcelero": "boss_carcelero_forrix",
    "boss_cirujano": "boss_cirujano_fabius",
    "boss_sombra": "boss_sombra_sangrienta",
    "final": "boss_bel_akhor",
    "evento_lore": "lore_revelation",
    "derrota": "derrota_final",
    "victoria": "victoria_final",
    "menu": "menu_principal",
}
```

### 3.3 Modificar: `TLDRDC_Prueba1.py` (Vista.procesar_mensaje)

Agregar lógica para detectar y reproducir tema:

```python
def procesar_mensaje(self, msg):
    tipo = msg["tipo"]
    contenido = msg["contenido"]
    
    # ← NUEVO: Extraer tema si viene en el contenido
    tema_sonoro = None
    if isinstance(contenido, dict):
        tema_sonoro = contenido.pop("tema", None)
        if tema_sonoro and tema_sonoro in TEMAS_AUDIO:
            from modules.ui_sonido import audio
            audio.reproducir_tema(TEMAS_AUDIO[tema_sonoro])
    
    # Rest of procesar_mensaje stays the same...
```

---

## 4. Estructura de Carpetas

```
TLDRDC/
├── Sonido/                           ← NUEVA CARPETA
│   ├── ambiente_mazmorra.ogg         (3-5 MB, loop)
│   ├── combate_generico.ogg          (loop)
│   ├── boss_carcelero_forrix.ogg     (loop)
│   ├── boss_cirujano_fabius.ogg      (loop)
│   ├── boss_sombra_sangrienta.ogg    (loop)
│   ├── boss_bel_akhor.ogg            (final boss)
│   ├── lore_revelation.ogg           (misterioso)
│   ├── derrota_final.ogg             (ending)
│   ├── victoria_final.ogg            (ending)
│   ├── menu_principal.ogg            (menú)
│   ├── sfx_golpe_critico.ogg         (corto)
│   ├── sfx_goteo_agua.ogg            (loop corto)
│   ├── sfx_grito_enemigo.ogg         (variable)
│   └── ... más SFX según sea necesario
│
├── modules/
│   ├── ui_sonido.py                  ← NUEVO
│   ├── ui_config.py                  ← MODIFICADO
│   └── ...
├── code/
│   └── TLDRDC_Prueba1.py             ← MODIFICADO
└── Futura implementacion de sonido.md
```

---

## 5. Plan de Implementación Paso a Paso

### Fase 1: Infraestructura Base (1-2 horas)
1. Crear `modules/ui_sonido.py` con clase `GestorAudio`
2. Agregar `TEMAS_AUDIO` a `ui_config.py`
3. Modificar `procesar_mensaje()` en Vista
4. Crear carpeta `Sonido/` vacía
5. **Testear sin archivos:** Debe no fallar si los audios no existen

### Fase 2: Audio Assets (variable)
6. Obtener/crear 10-11 temas ambientales (`.ogg`)
7. Obtener/crear 3-5 SFX iniciales
8. Verificar duración y formatos

### Fase 3: Integración en Juego (1-2 horas)
9. Agregar `"tema": "exploración"` en `celda_inicial()`
10. Agregar triggers en combate (`turno_enemigo`, `turno_jugador`)
11. Agregar SFX aleatorios en exploración (`_explorar_paso`)
12. Testear crossfade entre temas

### Fase 4: Pulido (30 min)
13. Ajustar volúmenes (música 0.6, SFX 0.8)
14. Verificar que los finales tengan audio especial
15. Documentar decisiones en `LECCIONES_APRENDIDAS.md`

---

## 6. Ejemplos de Uso en Código Actual

### 6.1 En Combate (turno_enemigo)

```python
def turno_enemigo(personaje, enemigo, stance=None):
    # Primera emitida debería cambiar tema
    emitir("narrar", {
        "texto": f"¡Te enfrentas a {enemigo['nombre']}!",
        "tema": "combate"  # ← Dispara cambio de música
    })
    
    # SFX en daño
    if daño_final > 10:
        from modules.ui_sonido import audio
        audio.reproducir_sfx("golpe_critico", volumen=0.8)
```

### 6.2 En Exploración (aleatorio)

```python
def _explorar_paso(personaje):
    # Random ambient SFX durante exploración
    if random.random() < 0.05:  # 5% por paso
        from modules.ui_sonido import audio
        audio.reproducir_sfx("goteo_agua", volumen=0.4)
    
    # Rest of logic...
```

### 6.3 Encounters Especiales

```python
def crear_carcelero():
    emitir("narrar", {
        "texto": "Una sombra se alza ante ti. El Carcelero.",
        "tema": "boss_carcelero"  # ← Boss theme
    })
    # ...
```

---

## 7. Detalles Técnicos

### Crossfade
```python
pygame.mixer.music.fadeout(1000)  # 1 segundo
pygame.mixer.music.load(ruta)
pygame.mixer.music.set_volume(0.6)
pygame.mixer.music.play(-1)  # -1 = loop infinito
```

### SFX (No hay crossfade)
```python
sonido = pygame.mixer.Sound(ruta)
sonido.set_volume(0.8)
sonido.play()  # Play once
```

### Thread Safety
- ✅ Todo corre en main thread (Tkinter event loop)
- ✅ Pygame mixer es thread-safe en el mismo thread
- ✅ Game logic solo **emite mensajes**, no toca audio

---

## 8. Dependencias

```
pygame >= 2.0
```

**Instalación:**
```bash
pip install pygame
```

Si falla: usuario puede agregar `AUDIO_DISPONIBLE = False` en ui_sonido.py y seguir jugando sin audio.

---

## 9. Volúmenes Recomendados

| Elemento | Volumen | Razón |
|----------|---------|-------|
| Música | 0.6 | No abrumar el diálogo |
| SFX Combate | 0.7-0.9 | Impactantes pero claros |
| SFX Ambiente | 0.3-0.5 | De fondo, sutiles |
| SFX Crítico | 1.0 | Debe sonar intenso |

---

## 10. Características Avanzadas (v0.4+)

### Capas Dinámicas
```python
# Música combate + intensidad según HP
base_theme = "combate"
if hp_enemy < 25:
    audio.reproducir_tema("combate_intenso")
```

### Sistema de Eventos Sonoros
```python
emitir("sfx", "golpe_critico")
```

### Mute/Volume Settings
```python
audio.set_master_volume(0.5)  # Global
audio.set_music_volume(0.3)
audio.set_sfx_volume(0.8)
```

---

## 11. Testing Checklist

- [ ] Pygame importa sin errores
- [ ] Mixer se inicializa sin fallar
- [ ] Archivos de audio no encontrados → no crashea
- [ ] Crossfade funciona suavemente
- [ ] SFX se reproducen sobre música
- [ ] Temas cambian al entrar en combate
- [ ] Menu_principal tiene música
- [ ] Finales tienen temas diferentes
- [ ] Volúmenes son audibles sin lastimar

---

## 12. Git Commit Message

```
v0.3: Add audio system infrastructure (no implementation yet)

- Create modules/ui_sonido.py with GestorAudio class
- Define TEMAS_AUDIO mapping in ui_config
- Hook procesar_mensaje() to detect theme triggers
- Document full implementation plan in MD

Assets are placeholders; full audio integration in next phase.
```

---

## Referencias

- **pygame.mixer docs:** https://www.pygame.org/docs/ref/mixer.html
- **OGG format:** Ligero, licencia libre, ideal para juegos
- **Crossfade pattern:** Fadeout + load + play
