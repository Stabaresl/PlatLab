from modules.lab_environments.domain.events import EntornoAprovisionamientoSolicitado
from modules.lab_environments.infrastructure.tasks import aprovisionar_entorno_task
from modules.shared.infrastructure.event_dispatcher import EventDispatcher


def _on_entorno_aprovisionamiento_solicitado(event: EntornoAprovisionamientoSolicitado) -> None:
    aprovisionar_entorno_task.delay(entorno_id=str(event.entorno_id), imagen=event.imagen)


def registrar_listeners(dispatcher: EventDispatcher) -> None:
    """
    Suscribe los listeners de lab_environments al `EventDispatcher`
    compartido. Invocado desde `LabEnvironmentsConfig.ready()` para
    quedar registrado una sola vez por proceso (mismo patrón que
    `modules.users`/`modules.notifications`).
    """
    dispatcher.subscribe(
        EntornoAprovisionamientoSolicitado, _on_entorno_aprovisionamiento_solicitado
    )
