# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
y este proyecto sigue [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Este es un proyecto de aprendizaje a traves de IA, por lo que puede contener errores. Agradezco cualquier sugerencia o reporte de errores :) 

---

## [0.2.0] - 2026-03-18

### 🎯 Tema: Modularización y Refactorización Masiva

Un cambio arquitectónico importante: el sistema de eventos ha sido extraído del archivo principal a un módulo separado. Esto reduce la complejidad, mejora la mantenibilidad y sienta las bases para futuras expansiones.

### ✨ Added
- **Módulo `modules/events.py`**: Sistema de eventos completamente modularizado
  - 20 funciones de eventos (`_evento_1` a `_evento_20`)
  - Tabla de distribución `_EVENTOS`
  - Sistema de bolsa de eventos mejorado
  - Inyección de dependencias para evitar imports circulares

- **Documentación Técnica**:
  - [ARQUITECTURA.md](docs/ARQUITECTURA.md) - Creada por IA, modificada y revisada por usuario
    - [+] Sección de Threading: Explicación del sistema de doble hilo con diagramas y flujos
  - [CONTRIBUYENDO.md](docs/CONTRIBUYENDO.md) - Creada por IA (reescrita por IA con dirección del usuario, ahora de tono honesto y auténtico)
  - [CREDITOS.md](docs/CREDITOS.md) - Creada por IA, documentando el viaje completo incluyendo asistencia de IA

- **Git Setup**:
  - `.gitignore` - Ignorar archivos innecesarios
  - Primer commit documentation

### 🔄 Changed
- **TLDRDC_Prueba1.py**: Reducción de 6,800+ líneas a 5,500+ líneas (~22% reduction)
  - **Migración print → Tkinter UI**: Realizada por IA (Claude Haiku-70% del código) bajo guía y dirección del usuario
  - Sistema refactorizado para usar interfaz gráfica en lugar de terminal
- **Imports**: Actualizados a usar `modules.ui_*` en lugar de `ui_*`
- **Inyección de Dependencias**: Colocada más tarde en ejecución (línea 5546) para evitar undefined values

### 🐛 Fixed
- **reportmissingimports** (3 errores en líneas 16-18):
  - `from modules.ui_config import` ✅
  - `from modules.ui_imagen_manager import` ✅
  - `from modules.ui_estructura import` ✅

- **reportundefinedvalue** (13 errores en líneas 733-746):
  - Movida inyección de dependencias a punto de ejecución seguro ✅
  - Todas las funciones ahora definidas antes de inyección ✅

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
