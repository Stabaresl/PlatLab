# PlatLAB

Plataforma de laboratorios prácticos de ciberseguridad / hacking ético. Un
instructor publica laboratorios (teoría + práctica guiada + flags + examen
final), invita estudiantes, y cada estudiante resuelve el laboratorio desde
una consola en el navegador — ya sea una terminal **simulada** (guion de
comandos predefinido) o una terminal **real**, conectada por WebSocket a un
contenedor Docker descartable y aislado por estudiante.

Backend en Django (arquitectura hexagonal por módulos) + frontend en React.
Documentación funcional y técnica extendida, sprint a sprint, en
[`Documentación/`](./Documentación).

---

## Índice

- [Stack](#stack)
- [Requisitos previos](#requisitos-previos)
- [Instalación y arranque (Docker — recomendado)](#instalación-y-arranque-docker--recomendado)
- [Frontend](#frontend)
- [Credenciales de prueba](#credenciales-de-prueba)
- [Probar el flujo completo](#probar-el-flujo-completo)
- [Correr sin Docker (backend nativo)](#correr-sin-docker-backend-nativo)
- [Tests](#tests)
- [Variables de entorno](#variables-de-entorno)
- [Solución de problemas comunes](#solución-de-problemas-comunes)
- [Estructura del proyecto](#estructura-del-proyecto)

---

## Stack

**Backend**
- Python 3.12, Django 6, Django REST Framework
- PostgreSQL 16, Redis 7
- Celery + Celery Beat (tareas asíncronas, vencimiento de asignaciones, reaper de entornos inactivos)
- Django Channels + Daphne (WebSocket, sirve la terminal real)
- `docker` (SDK de Python) — el backend crea/gestiona contenedores Docker "hermanos" para cada entorno de práctica

**Frontend**
- React 19 + TypeScript + Vite
- Tailwind CSS 4 + shadcn/ui (Radix UI)
- framer-motion, anime.js (animaciones)
- xterm.js (terminal real por WebSocket)

**Infraestructura de desarrollo**: Docker Compose (`postgres`, `redis`, `web`, `worker`, `beat`).

---

## Requisitos previos

Instalá esto **antes** de clonar/arrancar, o vas a tener errores:

| Herramienta | Versión mínima | Para qué | Verificar con |
|---|---|---|---|
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | reciente, con WSL2 backend en Windows | correr Postgres/Redis/backend y los contenedores de cada laboratorio | `docker --version` y `docker compose version` |
| [Git](https://git-scm.com/) | cualquiera reciente | clonar el repo | `git --version` |
| [Bun](https://bun.sh/) | 1.x (o Node.js 20+ y npm como alternativa) | frontend | `bun --version` |
| Python | 3.12+ | **solo** si vas a correr el backend fuera de Docker | `python --version` |

**Windows**: Docker Desktop debe estar corriendo con el backend **WSL2** activado (no Hyper-V clásico) — el backend monta `/var/run/docker.sock` dentro del contenedor `web`/`worker` para poder crear los contenedores de cada laboratorio, y eso solo funciona de forma confiable con WSL2. Abrí Docker Desktop y esperá a que la ballena del ícono de la bandeja quede fija (no animada) antes de arrancar.

---

## Instalación y arranque (Docker — recomendado)

Este es el camino soportado y probado: todo el backend (API, worker, beat, base de datos, Redis) corre en contenedores, y el mismo Docker que los corre es el que el backend usa para levantar los laboratorios ("Docker-outside-of-Docker").

### 1. Clonar el repositorio

```bash
git clone <url-del-repo>
cd PlatLab
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
```

Los valores por defecto de `.env.example` ya funcionan para desarrollo local (no hace falta tocar nada para levantar el proyecto). Si querés cambiar contraseñas de Postgres o activar OAuth real, editá `.env` — ver [Variables de entorno](#variables-de-entorno).

`.env` **nunca** se sube al repositorio (está en `.gitignore`) — cada quien mantiene el suyo local.

### 3. Levantar los servicios

```bash
docker compose up --build
```

Esto levanta 4 servicios (Postgres y Redis se descargan la primera vez, puede tardar unos minutos):

- `postgres` — base de datos (puerto `5432`)
- `redis` — caché / broker de Celery / refresh tokens (puerto `6379`)
- `web` — Daphne sirviendo la API REST + WebSocket en `http://localhost:8000` (HTTP y WS en el mismo proceso ASGI, por eso no se usa `runserver`)
- `worker` — Celery worker (notificaciones, auditoría, vencimiento de asignaciones)
- `beat` — Celery Beat (dispara tareas periódicas: expira asignaciones vencidas, apaga entornos Docker inactivos)

El contenedor `web` corre las migraciones automáticamente al arrancar (`docker/entrypoint.sh`) — no hace falta correr `migrate` a mano.

Para correrlo en segundo plano: `docker compose up -d --build`. Para ver logs: `docker compose logs -f web`. Para parar todo: `docker compose down` (agregá `-v` si además querés borrar los datos de Postgres).

### 4. Cargar datos de demo

Con los contenedores corriendo, en otra terminal:

```bash
docker compose exec web python manage.py seed_demo_data
```

Esto crea (si no existen ya) los tres usuarios de prueba de la sección siguiente, un laboratorio plantilla publicado y visible en el catálogo público, una copia del instructor con examen, y una asignación ya aceptada del estudiante — es decir, deja la plataforma en un estado navegable de punta a punta sin cargar nada a mano. El comando es idempotente: correrlo de nuevo no duplica datos.

En este punto el backend ya está arriba y probado en `http://localhost:8000/api/v1/`.

---

## Frontend

En otra terminal, desde la raíz del repo:

```bash
cd frontend
bun install     # o: npm install
bun run dev     # o: npm run dev
```

Se sirve en `http://localhost:5173`. Por defecto apunta al backend en `http://localhost:8000/api/v1` (ver `frontend/src/pages/api.ts`); si necesitás otra URL, creá `frontend/.env.local`:

```bash
VITE_API_URL=http://localhost:8000/api/v1
# Solo si configuraste credenciales OAuth reales en el backend:
# VITE_OAUTH_ENABLED=true
```

Los botones de login social (Google/GitHub) están ocultos por defecto porque no hay credenciales OAuth configuradas — es el comportamiento esperado en un entorno de prueba, no un error.

---

## Credenciales de prueba

Creadas por `seed_demo_data` (ver paso 4 arriba). Un rol por usuario:

| Rol | Email | Contraseña |
|---|---|---|
| Administrador | `admin@platlab.demo` | `Admin1234` |
| Instructor | `instructor@platlab.demo` | `Instructor1234` |
| Estudiante | `estudiante@platlab.demo` | `Estudiante1234` |

Entrá en `http://localhost:5173/login` con cualquiera de estos para ver el dashboard correspondiente a ese rol.

---

## Probar el flujo completo

Con backend + frontend arriba y `seed_demo_data` ya corrido:

1. **Como estudiante** (`estudiante@platlab.demo`) — entrá al Dashboard, vas a ver el laboratorio ya asignado por el seed. Abrilo, recorré las secciones (teoría + guía práctica), enviá la flag de la sección práctica y completá el examen final al terminar todas las secciones.
2. **Terminal simulada vs. real**: dentro de una sección con práctica, el toggle de terminal permite elegir entre la simulada (guion de comandos, no ejecuta nada real) y la real (xterm.js conectado por WebSocket a un contenedor Docker efímero — tarda unos segundos en "conectar" la primera vez mientras el backend levanta el contenedor).
3. **Como instructor** (`instructor@platlab.demo`) — vas a ver la copia del laboratorio que duplicó del catálogo, con la opción de editar secciones, definir flags y armar el examen.
4. **Como administrador** (`admin@platlab.demo`) — panel de administración general (usuarios, laboratorio plantilla).
5. **Catálogo público** (`http://localhost:5173/laboratorios`, sin necesidad de login) — muestra el laboratorio plantilla publicado por el admin.

Si algo de esto no carga, revisá primero [Solución de problemas comunes](#solución-de-problemas-comunes).

---

## Correr sin Docker (backend nativo)

Alternativa para desarrollar el backend sin reconstruir la imagen en cada cambio. Necesitás igualmente **Postgres y Redis corriendo** (podés levantar solo esos dos con Docker: `docker compose up postgres redis`) **y Docker Desktop corriendo en el host** si querés que funcionen los entornos reales de laboratorio (el backend igual necesita hablarle a un daemon Docker).

```bash
python -m venv venv
# Windows (PowerShell):
venv\Scripts\Activate.ps1
# Linux/Mac:
source venv/bin/activate

pip install -r requirements/dev.txt

# Editá .env: POSTGRES_HOST=localhost (no "postgres", ese nombre solo
# resuelve dentro de la red de docker-compose)

python manage.py migrate
python manage.py seed_demo_data

# Daphne, no runserver — runserver no entiende WebSockets y la terminal
# real del frontend se queda "conectando" para siempre:
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

En otra terminal, para las tareas periódicas (vencimiento de asignaciones, apagado de entornos inactivos):

```bash
celery -A config worker -l info
celery -A config beat -l info
```

---

## Tests

**Backend** (pytest, corre contra `config.settings.test` — Celery en modo síncrono, no necesita worker real):

```bash
docker compose exec web pytest
# o, con el venv activado y Postgres/Redis corriendo:
pytest
```

**Frontend** (type-check + lint):

```bash
cd frontend
bun run build   # tsc -b + vite build, falla si hay errores de tipos
bun run lint
```

---

## Variables de entorno

Definidas en `.env` (ver `.env.example` para la plantilla completa):

| Variable | Uso | ¿Hace falta tocarla para desarrollo local? |
|---|---|---|
| `SECRET_KEY` | clave de Django | no (usá el valor de ejemplo solo en local, nunca en producción) |
| `DEBUG` | modo debug de Django | no |
| `ALLOWED_HOSTS` | hosts permitidos | no |
| `CORS_ALLOWED_ORIGINS` | orígenes permitidos para el frontend | no, ya incluye `localhost:5173` |
| `POSTGRES_*` | conexión a la base de datos | no, salvo que cambies credenciales |
| `REDIS_URL` | Celery/refresh tokens/canal de Channels | no |
| `DEFAULT_FROM_EMAIL` | remitente de emails (dev usa consola, no envía nada real) | no |
| `GOOGLE_OAUTH_*`, `GITHUB_OAUTH_*` | login social | solo si querés probar OAuth real; si no, dejalos en `changeme` y los botones quedan ocultos |

**Frontend** (`frontend/.env.local`, opcional, no versionado):

| Variable | Default si no se define |
|---|---|
| `VITE_API_URL` | `http://localhost:8000/api/v1` |
| `VITE_OAUTH_ENABLED` | `false` (oculta los botones de Google/GitHub) |

---

## Solución de problemas comunes

**`docker compose up` falla en `web` con error de permisos sobre `/var/run/docker.sock`**
En Windows, confirmá que Docker Desktop esté corriendo con el backend **WSL2** (Settings → General → "Use the WSL 2 based engine"). Con el backend Hyper-V clásico, el socket no queda expuesto de forma compatible con este montaje.

**`port is already allocated` para 5432 / 6379 / 8000 / 5173**
Ya tenés otro Postgres/Redis/servidor corriendo en ese puerto (local o de otro proyecto). Parálo, o cambiá el mapeo de puertos en `docker-compose.yml`/`vite.config.ts` para ese servicio.

**El frontend carga pero todas las peticiones a la API fallan / error de CORS en la consola del navegador**
Confirmá que el backend esté arriba en `http://localhost:8000` y que `CORS_ALLOWED_ORIGINS` en `.env` incluya la URL exacta desde la que corre el frontend (por defecto `http://localhost:5173`).

**La terminal "real" de un laboratorio se queda en "conectando..." indefinidamente**
- Confirmá que el backend se está sirviendo con `daphne` (Docker Compose ya lo hace) y no con `python manage.py runserver` — `runserver` no soporta WebSockets.
- Confirmá que Docker Desktop está corriendo (el backend necesita crear un contenedor nuevo para ese entorno) y que el contenedor `web` tiene montado `/var/run/docker.sock` (ya viene así en `docker-compose.yml`).
- Mirá `docker compose logs -f worker` y `docker compose logs -f web` por errores del SDK de Docker.

**`seed_demo_data` falla o no crea nada**
Es idempotente pero necesita las migraciones ya aplicadas — si corriste el backend sin Docker, asegurate de haber corrido `python manage.py migrate` antes. Si falla a mitad de camino (por ejemplo, se cortó Postgres), volvé a correrlo: retoma desde donde falló sin duplicar lo ya creado.

**No tengo Bun instalado**
Todos los comandos `bun ...` de este README tienen equivalente en `npm`: `bun install` → `npm install`, `bun run dev` → `npm run dev`, etc. El repo versiona `bun.lock`, así que si usás npm vas a generar tu propio `package-lock.json` local (no hace falta commitearlo salvo que el equipo decida migrar el proyecto a npm).

**Los botones de login con Google/GitHub no aparecen**
Es el comportamiento esperado sin credenciales OAuth reales configuradas — ver [Variables de entorno](#variables-de-entorno). No es un bug.

---

## Estructura del proyecto

Backend organizado por módulos con arquitectura hexagonal (domain / application / infrastructure / presentation) — detalle completo, módulo por módulo, en [`Documentación/estructura-carpetas.md`](./Documentación/estructura-carpetas.md).

```
PlatLab/
├── config/                 # settings, urls, asgi (Channels), celery
├── modules/                 # authentication, users, laboratories, assignments,
│                             # progress, lab_environments, reports,
│                             # notifications, audit — cada uno con sus 4 capas
├── docker/                  # entrypoint.sh + targets vulnerables de demo
├── frontend/                # React + Vite + Tailwind + shadcn/ui
├── requirements/             # base / dev / prod
├── Documentación/            # documentación funcional y técnica por sprint
├── docker-compose.yml
└── .env.example
```

Para el detalle funcional (casos de uso, reglas de negocio, dominio) y el progreso del proyecto sprint a sprint, ver [`Documentación/`](./Documentación).
