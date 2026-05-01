# 🎮 UI TESTER - REFERENCIA COMPLETA DE COMANDOS

## 📋 ALCANCE VERIFICADO

### 1. ARMAS (12 total)
**Nombres exactos (case-insensitive):**
```
daga
espada
martillo
porra
maza
lanza
estoque
cimitarra
Mano de Dios
Hoz de Sangre
Hoja de la Noche
Hacha Ritual
```

**Abreviaturas aceptadas:**
```
dag  → daga
esp  → espada
mar  → martillo
por  → porra
maz  → maza
lan  → lanza
est  → estoque
cim  → cimitarra
man  → Mano de Dios
hoz  → Hoz de Sangre
hoj  → Hoja de la Noche
hac  → Hacha Ritual
```

---

### 2. ENEMIGOS (6 básicos + 1 jefe = 7 total)

**Enemigos normales (nombres exactos):**
```
Larvas de Sangre      [vida: 10,  daño: 1-2,  esquiva: 17]
Mosca de Sangre       [vida: 15,  daño: 1-2,  esquiva: 15]
Maniaco Mutilado      [vida: 14,  daño: 1-3,  esquiva: 10]
Perturbado            [vida: 18,  daño: 2-3,  esquiva: 12]
Rabioso               [vida: 22,  daño: 2-4,  esquiva: 5]
Sombra tenebrosa      [vida: 15,  daño: 3-5,  esquiva: 15]
```

**Enemigo Jefe:**
```
Carcelero             [vida: 30+, daño: 4-6,  esquiva: 10] (evento 13 / final)
```

---

### 3. EVENTOS (20 procedimentalmente generados)

**Cada evento está mapeado en modules/events.py:**
```
_evento_1   → ... (búsqueda de cofre)
_evento_2   → ...
...
_evento_13  → JEFE: Carcelero
...
_evento_20  → ... (final del nivel actual)
```

**Nota:** Eventos pueden activar combates derivados:
- Algunos eventos → enemigo_aleatorio()
- Otros eventos → enemigo_aleatorio("nombre_específico")
- Algunos eventos → aparecen múltiples enemigos

---

## 🎯 FASE 1: ESTRUCTURA BASE + PARSER + ARMAS

### Funcionalidades:
1. ✅ Importar `Vista` sin modificación
2. ✅ Mocks: personaje_global, funciones narrativas
3. ✅ Parser con comando: `arma [nombre]`
4. ✅ Prueba flujo completo: arma → dropdown → sprite actualiza

### Viabilidad: **9.5/10** ✅
- Reutiliza `añadir_arma()` existente
- No necesita Queue aún (sin combates)
- Testing simple: agregar armas, ver sprites

### Riesgos: NINGUNO (fase trivial)

---

## 🎯 FASE 2: COMBATE CON QUEUE

### Viabilidad: **9/10** (con cuidado de sincronización)

**Cómo funciona:**
1. Parser recibe: `combate [enemigo_nombre]`
2. Crea Queue para input
3. Ejecuta: `combate(personaje_global, enemigo)` en worker thread
4. Combate llama: `pedir_input()` → **QUEDA ESPERANDO EN QUEUE**
5. Parser escribe en queue: "d" (atacar)
6. Combate continúa
7. Se repite hasta victoría/derrota

**Riesgos mitigados:**
- ⚠️ Timeout en Queue (evita bloqueo infinito)
- ⚠️ Validación de entrada (solo "d", "p", etc)
- ⚠️ Sincronización de UI (root.after() para widgets)

---

## 🎯 FASE 3: EVENTOS

### Viabilidad: **8.5/10** (algunos eventos son complejos)

**Funciones requeridas:**
- `evento_aleatorio(personaje)` → ejecuta evento N
- `obtener_evento_de_bolsa()` → tipo random de bolsa
- Cada `_evento_X()` puede tener múltiples `pedir_input()`

**Riesgos:**
- ⚠️ Eventos con diálogos complejos (múltiples inputs)
- ⚠️ Algunos eventos muestran imágenes (panel derecho)
- ⚠️ Eventos pueden triggerar combates anidados

---

## ✅ RECOMENDACIÓN FINAL

**OPCIÓN A ES 100% VIABLE**

### Razones:
1. **Cola de entrada (Queue)** es patrón probado en UI + threads
2. **Todos los nombres clave están mapeados** - parser puede validar
3. **Funciones originales son importables** - Sin modificación
4. **UI es reutilizable** - No hay conflictos de arquitectura

### Implementación secuencial:
```
Fase 1: 2 horas   (parser + armas)
Fase 2: 3 horas   (Queue + combate)
Fase 3: 2 horas   (eventos simples)
Bonus: 1 hora     (debugging tools)
─────────────────
Total: 8 horas
```

---

## 🔧 PARSER SPECIFICATION (Fase 1 + 2 + 3)

```
COMANDO              PARÁMETRO            FUNCIÓN
─────────────────────────────────────────────────────────────
arma [nombre]        arg1: nombre arma    → Ejecuta añadir_arma()
                                          Valida contra: [12 nombres]

combate [enemigo]    arg1: enemigo        → Ejecuta combate()
                                          Valida contra: [6 nombres + aleatorio]

evento [número]      arg1: 1-20           → Ejecuta _evento_X()
                                          Valida: 1-20 (inyectar en _evento_X)

pociones [número]    arg1: 0-10           → SOLO TEST: set personaje["pociones"]

stats [attr] [val]   arg1: atributo       → SOLO TEST: set personaje[attr] = val
                     arg2: número         Válidos: vida, fuerza, destreza, armadura

inventory            -                    → Lista armas actuales

help                 -                    → Muestra todos los comandos

status               -                    → Muestra estado actual (vida, armas, etc)

clear                -                    → Limpia panel de texto

exit                 -                    → Salir tester
```

---

## 🚀 LISTO PARA FASE 1

Todos los nombres clave están validados. Parser puede chequear entrada contra listas hardcodeadas.

**Siguiente paso:** Implementar Fase 1
