from modules.assignments.domain.events import AssignmentExpired, AssignmentInvited
from modules.notifications.domain.value_objects import TipoNotificacion
from modules.notifications.infrastructure.celery_tasks import despachar_notificacion_task
from modules.reports.domain.events import ReportResolved
from modules.shared.infrastructure.event_dispatcher import EventDispatcher

_MSG_INVITACION = "Fuiste invitado a un nuevo laboratorio."
_MSG_ACCESO_VENCIDO = "Tu acceso a un laboratorio ha vencido."
_MSG_REPORTE_RESUELTO = "Tu reporte fue resuelto."


def _on_assignment_invited(event: AssignmentInvited) -> None:
    despachar_notificacion_task.delay(
        user_id=str(event.estudiante_id),
        tipo=TipoNotificacion.INVITACION.value,
        mensaje=_MSG_INVITACION,
        entidad_tipo="asignacion",
        entidad_id=str(event.asignacion_id),
    )


def _on_assignment_expired(event: AssignmentExpired) -> None:
    despachar_notificacion_task.delay(
        user_id=str(event.estudiante_id),
        tipo=TipoNotificacion.ACCESO_VENCIDO.value,
        mensaje=_MSG_ACCESO_VENCIDO,
        entidad_tipo="asignacion",
        entidad_id=str(event.asignacion_id),
    )


def _on_report_resolved(event: ReportResolved) -> None:
    despachar_notificacion_task.delay(
        user_id=str(event.estudiante_id),
        tipo=TipoNotificacion.REPORTE_RESUELTO.value,
        mensaje=_MSG_REPORTE_RESUELTO,
        entidad_tipo="reporte",
        entidad_id=str(event.reporte_id),
    )


def registrar_listeners(dispatcher: EventDispatcher) -> None:
    """
    HE-13/UC-11: suscribe los listeners de Notifications al
    `EventDispatcher` compartido (singleton, ver
    `modules.shared.infrastructure.event_dispatcher`). Invocado desde
    `NotificationsConfig.ready()` para quedar registrado una sola vez
    por proceso.
    """
    dispatcher.subscribe(AssignmentInvited, _on_assignment_invited)
    dispatcher.subscribe(AssignmentExpired, _on_assignment_expired)
    dispatcher.subscribe(ReportResolved, _on_report_resolved)
