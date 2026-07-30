from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.users.domain.events import InstructorVerificationRequested
from modules.users.infrastructure.celery_tasks import verificar_solicitud_instructor_task


def _on_instructor_verification_requested(event: InstructorVerificationRequested) -> None:
    verificar_solicitud_instructor_task.delay(solicitud_id=str(event.solicitud_id))


def registrar_listeners(dispatcher: EventDispatcher) -> None:
    """
    Suscribe los listeners de Users al `EventDispatcher` compartido.
    Invocado desde `UsersConfig.ready()` para quedar registrado una sola
    vez por proceso (mismo patrón que `modules.notifications`).
    """
    dispatcher.subscribe(InstructorVerificationRequested, _on_instructor_verification_requested)
