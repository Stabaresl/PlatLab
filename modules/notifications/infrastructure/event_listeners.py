from modules.assignments.domain.events import AssignmentExpired, AssignmentInvited
from modules.laboratories.domain.events import LaboratoryApproved, LaboratoryRejected
from modules.notifications.domain.value_objects import TipoNotificacion
from modules.notifications.infrastructure.celery_tasks import despachar_notificacion_task
from modules.reports.domain.events import ReportResolved
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.users.domain.events import InstructorVerificationResolved

_MSG_INVITACION = "Fuiste invitado a un nuevo laboratorio."
_MSG_ACCESO_VENCIDO = "Tu acceso a un laboratorio ha vencido."
_MSG_REPORTE_RESUELTO = "Tu reporte fue resuelto."
_MSG_INSTRUCTOR_APROBADO = (
    "Tu ORCID fue verificado en OpenAlex. Ya eres instructor en PlatLAB."
)
_MSG_LABORATORIO_APROBADO = "Tu laboratorio fue aprobado y ya está publicado en el catálogo."


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


def _on_instructor_verification_resolved(event: InstructorVerificationResolved) -> None:
    despachar_notificacion_task.delay(
        user_id=str(event.user_id),
        tipo=(
            TipoNotificacion.INSTRUCTOR_APROBADO.value
            if event.aprobada
            else TipoNotificacion.INSTRUCTOR_RECHAZADO.value
        ),
        mensaje=event.motivo_rechazo if not event.aprobada else _MSG_INSTRUCTOR_APROBADO,
        entidad_tipo="solicitud_instructor",
        entidad_id=str(event.solicitud_id),
    )


def _on_laboratory_approved(event: LaboratoryApproved) -> None:
    if event.instructor_id is None:
        return
    despachar_notificacion_task.delay(
        user_id=str(event.instructor_id),
        tipo=TipoNotificacion.LABORATORIO_APROBADO.value,
        mensaje=_MSG_LABORATORIO_APROBADO,
        entidad_tipo="laboratorio",
        entidad_id=str(event.laboratorio_id),
    )


def _on_laboratory_rejected(event: LaboratoryRejected) -> None:
    if event.instructor_id is None:
        return
    despachar_notificacion_task.delay(
        user_id=str(event.instructor_id),
        tipo=TipoNotificacion.LABORATORIO_RECHAZADO.value,
        mensaje=event.motivo,
        entidad_tipo="laboratorio",
        entidad_id=str(event.laboratorio_id),
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
    dispatcher.subscribe(InstructorVerificationResolved, _on_instructor_verification_resolved)
    dispatcher.subscribe(LaboratoryApproved, _on_laboratory_approved)
    dispatcher.subscribe(LaboratoryRejected, _on_laboratory_rejected)
