# Sprint 0 — Punto 2: Docker Compose / Dockerfile

## ¿Qué es esto?

Es la infraestructura que permite que todo el equipo (sin importar si usa Windows, Mac o Linux) levante el proyecto completo con un solo comando, en un entorno idéntico para todos.

## ¿Por qué es importante?

PlatLAB no es solo "un servidor Django": necesita una base de datos (PostgreSQL), un sistema de colas para tareas en segundo plano (Redis + Celery), y el propio backend corriendo. Sin Docker, cada desarrollador tendría que instalar y configurar manualmente PostgreSQL, Redis, Python, y las versiones exactas de cada uno — con alta probabilidad de que algo funcione distinto en la máquina de cada persona ("en mi computador sí funciona"). Docker empaqueta todo eso en contenedores idénticos para todo el equipo y para el servidor de producción.

## ¿Qué se hizo exactamente?

### 1. `Dockerfile`
Receta que construye la imagen del backend: parte de Python 3.12, instala las dependencias del proyecto (`requirements/`) y copia el código. Incluye un script de arranque (`entrypoint.sh`) que espera a que la base de datos esté lista antes de aplicar migraciones automáticamente.

### 2. `docker-compose.yml`
Define y conecta 5 servicios que trabajan juntos:
- **`web`**: el backend Django (lo que responde a las peticiones HTTP).
- **`worker`**: procesa tareas en segundo plano (ej. envío de emails, notificaciones) sin bloquear al usuario mientras espera.
- **`beat`**: dispara tareas programadas (ej. cerrar automáticamente laboratorios vencidos cada cierto tiempo).
- **`postgres`**: la base de datos real del proyecto.
- **`redis`**: memoria rápida usada como cola de mensajes entre `web` y `worker`/`beat`, y para guardar datos temporales (como sesiones de refresh token).

Cada servicio espera a que sus dependencias estén "saludables" (`healthcheck`) antes de arrancar — así se evita que `web` intente conectarse a una base de datos que todavía se está iniciando.

### 3. `requirements/{base,dev,prod}.txt`
Las librerías de Python que el proyecto necesita, separadas por ambiente: `base.txt` son las que siempre se necesitan (Django, conexión a Postgres, Celery, etc.), `dev.txt` agrega herramientas de testing solo para desarrollo, y `prod.txt` agrega el servidor de producción (`gunicorn`).

### 4. `.dockerignore`
Evita que archivos innecesarios (entorno virtual, caché, `.env` con contraseñas) se copien dentro de la imagen de Docker, para que sea más liviana y no exponga secretos por accidente.

## ¿Qué NO incluye este punto?

- Las variables de entorno reales (`.env`) — eso es el punto 3.
- `worker` y `beat` todavía no funcionan del todo porque `config/celery.py` (la configuración de Celery) aún no existe — se crea más adelante junto con el kernel de infraestructura.

## En una frase

Se construyó el entorno de contenedores que hace que todo el equipo trabaje sobre la misma base (mismas versiones, misma configuración), sin depender de lo que cada quien tenga instalado en su computador.
