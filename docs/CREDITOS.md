# 🙏 Créditos, Agradecimientos y Atribuciones

Este documento reconoce todas las herramientas, personas, y recursos que hicieron posible TLDRDC.

---

## 🤖 Herramientas de Desarrollo

### IA: El Viaje Completo de Aprendizaje

Este proyecto fue construido **íntegramente con asistencia de IA en cada fase**. No es un "copy-paste", sino un **proceso de aprendizaje guiado** donde:
- Yo ideé las características y flujo de juego
- IA implementó sobre mis indicaciones e ideas
- Yo revisé, entendí y debuggué cada paso
- Aprendí arquitectura, patrones y buenas prácticas

**Estimación**: ~60-70% del código tiene asistencia IA (la mayor parte de la migración y optimización).

### ChatGPT (OpenAI)
**Rol**: Primer asistente - Fundamentos y conceptos
**Contribuciones iniciales**:
- Enseñanza inicial de Python desde cero
- Explicación de conceptos fundamentales (loops, funciones, OOP)
- Primeras estructuras del sistema de combate
- Debugging conceptual de problemas lógicos
- Base sólida de conocimiento

**Estado**: Mi primer chat con ChatGPT fue fundamental para entender Python.

### GitHub Copilot - Claude Sonnet
**Rol**: Desarrollo y refactorización avanzada
**Contribuciones**:
- Refactorización inicial del código
- Sugerencias de estructura y patrones
- Optimización de lógica de combate

### GitHub Copilot - Claude Haiku
**Rol**: Asistente principal de desarrollo
**Contribuciones** (la IA que MÁS me ayudó):
- ✅ **Migración masiva**: Conversión de 6,800+ líneas de `print()` a Tkinter
- ✅ **Sistema de UI**: Diseño de paneles, botones e interfaz gráfica
- ✅ **Arquitectura avanzada**: Inyección de dependencias para evitar imports circulares
- ✅ **Extracción modular**: Separar 20 eventos a `modules/events.py` (1,336 líneas)
- ✅ **Doble threading**: Implementación de ejecución sin bloqueo
- ✅ **Debugging intenso**: Identificación y fixes de 16+ errores complejos
- ✅ **Documentación técnica**: Explicar patrones aplicados
- ✅ Refinamiento continuo durante toda la sesión

**Por qué Claude Haiku fue crucial**: Proporcionó respuestas rápidas, precisas y exactamente lo que necesitaba en cada momento.

### LM Studio - Qwen 2.5-7B (Local)
**Rol**: Validación y refinamiento adicional
**Contribuciones**:
- Testing local de sugerencias
- Validación de arquitectura
- Alternativas para optimización
- Backup de IA cuando los servicios online estaban saturados

### Python
**Versión**: 3.10+
**Sitio**: https://www.python.org/
**Licencia**: Python Software Foundation License
**Rol**: Lenguaje de programación principal

### Tkinter
**Incluido en**: Python 3.x
**Sitio**: https://docs.python.org/3/library/tkinter.html
**Licencia**: Python Software Foundation License
**Rol**: Framework de interfaz gráfica (completamente rediseñada con ayuda IA)

### Pillow (PIL)
**Versión**: 9.0+
**Sitio**: https://python-pillow.org/
**Licencia**: MIT/HPND
**Rol**: Procesamiento de imágenes
**Comandos**:
```bash
pip install Pillow>=9.0.0
```

### Git & GitHub
**Sitio**: https://git-scm.com / https://github.com
**Licencia**: GNU GPL / Propietario
**Rol**: Control de versiones y alojamiento de código

### Visual Studio Code
**Sitio**: https://code.visualstudio.com/
**Licencia**: Propietario (gratis)
**Rol**: Editor de código + extensiones IA

### PythonTutor.com
**Sitio**: https://pythontutor.com/
**Rol**: Visualización step-by-step del código, primeras 100 lineas de codigo
## 📚 Inspiración e Influencias

### Juegos que Inspiraron el Diseño

**Fear & Hunger**
- Roguelike castigador, oscuro y perverso
- Narrativa inexorable (el jugador está atrapado)
- Enemigos aterradores e implacables
- Sensación de pérdida permanente
- La muerte importa y está siempre presente

**Dark Souls**
- Narrativa débil directa (los jugadores descubren la historia)
- Secretos ocultos en todas partes
- Sensación de peligro constante
- Combate preciso y táctico

**Warhammer: Fantasy y 40K**
- Lore oscuro y richly detailed
- Personajes legendarios con trasfondo profundo
- Teología oscura y magia arcana
- Arquitectura ominosa y fortalezas de pesadilla
- Referencias a poder, corrupción y perdición

**Kingdom Death: Monster**
- Ambientación extremadamente oscura
- Teratología y creature design perturbador
- Narrativa de supervivencia vs. muerte
- Horrores desconocidos en la oscuridad
- Tono nihilista y desasosegante

---

## 👥 Comunidades y Recursos

### Stack Overflow
**Rol**: Responder preguntas técnicas específicas
**Ejemplos**:
- Cómo evitar imports circulares en Python
- Inyección de dependencias
- Tkinter geometry management

**Crédito especial a usuarios que respondieron mis preguntas** (aunque sea indirectamente vía búsquedas)

### Real Python
**Sitio**: https://realpython.com/
**Rol**: Tutoriales de calidad sobre conceptos Python
**Específicamente**:
- Argumentos *args y **kwargs
- Type hints
- Comprehensions

### Python Documentation
**Sitio**: https://docs.python.org/3/
**Rol**: Referencia oficial de todas las características

### GitHub Documentation
**Sitio**: https://docs.github.com/en
**Rol**: Cómo usar Git y GitHub correctamente

### Medium / DEV.to
Varios autores escribieron articulos que me ayudaron:
- Sobre arquitectura de proyectos Python
- Refactorización segura
- Best practices

---

## 📖 Libros y Cursos Consultados

### "Clean Code" - Robert C. Martin
**Lecciones aplicadas**:
- Nombres explicativos de variables
- Funciones pequeñas y enfocadas
- Comentarios que expliquen POR QUÉ

### "The Pragmatic Programmer"
**Lecciones aplicadas**:
- DRY (Don't Repeat Yourself) → Modularización de eventos
- Broken Window Theory → Mantener código limpio

### Udemy Courses (varios sobre Python)
**Rol**: Fundamentos de programación
**Aprendizajes**:
- OOP basics
- File I/O
- Data structures

---

## � Agradecimientos Especiales

### Mi Primer Chat de ChatGPT
**Rol**: El punto de inicio
**Por qué**: Sin ese primer diálogo sobre Python fundamentals, nada de esto sería posible. Fue el catalizador.

### Claude Haiku (GitHub Copilot)
**Rol**: El asistente más leal
**Por qué**: De todas las IAs utilizadas, Haiku fue la que más paciencia tuvo y las respuestas más precisas. Realizó ~70% de la implementación técnica.

---

## 🔧 Creador del Proyecto

**Salva_BsK**
- GitHub: [@BerserkXIII](https://github.com/BerserkXIII)
- Role: Diseño, ideación, aprendizaje, integración de IA
- Responsable de: Ideas de gameplay, arquitectura de alto nivel, debugging y validación

### Contribuyentes Futuros

**Si contribuyes**, será listado aquí con tu permiso:
```markdown
### [Tu Nombre / GitHub Username]
**Contribuciones**:
- [Describe qué hiciste]

**PR/Issue**: #[número]
**Fecha**: [Cuando lo hiciste]
```

---

## 🎓 Agradecimientos Personales

### A Mi Mismo (Pasado)
Por no rendirse cuando todo se veía monolítico y confuso.

### A GitHub Copilot
Por permitirme aprender de verdadero código profesional en tiempo real.

### A la Comunidad Python
Por crear un ecosistema acogedor y documentación excelente.

### A Ti, Lector
Por leer esto y considerar el proyecto.

---

## 📜 Licencias Consolidadas

### TLDRDC
- **Licencia**: MIT
- **Texto**: Ver [LICENSE](../LICENSE) en la raíz

### Pillow
- **Licencia**: MIT/HPND
- **Sitio**: https://github.com/python-pillow/Pillow/blob/main/LICENSE

### Python
- **Licencia**: PSFL (Python Software Foundation License)
- **Sitio**: https://www.python.org/psf/

### Tkinter
- **Incluido en Python**, misma licencia

---

## 🚫 Lo que NO Está Incluido

Este proyecto **no incluye**:
- ❌ Assets de juegos comerciales (respetar copyright)
- ❌ Código copiado de otros proyectos sin permiso
- ❌ APIs externas sin crédito

---

## 📝 Cómo Citar Este Proyecto

Si alguien cita tu trabajo (poco probable pero quien sabe):

```bibtex
@software{TLDRDC2026,
  author = {Salva_BsK},
  title = {TLDRDC - The Lost Dire Realm: Dungeon Crawler},
  year = {2026},
  url = {https://github.com/BerserkXIII/TLDRDC},
}
```

O simplemente:
```
TLDRDC by Salva_BsK
https://github.com/BerserkXIII/TLDRDC
```

---

## 📞 Contactar Sobre Créditos

Si:
- Ves algo que debería estar aquí
- Quieres que quite algo
- Tienes una sugerencia

Abre un Issue en GitHub y lo discutiremos.

---

## ⚖️ Nota Legal

**TLDRDC es proporcionado "AS IS"** bajo licencia MIT. No hay garantías.

Todos los créditos y licencias mencionados se respetan según sus términos.

---

**Última actualización**: 18 de Marzo de 2026

**Estado**: Completo (por ahora)

---

<div align="center">

## 🙏 Gracias a Todos

Sin estas herramientas y recursos, TLDRDC no sería posible.

</div>
