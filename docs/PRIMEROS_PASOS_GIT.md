# Primeros Pasos con Git y GitHub

Una guía técnica y didáctica para entender las bases de versionado con Git y cómo utilizarlo en GitHub.

---

## 1. Conceptos Fundamentales

### ¿Qué es Git?

Git es un **sistema de control de versiones distribuido** que registra cambios en archivos a lo largo del tiempo. Permite:

- Rastrear quién cambió qué y cuándo
- Revertir cambios a versiones anteriores
- Trabajar en paralelo sin perder el historial
- Mantener un registro completo de la evolución del proyecto

### ¿Qué es GitHub?

GitHub es una **plataforma web** que aloja repositorios Git en la nube. Funciona como:

- Servidor remoto (almacenamiento en la nube)
- Interfaz visual para gestionar proyectos
- Sistema de colaboración (pull requests, issues)
- Portfolio de código para desarrolladores

### La Relación: Local vs Remoto

```
Tu Computadora (Local)          GitHub (Remoto)
┌──────────────────┐            ┌──────────────────┐
│  Repository      │  ← git ──→ │  Repository      │
│  (carpeta .git)  │   push     │  (en la nube)    │
│                  │   pull     │                  │
└──────────────────┘            └──────────────────┘
```

---

## 2. Instalación y Configuración Inicial

### Paso 1: Instalar Git

**Windows**: Descarga desde [git-scm.com](https://git-scm.com)

Verifica la instalación:
```bash
git --version
```

### Paso 2: Configurar Identidad Global

Git necesita saber quién eres para registrar cambios:

```bash
git config --global user.name "Tu Nombre"
git config --global user.email "tu.email@ejemplo.com"
```

**Verificar configuración**:
```bash
git config --list
```

---

## 3. Flujo de Trabajo Básico

### El Ciclo: Working Directory → Staging → Repository

```
Cambios sin    Cambios        Cambios
registrar      preparados     guardados
    ↓             ↓              ↓
[Working Dir] → [Staging] → [Repository]
    ↑             ↑              ↑
 git add      git commit    (histórico)
```

### Fase 1: Inicializar un Repositorio Local

En la carpeta de tu proyecto:

```bash
git init
```

Esto crea una carpeta oculta `.git` que almacena todo el historial.

### Fase 2: Agregar Archivos al Staging

Después de realizar cambios, prepáralos para guardar:

```bash
# Agregar un archivo específico
git add archivo.py

# Agregar todos los cambios
git add .
```

**Visualizar cambios pendientes**:
```bash
git status
```

### Fase 3: Hacer un Commit

Guardar cambios con un mensaje descriptivo:

```bash
git commit -m "Descripción clara del cambio"
```

**Estructura de mensaje recomendada** (Conventional Commits):
```
tipo(alcance): descripción corta

Descripción más detallada si es necesario.
```

**Tipos comunes**:
- `feat`: Nueva funcionalidad
- `fix`: Corrección de error
- `docs`: Cambios en documentación
- `refactor`: Reescritura sin cambiar funcionalidad
- `perf`: Mejoras de rendimiento
- `test`: Cambios en tests

**Ejemplo**:
```bash
git commit -m "feat(events): agregar nuevo sistema de eventos modularizado"
```

### Fase 4: Ver el Histórico

Visualizar todos los commits realizados:

```bash
git log
```

Versión más visual:
```bash
git log --oneline --graph --all
```

---

## 4. Conectar con GitHub

### Paso 1: Crear Repositorio en GitHub

1. Ve a [github.com](https://github.com)
2. Click en "New" (botón verde)
3. Nombre: `TLDRDC`
4. Descripción: "The Lost Dire Realm: Dungeon Crawler"
5. Público o Privado (tu elección)
6. **NO inicialices con README** (ya lo tienes localmente)
7. Click "Create repository"

### Paso 2: Conectar Local con Remoto

GitHub te mostrará comandos. En tu terminal local:

```bash
git remote add origin https://github.com/TU_USUARIO/TLDRDC.git
git branch -M main
git push -u origin main
```

**Explicación**:
- `git remote add origin URL`: Registra dónde está el repositorio remoto
- `git branch -M main`: Renombra rama principal a `main` (estándar de GitHub)
- `git push -u origin main`: Sube todos tus commits a GitHub

### Paso 3: Verificar Conexión

```bash
git remote -v
```

Deberías ver:
```
origin  https://github.com/TU_USUARIO/TLDRDC.git (fetch)
origin  https://github.com/TU_USUARIO/TLDRDC.git (push)
```

---

## 5. Flujo de Trabajo Diario

### Ciclo Típico

```bash
# 1. Ver estado actual
git status

# 2. Hacer cambios en tus archivos (editor de código)

# 3. Ver qué cambió
git diff

# 4. Preparar cambios
git add .

# 5. Guardar con mensaje
git commit -m "tipo: descripción del cambio"

# 6. Sincronizar con GitHub
git push origin main
```

### Actualizar tu Local desde GitHub

Si alguien más realizó cambios (o trabajas desde otra máquina):

```bash
git pull origin main
```

Esto descarga y fusiona cambios automáticamente.

---

## 6. Ramas (Branches)

### ¿Qué es una Rama?

Una rama es una **línea paralela de desarrollo**. Permite:

- Trabajar en nuevas funciones sin afectar el código principal
- Mantener una rama `main` siempre funcional
- Colaborar sin conflictos

```
main    ──●──●──●──●──●
              │
develop      └──●──●──●
```

### Usar Ramas Locales

**Crear nueva rama**:
```bash
git branch nombre-rama
```

**Cambiar a una rama**:
```bash
git checkout nombre-rama
```

**O ambos en uno**:
```bash
git checkout -b nombre-rama
```

**Ver todas las ramas**:
```bash
git branch -a
```

**Ver en qué rama estás**:
```bash
git status
```

### Ejemplo Práctico

```bash
# Crear rama para nueva funcionalidad
git checkout -b feat/sistema-guardado

# Trabajar en la rama...
# Hacer cambios, commits, etc.

# Cambiar a main
git checkout main

# Merging: fusionar cambios de rama en main
git merge feat/sistema-guardado

# Eliminar rama (ya no la necesitas)
git branch -d feat/sistema-guardado

# Subir main actualizado a GitHub
git push origin main
```

---

## 7. Buenas Prácticas

### Mensajes de Commit Claros

❌ **Malo**:
```
git commit -m "cambios"
git commit -m "fix stuff"
git commit -m "updates"
```

✅ **Bueno**:
```bash
git commit -m "fix(ui): corregir alineación de botones en pantalla de combate"
git commit -m "feat(events): agregar nuevo evento de encuentro con NPC"
git commit -m "docs: actualizar README con instrucciones de instalación"
```

### Commits Pequeños y Lógicos

❌ **Malo**: Un commit gigante cada semana

✅ **Bueno**: Múltiples commits pequeños, cada uno representa un cambio lógico

### .gitignore

Archivo que especifica qué NO subir a GitHub:

```
# .gitignore
__pycache__/
*.pyc
.venv/
.env
node_modules/
dist/
build/
```

---

## 8. Resolver Conflictos

### ¿Cuándo Ocurren Conflictos?

Cuando dos ramas modifican el mismo archivo en el mismo lugar durante un merge.

### Solucionar Conflictos

1. **Git te avisará**:
```
CONFLICT (content merge): Merge conflict in archivo.py
```

2. **Abre el archivo** - verás algo así:
```python
<<<<<<< HEAD
código de main
=======
código de la rama
>>>>>>> feat/mi-rama
```

3. **Resuelve manualmente**: Elige qué código mantener

4. **Marca como resuelto**:
```bash
git add archivo.py
git commit -m "Resolver conflicto de merge"
```

---

## 9. Referencia de Comandos Útiles

| Comando | Función |
|---------|---------|
| `git init` | Inicializar repositorio |
| `git add .` | Preparar todos los cambios |
| `git commit -m "msg"` | Guardar cambios |
| `git push` | Subir a GitHub |
| `git pull` | Descargar cambios de GitHub |
| `git status` | Ver estado actual |
| `git log` | Ver histórico de commits |
| `git branch` | Listar/crear/eliminar ramas |
| `git checkout -b rama` | Crear y cambiar a rama |
| `git merge rama` | Fusionar rama en actual |
| `git diff` | Ver cambios no preparados |
| `git reset HEAD archivo` | Deshacer `git add` |
| `git revert COMMIT` | Deshacer commit (crea nuevo commit inverso) |

---

## 10. Primeros Pasos en Tu Proyecto TLDRDC

### Desglose Paso a Paso

```bash
# 1. Navega a tu carpeta del proyecto
cd c:\Users\User\Desktop\codigos\TLDRDC

# 2. Inicializa Git
git init

# 3. Configura tu identidad (si no lo hiciste globalmente)
git config user.name "Salva_BsK"
git config user.email "tu.email@ejemplo.com"

# 4. Agrega todos los archivos
git add .

# 5. Primer commit
git commit -m "Initial commit: TLDRDC v0.2.0 - Modularización y Refactorización"

# 6. Ve a GitHub y crea nuevo repositorio 'TLDRDC'

# 7. Conecta con remoto
git remote add origin https://github.com/BerserkXIII/TLDRDC.git
git branch -M main
git push -u origin main

# 8. Verifica en GitHub.com/BerserkXIII/TLDRDC
```

---

## Glosario de Términos

### A

**Add (git add)**
Preparar cambios para hacer commit. Los archivos pasan del Working Directory al Staging Area.

**Archivo .git**
Carpeta oculta creada por `git init` que contiene todo el historial y metadatos del repositorio.

---

### B

**Branch (Rama)**
Línea paralela de desarrollo. Permite trabajar en nuevas funciones sin afectar el código principal.

**Backup**
Copia de seguridad. Git mantiene backups implícitos en el histórico de commits.

---

### C

**Checkout**
Cambiar a una rama o versión diferente del código.

**Clone**
Descargar un repositorio remoto completo a tu máquina local.

**Commit**
Guardar cambios con un mensaje descriptivo. Es un "snapshot" del proyecto en ese momento.

**Conflicto (Merge Conflict)**
Situación donde dos cambios en el mismo archivo entran en conflicto durante un merge.

---

### D

**Diff**
Mostrar las diferencias entre versiones. Qué líneas se agregaron, eliminaron o modificaron.

**Distributed (Distribuido)**
Git es distribuido: cada clon local es un repositorio completo con todo el historial.

---

### F

**Fetch**
Descargar cambios de GitHub sin fusionarlos automáticamente.

**Fork**
Copia de un repositorio en tu cuenta de GitHub, útil para contribuir a proyectos ajenos.

---

### G

**GitHub**
Plataforma web que aloja repositorios Git y facilita colaboración.

**Git**
Sistema de control de versiones distribuido. Registra cambios en archivos a lo largo del tiempo.

**Gitignore**
Archivo que especifica qué archivos/carpetas NO deben ser rastreados por Git.

---

### H

**HEAD**
Referencia apuntando al commit actual (usualmente el último de la rama en la que estás).

**History (Histórico)**
Registro completo de todos los commits realizados. Visible con `git log`.

---

### I

**Issue**
Tarea, bug o mejora registrada en GitHub. Parte del sistema de seguimiento de proyectos.

---

### L

**Local**
Tu computadora. El repositorio en tu máquina.

---

### M

**Main**
Nombre de la rama principal (reemplazó a "master" en 2020). Usualmente la rama de código producción-listo.

**Merge**
Fusionar cambios de una rama a otra. Combina el histórico de commits.

---

### O

**Origin**
Nombre por defecto del repositorio remoto en GitHub. Referencia a la ubicación en la nube.

---

### P

**Pull**
Descargar cambios de GitHub y fusionarlos automáticamente en tu rama local.

**Push**
Subir tus commits locales a GitHub.

---

### R

**Remote**
Ubicación del repositorio en la nube (GitHub). Opuesto a "local".

**Repository (Repositorio)**
Carpeta que contiene el proyecto completo con histórico de Git.

**Revert**
Deshacer un commit creando un nuevo commit inverso (no elimina el histórico).

---

### S

**Staging Area (Índice)**
Zona intermedia donde preparas cambios antes de hacer commit.

**Stash**
Guardar cambios temporalmente sin hacer commit, útil para cambiar de rama sin perder trabajo.

---

### V

**Version Control**
Sistema que registra cambios en archivos a lo largo del tiempo.

---

### W

**Working Directory**
Carpeta donde trabajas localmente. Los archivos que ves y editas día a día.

---

### Z

**Zona de Conflicto**
Área dentro de un archivo donde Git no puede resolver automáticamente qué cambios mantener durante un merge.

---

## Recursos Adicionales

- **Documentación oficial Git**: https://git-scm.com/doc
- **GitHub Guides**: https://guides.github.com
- **Visualizador interactivo**: https://git-school.github.io/visualizing-git/
- **Cheat Sheet Git**: https://education.github.com/git-cheat-sheet-education.pdf

---

## Siguientes Pasos

1. ✅ Instala Git y configúralo
2. ✅ Haz `git init` en tu proyecto TLDRDC
3. ✅ Crea tu primer commit
4. ✅ Crea un repositorio en GitHub
5. ✅ Conecta local con remoto (`git remote add origin`)
6. ✅ Haz tu primer push (`git push -u origin main`)
7. ⏭️ Explora ramas y colaboración

---

**Última actualización**: 19 de marzo de 2026  
**Versión**: 1.0  
**Autor**: Documentación creada por IA, dirigida y revisada por Salva_BsK
