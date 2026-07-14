# Sprint 0 — Punto 1: Inicializar proyecto Django

## ¿Qué es esto?

Es la base sobre la que se construye todo PlatLAB. No tiene funcionalidades todavía (no hay login, no hay laboratorios, no hay nada usable), pero define **cómo va a estar organizado el código** durante todo el proyecto.

## ¿Por qué es importante?

Antes de escribir la primera línea de lógica de negocio, el equipo necesita ponerse de acuerdo en una estructura común. Si cada desarrollador organiza su código a su manera, el proyecto se vuelve imposible de mantener a medida que crece. Este punto resuelve eso: deja una carpeta por cada módulo del sistema (autenticación, usuarios, laboratorios, etc.), todas con la misma forma interna, para que cualquiera del equipo pueda entrar a un módulo nuevo y saber dónde está cada cosa sin tener que preguntar.

## ¿Qué se hizo exactamente?

### 1. Se creó el proyecto Django base
Django es el framework (herramienta) sobre el que está construido el backend de PlatLAB. Se generó la estructura mínima que Django necesita para arrancar: un archivo `manage.py` (el comando principal para ejecutar el proyecto) y una carpeta `config/` con la configuración general.

### 2. Se separó la configuración por ambiente
Dentro de `config/settings/` hay tres archivos:
- `base.py`: configuración común a todos los ambientes.
- `dev.py`: configuración para desarrollo (lo que usa el equipo mientras programa).
- `prod.py`: configuración para producción (lo que usará el servidor real).

**Por qué importa:** así se evita el error clásico de mezclar configuración de pruebas con configuración real (por ejemplo, tener `DEBUG=True` — que expone información sensible — activado por accidente en el servidor de producción).

### 3. Se creó una carpeta por cada módulo de negocio
Dentro de `modules/` hay una carpeta por cada área funcional de la plataforma:

| Carpeta | Qué maneja |
|---|---|
| `authentication` | Login, registro, recuperación de contraseña |
| `users` | Perfiles y administración de usuarios |
| `laboratories` | Laboratorios, secciones, flags, exámenes |
| `assignments` | Invitaciones y asignaciones a estudiantes |
| `progress` | Avance de cada estudiante |
| `reports` | Reportes de problemas técnicos |
| `notifications` | Notificaciones a usuarios |
| `audit` | Registro de auditoría (quién hizo qué y cuándo) |
| `lab_environments` | Reservado a futuro (entornos de laboratorio en vivo), aún sin desarrollar |
| `shared` | Código común reutilizado por todos los módulos anteriores |

**Por qué importa:** cada módulo corresponde 1 a 1 con una parte del sistema que el equipo ya definió en los documentos de arquitectura y casos de uso. Esto significa que un bug o una tarea de "Laboratorios" se resuelve **solo** dentro de la carpeta `laboratories/`, sin tocar el código de otros módulos. Reduce el riesgo de que un cambio en un módulo rompa otro por accidente.

### 4. Cada módulo tiene la misma estructura interna (4 capas)
Dentro de cada carpeta de módulo hay siempre las mismas 4 subcarpetas:

- **`domain/`** — Las reglas de negocio puras (ej. "una sección práctica no se puede publicar sin al menos una flag"). No sabe nada de Django, de la base de datos ni de la web.
- **`application/`** — Los casos de uso (ej. "crear laboratorio", "validar flag"). Coordina el `domain` con la infraestructura, pero tampoco depende de Django.
- **`infrastructure/`** — Todo lo técnico: modelos de base de datos, conexión a Redis, envío de emails, etc.
- **`presentation/`** — Los endpoints de la API (lo que el frontend consume): vistas, serializers, permisos.

**Por qué importa:** esta separación (llamada arquitectura por capas / Clean Architecture) permite que la lógica de negocio se pueda probar sin necesitar una base de datos real, y que si en el futuro se decide cambiar de PostgreSQL a otra base de datos, o de Django a otro framework, la lógica de negocio (`domain` y `application`) no se toca. Es una inversión que cuesta un poco más de tiempo ahora pero evita reescribir el sistema completo más adelante.

### 5. Se validó que el proyecto arranca correctamente
Se corrió `python manage.py check` (revisa que no haya errores de configuración) y `python manage.py migrate` (crea las tablas base que Django necesita internamente, como usuarios y sesiones administrativas). Ambos comandos terminaron sin errores, confirmando que la base está lista para que el equipo empiece a agregar funcionalidad real sobre ella.

## ¿Qué NO incluye este punto todavía?

- No hay conexión a PostgreSQL (sigue usando una base de datos temporal SQLite).
- No hay Docker configurado (eso es el punto 2 del Sprint 0).
- No hay ningún endpoint funcional (login, catálogo, etc.) — eso empieza en el Sprint 1.
- No hay variables de entorno (`.env`) configuradas — eso es el punto 3.

## En una frase

Se construyó el "esqueleto" ordenado del backend: las carpetas y reglas de organización que todo el equipo va a seguir de aquí en adelante, sin haber programado todavía ninguna funcionalidad de negocio.
