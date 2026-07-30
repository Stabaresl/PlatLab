# Sprint 2 — Punto 3: Vencimiento de la asignación + habilitación del examen final

## ¿Qué es esto?

Dos reglas de negocio relacionadas con "hasta cuándo y hasta dónde puede
avanzar un estudiante en un laboratorio":

1. Una **Asignación** vence a **un mes** de haberse aceptado, y a partir de
   ahí el estudiante ya no puede seguir progresando (ni flags, ni secciones
   teóricas, ni examen) — aunque el material sigue siendo visible.
2. El **examen final** de un laboratorio solo se puede enviar una vez que
   **todas** las secciones están completadas.

## ¿Por qué es importante?

**Vencimiento**: sin este límite, una asignación quedaba abierta
indefinidamente — no había ninguna presión de tiempo real, y RF-32/HI-07
(backlog) piden explícitamente esa ventana. La decisión de diseño clave acá
es que vencer **no oculta el contenido**: el estudiante puede seguir viendo
la teoría y su progreso ya hecho, solo pierde la capacidad de seguir
avanzando — evita que alguien pierda acceso a lo que ya estudió por una
razón administrativa.

**Examen**: sin la validación, un estudiante podía enviar el examen sin
haber tocado ninguna sección, lo cual rompe el sentido pedagógico del
laboratorio (el examen evalúa lo que las secciones enseñaron).

## ¿Qué se hizo exactamente?

### 1. Vencimiento — puerto `IEstadoAsignacionProvider` (Domain, `progress/domain/ports.py`)

`Progress` necesita saber si la `Asignación` de un progreso sigue vigente,
pero **no puede depender directamente** del módulo `Assignments`
(`dominio.md §4`: los agregados de distintos módulos se referencian solo por
"id suelto", nunca por importación cruzada de repositorios). Se resolvió con
un **puerto** (`Protocol`) que `Progress` define y `Assignments` implementa:

- `EstadoAsignacionInfo(vencida: bool, fecha_vencimiento: datetime | None)`
- `IEstadoAsignacionProvider.obtener_estado(asignacion_id) -> EstadoAsignacionInfo | None`

**Implementación real** — `AsignacionEstadoProvider`
(`progress/infrastructure/asignacion_estado_provider.py`): no confía
ciegamente en el campo `estado` ya persistido de la asignación, porque el
job periódico que lo actualiza (`CerrarAsignacionesVencidasJob`, Celery
Beat) puede no haber corrido todavía sobre esa fila puntual. En cambio,
**recalcula** contra `fecha_vencimiento` con `VentanaVencimiento(...).ya_vencio()`
cada vez que se le pregunta — así la regla se cumple en el momento exacto,
sin depender de la cadencia del job de fondo.

Este provider se inyectó en los tres puntos donde el estudiante puede
avanzar progreso, y los tres ahora rechazan con `AsignacionVencidaError` si
la asignación venció:
- `ValidarFlagUseCase`
- `CompletarSeccionTeoricaUseCase`
- `EnviarExamenUseCase`

### 2. Examen — validación ya existente, ahora reforzada
`EnviarExamenUseCase` ya exigía `_SECCIONES_INCOMPLETAS_MSG` si no todas las
secciones estaban en estado `COMPLETADA` — ese chequeo no es nuevo de este
sprint, pero ahora convive con el chequeo de vencimiento (se valida primero
que el progreso exista, después vencimiento, después secciones completas) —
un examen no se puede enviar ni con secciones pendientes ni con la
asignación vencida, en ese orden.

### 3. Historial de completitud
Tanto `ValidarFlagUseCase` como `CompletarSeccionTeoricaUseCase` registran
un `HistorialCompletitud` automáticamente cuando se completa la última
sección **y el laboratorio no tiene examen configurado** — si tiene examen,
el historial se registra en cambio al calificar el examen
(`EnviarExamenUseCase` → `CalificadorDeExamen`). Evita registrar dos veces
la finalización de un mismo laboratorio.

## ¿Qué NO incluye este punto?

- El job que efectivamente marca la asignación como `VENCIDA` en la base
  (`CerrarAsignacionesVencidasJob` vía Celery Beat) — ya existía de un
  sprint anterior; este punto solo agrega la capa de "aunque el job no haya
  corrido todavía, la regla se cumple igual".
- Notificar al estudiante cuando su asignación está por vencer — no hay
  aviso proactivo, solo el bloqueo al intentar avanzar.

## En una frase

Cada asignación tiene ahora una fecha de vencimiento real que se hace
cumplir en el momento (no solo cuando corre el job de fondo) sin ocultar el
contenido ya visto, y el examen final quedó explícitamente atado a haber
completado el 100% de las secciones.
