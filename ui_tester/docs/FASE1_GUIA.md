# 🎮 UI TESTER - FASE 1 GUÍA RÁPIDA

## ¿QUÉ ES?
Interfaz gráfica idéntica a TLDRDC con parser interactivo para:
- ✅ Agregar/cambiar armas y ver sprites en tiempo real
- ✅ Cambiar pociones y ver sprite actualizar (0-10)
- ✅ Ver paneles, bordes, botones exactamente como el juego

## REQUISITOS
- Python 3.8+
- Tkinter (viene con Python)
- Módulos TLDRDC: `modules/ui_config.py`, `modules/ui_imagen_manager.py`, etc.
- Imágenes en: `code/images/Botones/` (pociones, stances, armas)

## EJECUTAR

**Opción 1: Desde terminal**
```powershell
cd c:\Users\User\Desktop\codigos\TLDRDC\code
python ui_tester.py
```

**Opción 2: Desde VS Code**
- Click derecho en `ui_tester.py` → "Run Python File"
- O presiona F5 (si está configurado)

## INTERFAZ

```
┌───────────────────────────┬──────────────────┐
│                           │                  │
│   PANEL TEXTO (aquí       │   PANEL IMAGEN   │
│   aparecen logs del       │   (decorativa)   │
│   parser y eventos)       │                  │
│                           │                  │
├───────────────────────────┼──────────────────┤
│ PARSER (input) →          │ STATS + BOTONES  │
│ Escribe comandos          │ Actualizan en    │
│ (arma daga,               │ tiempo real      │
│  pociones 5, etc)         │                  │
└───────────────────────────┴──────────────────┘
```

## COMANDOS DISPONIBLES

### Agregar Armas
```
arma daga           → Agrega una daga
arma espada         → Agrega una espada  
arma martillo       → Agrega un martillo
arma "Mano de Dios" → Armas largas con comillas
```

**Nombres válidos (uno a la vez):**
- daga, espada, martillo, porra, maza, lanza
- estoque, cimitarra, Mano de Dios, Hoz de Sangre
- Hoja de la Noche, Hacha Ritual

**Abreviaturas (más rápidas):**
- `arma dag` → daga
- `arma esp` → espada
- `arma lan` → lanza
- etc. (ver TESTER_COMMANDS_REFERENCE.md)

### Cambiar Pociones
```
pociones 0    → 0 pociones (sprite vacío)
pociones 5    → 5 pociones (sprite medio)
pociones 10   → 10 pociones (sprite lleno)
```

### Ver Estado
```
status      → Muestra vida, armas, pociones actuales
inventory   → Lista solo las armas
help        → Muestra esta ayuda
clear       → Limpia el panel de texto
exit        → Cerrar tester
```

## QUÉ VAS A VER

### Cuando ejecutes por primera vez:
1. ✅ Ventana de Tkinter abre (pantalla completa)
2. ✅ 4 paneles: Texto (arriba-izquierda), Imagen (arriba-derecha), Parser (abajo-izquierda), Botones (abajo-derecha)
3. ✅ Panel de texto muestra logs de inicialización
4. ✅ Botones visibles pero inactivos
5. ✅ Cursor en parser

### Cuando escribas "arma daga":
1. ✅ Se ejecuta `añadir_arma()` del juego ORIGINAL
2. ✅ `personaje_global["armas"]` se actualiza
3. ✅ Observador se dispara automáticamente
4. ✅ Botón de arma se actualiza con SPRITE
5. ✅ Sprite "daga" aparece en botón 1

### Cuando cambies pociones a 5:
1. ✅ `personaje_global["pociones"]` → 5
2. ✅ Observador `_on_pociones_cambio()` se dispara
3. ✅ Sprite de botón de pociones cambia a "5pociones.png"

## LIMITACIONES FASE 1

❌ **NO FUNCIONA AÚN:**
- Combates (Fase 2)
- Eventos (Fase 3)
- Botones interactivos (necesitan combate activo)
- Stances (necesitan combate)
- Sonidos (Fase 3)

✅ **SÍ FUNCIONA:**
- Carga y render de imágenes
- Actualización reactiva de sprites
- Layout y paneles idénticos
- Parser simple

## DEBUGGING

Si algo falla, mira la consola (PowerShell/Terminal) para ver los mensajes:
```
[✓] Módulos UI cargados correctamente
[✓] TLDRDC_Prueba1.py cargado dinámicamente
[✓] Vista cargada correctamente
[✓] Tester listo

[*] Inicializando parser...
```

## PRÓXIMAS FASES

**Fase 2 (Combate con Queue):**
```
combate goblin      → Inicia combate vs Goblin
[Durante combate]
d                   → Ataca
p                   → Usa poción
esq                 → Esquiva
bl                  → Bloquea
h                   → Intenta huir
```

**Fase 3 (Eventos):**
```
evento 5            → Ejecuta evento 5
evento random       → Evento aleatorio
```

---

## TIPS

1. **Inventario máximo:** 3 armas. Si intentas agregar una 4ª, se pide descartar.
2. **Nombres exactos:** "Mano de Dios" ≠ "mano de dios" (aunque funciona sin importar mayúsculas)
3. **Sin combate:** Los botones de arma no son clicables (por eso estate atento a los sprites)
4. **Logs:** Todo lo que pasa aparece en el panel de texto (narrar, sistema, etc.)

---

## REPORTE DE BUGS

Si encuentras problemas, copia el error de la consola y abre un issue.

**Contacto:** Ver ARCHITECTURE.md para detalles del sistema
