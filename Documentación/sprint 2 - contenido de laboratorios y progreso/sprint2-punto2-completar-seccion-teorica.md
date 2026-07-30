# Sprint 2 — Punto 2: Completar secciones solo-teoría (`CompletarSeccionTeoricaUseCase`)

## ¿Qué es esto?

Un caso de uso nuevo (`UC-02 bis`) que le permite al estudiante marcar como
completada una `Sección` que **no tiene práctica** (`tiene_practica=False`,
por ejemplo una introducción puramente teórica), y con eso desbloquear la
siguiente sección de la secuencia.

## ¿Por qué es importante?

`dominio.md §3` ya describía cómo avanza el progreso: al validar la última
flag correcta de una sección, se desbloquea la siguiente
(`ValidarFlagUseCase` + `GestorDeSecuencia`). El hueco era que una sección
sin práctica **no tiene ninguna flag que validar** — no existía ningún
caso de uso que la marcara como completada. Resultado: si un laboratorio
tenía una sección introductoria solo de lectura, el laboratorio quedaba
**trabado ahí para siempre**, sin forma de avanzar. Este punto cierra ese
hueco.

## ¿Qué se hizo exactamente?

### 1. `CompletarSeccionTeoricaUseCase` (Application)
Nuevo caso de uso en `modules/progress/application/use_cases/completar_seccion_teorica.py`
que reutiliza la misma pieza de dominio que ya usa `ValidarFlagUseCase`
(`GestorDeSecuencia.completar_y_desbloquear_siguiente`), pero sin pasar por
la validación de flag:

- **Valida** que el progreso exista y sea del estudiante que lo pide, que la
  asignación no esté vencida (ver punto 3 de este sprint), que la sección no
  esté bloqueada, y — la regla central — que la sección **no tenga
  práctica** (`SeccionRequierePracticaError` si la tiene: esta vía no sirve
  para saltarse una flag).
- **Es idempotente**: reintentar sobre una sección ya completada no
  reprocesa el desbloqueo ni duplica el historial (protege contra doble
  click o reintento de red).
- Emite `SectionCompleted`, y si era la última sección, también
  `LabCompleted` — los mismos eventos de dominio que dispara
  `ValidarFlagUseCase`, así que Notifications/Audit no necesitan saber por
  cuál de los dos caminos se completó una sección.
- Si el laboratorio no tiene examen configurado, registra directamente el
  `HistorialCompletitud` (ver punto 3) — misma lógica que ya existía en
  `ValidarFlagUseCase` para ese caso.

### 2. Excepciones de dominio nuevas — `progress/domain/exceptions.py`
- `SeccionRequierePracticaError`: se intentó completar por esta vía una
  sección que sí requiere flag.
- `AsignacionVencidaError`: ver punto 3.

### 3. Endpoint — `progress/presentation/urls.py`
Se agregó la ruta correspondiente para que el frontend pueda invocar este
caso de uso desde la vista de resolución de laboratorio, en el mismo lugar
donde antes solo existía "enviar flag".

## ¿Qué NO incluye este punto?

- Reordenar ni cambiar la lógica de secuencia (`GestorDeSecuencia`) — se
  reutiliza tal cual estaba.
- El chequeo de vencimiento de la asignación en sí (`IEstadoAsignacionProvider`)
  — ver el punto siguiente, aunque este caso de uso ya lo consume desde que
  se creó.

## En una frase

Se cerró el hueco donde un laboratorio con secciones puramente teóricas
quedaba trabado sin posibilidad de avanzar, dándole a esas secciones una
forma explícita de completarse que respeta las mismas reglas de secuencia y
dispara los mismos eventos que completar una sección con flag.
