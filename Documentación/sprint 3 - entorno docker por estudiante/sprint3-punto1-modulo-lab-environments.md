# Sprint 3 — Punto 1: Módulo `lab_environments` (dominio/aplicación/infraestructura)

## ¿Qué es esto?

Un módulo nuevo, completo, que le da a cada sección práctica un **contenedor
Docker real y descartable** por estudiante — la terminal simulada del
Sprint 2 (`EntornoPractica`, guion de comandos) sigue existiendo, pero ahora
existe también la opción de ejecutar comandos **de verdad** contra un
sistema vulnerable de mentira, aislado y de un solo uso.

## ¿Por qué es importante?

Un guion de comandos predefinido (Sprint 2) enseña, pero no permite
explorar: el estudiante no puede probar variantes del ataque, cometer
errores, o investigar por su cuenta — solo puede seguir el libreto exacto
que escribió el instructor. Un contenedor real resuelve eso, pero trae un
problema serio de seguridad: si no se aísla correctamente, un estudiante
podría usar ese contenedor para atacar al host o a otros estudiantes. Este
punto se construyó con esa restricción como primera prioridad, no como
detalle secundario.

## ¿Qué se hizo exactamente?

### 1. Dominio — agregado `EntornoActivo`

- **`EntornoActivo`** (`domain/entities.py`): agregado raíz del módulo — una
  instancia de contenedor asociada 1:1 a `(Progreso, Sección)`, vinculada
  por "id suelto" (mismo patrón que el resto del dominio, sin FK real hacia
  `Progress`/`Laboratories`). Se separó de `Progreso` a propósito porque
  tiene un ciclo de vida propio y mucho más corto (minutos/horas, no la
  duración completa del laboratorio).
- **`EstadoEntorno`** (`domain/value_objects.py`): `iniciando` → `activo` →
  `detenido` (apagado explícito o por el reaper de inactividad) o `error`.
- **`IContenedorProvider`** (`domain/ports.py`): puerto — ni el dominio ni
  la aplicación importan el SDK de `docker` directamente, para que el motor
  de orquestación sea intercambiable (Docker de un solo host hoy;
  Kubernetes u otro más adelante) sin tocar los casos de uso.

### 2. Aplicación — tres casos de uso + una query

- **`IniciarEntornoUseCase`**: crea (o reconecta a) el contenedor de una
  sección para un estudiante. Reglas clave:
  - Un entorno por `(progreso, sección)`, nunca dos a la vez — si ya hay
    uno vivo, lo devuelve en vez de crear otro (idempotente).
  - Respeta un **cupo global** (`max_concurrentes`, default 5) — si está
    lleno, rechaza con un mensaje de "reintentá en unos minutos" en vez de
    dejar que el host se sature.
  - El contenedor se arranca **antes** de abrir la transacción de base de
    datos: si Docker falla, nunca se llega a persistir un `EntornoActivo`
    "fantasma" sin contenedor real detrás.
  - Rechaza si la sección no tiene `imagen_practica` configurada
    (`SeccionSinEntornoRealError`) — no toda sección práctica necesita
    contenedor real, algunas solo usan la consola simulada.
- **`DetenerEntornoUseCase`**: apagado explícito por el estudiante (botón
  "Detener" en el frontend).
- **`ReapEntornosInactivosUseCase`**: protege al host de acumular
  contenedores olvidados, con **dos gatillos independientes**:
  - Inactividad: sin comandos en `idle_timeout_minutos` (default 20) — el
    estudiante se fue sin avisar.
  - Vida máxima: `max_lifetime_minutos` desde que arrancó (default 120),
    sin importar actividad — ningún contenedor corre indefinidamente,
    aunque el estudiante deje la terminal abierta todo el día.
  Se dispara desde Celery Beat, no desde un usuario (mismo criterio que
  `CerrarAsignacionesVencidasUseCase` de `Assignments`).
- **`ObtenerEstadoEntornoQuery`**: le dice al frontend si ya hay un entorno
  activo para esa sección (para no mostrar "Iniciar" si ya hay uno
  corriendo).

### 3. Infraestructura — `DockerContenedorProvider`

Implementación real de `IContenedorProvider` sobre **Docker-outside-of-Docker**:
el contenedor `web`/`worker` habla con el Docker del *host* a través del
socket montado en `/var/run/docker.sock` (ver `docker-compose.yml`), y crea
contenedores "hermanos" — no anidados dentro de sí mismo.

Cada contenedor de práctica se crea con un endurecimiento explícito:

| Límite | Valor | Por qué |
|---|---|---|
| Memoria | `256m` | evita que un estudiante agote la RAM del host |
| CPU | `0.5` (nano_cpus) | evita que un estudiante degrade a los demás |
| PIDs | `128` | evita fork-bombs |
| Red | `network_disabled=True` | el contenedor no puede salir a Internet ni ver la red del host |
| Privilegios | `no-new-privileges`, `cap_drop=["ALL"]` | superficie de escalación mínima dentro del propio contenedor |
| `/tmp` | `tmpfs`, `size=32m` | espacio de escritura acotado y volátil |

También resuelve una **carrera real observada en pruebas**: si se abre una
sesión `exec` apenas arranca el contenedor, el proceso objetivo (por
ejemplo el servidor HTTP del target vulnerable) puede no haber terminado de
bindear su puerto todavía, y el primer comando del estudiante se pierde en
silencio. `_esperar_listo()` espera al `HEALTHCHECK` de la imagen si define
uno, o usa un margen fijo corto como resguardo si no.

### Nota de seguridad documentada explícitamente

Montar `/var/run/docker.sock` le da al proceso que lo usa **control
equivalente a root sobre el Docker del host** — se documentó como
aceptable para desarrollo/pruebas en una máquina propia, pero **no** apto
para exponer a estudiantes reales por Internet sin antes separar el
ejecutor de contenedores del backend (host/VM dedicado) y reforzar el
aislamiento (gVisor/Kata) — trade-off explícito, no resuelto en esta
iteración, dejado por escrito en el código y en el `README.md`.

## ¿Qué NO incluye este punto?

- La exposición de este módulo por HTTP/WebSocket al frontend — eso es el
  punto siguiente de este sprint.
- El target vulnerable de demo en sí — punto 3 de este sprint.

## En una frase

Se construyó, con la seguridad del host como restricción de diseño desde el
primer commit (no como parche después), el módulo que le da a cada
estudiante su propio contenedor Docker descartable, aislado de red y con
límites de recursos duros, para practicar contra un objetivo real en vez de
un guion simulado.
