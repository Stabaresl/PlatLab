# Sprint 0 — Punto 6: EventDispatcher

## ¿Qué es esto?

Es la pieza que conecta el paso 4 de `BaseUseCase` (punto 5, "avisar del evento") con el código real que reacciona a cada evento. Es el "cartero" del sistema: recibe un evento y lo entrega a todos los interesados en enterarse de él.

## ¿Por qué es importante?

Muchas acciones del sistema disparan efectos secundarios en módulos completamente distintos. Ejemplo: cuando un estudiante **acepta una invitación** (módulo Assignments), automáticamente:
- se debe crear su registro de Progreso (módulo Progress),
- se le debe enviar una notificación (módulo Notifications),
- se debe registrar la acción en auditoría (módulo Audit).

Sin este mecanismo, el código de "aceptar invitación" tendría que importar y llamar directamente a Progress, Notifications y Audit — mezclando 4 módulos que se supone deben mantenerse independientes entre sí (regla ya definida en la Arquitectura del proyecto). Con `EventDispatcher`, el módulo Assignments simplemente anuncia "acepté una invitación" sin saber ni importarle quién está escuchando — cada módulo interesado se suscribe por su cuenta.

## ¿Qué se hizo exactamente?

Se creó `EventDispatcher` en `modules/shared/infrastructure/`, con dos operaciones:

- **`subscribe(tipo_de_evento, funcion)`**: registra que, cuando ocurra un evento de determinado tipo (ej. `AssignmentAccepted`), se debe ejecutar cierta función.
- **`dispatch(evento)`**: cuando ocurre el evento real, ejecuta automáticamente **todas** las funciones que se suscribieron a ese tipo de evento.

Características clave de esta primera versión:
- **Funciona en memoria**, de forma síncrona (todo ocurre inmediatamente, dentro del mismo proceso).
- **Aislamiento de fallas:** si uno de los "escuchas" de un evento falla (ej. el envío de notificación tiene un bug), los demás escuchas de ese mismo evento igual se ejecutan — un error en Notifications no debe impedir que Audit registre lo que pasó.
- **Reemplazable a futuro sin tocar el resto del código:** el día que el proyecto crezca y se necesite un sistema de eventos más robusto (por ejemplo, distribuido entre varios servidores), solo se cambia esta pieza — ni el Domain ni el Application se enteran del cambio, porque ambos dependen únicamente del "contrato" (`IEventDispatcher`, definido en el punto 5), no de esta implementación específica.

## ¿Qué NO incluye este punto?

- Los eventos reales del negocio (`AssignmentAccepted`, `FlagValidated`, etc.) — se crean en los sprints donde se implementa cada caso de uso.
- Que los efectos pesados (como enviar un email) se ejecuten en segundo plano sin bloquear al usuario — hoy todo ocurre de forma síncrona; la integración con Celery (para que esas tareas no demoren la respuesta al usuario) se conecta más adelante.

## En una frase

Se construyó el mecanismo que permite que un módulo anuncie "esto acaba de pasar" sin necesidad de conocer ni depender de quién más en el sistema está interesado en reaccionar a esa noticia.
