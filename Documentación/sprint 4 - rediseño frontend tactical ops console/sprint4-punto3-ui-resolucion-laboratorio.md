# Sprint 4 — Punto 3: UI de resolución de laboratorios (terminal simulada + real)

## ¿Qué es esto?

La interfaz donde el estudiante efectivamente resuelve un laboratorio:
`ResolverLaboratorioPage` (navegación entre secciones + examen) y
`SeccionMaterialPage` (contenido de una sección puntual), con dos
componentes de terminal nuevos que exponen, del lado del frontend, los dos
modos construidos en los sprints anteriores — consola simulada (Sprint 2) y
entorno Docker real (Sprint 3).

## ¿Por qué es importante?

Es la pantalla donde el estudiante pasa la mayor parte del tiempo dentro de
la plataforma — el resto del rediseño (Sprint 4, puntos 1-2) construye el
lenguaje visual, pero esta es la vista que tiene que sostener una sesión de
trabajo larga y concentrada, no solo verse bien de forma estática.

## ¿Qué se hizo exactamente?

### 1. `SimulatedTerminal.tsx` — consola guionada

Terminal interactiva que **no ejecuta nada real**: compara el comando
tipeado contra el guion que autoría el instructor
(`EntornoPractica.comandos`, Sprint 2) y devuelve la salida asociada.
Detalles de UX pensados para que se sienta como una terminal de verdad sin
serlo:

- `help`/`?` y `clear`/`cls` son *builtins* del frontend, disponibles
  siempre sin importar el guion del instructor — la consola nunca se
  siente "trabada" sin salida.
- Historial de comandos navegable con flechas arriba/abajo, como una shell
  real.
- Comandos no reconocidos devuelven `bash: <cmd>: comando no encontrado`,
  igual que una shell real, en vez de un error genérico del frontend.
- Accesible: `role="log"` + `aria-live="polite"` sobre el área de salida,
  para que un lector de pantalla anuncie las nuevas líneas.

### 2. `RealTerminal.tsx` — terminal real (xterm.js + WebSocket)

Conectada al `TerminalConsumer` del backend (Sprint 3, punto 2) vía
WebSocket, usando `@xterm/xterm` + `@xterm/addon-fit` para el renderizado
de terminal real (no es un `<textarea>` disfrazado). A diferencia de
`SimulatedTerminal`, acá los comandos que tipea el estudiante se ejecutan
de verdad dentro de un contenedor descartable y aislado.

- La URL del WebSocket (`labEnvironmentTerminalUrl`, `pages/api.ts`) arma
  la conexión a partir de la misma `VITE_API_URL` configurada para HTTP,
  reemplazando `http`→`ws` y quitando el sufijo `/api/v1` — el WebSocket
  vive en la raíz ASGI, no bajo el prefijo de la API REST.
- El JWT de acceso viaja como query param (`?token=...`) porque un
  `WebSocket` nativo del navegador no permite mandar headers custom — el
  mismo mecanismo que implementa `JWTAuthMiddleware` del lado del backend.
- Expone estado de conexión (`conectando` / `conectado` / error) al
  componente padre, para que la UI pueda mostrar feedback mientras el
  backend termina de levantar el contenedor Docker (puede tardar unos
  segundos la primera vez).
- `fitAddon.fit()` se recalcula en cada resize de ventana, para que la
  terminal real siempre ocupe el espacio disponible sin scroll interno
  roto.

### 3. `ResolverLaboratorioPage.tsx` / `SeccionMaterialPage.tsx`

Reconstruidas sobre `TerminalHeader` y el resto del sistema de diseño del
sprint, agregan:

- Navegación entre secciones respetando el estado de bloqueo/desbloqueo
  que ya maneja el backend (`GestorDeSecuencia`, Sprint 2).
- Selector entre terminal simulada y real cuando la sección tiene ambas
  disponibles (`entorno_practica` y/o `imagen_practica` configurados).
- Flujo de envío de flag y de completar secciones sin práctica
  (`CompletarSeccionTeoricaUseCase`, Sprint 2), y del examen final al
  completar todas las secciones.
- Feedback visual de vencimiento de asignación (`AsignacionVencidaError`,
  Sprint 2) cuando corresponde.

## ¿Qué NO incluye este punto?

- Reconexión automática de `RealTerminal` ante un corte de red — si el
  WebSocket se cae, el estudiante tiene que recargar o reabrir la
  terminal; no hay retry automático todavía.
- Multiplexado de varias sesiones de terminal en paralelo dentro de la
  misma pestaña (una terminal real a la vez por sección, que es como está
  modelado también del lado del backend).

## En una frase

Se construyó la pantalla central de la experiencia del estudiante,
integrando en una sola interfaz consistente los dos modos de práctica
construidos en sprints anteriores — la consola simulada guionada y la
terminal real conectada por WebSocket a un contenedor Docker aislado — con
la navegación de secciones, flags y examen final del módulo `progress`.
