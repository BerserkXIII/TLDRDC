# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
y este proyecto sigue [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Este es un proyecto de aprendizaje a traves de IA, por lo que puede contener errores. Agradezco cualquier sugerencia o reporte de errores :) 

---

## [0.2.1] - 2026-03-25

### 🎯 Tema: UI Refinement y Sistema de Stances Corregido

Rework visual completo del sistema de botones y fix crítico en la sincronización de las stances (bloquear/esquivar). El sistema ahora es completamente estable y juega sin errores visuales.

### ✨ Added
- **Documentación Actualizada**:
  - [GUIA_BOTONES.md](docs/GUIA_BOTONES.md) - **ACTUALIZADA**: Información sobre sistema de stances y toggles
  - [LECCIONES_APRENDIDAS.md](docs/LECCIONES_APRENDIDAS.md) - **ACTUALIZADA**: Lección 11 sobre bugs de sincronización botón-estado

### 🎨 Changed
- **UI/Visual Rework**: Rework completo de botones y elementos visuales
  - Mejora en respuesta visual de botones
  - Optimización de redibujado (menos parpadeos)
  - Mejor feedback visual en cambios de estado

### 🐛 Fixed (Sistema de Stances - 25 de Marzo)

#### Bug 1: Doble Procesamiento (Líneas 4883-4897)
- **Problema**: Click en botón llamaba `_enviar_comando()` que inyectaba el comando en el parser y lo procesaba
- **Resultado**: El botón alternaba DOS VECES (una vez en click, otra en parser) → estado final incorrecto
- **Síntoma**: Click "bl" no se mantenía, alternancia inconsistente entre click y parser
- **Solución**: Cambiar `_select_stance()` para usar alternancia consistente CON parser, sin `_enviar_comando()`
  ```python
  # ANTES: era SET simple + _enviar_comando
  # AHORA: ALTERNANCIA igual que parser + on_input()
  if self._toggle_state.get('activa') == cual:
      self._toggle_state['activa'] = None
  else:
      self._toggle_state['activa'] = cual
  ```
- **Alcance**: Clicks y parser ahora completamente sincronizados ✅

#### Bug 2: Desincronización de Formatos (Líneas 5188-5201)
- **Problema**: UI usa `"bl"` / `"esq"`, pero juego usa `"bloquear"` / `"esquivar"`
- **Resultado**: Botón parpadeaba en primera activación (se enciende, luego se apaga)
- **Síntoma**: `_toggle_state['activa'] = "bloquear"` pero `_actualizar_stances_visual()` busca `activa == 'bl'` → no encuentra → botón APAGADO
- **Solución**: Normalizar formato en `actualizar_botones_combate()`
  ```python
  stance_normalizado = {
      "bloquear": "bl",
      "esquivar": "esq"
  }.get(stance, stance)
  self._toggle_state['activa'] = stance_normalizado
  ```
- **Alcance**: Estado visual consistente con estado lógico ✅

#### Bug 3: Botón No Se Apagaba Post-Turno (Líneas 5188-5201)
- **Problema**: Después de atacar, la stance se desactivaba (state=None) pero el botón permanecía encendido
- **Causa**: En `actualizar_botones_combate()`, si `stance is None` no hacía nada → `_toggle_state['activa']` guardaba "bl" del turno anterior
- **Síntoma**: Siguiente turno comienza con botón encendido pero stance NULL → visual ≠ lógico
- **Solución**: Agregar `else` explícito
  ```python
  if stance is not None:
      # ... normalizar
  else:
      self._toggle_state['activa'] = None  # ← Reset cuando stance=None
  self._actualizar_stances_visual()
  ```
- **Alcance**: Botones se apagan correctamente al final de turno ✅

#### Resultado Final
Sistema de stances completamente funcional:
- ✅ Click enciende/apaga botón consistentemente
- ✅ Parser y clicks tienen mismo comportamiento  
- ✅ Estado visual siempre sincronizado con estado lógico
- ✅ Botón se apaga al final de turno
- ✅ Formato de datos centralizado

---

## [0.2.0] - 2026-03-22

### 🎯 Tema: Modularización, Refactorización y Profesionalización

Un cambio arquitectónico importante: el sistema de eventos ha sido extraído del archivo principal a un módulo separado. Esto reduce la complejidad, mejora la mantenibilidad y sienta las bases para futuras expansiones. Se añade enfoque fuerte en documentación, trasparencia y profesionalismo del proyecto.

### ✨ Added
- **Módulo `modules/events.py`**: Sistema de eventos completamente modularizado
  - 20 funciones de eventos (`_evento_1` a `_evento_20`)
  - Tabla de distribución `_EVENTOS`
  - Sistema de bolsa de eventos mejorado
  - Inyección de dependencias para evitar imports circulares

- **Documentación Técnica**:
  - [ARQUITECTURA.md](docs/ARQUITECTURA.md) - Creada por IA, modificada y revisada por usuario
    - [+] Sección de Threading (Doble Hilo): Explicación completa con diagramas, flujos, componentes y limitaciones
    - [+] Tabla de Contenidos: Actualizada para incluir nueva sección
  - [CONTRIBUYIENDO.md](docs/CONTRIBUYIENDO.md) - Creada por IA (reescrita por IA con dirección del usuario, ahora de tono honesto y auténtico)
  - [CREDITOS.md](docs/CREDITOS.md) - Creada por IA, documentando el viaje completo incluyendo asistencia de IA
  - [LECCIONES_APRENDIDAS.md](docs/LECCIONES_APRENDIDAS.md) - **NUEVO**: 10 lecciones técnicas y de comunicación del desarrollo
    - Reflexiones sobre arquitectura, threading, documentación
    - Insights sobre testing manual y herramientas
    - Plan de mejora para v0.3.0

- **Mejoras de Navegación**:
  - [README.md](README.md) - Sección de documentación reformatada con tabla clara de referencias
  - [README.md](README.md) - **NUEVO**: 4 badges de estado (Python 3.10+, MIT License, v0.2.0, Multiplataforma)

- **Git Setup**:
  - `.gitignore` - Ignorar archivos innecesarios
  - Primer commit documentation

- **Mejoras Profesionales** (22 de Marzo):
  - `.gitignore` - **EXPANDIDO**: Agregados 20+ patrones profesionales Python
    - Database: *.db, *.sqlite, *.sqlite3
    - Environment: .env, .env.local, .env.*.local, .venv/
    - System: Thumbs.db, .DS_Store, ehthumbs.db
    - Test/Build: htmlcov/, .pytest_cache/, .mypy_cache/, dist/, build/, *.egg-info/
    - Project temp: temp/, tmp/, logs/, debug_output/
  - README badges - **AÑADIDOS**: 4 shields.io que indican estado rápidamente

### 🔄 Changed
- **TLDRDC_Prueba1.py**: Reducción de 6,800+ líneas a 5,500+ líneas (~22% reduction)
  - **Migración print → Tkinter UI**: Realizada por IA (Claude Haiku-70% del código) bajo guía y dirección del usuario
  - Sistema refactorizado para usar interfaz gráfica en lugar de terminal
- **Imports**: Actualizados a usar `modules.ui_*` en lugar de `ui_*`
- **Inyección de Dependencias**: Colocada más tarde en ejecución (línea 5546) para evitar undefined values

### 🐛 Fixed (Modularización - 21 de Marzo)
- **reportmissingimports** (3 errores en líneas 16-18):
  - `from modules.ui_config import` ✅
  - `from modules.ui_imagen_manager import` ✅
  - `from modules.ui_estructura import` ✅

- **reportundefinedvalue** (13 errores en líneas 733-746):
  - Movida inyección de dependencias a punto de ejecución seguro ✅
  - Todas las funciones ahora definidas antes de inyección ✅

### 🐛 Fixed (Bug Crítico de Imports - 22 de Marzo, PM)
- **KeyError: 'fondo'** - Sistema de imports completamente roto
  - **Problema**: `sys.path.insert()` estaba configurado DESPUÉS de los imports de módulos
  - **Causa**: Python no podía encontrar la carpeta `modules/` ejecutando desde cualquier directorio
  - **Síntoma**: `COLORES`, `RUTAS_IMAGENES_PANELES`, etc. nunca se cargaban → KeyError en Vista.__init__
  - **Solución**: Mover configuración de paths al inicio del archivo (línea 13-17)
    - Cálculo de raíz del proyecto: `os.path.dirname(os.path.dirname(os.path.abspath(__file__)))`
    - `sys.path.insert(0, _proyecto_root)` ANTES de importar módulos locales
  - **Alcance**: 0 nuevos bugs (solo reordenamiento de código existente)
  - **Resultado**: ✅ Juego inicia correctamente desde cualquier ubicación

### 📋 Documentation & Polish (22 de Marzo)
- `.gitignore` - Expandida cobertura de patrones (40 → 60+ patterns)
- `README.md` - Agregados badges de estado para visibilidad rápida
- `LECCIONES_APRENDIDAS.md` - 10 insights clave del desarrollo para futuros proyectos

### 🗑️ Removed
- Código duplicado de eventos (1,338 líneas eliminadas)
- `clean_events.py` - Script temporal de limpieza
- `debug_reports/` - Carpeta vacía

### ⚠️ Deprecated
- Estructura monolítica previa (fue reemplazada, no uses más)

### 🔒 Security
- Ningún cambio de seguridad en esta versión

### 📊 Estadísticas
- **Cambios totales**: ~1,400 líneas (eliminadas/refactorizadas)
- **Tiempo de trabajo**: ~8 horas
- **Implicación IA**: 
  - ~60-70% del código refactorizado/migrado (Claude Haiku como MVP)
  - 100% de la documentación creada por IA (README, LICENSE, CHANGELOG, docs/)
  - Diseño y dirección: Usuario (Salva_BsK)
  - Supervisión, modificación y comprensión: Usuario
- **Commits**: 1 (squashed)
- **Tests**: Verificación manual completa

---

## [0.1.0] - 2026-03-01

### 🎯 Tema: Versión Inicial Funcional

Primera release funcional del juego. Sistema base completamente implementado con game loop, combate y eventos.

### ✨ Added
- **Game Loop**: Sistema principal de turnos
- **Sistema de Eventos**: 20 eventos únicos con mecánica de bolsa
- **Combate**: Sistema de turnos con enemigos procedurales
- **Interfaz Gráfica**: Tkinter UI (experimental)
- **Sistema de Secretos**: Mecanismos ocultos (6 descubiertos)
- **Narrativa**: 3 finales únicos
- **Enemies**: 10+ tipos diferentes de enemies

### 🔄 Changed
- N/A (primera versión)

### 🐛 Fixed
- N/A (primera versión)

### 🗑️ Removed
- N/A (primera versión)

---

## Plan Futuro (Próximas Versiones)

### [0.3.0] - Interfaz Completa 
- [ ] UI completamente funcional en Tkinter
- [ ] Pantalla de inicio y menú
- [ ] Mejoras visuales
- [ ] Sistema de guardado mejorado

### [0.4.0] - Expansión de Contenido 
- [ ] Más eventos (30-40)
- [ ] Más tipos de enemigos
- [ ] Sistema de habilidades
- [ ] Más armas epicasy secretos

### [0.5.0] - Progresión 
- [ ] Múltiples mazmorras
- [ ] Sistema de progresión entre run
- [ ] Achievements
- [ ] Leaderboard local

### [1.0.0] - Release Completo 
- [ ] Todo lo anterior pulido
- [ ] Documentación final
- [ ] Testing completo
- [ ] Performance optimizado

---

## Notas de Desarrollo

### 🤖 Sobre IA Assistance

A partir de v0.2.0, cierto porcentaje de este proyecto ha sido asistido por **GitHub Copilot** para:
- Refactorización de código
- Identificación y fix de bugs
- Asistencia de sintaxis
- Documentación técnica

Esto se nota especialmente en:
- ✅ Módulo `modules/events.py` - Diseño y refactoring
- ✅ Imports y organization
- ✅ Este CHANGELOG

**Razonamiento**: Usar IA como herramienta de aprendizaje mientras se entiende cada cambio. Esto me permitió aprender patrones de código profesional más rápidamente.

### 📚 Aprendizajes Documentados

Ver [ARQUITECTURA.md](docs/ARQUITECTURA.md) para entender decisiones de diseño.

---

## Cómo Se Versionan los Cambios

### Tipos de Cambios
- **Added**: Nuevas características
- **Changed**: Cambios en funcionalidad existente
- **Deprecated**: Funcionalidad que será removida pronto
- **Removed**: Funcionalidad removida
- **Fixed**: Bugs corregidos
- **Security**: Fixes de seguridad

### Formato de Versión
Semántico: `MAJOR.MINOR.PATCH`
- `MAJOR`: Cambios de arquitectura o breaking
- `MINOR`: Nuevas features o modularización
- `PATCH`: Bug fixes y pequeñas mejoras

---

**Última actualización**: 18 de Marzo de 2026

Para reportar cambios o sugerir versioning, abre un Issue en GitHub.
