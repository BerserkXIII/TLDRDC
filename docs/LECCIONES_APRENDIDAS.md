# 📚 Lecciones Aprendidas

Reflexiones técnicas y no-técnicas del desarrollo de TLDRDC. Este documento captura problemas encontrados, soluciones implementadas, y insights para futuros proyectos.

---

## Arquitectura & Diseño

### Lección 1: El Monolito No Escala

**Problema**: La versión inicial (v0.1.0) era un archivo único de 6,800+ líneas.

**Síntomas**:
- Imposible encontrar código específico (¿dónde está la función de combate?)
- 1,338 líneas eran eventos duplicados (`evento_X` vs `_evento_X`)
- IDE lento (archivo muy grande)
- Confusión sobre responsabilidades

**Solución**: Modularización en v0.2.0
- `modules/events.py` para los 20 eventos
- `modules/ui_*.py` para componentes gráficos
- `TLDRDC_Prueba1.py` para lógica del juego

**Insight**: **Modularizar temprano, aunque sea pequeño.** No esperes a que sea insostenible.

---

### Lección 2: Evitar Imports Circulares es Crítico

**Problema**: 
```
eventos.py necesita evento_aleatorio() de main
main.py importa eventos.py
↓
IMPORT CIRCULAR ❌
```

**Primera solución (fallida)**: Imports condicionales.

**Solución correcta**: **Late Binding (Inyección de Dependencias)**
```python
# modules/events.py
evento_aleatorio = None  # Placeholder globales

# TLDRDC_Prueba1.py (línea 5,546)
events.evento_aleatorio = evento_aleatorio  # Inyectar DESPUÉS de definir
```

**Insight**: **Inyección de dependencias en Python es simple pero poderosa.** No necesitas framework.

---

### Lección 3: El Orden de Ejecución Importa

**Problema**: Línea 735 tenía inyección de dependencias, pero algunas funciones no estaban definidas aún.
```
Error: NameError: name 'evento_aleatorio' is not defined
```

**Solución**: Mover inyección a línea 5,546 (después de TODAS las definiciones).

```
1. Líneas 1-40: Imports
2. Líneas 41-5,500: Definir TODO
3. Línea 5,546: Inyectar dependencias ← AQUÍ
4. Línea 5,550+: Main loop
```

**Insight**: **En Python, el orden de ejecución es crítico.** Piensa en la geometría de tu código.

---

## Threading & UI

### Lección 4: Never Block the Event Loop

**Problema inicial**: Usar `input()` en Python nativo congela la UI.

**¿Por qué?** Tkinter tiene un loop de eventos. Si ese loop se detiene, la UI muere (no responde a clics, no renderiza).

**Solución**: Doble hilo
- **Hilo 1 (Tkinter)**: Nunca se bloquea, solo procesa eventos
- **Hilo 2 (Juego)**: Puede bloquearse esperando entrada

```python
class _Bridge:
    def esperar(self):
        self._evento.wait()  # Hilo juego BLOQUEA
    
    def recibir(self, texto):
        self._evento.set()   # Hilo tkinter DESBLOQUEA
```

**Insight**: **Threading resuelve el problema de responsividad.** El código del juego sigue siendo lineal y simple.

---

### Lección 5: Thread-Safe es No Negociable

**Riesgo**: Dos hilos modificando el mismo dato sin sincronización = race condition.

**Solución en este proyecto**:
- `cola_mensajes` es thread-safe (deque de Python)
- Personaje solo se modifica en hilo juego
- Tkinter nunca modifica lógica, solo LEE

**Insight**: **No necesitas locks complejos si diseñas bien.** Una dirección de comunicación (game → UI) simplifica todo.

---

## Documentación & Comunicación

### Lección 6: Documentar es Comunicar

**Descubrimiento**: Documentación técnica NO es aburrida cuando explica DECISIONES, no solo código.

**ARQUITECTURA.md** enfatiza:
- POR QUÉ se hizo cada cosa (no solo QUÉ)
- Problema → Solución → Trade-offs
- Diagramas ASCII son tus amigos

**Insight**: **Código sin contexto es arqueología.** Explica el "por qué" → Los lectores (incluyéndote en 6 meses) lo entenderán.

---

### Lección 7: Transparencia Construye Confianza

**Decisión**: Documentar claramente quién hizo qué (usuario vs IA).

```markdown
✅ LO QUE HIZO USUARIO: Concepto, narrativa, decisiones
🤖 LO QUE HIZO IA: Refactorización, UI, debugging
```

**Beneficio**: 
- Honestidad atraer gente que quiere aprender (no admiradores falsos)
- Claridad evita acusaciones de "plagio"
- Muestra que entiendo mis limitaciones

**Insight**: **Transparencia no es debilidad, es fortaleza.** Los mejores portfolios son honestos.

---

## Testing & Validación

### Lección 8: Testing Manual ≠ No Testing

**Situación**: Sin automatización de tests, todavía hubo QA.

**Proceso realizado**:
- Reproducir cada bug encontrado manualmente
- Escribir exactitud: "Cuando A sucede, B debería ocurrir"
- Verificar puntos de quiebre (errores edge cases)

**Métodos usados**:
- Leer código críticamente (¿tiene sentido esto?)
- Pruebas exploratorias (¿y si hago...?)
- Debugging con prints y logging

**Insight**: **Testing manual es tedioso pero efectivo en proyectos pequeños.** Vale la pena para v0.1.

---

## Herramientas & Workflow

### Lección 9: Git es Más que Backups

**Descubrimiento**: Usar `git log` como narrativa del proyecto.

Cada commit cuenta una historia:
```
Initial commit: TLDRDC v0.2.0 - Modularización masiva
docs: agregar sección de threading a ARQUITECTURA
chore: mejorar .gitignore
```

**Beneficio**: Meses después, sé exactamente QUÉ cambió en CUÁNDO.

**Insight**: **Git es un time machine.** Commits granulares = mejor narrativa.

---

### Lección 10: IAs Son Herramientas, No Reemplazos

**Realoización**: La IA hizo ~70% del código, pero YO hice ~70% del pensamiento.

**Cómo usé IA correctamente**:
1. Planteé el problema claramente
2. Recibí sugerencia
3. **VERIFIQUÉ** entendiendo el código
4. Modifiqué según mi dirección
5. Debuggeé lo que no funcionaba

**Cómo NO usé IA**: Simplemente copiar/pegar sin entender.

**Insight**: **IA es un multiplicador, no un sustituto.** "Multiplica" el 30% de pensamiento tuyo en 100% de output.

---

### Lección 11: La Sincronización es el Diablo (Bugs de Stances - 25 de Marzo)

**El Bug Más Difícil**: Sistema de botones de stances (bloquear/esquivar) que parecía tener 3 bugs separados.

**La Realidad**: Un ÚNICO problema de arquitectura manifestándose de 3 formas diferentes.

#### El Raíz: Dos Caminos, Dos Lógicas

El código permitía DOS formas de activar stance:
1. **Click en botón** → Llamaba a `_select_stance()` 
2. **Parser (teclado)** → Llamaba a `_enviar_input()`

Problema: Usaban lógica diferente:
- **Click**: SET simple (`_toggle_state['activa'] = 'bl'`)
- **Parser**: ALTERNANCIA (`if activa == 'bl': activa = None; else: activa = 'bl'`)

Resultado: Click → SET → redibuja ENCENDIDO ✓
Pero luego: `_enviar_comando()` inyecta en parser → reprocesa CON ALTERNANCIA → SET vuelto NULL → redibuja APAGADO ❌

#### Manifestación 1: "Doble Procesamiento"
```
Click "bl" → SET a "bl" → Botón ENCENDIDO
           → _enviar_comando("bl")
           → Parser ALTERNA: "bl" → NULL
           → Botón APAGADO
Resultado: Botón parpadeaba, estado final incorrecto
```

#### Manifestación 2: "Desincronización de Formatos"
Juego dice `"bloquear"` pero UI busca `"bl"`:
```
Click → SET _toggle_state['activa'] = "bl" → botón ENCENDIDO ✓
Juego emite opciones_combate con stance="bloquear"
UI: _toggle_state['activa'] = "bloquear" (no normaliza)
Redibuja busca: activa == 'bl' ? NO ENCUENTRA
Botón APAGADO sin razón lógica
```

#### Manifestación 3: "Botón No Se Apaga"
Después de atacar, stance=None pero botón sigue encendido:
```
Atacas, stance se usa
Final turno: opciones_combate(..., stance=None)
UI: if stance is not None: ... 
    # NO ENTRA (stance es None)
    # _toggle_state['activa'] sigue siendo 'bl' del turno anterior
Botón mantiene "bl", redibuja encuentra activa=='bl' → ENCENDIDO
```

#### La Solución Unificada
1. **Usar MISMO código para clicks y parser**: ALTERNANCIA en ambos
2. **Normalizar formatos**: "bloquear" ↔ "bl" en UN solo lugar
3. **Resetear explícitamente**: `else: _toggle_state['activa'] = None` cuando stance=None

**Resultado**: 3 bugs = 1 solución simple.

**Insight Original**: **Cuando veas 3 bugs que parecen independientes, busca 1 raíz de arquitectura.** Los síntomas engañan.

**Insight Aplicado**: **Synchronization problems require unified source of truth.** 
- Dos caminos diferentes = bugs
- Un camino con normalización = limpio

**Insight Para Proyectos Futuros**:
```python
# ❌ MAL
if user_input == "click":
    lógica_click()
elif user_input == "parser":
    lógica_parser()

# ✅ BIEN  
normalizar(user_input)  # Convert all inputs to common format
lógica_unificada()      # ONE path for all inputs
```

**Resumen**: Este bug enseñó que **UI + Game Logic sincronización es crítica.** Estado visual debe siempre derivarse de estado lógico, con formato unificado. Jamás dejes que dos subsistemas mantengan el mismo dato con representaciones diferentes.

---

## Si Vuelvo a Empezar

### Qué Repetiría
✅ Documentación honesta desde el inicio  
✅ Modularización temprana  
✅ Commits pequeños y frecuentes  
✅ Sistema de threading para UI responsiva  

### Qué Cambiaría
❌ Menos funcionalidad, más documentación en v0.1 (tenía 20 eventos de una)  
❌ Type hints desde el inicio (Python sin tipos = debugging más lento)  
❌ Más tests automatizados (Jest, pytest desde v0.1)  
❌ Configuración externa (YAML/JSON) para valores mágicos  

### Pasos para v0.3.0
- [ ] Agregar type hints completos
- [ ] Unit tests con pytest
- [ ] Logger estruturado (no solo prints)
- [ ] Configuración externa (colores, enemigos, events en JSON)
- [ ] Performance profiling (¿dónde está el cuello de botella?)

---

## Reflexión Final

Este proyecto me enseñó que **ser buen programador NO es escribir código perfecto a la primera.** Es:
- ✅ Cambiar de dirección cuando algo sale mal
- ✅ Documentar decisiones
- ✅ Forzarse a entender lo que otros escriben (incluyendo IA)
- ✅ Preguntar "¿por qué?" constantemente
- ✅ Ser honesto sobre limitaciones

**La mayor lección**: El viaje (lecciones, debugging, arquitectura) es más valioso que el destino (un juego funcional).

---

**Escrito por**: Salva_BsK  
**Fecha**: 22 de Marzo de 2026  
**Versión**: 1.0 (para v0.2.0)
