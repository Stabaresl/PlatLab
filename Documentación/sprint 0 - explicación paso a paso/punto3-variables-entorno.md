# Sprint 0 — Punto 3: Variables de entorno y settings por ambiente

## ¿Qué es esto?

Es lo que conecta el proyecto Django a servicios reales: la base de datos PostgreSQL, Redis, y datos sensibles como claves secretas — todo leído desde variables de entorno en vez de estar escrito directamente en el código.

## ¿Por qué es importante?

Antes de este punto, el proyecto usaba una base de datos temporal (SQLite) y una clave secreta genérica escrita en el código fuente. Eso es inaceptable para un proyecto real por dos razones:

1. **Seguridad:** si la clave secreta (`SECRET_KEY`) o las contraseñas de la base de datos quedan escritas en el código y ese código se sube a GitHub, cualquiera con acceso al repositorio (o si el repositorio se hace público accidentalmente) tiene esas credenciales.
2. **Portabilidad:** cada ambiente (tu computador, el de un compañero, o el servidor real de producción) necesita conectarse a *su propia* base de datos con *sus propias* credenciales. Si esos datos estuvieran fijos en el código, sería imposible tener ambientes distintos sin reescribir el código cada vez.

La solución estándar (y la que usa este proyecto) es leer esos datos desde variables de entorno: un archivo `.env` que **nunca se sube al repositorio** (ver `.gitignore`) y que cada persona/servidor configura con sus propios valores.

## ¿Qué se hizo exactamente?

### 1. `.env.example`
Es una plantilla pública (sí se sube al repositorio) que lista **qué** variables necesita el proyecto, sin los valores reales — solo placeholders. Cualquiera que clona el proyecto sabe exactamente qué archivo `.env` tiene que crear y qué debe contener, sin exponer ningún secreto real.

### 2. `settings/base.py` conectado a variables de entorno
Se modificó para que, en vez de tener la clave secreta y la configuración de base de datos escritas directamente, las lea del archivo `.env` usando la librería `django-environ`:
- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` → configuración general de Django.
- `DATABASES` → ahora apunta a PostgreSQL real (antes era SQLite), leyendo host, usuario, contraseña y nombre de la base desde el `.env`.
- `REDIS_URL` → dirección de conexión a Redis, usada tanto por Celery como por el `RedisClient` (punto 8).

### 3. `settings/dev.py` y `settings/prod.py` diferenciados de verdad
- **`dev.py`**: activa `DEBUG=True` (muestra errores detallados, útil mientras se programa) y usa hosts locales por defecto.
- **`prod.py`**: fuerza `DEBUG=False` (nunca se debe exponer información de errores en producción, es un riesgo de seguridad) y activa cabeceras de seguridad adicionales (HTTPS obligatorio, protección contra clickjacking, cookies seguras) que solo tienen sentido en un servidor real con dominio propio.

## ¿Qué NO incluye este punto?

- Las credenciales reales de producción (esas las define el equipo de DevOps al desplegar, nunca se comparten en el repositorio ni en el chat).
- Configuración de email real (SMTP) — el punto 8 la deja preparada pero por defecto en desarrollo los emails solo se imprimen en el log, no se envían de verdad.

## En una frase

El proyecto dejó de depender de una base de datos de prueba y de una clave insegura escrita en el código, y pasó a conectarse a PostgreSQL real leyendo toda la configuración sensible desde un archivo `.env` que cada persona configura localmente y que nunca se comparte por Git.
