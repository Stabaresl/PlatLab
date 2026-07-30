# Sprint 3 — Punto 2: Exposición del entorno real por WebSocket (Channels/Daphne)

## ¿Qué es esto?

La capa que conecta el `EntornoActivo` del punto 1 con el navegador del
estudiante: tres endpoints REST (iniciar / detener / consultar estado) y un
**WebSocket** que hace de puente en tiempo real entre una sesión
`docker exec -it bash` real y la terminal (xterm.js) del frontend.

## ¿Por qué es importante?

Una terminal interactiva no se puede modelar como request/response HTTP
normal — hace falta un canal bidireccional y persistente. Django por sí
solo (WSGI, `runserver`) no soporta WebSockets; había que sumar una pieza
de infraestructura nueva (Django Channels + un servidor ASGI) sin romper
todo lo que ya corría sobre HTTP normal.

## ¿Qué se hizo exactamente?

### 1. Endpoints REST — `presentation/views.py` + `urls.py`

- `POST /lab-environments/{assignment_id}/sections/{section_id}/start/` —
  `EntornoStartView`, invoca `IniciarEntornoUseCase`.
- `POST /lab-environments/{entorno_id}/stop/` — `EntornoStopView`, invoca
  `DetenerEntornoUseCase`.
- `GET /lab-environments/{assignment_id}/sections/{section_id}/status/` —
  `EntornoStatusView`, invoca `ObtenerEstadoEntornoQuery`.

Todos exigen `IsAuthenticated`; la pertenencia del entorno al estudiante que
pide la acción se valida dentro de cada caso de uso (`es_propio_de`), no en
la vista.

### 2. El WebSocket — `TerminalConsumer` (`presentation/consumers.py`)

Un `AsyncWebsocketConsumer` de Channels, un consumer por conexión:

- **Al conectar**: valida que el `entorno_id` de la URL exista, pertenezca
  al usuario autenticado del socket, y esté en estado `activo` — si no,
  cierra la conexión con un código específico (`4401` sin usuario, `4404`
  no encontrado/no es suyo, `4409` no está activo, `4500` si Docker
  falla al abrir la sesión exec). Después abre una sesión
  `docker exec -it bash` **nueva** sobre el contenedor existente —
  reconectar no reinicia el contenedor, solo abre otra shell dentro de él.
- **Mientras dura la conexión**: dos direcciones corriendo en paralelo —
  una tarea de fondo lee continuamente la salida del proceso exec y la
  reenvía por el socket (`_leer_salida`), y `receive()` escribe cada
  mensaje entrante del navegador hacia el stdin del proceso. Cada mensaje
  entrante también "toca" la actividad del entorno (con throttling de 20s,
  para no golpear la base de datos en cada tecla) — así el reaper de
  inactividad del punto 1 sabe que la sesión sigue viva.
- **Al desconectar**: cierra la sesión exec y el socket subyacente, pero
  **deja el contenedor corriendo** — lo apaga explícitamente el estudiante
  (botón "Detener") o el reaper por inactividad/vida máxima. Cerrar la
  pestaña del navegador no destruye el trabajo del estudiante dentro del
  contenedor.

`docker-py` devuelve, para una sesión exec vía socket, un wrapper de solo
lectura (`socket.SocketIO`) — se verificó en tiempo real contra un
contenedor real que para **escribir** hace falta el socket crudo
subyacente (`.raw_socket`), no la propia `SocketIO`. `ExecSession`
(`infrastructure/docker_provider.py`) encapsula ese detalle para que el
consumer no tenga que conocerlo.

### 3. Autenticación de WebSocket — `JWTAuthMiddleware` (`ws_auth_middleware.py`)

Channels no tiene acceso al header `Authorization` del navegador para
conexiones WebSocket — el único mecanismo estándar disponible desde un
cliente WebSocket nativo es pasar el token como **query param**
(`?token=...`). El middleware decodifica ese token reutilizando el mismo
`JWTService` que usa la autenticación HTTP normal (DRF) — un solo lugar en
todo el sistema que sabe decodificar tokens JWT.

### 4. Servidor ASGI — `config/asgi.py` + Daphne

`ProtocolTypeRouter` de Channels separa el tráfico por protocolo dentro del
mismo proceso: `http` sigue yendo a Django/DRF sin cambios, `websocket` pasa
por `JWTAuthMiddleware` y de ahí al `TerminalConsumer`. El orden de imports
en `asgi.py` importa: `get_asgi_application()` tiene que llamarse **antes**
de importar cualquier cosa que toque modelos de Django (incluido el
routing de Channels), o falla con `AppRegistryNotReady`.

`docker-compose.yml` cambió el comando del servicio `web` de
`runserver` a:

```
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

Daphne sirve HTTP **y** WebSocket en un solo proceso ASGI — es el
reemplazo necesario de `runserver`, que no entiende WebSockets y hubiera
dejado la terminal real "conectando" para siempre.

### 5. Dependencias nuevas

`channels==4.1.0`, `daphne==4.1.2` (`requirements/base.txt`).

## ¿Qué NO incluye este punto?

- Channel layer distribuido (Redis) para escalar Daphne a múltiples
  procesos/réplicas — en este alcance corre un solo proceso Daphne, cada
  consumer maneja su propia conexión Docker directamente sin coordinarse
  con otras réplicas.
- Reconexión automática del lado del frontend ante un corte de red — ver
  Sprint 4, `RealTerminal.tsx`.

## En una frase

Se sumó Channels + Daphne para servir, en el mismo proceso ASGI que ya
servía la API REST, un WebSocket autenticado por JWT que hace de puente en
tiempo real entre el navegador del estudiante y una sesión `docker exec`
real sobre su contenedor de práctica.
