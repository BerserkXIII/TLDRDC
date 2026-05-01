# TLDRDC: Glosario Completo de Secretos y Mecánicas Ocultas

> **Documento técnico de referencia** para todas las mecánicas secretas, eventos especiales y ramificaciones narrativas ocultas del juego.

---

## 📋 TABLA DE CONTENIDOS

1. [Sistemas de Progresión Oculta](#sistemas-de-progresión-oculta)
2. [Los 6 Secretos Desbloqueables](#los-6-secretos-desbloqueables)
3. [Mecánica de Sangre](#mecánica-de-sangre)
4. [Mecánica de Sombra](#mecánica-de-sombra)
5. [Mecánica de Brazos](#mecánica-de-brazos)
6. [La Ruta Secreta del Demonio Final](#la-ruta-secreta-del-demonio-final)
7. [Finales Secretos y Condiciones](#finales-secretos-y-condiciones)
8. [Variables de Control Ocultas](#variables-de-control-ocultas)
9. [Referencias Cruzadas](#referencias-cruzadas)

---

## 🔐 Sistemas de Progresión Oculta

El juego rastrea múltiples variables para activar contenido secreto:

### Sistema de Atributos Sobrenaturales

| Atributo | Inicio | Máximo | Descripción |
|----------|--------|--------|-------------|
| `sangre` | 0 | ∞ | Representa conexión con el poder oscuro y ritual de sangre |
| `sombra` | 0 | ∞ | Afinidad con criaturas de oscuridad y resonancia infernal |
| `brazos` | 0 | ∞ | Brazos reclamados para el desconocido cosedor |
| `moscas` | 0 | ∞ | Sincronización con la voluntad colmena |
| `conocimiento_plaga` | NULL | TRUE | Flag binario: conocimiento de la plaga ancestral |

### Sistema de Rayado (Racha)

- `estado["ruta_jugador"]` → Rastrea cada decisión izquierda/derecha
- `estado["pasos_secretos"]` → Compara contra la ruta secreta
- `racha(ruta_actual, ruta_secreta)` → Función que calcula coincidencia

---

## 🎮 Los 6 Secretos Desbloqueables

### SECRETO 1: La Sombra Comprende

**Ubicación:** Evento de exploración (encuentro con "Sombra tenebrosa")  
**Condición:** `personaje["sombra"] > 1` (necesita sangre previa)  
**Comando:** `hablar`  
**Efecto:**
```python
personaje["sombra"] += 1  # La sombra reconoce tu naturaleza
```

**Narrativa:**
```
"Abres la boca, pero lo que sale no es tu voz.
Es un susurro que resuena en las paredes: antiguo, inhumano.
La criatura levanta la cabeza lentamente. 
Por un instante, algo que no es humano mira a través de sus ojos.
La sombra nunca abandona a los suyos."
```

**Nota:** Solo funciona si ya has incrementado `sombra` una vez (requisito previo desconocido).

---

### SECRETO 2a & 2b: Dominio de la Sangre (Foso)

**Ubicación:** Evento del Foso (encuentro doble con Maniacos)  
**Condición:** `personaje["sangre"] > 1`  
**Comando:** `hablar` (en ambas ocurrencias)  
**Efecto:**
```python
personaje["sangre"] += 1  # La sangre grita más fuerte
```

**Narrativa:**
```
"Cierras los ojos. La sangre en tus manos grita más fuerte que los maniacos.
Cuando hablas, es con una voz que no reconoces: antigua, sangrienta.
Los maniacos se detienen. Entienden lo que eres."
```

**Mecánica bifurcada:**
- Luego permite elegir: `(s)eguir` o `(h)uir` del foso
- Huir requiere tirada: destreza O fuerza > `random(1,25)`

---

### SECRETO 3: Revelación de la Plaga

**Ubicación:** Templo Subterráneo (Exploración #14)  
**Condición:** `textos_exploracion == 14`  
**Comando:** `rezar`  
**Efecto:**
```python
personaje["conocimiento_plaga"] = True  # Desbloquea diáLogo futuro
```

**Narrativa:**
```
"Cierras los ojos en el templo subterráneo.
Ves figuras en la oscuridad: no son personas.
Son cosas que fueron personas una vez, hace siglos.
La plaga los hizo así."
```

**Implicaciones:** Flag activa líneas narrativas futuras (no documentadas completamente en v0.2.3).

---

### SECRETO 5: Pacto con el Desconocido

**Ubicación:** Encuentro con el "hombrecillo" (siempre activo)  
**Condición:** Siempre disponible  
**Comando:** `hablar`  
**Requisito narrativo:** Elegir `(s)í` al trato  
**Efecto:**
```python
personaje["brazos"] += 1  # Registra un trato de brazos
```

**Personaje:** Ser deforme que "cose para acompañar"  
**Diálogo clave:**
```
"'Yo coso para acompañar. No me gusta estar solo cuando la piedra 
empieza a respirar y decir cosas.'
'¡Sabía que eras listo! Yo noto estas cosas. 
Sabré cuándo tengas brazos para mí.'"
```

**Mecánica:** 
- Si aceptas: `brazos += 1` (se repite cada encuentro)
- Si rechazas: Narrativa amargada, sin cambio de variable
- Relacionado a: `hitos_brazos_reclamados[]`, `evento_brazos_final_completado`

---

### SECRETO 6: Resurrección del Muerto

**Ubicación:** Pantalla de Game Over (Derrota)  
**Condición:** `not personaje.get("_x9f")` (primera muerte apenas)  
**Comando:** `lo que esta muerto no puede morir`  
**Efecto:**
```python
personaje["_x9f"] = True              # Flag de resurrección usada
personaje["vida"] = vida_max // 2     # Revive a media vida
personaje["_flg1"] = True             # Marca revival especial
return False  # Continúa el juego
```

**Narrativa:**
```
"Pero la muerte aquí no es el final.
La mazmorra es un lugar donde los muertos siguen sirviendo.
Y algo en ti aún tiene hambre. Aún tiene propósito.
Despiertas en un cruce desconocido, confuso pero vivo."
```

**Variables relacionadas:**
- `personaje["_x9f"]` → Una sola revivida permitida
- `personaje["_flg1"]` → Marcador de resurrección activo

---

## 🩸 Mecánica de Sangre

### Fuentes de Sangre

| Fuente | Valor | Contexto |
|--------|-------|---------|
| SECRETO 2a (Foso primera vez) | +1 | Dominar maniacos con poder de sangre |
| SECRETO 2b (Foso segunda vez) | +1 | Repetir dominio en segundo encuentro |
| Evento ritual de sangre | VAR | (No documentado en exploración) |

### Efectos de Sangre

#### Sangre > 1: Desbloquea SECRETO 2a y 2b
- Comando `hablar` en encuentros de maniacos
- Permite persuasión con poder ancestral
- +1 adicional por cada secreto desbloqueado

#### Sangre en Finales
- **Hoz de Sangre equipada + derrotar Amo** → `_fate_02()` – HEREDERO DE LA SANGRE
- **66 kills + poder ≥ 1** → `_fate_06()` – FINAL SUPER HIPER SECRETO (Rickroll)

### Narrativa de Sangre

> "La sangre siempre reconoce a los suyos"  
> "La sangre en tus manos grita más fuerte que los maniacos"

---

## 🌑 Mecánica de Sombra

### Fuentes de Sombra

| Fuente | Valor | Contexto |
|--------|-------|---------|
| SECRETO 1 (Hablar a sombra) | +1 | Encuentro con Sombra Tenebrosa |
| Evento de exploración | VAR | Encuentros con elementales oscuros |

### Efectos de Sombra

#### Sombra > 1: Desbloquea SECRETO 1
- Comando `hablar` contra Sombra Tenebrosa
- Criatura reconoce tu naturaleza infernal
- +1 por activación del secreto

#### Sombra en Finales
- **Hoja de la Noche equipada + derrotar Amo** → `_fate_03()` – PORTADOR DE LA NOCHE
- Las sombras no devoran, reconocen

### Narrativa de Sombra

> "La sombra nunca abandona a los suyos"  
> "Las sombras no te devoran. Te reconocen."

---

## 🦾 Mecánica de Brazos

### Sistema de Brazos Reclamados

El desconocido "cosedor" colecciona brazos de cadáveres mutilados:

```python
"brazos": 0,                              # Contador de brazos reclamados
"hitos_brazos_reclamados": [],           # Registro de qué brazos
"evento_brazos_final_completado": False, # Evento final de brazos
"evento_brazos_segundo_completado": False,
```

### SECRETO 5: Pacto de Brazos

**Trigger:** `hablar` con el desconocido (siempre disponible)  
**Respuesta:** `(s)í` al trato  
**Efecto:**
```python
personaje["brazos"] += 1
```

### Diálogos del Desconocido

**Primer encuentro:**
```
"'¿Quieres saber qué soy?'
'Soy lo que los dioses dejaron olvidado. Lo que no se atrevieron a destruir.'
'Soy el que cose lo roto. El que acompaña a los que la piedra ha llamado.'
'Y tú... tú también escuchas cuando la piedra habla, ¿verdad?'"
```

**Si aceptas:**
```
"'¡Sabía que eras listo! No te arrepentirás. 
Yo... noto estas cosas. Sabré cuándo tengas brazos para mí.'"
```

**Si rechazas:**
```
"'Cuando le dices que no, no reacciona de inmediato.
Parpadea lentamente.'"
```

### Filosofía de Brazos

El personaje representa la soledad de la mazmorra:
- Recoge brazos de muertos que "ya no sirven"
- "Aquí abajo nadie quiere los brazos cuando dejan de obedecer. Los arrancan. Los olvidan."
- Su propósito: "Yo puedo arreglarlos... No me gusta estar solo cuando la piedra empieza a respirar"

---

## 🗺️ Rutas de Navegación

### La Ruta Normal (Final Superviviente)

**Definición:** Cualquier combinación de izquierda/derecha que **NO** coincida exactamente con la ruta secreta.

**Ejemplo de ruta normal simple:**
```python
# Opción 1: Siempre izquierda
ruta_normal_1 = ["i", "i", "i", "i", "i", "i", "i", "i", "i", "i"]

# Opción 2: Siempre derecha
ruta_normal_2 = ["d", "d", "d", "d", "d", "d", "d", "d", "d", "d"]

# Opción 3: Alternado
ruta_normal_3 = ["i", "d", "i", "d", "i", "d", "i", "d", "i", "d"]
```

**Resultado:** 
```
Sales de la sala del Amo de la Mazmorra tambaleándote.
No hay gloria, ni revelaciones, solo pasillos que por fin dejan de cerrarse.
La oscuridad sigue ahí, pero ya no te traga: esta vez te deja pasar.
Respiras hondo por primera vez en mucho tiempo.
Has sobrevivido a la mazmorra.
```

**Final:** `_fate_01()` → **FINAL: SUPERVIVIENTE** (amarillo)

---

### La Ruta Secreta del Demonio Final

### Patrón Exacto

```python
ruta_secreta = ["d", "i", "d", "d", "i", "d", "i", "d", "i", "d"]
```

**Desglose:**
1. **D**erecha
2. **I**zquierda
3. **D**erecha
4. **D**erecha
5. **I**zquierda
6. **D**erecha
7. **I**zquierda
8. **D**erecha
9. **I**zquierda
10. **D**erecha

### Mecánica de Rayado

La función `racha()` compara la ruta actual contra la secreta:

```python
progreso_s = racha(estado["ruta_jugador"], ruta_secreta)
estado["pasos_secretos"][:] = ruta_secreta[:progreso_s]
```

### Condiciones de Trigger

En cada paso:
1. Se registra la decisión (`i` o `d`)
2. Se compara contra el patrón secreto
3. Si hay coincidencia, `estado["pasos_secretos"]` avanza
4. Si hay divergencia, se "resetea" a 0

### Recompensa Final

**Cuando:** `estado["pasos_secretos"] == ruta_secreta` (10/10 pasos correctos)

```
La oscuridad se condensa a tu alrededor.
Algo emerge desde las sombras para recibirte.
```

**Enemigo:** `crear_demonio_final()` – Jefe secreto sin identificar en v0.2.3

---

## 🎬 Finales Secretos y Condiciones

### Matriz de Finales

| Final | Código | Arma | Condición | Narrativa |
|-------|--------|------|-----------|-----------|
| **Derrota Normal** | `fin_derrota()` | Cualquiera | Perder combate | Game Over → Muerte |
| **Resurrección** | `fin_derrota()` → `_flg1` | Cualquiera | Usar SECRETO 6 | Revive a media vida |
| **Heredero de Sangre** | `_fate_02()` | **Hoz de Sangre** | Derrotar Amo | Poder oscuro adquirido |
| **Portador de Noche** | `_fate_03()` | **Hoja de la Noche** | Derrotar Amo | Las sombras reconocen |
| **Final Normal** | `_fate_01()` | Otra/Ninguna | Derrota Amo base | Escape ordinario |
| **Matanza Extrema** | `_fate_04()` | Cualquiera | **100+ kills** | Bestia de mazmorra |
| **Sangre Dominada** | `_fate_06()` | Cualquiera | **66+ kills + sangre ≥ 1** | Portal final (Rickroll) |
| **Resurrección Maldita** | `_fate_05()` | Cualquiera | Morir + SECRETO 6 | Descomposición eterna |

### Decisión de Finales en Flujo

```
1. ¿Está vivo al terminar?
   ├─ NO → fin_derrota()
   │      └─ SECRETO 6 disponible: "lo que esta muerto no puede morir"
   │
   └─ SÍ → Chequear enemigo vencido
          ├─ Si enemigo.final_secreto → _fate_02() (AMO)
          │
          └─ Chequear ruta secreta
             ├─ Si estado["pasos_secretos"] == ruta_secreta
             │  └─ Combate final contra demonio
             │
             └─ Chequear kills
                ├─ Si kills ≥ 100 → _fate_04()
                ├─ Si kills ≥ 66 AND sangre ≥ 1 → _fate_06()
                ├─ Si "Hoja de la Noche" → _fate_03()
                ├─ Si "Hoz de Sangre" → _fate_02()
                └─ Sino → _fate_01()
```

---

## 🔐 Variables de Control Ocultas

### Flags de Progresión Especial

| Variable | Tipo | Alcance | Descripción |
|----------|------|---------|-------------|
| `_x9f` | BOOL | Personaje | Se activó SECRETO 6 (resurrección) |
| `_flg1` | BOOL | Personaje | Marcador de renacimiento especial |
| `_huyo_combate` | BOOL | Personaje | Flag temporal de escape en combate |
| `final_secreto` | BOOL | Enemigo | Marks si es Amo (trigger `_fate_02`) |
| `conocimiento_plaga` | BOOL | Personaje | SECRETO 3 desbloqueado |

### Variables de Persistencia

Se guardan en `savefile.json`:

```python
"pasos_secretos": [],           # Progreso en ruta secreta
"ruta_jugador": [],             # Historial completo de movimientos (i/d)
"hitos_brazos_reclamados": [],  # Brazos específicos reclamados
```

### Variables de Rastreo

| Variable | Inicio | Rango | Uso |
|----------|--------|-------|-----|
| `textos_exploracion` | 0 | 1-15 | Índice de exploración actual |
| `progreso_s` | 0 | 0-10 | Avance en ruta secreta |
| `racha_previa` | 0 | 0-10 | Racha anterior (para cambios) |

---

## 📚 Referencias Cruzadas

### Eventos que Modifican Secretos

```
Evento 1 (Descanso)
 → Oportunidad de dormirse en lugar tranquilo

Evento 5 (Sombra Tenebrosa)
 → SECRETO 1 (si sombra > 1)
 → +1 armadura si rematada

Evento 9 (Foso de Maniacos) - 1ª vez
 → SECRETO 2a (si sangre > 1)
 → +1 armadura si escapado
 → Final anticipado

Evento 12 (Foso de Maniacos) - 2ª vez
 → SECRETO 2b (idéntico a 2a)
 → Difícil sin mejoras de armas

Exploración 14 (Templo Subterráneo)
 → SECRETO 3 (rezar)
 → Desbloquea conocimiento_plaga

Encuentro Hombrecillo (Variable)
 → SECRETO 5 (hablar)
 → +1 brazos por cada aceptación
```

### Armas que Importan

| Arma | Efecto Secreto | Ruta |
|------|---|---|
| **Hoz de Sangre** | Trigger final Blood Heir | Sangre → Evento ritual |
| **Hoja de la Noche** | Trigger final Night Bearer | Sombra → Reconnaissance |
| **Otra/Ninguna** | Final normal | Neutral |

### Enemigos Especiales

| Enemigo | Variable | Trigger |
|---------|----------|---------|
| **Sombra Tenebrosa** | sombra | Exploración normal |
| **Rabioso** | sangre | Eventos violentos |
| **Hombrecillo** | brazos | Encuentro fijo |
| **Amo de la Mazmorra** | `final_secreto=True` | Combate épico |
| **Demonio Final** | Ruta secreta | 10/10 pasos |

---

## 💾 Resumen de Archivo

**Archivo Principal:** `TLDRDC/code/TLDRDC_Prueba1.py`

**Funciones Clave:**
- `susurros_aleatorios()` → Línea 2374 (diálogos ocultos)
- `fin_derrota()` → Línea 2403 (SECRETO 6)
- `_fate_01/02/03/04/05/06()` → Líneas 2420-2550 (finales)
- `ejecutar_final_normal_por_arma()` → Línea 2517
- `racha()` → No encontrado (importado, verificar módulos)

**Variables Globales:**
- `estado["pasos_secretos"]` → Línea 285
- `ruta_secreta` → Línea 722
- `personaje["sangre/sombra/brazos"]` → Línea 768-769

---

## 🎯 Guía de Uso

### Para Jugadores

1. **Busca SECRETO 3** primero (templo, exploración 14, `rezar`)
2. **Aumenta sangre/sombra** mediante eventos
3. **Sigue la ruta secreta**: `d-i-d-d-i-d-i-d-i-d`
4. **Negocia con el desconocido** (`brazos`)
5. **Muere intentando SECRETO 6**: `lo que esta muerto no puede morir`
6. **Equipate la Hoz o Hoja** para finales específicos

### Para Desarrolladores

1. Agregar nuevo secreto → Duplicar estructura SECRETO_N
2. Modificar ruta secreta → Editar `ruta_secreta = [...]` línea 722
3. Nuevo final → Crear `_fate_0X()` y enlazar en flujo
4. Verificar variables → Revisar `_KEYS_VALIDAS` línea 2551

---

**Última actualización:** v0.2.3 (abril 2026)  
**Autor:** TLDRDC Game Logic  
**Estado:** Completo (6/6 secretos documentados)
