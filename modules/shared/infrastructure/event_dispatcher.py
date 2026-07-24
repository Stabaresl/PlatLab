from collections import defaultdict
from typing import Callable

from modules.shared.domain.domain_event import DomainEvent

Listener = Callable[[DomainEvent], None]


class EventDispatcher:
    """
    Implementación de `IEventDispatcher` (ver modules.shared.application.ports).

    Hoy: registro y despacho en memoria, síncrono. Cada listener se ejecuta
    en el mismo proceso/request que disparó el evento.

    Mañana: los listeners que necesiten trabajo asíncrono (envío de email,
    notificación push) no deben ejecutar ese trabajo directamente aquí —
    deben encolar una tarea de Celery y retornar de inmediato, para no
    bloquear el request. `EventDispatcher` en sí no cambia si el día de
    mañana se reemplaza por un bus de eventos real (ej. Kafka, SQS): solo
    cambia la implementación de Infrastructure, Domain/Application no se
    tocan porque dependen de `IEventDispatcher`, no de esta clase.

    Un único listener puede fallar sin frenar el despacho a los demás
    listeners del mismo evento (falla aislada, se recolectan y se re-lanzan
    al final para no ocultar el error).
    """

    def __init__(self):
        self._listeners: dict[type[DomainEvent], list[Listener]] = defaultdict(list)

    def subscribe(self, event_type: type[DomainEvent], listener: Listener) -> None:
        self._listeners[event_type].append(listener)

    def dispatch(self, event: DomainEvent) -> None:
        errors: list[Exception] = []
        for listener in self._listeners[type(event)]:
            try:
                listener(event)
            except Exception as exc:  # noqa: BLE001 — aislar fallas entre listeners
                errors.append(exc)

        if errors:
            raise ExceptionGroup(
                f"{len(errors)} listener(s) fallaron al procesar {type(event).__name__}",
                errors,
            )
