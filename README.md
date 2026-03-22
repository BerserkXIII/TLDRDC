# 🏰 TLDRDC - The Lost Dire Realm: Dungeon Crawler

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Status](https://img.shields.io/badge/Status-v0.2.0-orange?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=flat-square)

> **⚠️ NOTA DE TRANSPARENCIA**: Este es un proyecto de **aprendizaje autodidacta** realizado por un programador principiante (*super-low level*) **con asistencia significativa de IA**. La arquitectura, sintaxis y refactorizaciones han sido heavily aided por GitHub Copilot. Este repositorio existe como **documentación honesta de aprendizaje**, no como código profesional paritario. Agradezco cualquier feedback, crítica constructiva y ayuda de la comunidad. 🙏

Primero: **gracias por estar aquí**. En serio. 
No me puedo llegar a considerar programador, asi que seguramente no tendre manera de solucionar posibles reportes de bugs o PRs. No busco "sacar" el juego, todavia, pero si comenzar a tratarlo de manera "profesional" mientras aprendo.
Actualmente estoy aprendiendo a programar con Python, y por motivos laborales he de enfocar mis estudios en una direccion que no aporta mucho a este proyecto. Por eso, si me das algo de conocimiento extra, lo agradeceré. <3

Toda la documentacion ha sido creada con GitHub Copilot, de manera didactica para mi aprendizaje.

---

## 📖 ¿Qué es TLDRDC?

Un juego de **roguelike basado en texto** construido con Python y Tkinter. El jugador explora una mazmorra oscura, combate enemigos procedurales, descubre eventos misteriosos y debe encontrar la salida...o eso cree.

### 🎮 Características Principales

- **20 Eventos Únicos**: Sistema de bolsa (cada evento ocurre exactamente una vez)
- **Combate Dinámico**: Enemies con diferentes tipos y comportamientos
- **3 Finales Únicos**: Dependiendo de decisiones y secretos descubiertos
- **Sistema de Secretos**: Mecanismos ocultos que alteran la narrativa
- **UI Gráfica**: Interfaz con Tkinter (trabajo en progreso)

> **Estado Actual**: v0.2.0 - Modularización completada, funcional pero en desarrollo

---

## 🔍 Honestidad Sobre Este Proyecto

> **Mi Nombre**: @[Salva_BsK](https://github.com/BerserkXIII)
> 
> **Nivel de Programación**: Principiante autodidata (~6 semanas)
> 
> **Asistencia IA**: ~60-70% (la mayoría en arquitectura y migración)

### ✅ Lo que Hice YO:
- ✅ **Concepto y Game Design**: Idea original, narrativa, 20 eventos, 3 finales
- ✅ **Pruebas Manuales**: Testing y debugging de cada característica
- ✅ **Decisiones de Arquitectura**: Identificar problemas, proponer soluciones
- ✅ **Lógica de Gameplay**: Sistema de combate, bolsa de eventos, eventos especiales
- ✅ **Investigación & Aprendizaje**: Aprender cómo estructurar proyectos Python
- ✅ **Documentación**: Escribir sobre decisiones y aprendizajes

### 🤖 Lo que Hizo IA:

**ChatGPT** (OpenAI) - Inicio, fundamentos:
- Enseñanza inicial de Python
- Conceptos fundamentales (loops, OOP, funciones)
- Primeros ejercicios en PythonTutor.com

**GitHub Copilot - Claude Sonnet**:
- Refactorización inicial
- Sugerencias de patrones

**GitHub Copilot - Claude Haiku** (LA IA QUE MÁS AYUDÓ):
- 🤖 **Migración masiva**: 6,800+ líneas de `print()` a Tkinter
- 🤖 **Sistema de UI**: Diseño de paneles, botones, layout
- 🤖 **Inyección de Dependencias**: Arquitectura para evitar imports circulares
- 🤖 **Extracción modular**: Separar 1,338 líneas duplicadas a `modules/events.py`
- 🤖 **Doble threading**: Implementación de ejecución sin bloqueo
- 🤖 **Debugging intenso**: Fix de 16+ errores complejos (imports, undefined values)
- 🤖 **Documentación técnica**: Explicar patrones aplicados

**LM Studio - Qwen 2.5-7B** (Local):
- Validación de sugerencias
- Alternativas de optimización

### 📚 Lo que Aprendí:
1. **Arquitectura de Proyectos**: Modularización, evitar monolitos
2. **Patrones Profesionales**: Inyección de dependencias, Registry pattern
3. **Git/GitHub/Versionado**: Commits, branches, semantic versioning
4. **Documentación Técnica**: Explicar decisiones, no solo código
5. **Cuándo Pedir Ayuda**: IA es herramienta, no sustituto
6. **Verificación Crítica**: Revisar, entender, debuggear todo lo que recibo

---

## 📦 Instalación

### Requisitos
- **Python 3.10+** (recomendado 3.11+)
- **Tkinter** (incluido en Python, salvo algunas distros Linux)
- **Pillow** (para imágenes)

### Pasos

#### 1. Clonar el Repositorio
```bash
git clone https://github.com/BerserkXIII/TLDRDC.git
cd TLDRDC
```

#### 2. Crear Entorno Virtual (RECOMENDADO)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

#### 4. Ejecutar el Juego
```bash
cd code
python TLDRDC_Prueba1.py
```

### Controles en Juego
- **Escritura**: Seguir las instrucciones en pantalla
- **[Enter]**: Confirmar acciones
- **[Ctrl+C]**: Terminar (emergencia)

---

## 📁 Estructura del Proyecto

```
TLDRDC/
├── README.md                  ← Estás aquí
├── LICENSE                    ← MIT License
├── CHANGELOG.md               ← Historial de versiones
├── requirements.txt           ← Dependencias
├── .gitignore                 ← Configuración Git
│
├── docs/                      ← Documentación técnica
│   ├── ARQUITECTURA.md
│   ├── CONTRIBUYENDO.md
│   └── CREDITOS.md
│
├── code/                      ← Código fuente
│   ├── TLDRDC_Prueba1.py      ← Main (~5,500 líneas)
│   ├── TLDRDC_Prueba1_backup.py
│   ├── images/
│   ├── sounds/
│   └── __pycache__/
│
└── modules/                   ← Módulos importables
    ├── events.py              ← 20 eventos
    ├── ui_config.py
    ├── ui_estructura.py
    ├── ui_imagen_manager.py
    └── __pycache__/
```

---

## 🎯 Características

### Sistema de Eventos
- **20 Eventos Procedurales**: Cofres, trampas, cultistas, demonios, encuentros misteriosos
- **Bolsa de Eventos**: Cada evento ocurre máximo una vez por ciclo (garantiza variedad)
- **Resultados Dinámicos**: Cambios de HP, armaduras, pociones, armas, stats personalizados
- **Eventos Especiales**: Algunos eventos pueden activar finales alternativos

### Combate Táctico
- **Turnos**: Tú atacas → Enemigo ataca → Sistema de iteraciones
- **3 Posturas Estratégicas**: Atacar (daño), Bloquear (defensa), Esquivar (agilidad)
- **Enemigos Variados**: Rabiosos, Sombras, Demonios, Perturbados,Mutilados, el Carcelero (jefe final)
- **Dinámicas Especiales**: Algunos enemigos requieren estrategias particulares

### Sistema de Secretos
- **Secreto #1**: Comando oculto accesible en la celda inicial
- **Secreto #2a/2b**: Mecánica de lenguaje ancestral durante combates específicos
- **Secreto #3+**: Mechánicas avanzadas vinculadas a eventos particulares
- **Efectos**: Los secretos pueden modificar enemigos, eventos y finales

### Finales
- **Final Normal**: Escapar de la mazmorra
- **Final Secreto A**: Accesible si activas ciertos secretos (condición 1)
- **Final Secreto B**: Accesible si activas otros secretos (condición 2)
- **Pistas**: Hay pistas distribuidas para guiar al jugador (pero ocultas)

---

## 📚 Documentación

**Referencia técnica completa**:

| Documento | Contenido |
|-----------|-----------|
| [**ARQUITECTURA.md**](docs/ARQUITECTURA.md) | Decisiones de diseño, patrones aplicados (Inyección de Dependencias, Registry Pattern, **Sistema de Threading**), y estructura modular |
| [**CONTRIBUYIENDO.md**](docs/CONTRIBUYIENDO.md) | Cómo contribuir: guía honesta enfocada en enseñanza y aprendizaje compartido |
| [**CREDITOS.md**](docs/CREDITOS.md) | Viaje completo de desarrollo: herramientas, IA usada, inspiraciones del juego |
| [**CHANGELOG.md**](CHANGELOG.md) | Historial de versiones y cambios por release |

---

## 🐛 Bugs Conocidos

**Ninguno reportado actualmente**, pero:
- UI en Tkinter aún en development (experimental)
- Algunos eventos pueden sentirse "loose" en narrativa
- Performance no optimizada (pero funciona)

### ⚠️ Si Encuentras un Bug
1. Abre un **Issue** en GitHub (sí, incluso si es "obvio" para ti)
2. Describe:
   - Qué hiciste
   - Qué pasó inesperadamente
   - Qué esperabas que pasara
3. ¡Muchas gracias! 🙏

---

## 🤝 Contribuciones

### ¿Quiero Contribuir!

Perfecto! Lee primero [CONTRIBUYENDO.md](docs/CONTRIBUYENDO.md) para:
- Cómo reporting bugs
- Cómo sugerir features
- Cómo hacer pull requests
- Limitaciones actuales

### Tipos de Ayuda que Acepto
- ✅ **Feedback**: "Esto no funciona porque..."
- ✅ **Sugerencias**: "Podrías mejorar X haciendo Y"
- ✅ **Pull Requests**: Cambios de código (pequeños primero!)
- ✅ **Documentación**: Mejorar explicaciones
- ✅ **Testing**: Encontrar bugs
- ❓ **Código de MI Nivel**: Prefiero aprender, así que aunque fixes mi código, explica POR QUÉ es mejor

---

## 📝 Changelog

Ver [CHANGELOG.md](CHANGELOG.md) para historial completo de versiones.

**Últimas Versiones:**
- **v0.2.0** (18 Mar 2026): Modularización de eventos, refactoring masivo
- **v0.1.0** (01 Mar 2026): Versión inicial funcional

---

## 📊 Estadísticas del Proyecto

- **Líneas de Código**: ~5,500 (principal), ~1,336 (módulo eventos)
- **Directorio**: ~500 archivos (incluyendo assets)
- **Tiempo de Desarrollo**: ~6 semanas (autodidacta)
- **% Código Asistido por IA**: ~40% (arquitectura, refactoring, bugfixes)
- **% Código Original**: ~60% (lógica game, narrativa, decisiones)

---

## 📜 Licencia

Este proyecto está bajo la **Licencia MIT** - totalmente open source.

Ver [LICENSE](LICENSE) para detalles completos.

---

## 📞 Contacto / Soporte

- **Issues en GitHub**: Para bugs y features
- **Discussions**: Para preguntas generales
- **Email**: (si quieres agregar)

---

## 🗺️ Roadmap (Lo que Sueño)

- [ ] **v0.3.0**: UI completamente funcional en Tkinter
- [ ] **v0.4.0**: Más eventos (30+)
- [ ] **v0.5.0**: Sistema de progresión (múltiples mazmorras)
- [ ] **v1.0.0**: Release estable, dokumentación completa
- [ ] **v2.0.0**: Multiplayer? (probablemente no 😅)

---

## 🎓 Aprendizajes Documentados

Si quieres ver MI proceso de aprendizaje:
1. Ve a [CONTRIBUYENDO.md](docs/CONTRIBUYENDO.md) - Cómo pienso
2. Lee [ARQUITECTURA.md](docs/ARQUITECTURA.md) - Decisiones técnicas
3. Revisa [CHANGELOG.md](CHANGELOG.md) - Evolución del proyecto
4. Explora `docs/` - Todo mi pensamiento documentado

---

## 📄 Última Actualización

**18 de Marzo de 2026**
- Modularización completada
- Documentación extendida
- Primer release prep
- README honesto y transparente

---

<div align="center">

### 🙏 Gracias por leer esto. Significa que realmente te importa entender el contexto.

**Si este proyecto te ayudó a aprender**, consideralo un win. 🎉

**Si encuentras bugs**, abre un Issue. 🐛

**Si tienes ideas**, sugierelas. 💡

**Si ves código malo**, vamos a aprenderlo juntos. 🤝

</div>

---

**Made with ❤️, Python, and a Healthy Dose of IA Assistance**

*- Un programador principiante explorando las profundidades del código, sin miedo. - Bsk_XIII*
