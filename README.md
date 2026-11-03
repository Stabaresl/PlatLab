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

## Instalación rápida (para usar la plataforma)

Solo necesitas **Docker Desktop** (Windows/macOS) o **Docker Engine + compose** (Linux), encendido. No hace falta instalar Python, Node ni Bun: todo se construye dentro de Docker.

```bash
git clone <url-del-repo>
cd PlatLab
```

| Sistema | Cómo instalar |
|---|---|
| Windows | Doble clic en **`instalar.cmd`** (o en PowerShell: `.\platlab.ps1`) |
| Linux / macOS | `bash platlab.sh` |

El instalador revisa los requisitos, crea el `.env` con claves aleatorias, construye las imágenes (también las de los laboratorios), levanta todo, carga los laboratorios, el mapa de aprendizaje y los logros, y al final te muestra la dirección para entrar. La primera vez tarda varios minutos; después arranca en segundos.

Te pregunta **cómo se va a usar**:

- **Solo en este computador**: entra por `http://localhost:8080`, con las cuentas demo de la tabla de [credenciales](#credenciales-de-prueba). Nadie más en la red puede entrar.
- **En red / aula**: otros equipos entran por `http://<IP-de-este-equipo>:8080`. Las cuentas demo quedan desactivadas (sus contraseñas están en este README) y creas tu cuenta de administrador; la contraseña se genera y se muestra una sola vez. En Windows, abre el puerto en el firewall (el instalador lo hace si lo ejecutas como administrador, o te da el comando) y verifica que tu red esté marcada como *Privada*.

Para el día a día (en Linux/macOS cambia `.\platlab.ps1` por `bash platlab.sh`):

| Comando | Qué hace |
|---|---|
| `.\platlab.ps1 iniciar` | Enciende la plataforma (por ejemplo, después de reiniciar el equipo) |
| `.\platlab.ps1 detener` | La apaga sin borrar nada |
| `.\platlab.ps1 estado` | Muestra qué servicios están corriendo |
| `.\platlab.ps1 logs [servicio]` | Muestra los registros (`web`, `worker`, `gateway`...) |
| `.\platlab.ps1 actualizar` | Descarga la última versión (`git pull`) y la reconstruye conservando los datos |
| `.\platlab.ps1 desinstalar [-BorrarDatos]` | Elimina los contenedores; con `-BorrarDatos` (`--borrar-datos` en Linux) también la base de datos |

Opciones sin preguntas, por ejemplo para preparar varios equipos: `.\platlab.ps1 instalar -Modo red -Puerto 8090 -AdminEmail profe@universidad.edu.co -SinPreguntas` (en Linux: `--modo red --puerto 8090 --admin-email ... --si`).

**Cómo queda armado.** Todo entra por un único puerto, servido por el contenedor `gateway` (Caddy). Ese contenedor entrega la interfaz ya compilada, hace de proxy hacia la API y el WebSocket de la terminal, y sirve los archivos subidos de forma aislada (`docker-compose.local.yml`, `frontend/Dockerfile`, `frontend/docker/Caddyfile`). El backend corre con `config.settings.local`: `DEBUG` apagado y sobre HTTP, porque en una red local no hay dominio para un certificado. Para publicarlo en internet con HTTPS existe `docker-compose.prod.yml`.

> El instalador y el entorno de desarrollo comparten proyecto de Docker: si después de instalar quieres volver al modo desarrollo (código montado, recarga en caliente, puerto 8000), basta con `docker compose up -d`. Para volver al modo instalado: `.\platlab.ps1 iniciar`.

---

## Índice

- [Instalación rápida (para usar la plataforma)](#instalación-rápida-para-usar-la-plataforma)
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
- Python 3.12, Django 6, Django REST Framework, SimpleJWT
- PostgreSQL 16 (pool de conexiones nativo de Django + psycopg 3), Redis 7
- Uvicorn con varios procesos (HTTP + WebSocket, ASGI) y Django Channels para la terminal real
- Celery + Celery Beat: tareas asíncronas, vencimiento de asignaciones, reaper de entornos inactivos y una cola dedicada (`entornos`) para levantar laboratorios en paralelo
- `docker` (SDK de Python): el backend crea contenedores Docker "hermanos", uno por estudiante, a través de un proxy del socket que solo deja pasar las llamadas necesarias

**Frontend**
- React 19 + TypeScript + Vite
- Tailwind CSS 4 + shadcn/ui (Radix UI)
- framer-motion (animaciones)
- xterm.js (terminal real por WebSocket)

**Infraestructura**: Docker Compose (`postgres`, `redis`, `docker-proxy`, `web`, `worker`, `worker-entornos`, `beat` y, en la instalación local, `gateway`).

---

## Requisitos previos

Para **usar** la plataforma basta con Docker (ver [Instalación rápida](#instalación-rápida-para-usar-la-plataforma)). Para **desarrollar**, instala además:

| Herramienta | Versión mínima | Para qué | Verificar con |
|---|---|---|---|
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | con compose 2.24.4 o superior; en Windows, backend WSL2 | correr Postgres/Redis/backend y los contenedores de cada laboratorio | `docker --version` y `docker compose version` |
| [Git](https://git-scm.com/) | cualquiera reciente | clonar el repo | `git --version` |
| [Bun](https://bun.sh/) | 1.2 o superior (o Node.js 20+ y npm) | frontend en modo desarrollo | `bun --version` |
| Python | 3.12+ | **solo** si vas a correr el backend fuera de Docker | `python --version` |

**Windows**: Docker Desktop debe estar corriendo con el backend **WSL2** activado (no Hyper-V clásico): el proxy del socket de Docker monta `/var/run/docker.sock`, y eso solo funciona de forma confiable con WSL2. Abre Docker Desktop y espera a que diga *Engine running* antes de arrancar.

---

## Instalación y arranque (Docker — recomendado)

Este es el modo de **desarrollo**: el código del repo se monta dentro de los contenedores. Todo el backend (API, workers, beat, base de datos, Redis) corre en Docker, y el mismo Docker que los corre es el que el backend usa para levantar los laboratorios ("Docker-outside-of-Docker").

### 1. Clonar el repositorio

```bash
git clone <url-del-repo>
cd PlatLab
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
```

Los valores de `.env.example` funcionan para desarrollo local. Para cambiar contraseñas de Postgres o activar OAuth real, edita `.env` (ver [Variables de entorno](#variables-de-entorno)).

`.env` **nunca** se sube al repositorio (está en `.gitignore`): cada quien mantiene el suyo.

### 3. Levantar los servicios

```bash
docker compose up --build
```

Esto levanta (la primera vez descarga imágenes y puede tardar unos minutos):

- `postgres`: base de datos (sin puerto publicado; ver `docker-compose.override.example.yml` si necesitas entrar desde el host)
- `redis`: caché, broker de Celery y refresh tokens (sin puerto publicado)
- `docker-proxy`: único punto de contacto con el Docker del host
- `web`: Uvicorn sirviendo la API REST + WebSocket en `http://localhost:8000`
- `worker`: Celery (notificaciones, auditoría, verificación OpenAlex, vencimientos)
- `worker-entornos`: Celery con hilos, dedicado a levantar contenedores de laboratorio
- `beat`: tareas periódicas (expira asignaciones vencidas, apaga entornos inactivos)

Solo `web` corre las migraciones al arrancar (`docker/entrypoint.sh`); los workers esperan a que esté sano.

En segundo plano: `docker compose up -d --build`. Logs: `docker compose logs -f web`. Para parar: `docker compose down` (con `-v` además borras los datos).

### 4. Cargar datos de demo

Con los contenedores corriendo:

```bash
docker compose exec web python manage.py seed_demo_data
docker compose exec web python manage.py seed_roadmap_labs
docker compose exec web python manage.py seed_labs_expansion
docker compose exec web python manage.py seed_gamification_catalog
docker build -t platlab-target-sqli:latest docker/targets/sqli-login   # imagen del laboratorio con terminal real
```

`seed_demo_data` crea los tres usuarios de prueba, un laboratorio plantilla publicado en el catálogo, una copia del instructor con examen y una asignación aceptada del estudiante. Los otros tres cargan el mapa de aprendizaje, los laboratorios adicionales y el catálogo de logros y títulos. Todos son idempotentes: correrlos de nuevo no duplica datos.

El backend queda en `http://localhost:8000/api/v1/`.

---

## Frontend

En otra terminal, desde la raíz del repo:

```bash
cd frontend
bun install     # o: npm install
bun run dev     # o: npm run dev
```

Se sirve en `http://localhost:5173` y apunta al backend en `http://localhost:8000/api/v1`. En el build de producción (el que usa el instalador) usa rutas relativas, porque la interfaz y la API comparten origen detrás del gateway. Para forzar otra URL, crea `frontend/.env.local`:

```bash
VITE_API_URL=http://localhost:8000/api/v1
# Solo si configuraste credenciales OAuth reales en el backend:
# VITE_OAUTH_ENABLED=true
```

Los botones de login social (Google/GitHub) están ocultos por defecto porque no hay credenciales OAuth configuradas: es lo esperado en un entorno de prueba, no un error.

---

## Credenciales de prueba

Creadas por `seed_demo_data`. Un rol por usuario:

| Rol | Email | Contraseña |
|---|---|---|
| Administrador | `admin@platlab.demo` | `Admin1234` |
| Instructor | `instructor@platlab.demo` | `Instructor1234` |
| Estudiante | `estudiante@platlab.demo` | `Estudiante1234` |

Estas contraseñas son públicas: el instalador en modo **red / aula** desactiva estas cuentas. Para cuentas reales usa `python manage.py create_production_users --admin-email ...` (genera la contraseña y la muestra una sola vez).

---

## Probar el flujo completo

Con backend + frontend arriba y las semillas cargadas:

1. **Como estudiante** (`estudiante@platlab.demo`): en el Dashboard verás el laboratorio asignado. Ábrelo, recorre las secciones (teoría + guía práctica), envía la flag de la sección práctica y completa el examen final.
2. **Terminal simulada vs. real**: en una sección con práctica puedes elegir la terminal simulada (guion de comandos, no ejecuta nada real) o la real (xterm.js conectado por WebSocket a un contenedor Docker propio y descartable; tarda unos segundos la primera vez mientras se levanta).
3. **Como estudiante, pedir ser instructor**: desde el Dashboard, con un ORCID. La solicitud queda pendiente; la plataforma consulta OpenAlex en segundo plano y guarda lo que encontró.
4. **Como administrador** (`admin@platlab.demo`): panel con usuarios, cola de revisión de laboratorios, actividad reciente y **solicitudes de instructor**, donde ves los datos de quien se inscribió junto a lo que dice OpenAlex de su ORCID, y apruebas o rechazas con un motivo.
5. **Como instructor** (`instructor@platlab.demo`): la copia del laboratorio duplicada del catálogo, con edición de secciones, flags y examen.
6. **Catálogo público** (`/laboratorios`, sin login): los laboratorios publicados.

Si algo no carga, revisa [Solución de problemas comunes](#solución-de-problemas-comunes).

---

## Correr sin Docker (backend nativo)

Alternativa para desarrollar el backend sin reconstruir la imagen. Igual necesitas **Postgres y Redis** (copia `docker-compose.override.example.yml` como `docker-compose.override.yml` para publicarlos en `127.0.0.1` y luego `docker compose up postgres redis`) y **Docker corriendo en el host** si quieres los entornos reales de laboratorio.

```bash
python -m venv venv
# Windows (PowerShell):
venv\Scripts\Activate.ps1
# Linux/Mac:
source venv/bin/activate

pip install -r requirements/dev.txt -c requirements/constraints.txt

# Edita .env: POSTGRES_HOST=localhost y REDIS_URL=redis://localhost:6379/0
# ("postgres"/"redis" solo resuelven dentro de la red de docker compose)

python manage.py migrate
python manage.py seed_demo_data

# Uvicorn, no runserver: runserver no entiende WebSockets y la terminal
# real se queda "conectando" para siempre.
uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --lifespan off
```

En otras terminales, los workers y las tareas periódicas:

```bash
celery -A config worker -l info
celery -A config worker -Q entornos --pool threads --concurrency 20 -n entornos@%h -l info
celery -A config beat -l info
```

---

## Tests

**Backend** (pytest contra `config.settings.test`: Celery en modo síncrono, no necesita worker):

```bash
docker compose exec web pytest
docker compose exec web ruff check .
```

**Frontend** (tipos + lint):

```bash
cd frontend
bun run build   # tsc -b + vite build: falla si hay errores de tipos
bun run lint
```

**Carga y estrés**: ver [`loadtests/README.md`](./loadtests/README.md) (Locust para la API y un script que levanta 100 laboratorios a la vez).

---

## Variables de entorno

Definidas en `.env` (plantilla completa en `.env.example`; el instalador las completa solo):

| Variable | Uso | ¿Hace falta tocarla para desarrollo local? |
|---|---|---|
| `SECRET_KEY` | clave de Django (firma de tokens) | no en local; en cualquier instalación compartida, una aleatoria (el instalador la genera) |
| `FLAG_HASH_KEY` | clave HMAC de flags y respuestas de examen; vacía = derivada de `SECRET_KEY` | no; si rotas `SECRET_KEY`, pon aquí la anterior |
| `DEBUG` | modo debug de Django | no |
| `ALLOWED_HOSTS` | hosts permitidos (dev/prod) | no |
| `CORS_ALLOWED_ORIGINS` | orígenes permitidos para el frontend de desarrollo | no, ya incluye `localhost:5173` |
| `POSTGRES_*` | conexión a la base de datos | no, salvo que cambies credenciales |
| `REDIS_URL` | Celery, refresh tokens, canal de Channels | no |
| `DJANGO_ADMIN_URL` | ruta del admin de Django | no; el instalador usa una ruta aleatoria |
| `PLATLAB_MODO`, `PLATLAB_PORT`, `PLATLAB_BIND` | modo, puerto y alcance de la instalación local | las escribe el instalador |
| `WEB_CONCURRENCY`, `CELERY_CONCURRENCY`, `LAB_ENV_*` | capacidad (procesos web, workers, laboratorios simultáneos) | solo para afinar con muchos usuarios |
| `DEFAULT_FROM_EMAIL` | remitente de emails (dev usa consola) | no |
| `GOOGLE_OAUTH_*`, `GITHUB_OAUTH_*` | login social | solo para probar OAuth real; si no, déjalos en `changeme` y los botones quedan ocultos |

**Frontend** (`frontend/.env.local`, opcional, no versionado):

| Variable | Valor si no se define |
|---|---|
| `VITE_API_URL` | `http://localhost:8000/api/v1` en desarrollo; `/api/v1` (mismo origen) en el build de producción |
| `VITE_OAUTH_ENABLED` | `false` (oculta los botones de Google/GitHub) |

---

## Solución de problemas comunes

**El instalador dice que Docker no está corriendo**
Abre Docker Desktop y espera a que diga *Engine running*. En Linux: `sudo systemctl start docker`; si el error es de permisos, agrega tu usuario al grupo `docker` (`sudo usermod -aG docker $USER`) y vuelve a iniciar sesión.

**El instalador falla descargando imágenes (`no such host`, `timeout`)**
Es la red: el instalador reintenta solo cuatro veces. Si sigue fallando, revisa la conexión (o el proxy de la red de la institución) y vuelve a ejecutarlo; retoma sin perder nada.

**Otros equipos de la red no logran entrar (modo red / aula)**
Comprueba que entras desde el propio equipo con `http://<IP>:8080`. Si ahí funciona, es el firewall: en Windows ejecuta el instalador como administrador o crea la regla que te sugiere, y marca la red como *Privada*. Si la IP del equipo cambió (DHCP), solo usa la nueva: no hace falta reinstalar.

**`docker compose up` falla en `docker-proxy` con error sobre `/var/run/docker.sock`**
En Windows, confirma que Docker Desktop usa el backend **WSL2** (Settings → General → "Use the WSL 2 based engine").

**`port is already allocated` para 8000 / 8080 / 5173**
Otro programa ya usa ese puerto. Detenlo o elige otro: `.\platlab.ps1 instalar -Puerto 8090` (instalación) o cambia el mapeo en `docker-compose.yml` / `vite.config.ts` (desarrollo).

**El frontend de desarrollo carga pero las peticiones a la API fallan / error de CORS**
Confirma que el backend esté arriba en `http://localhost:8000` y que `CORS_ALLOWED_ORIGINS` en `.env` incluya la URL exacta del frontend (por defecto `http://localhost:5173`).

**La terminal "real" de un laboratorio se queda en "conectando..."**
- Confirma que existe la imagen del laboratorio: `docker images platlab-target-sqli` (el instalador la construye; en desarrollo, ver el paso 4).
- Confirma que Docker está corriendo y revisa `docker compose logs -f worker-entornos web` por errores del SDK de Docker.
- Si corres el backend fuera de Docker, usa `uvicorn` (no `runserver`, que no soporta WebSockets).

**`seed_demo_data` falla o no crea nada**
Necesita las migraciones aplicadas: sin Docker, corre antes `python manage.py migrate`. Si falla a mitad de camino, vuelve a correrlo: retoma sin duplicar lo ya creado.

**No tengo Bun instalado**
Solo hace falta para el frontend en desarrollo. Todos los comandos `bun ...` tienen equivalente en `npm` (`npm install`, `npm run dev`); el repo versiona `bun.lock`, así que npm generará su propio `package-lock.json` local.

**Los botones de login con Google/GitHub no aparecen**
Es lo esperado sin credenciales OAuth reales (ver [Variables de entorno](#variables-de-entorno)).

---

## Estructura del proyecto

Backend organizado por módulos con arquitectura hexagonal (domain / application / infrastructure / presentation). Detalle módulo por módulo en [`Documentación/estructura-carpetas.md`](./Documentación/estructura-carpetas.md).

```
PlatLab/
├── config/                    # settings (dev, local, prod, test), urls, asgi, celery
├── modules/                   # authentication, users, laboratories, assignments,
│                              # progress, lab_environments, reports, notifications,
│                              # audit, gamification, roadmap, shared
├── docker/                    # entrypoint.sh + targets vulnerables de los laboratorios
├── frontend/                  # React + Vite + Tailwind + shadcn/ui (+ Dockerfile del gateway)
├── loadtests/                 # pruebas de carga (Locust) y de estrés de laboratorios
├── requirements/              # base / dev / prod + constraints.txt (versiones congeladas)
├── Documentación/             # documentación funcional y técnica por sprint
├── docker-compose.yml         # desarrollo
├── docker-compose.local.yml   # instalación local / aula (platlab.ps1, platlab.sh)
├── docker-compose.prod.yml    # servidor en internet con HTTPS (Caddy)
├── instalar.cmd, platlab.ps1  # instalador y administración en Windows
├── platlab.sh                 # instalador y administración en Linux/macOS
└── .env.example
```

Para el detalle funcional (casos de uso, reglas de negocio, dominio) y el progreso sprint a sprint, ver [`Documentación/`](./Documentación).
