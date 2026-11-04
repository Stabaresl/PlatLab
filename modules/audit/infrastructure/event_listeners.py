from modules.assignments.domain.events import (
    AssignmentAccepted,
    AssignmentExpired,
    AssignmentInvited,
    AssignmentRejected,
)
from modules.audit.domain.entities import RegistroAuditoria
from modules.audit.infrastructure.repositories import AuditoriaRepository
from modules.authentication.domain.events import (
    OAuthAccountLinked,
    PasswordResetRequested,
    UserLoggedIn,
    UserRegistered,
)
from modules.gamification.domain.events import LogroDesbloqueadoEvent
from modules.laboratories.domain.events import (
    LaboratoryApproved,
    LaboratoryCatalogVisibilityChanged,
    LaboratoryDuplicated,
    LaboratoryPublished,
    LaboratoryRejected,
    LaboratoryReviewRequested,
)
from modules.progress.domain.events import ExamGraded, FlagValidated, LabCompleted, SectionCompleted
from modules.progress.infrastructure.repositories import ProgresoRepository
from modules.reports.domain.events import ReportResolved, ReportSubmitted
from modules.rooms.domain.events import (
    EstadoSalaCambiado,
    EstudianteSeUnioASala,
    SalaCompletadaPorEstudiante,
    SalaCreada,
)
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.users.domain.events import (
    InstructorVerificationRequested,
    InstructorVerificationResolved,
    RolUsuarioCambiado,
    UsuarioDeshabilitado,
    UsuarioHabilitado,
)

_repo = AuditoriaRepository()


def _registrar(
    actor_id, accion: str, entidad_tipo: str | None, entidad_id, metadata: dict | None = None
) -> None:
    _repo.add(
        RegistroAuditoria(
            actor_id=actor_id,
            accion=accion,
            entidad_tipo=entidad_tipo,
            entidad_id=entidad_id,
            metadata=metadata,
        )
    )


def _estudiante_de(progreso_id):
    """Resuelve `estudiante_id` a partir de `progreso_id` (id suelto, Arquitectura §8)."""
    progreso = ProgresoRepository().get_by_id(progreso_id)
    return progreso.estudiante_id if progreso else None


# --- Authentication ---------------------------------------------------


def _on_user_registered(event: UserRegistered) -> None:
    _registrar(event.user_id, "user_registered", "user", event.user_id)


def _on_user_logged_in(event: UserLoggedIn) -> None:
    _registrar(event.user_id, "user_logged_in", "user", event.user_id)


def _on_password_reset_requested(event: PasswordResetRequested) -> None:
    # OJO (ver docstring del evento): nunca persistir `event.token` acá.
    _registrar(event.user_id, "password_reset_requested", "user", event.user_id)


def _on_oauth_account_linked(event: OAuthAccountLinked) -> None:
    _registrar(event.user_id, "oauth_account_linked", "user", event.user_id)


# --- Laboratories -------------------------------------------------------


def _on_laboratory_published(event: LaboratoryPublished) -> None:
    _registrar(event.instructor_id, "laboratory_published", "laboratorio", event.laboratorio_id)


def _on_laboratory_duplicated(event: LaboratoryDuplicated) -> None:
    _registrar(event.instructor_id, "laboratory_duplicated", "laboratorio", event.laboratorio_id)


def _on_laboratory_review_requested(event: LaboratoryReviewRequested) -> None:
    _registrar(
        event.instructor_id, "laboratory_review_requested", "laboratorio", event.laboratorio_id
    )


def _on_laboratory_approved(event: LaboratoryApproved) -> None:
    _registrar(event.admin_id, "laboratory_approved", "laboratorio", event.laboratorio_id)


def _on_laboratory_rejected(event: LaboratoryRejected) -> None:
    _registrar(event.admin_id, "laboratory_rejected", "laboratorio", event.laboratorio_id)


def _on_laboratory_catalog_visibility_changed(event: LaboratoryCatalogVisibilityChanged) -> None:
    accion = "laboratory_catalog_visibility_enabled" if event.visible else "laboratory_catalog_visibility_disabled"
    _registrar(event.actor_id, accion, "laboratorio", event.laboratorio_id)


# --- Gamification -----------------------------------------------------------


def _on_logro_desbloqueado(event: LogroDesbloqueadoEvent) -> None:
    _registrar(event.estudiante_id, "logro_desbloqueado", "logro", event.logro_id)


# --- Users (verificación de instructor) ------------------------------------


def _on_instructor_verification_requested(event: InstructorVerificationRequested) -> None:
    _registrar(
        event.user_id,
        "instructor_verification_requested",
        "solicitud_instructor",
        event.solicitud_id,
    )


def _on_instructor_verification_resolved(event: InstructorVerificationResolved) -> None:
    # La decide un administrador (OpenAlex solo aporta evidencia) — él es el
    # actor; el estudiante afectado queda en metadata.
    accion = (
        "instructor_verification_approved" if event.aprobada else "instructor_verification_rejected"
    )
    _registrar(
        event.admin_id,
        accion,
        "solicitud_instructor",
        event.solicitud_id,
        metadata={"user_id": str(event.user_id), "motivo": event.motivo_rechazo},
    )


# --- Users (administración: HA-01 exige auditar cada acción) ----------------
# El actor es el admin que tomó la decisión, la entidad es el usuario afectado.


def _on_usuario_deshabilitado(event: UsuarioDeshabilitado) -> None:
    _registrar(event.admin_id, "user_disabled", "user", event.user_id)


def _on_usuario_habilitado(event: UsuarioHabilitado) -> None:
    _registrar(event.admin_id, "user_enabled", "user", event.user_id)


def _on_rol_usuario_cambiado(event: RolUsuarioCambiado) -> None:
    _registrar(
        event.admin_id,
        "user_role_changed",
        "user",
        event.user_id,
        metadata={"rol_anterior": event.rol_anterior, "rol_nuevo": event.rol_nuevo},
    )


# --- Progress -------------------------------------------------------------


def _on_flag_validated(event: FlagValidated) -> None:
    _registrar(_estudiante_de(event.progreso_id), "flag_validated", "seccion", event.seccion_id)


def _on_section_completed(event: SectionCompleted) -> None:
    _registrar(_estudiante_de(event.progreso_id), "section_completed", "seccion", event.seccion_id)


def _on_lab_completed(event: LabCompleted) -> None:
    _registrar(_estudiante_de(event.progreso_id), "lab_completed", "progreso", event.progreso_id)


def _on_exam_graded(event: ExamGraded) -> None:
    _registrar(_estudiante_de(event.progreso_id), "exam_graded", "examen", event.examen_id)


# --- Assignments ----------------------------------------------------------


def _on_assignment_invited(event: AssignmentInvited) -> None:
    _registrar(event.estudiante_id, "assignment_invited", "asignacion", event.asignacion_id)


def _on_assignment_accepted(event: AssignmentAccepted) -> None:
    _registrar(event.estudiante_id, "assignment_accepted", "asignacion", event.asignacion_id)


def _on_assignment_rejected(event: AssignmentRejected) -> None:
    _registrar(event.estudiante_id, "assignment_rejected", "asignacion", event.asignacion_id)


def _on_assignment_expired(event: AssignmentExpired) -> None:
    _registrar(event.estudiante_id, "assignment_expired", "asignacion", event.asignacion_id)


# --- Reports ----------------------------------------------------------------


def _on_report_submitted(event: ReportSubmitted) -> None:
    _registrar(event.estudiante_id, "report_submitted", "reporte", event.reporte_id)


def _on_report_resolved(event: ReportResolved) -> None:
    _registrar(event.estudiante_id, "report_resolved", "reporte", event.reporte_id)


# --- Rooms --------------------------------------------------------------------


def _on_sala_creada(event: SalaCreada) -> None:
    metadata = {"laboratorio_id": str(event.laboratorio_id)}
    _registrar(event.anfitrion_id, "room_created", "sala", event.sala_id, metadata=metadata)


def _on_estado_sala_cambiado(event: EstadoSalaCambiado) -> None:
    _registrar(event.actor_id, "room_state_changed", "sala", event.sala_id, metadata={"estado": event.estado})


def _on_estudiante_se_unio(event: EstudianteSeUnioASala) -> None:
    _registrar(event.estudiante_id, "room_joined", "sala", event.sala_id)


def _on_sala_completada(event: SalaCompletadaPorEstudiante) -> None:
    _registrar(event.estudiante_id, "room_completed", "sala", event.sala_id, metadata={"posicion": event.posicion})


def registrar_listeners(dispatcher: EventDispatcher) -> None:
    """
    UC-12/RF-33: suscribe Audit a TODOS los eventos de dominio existentes
    en el sistema, sobre el `EventDispatcher` compartido (singleton).
    Invocado desde `AuditConfig.ready()` para quedar registrado una sola
    vez por proceso.
    """
    dispatcher.subscribe(UserRegistered, _on_user_registered)
    dispatcher.subscribe(UserLoggedIn, _on_user_logged_in)
    dispatcher.subscribe(PasswordResetRequested, _on_password_reset_requested)
    dispatcher.subscribe(OAuthAccountLinked, _on_oauth_account_linked)

    dispatcher.subscribe(LaboratoryPublished, _on_laboratory_published)
    dispatcher.subscribe(LaboratoryDuplicated, _on_laboratory_duplicated)
    dispatcher.subscribe(LaboratoryReviewRequested, _on_laboratory_review_requested)
    dispatcher.subscribe(LaboratoryApproved, _on_laboratory_approved)
    dispatcher.subscribe(LaboratoryRejected, _on_laboratory_rejected)
    dispatcher.subscribe(
        LaboratoryCatalogVisibilityChanged, _on_laboratory_catalog_visibility_changed
    )

    dispatcher.subscribe(LogroDesbloqueadoEvent, _on_logro_desbloqueado)

    dispatcher.subscribe(InstructorVerificationRequested, _on_instructor_verification_requested)
    dispatcher.subscribe(InstructorVerificationResolved, _on_instructor_verification_resolved)
    dispatcher.subscribe(UsuarioDeshabilitado, _on_usuario_deshabilitado)
    dispatcher.subscribe(UsuarioHabilitado, _on_usuario_habilitado)
    dispatcher.subscribe(RolUsuarioCambiado, _on_rol_usuario_cambiado)

    dispatcher.subscribe(FlagValidated, _on_flag_validated)
    dispatcher.subscribe(SectionCompleted, _on_section_completed)
    dispatcher.subscribe(LabCompleted, _on_lab_completed)
    dispatcher.subscribe(ExamGraded, _on_exam_graded)

    dispatcher.subscribe(AssignmentInvited, _on_assignment_invited)
    dispatcher.subscribe(AssignmentAccepted, _on_assignment_accepted)
    dispatcher.subscribe(AssignmentRejected, _on_assignment_rejected)
    dispatcher.subscribe(AssignmentExpired, _on_assignment_expired)

    dispatcher.subscribe(ReportSubmitted, _on_report_submitted)
    dispatcher.subscribe(ReportResolved, _on_report_resolved)

    dispatcher.subscribe(SalaCreada, _on_sala_creada)
    dispatcher.subscribe(EstadoSalaCambiado, _on_estado_sala_cambiado)
    dispatcher.subscribe(EstudianteSeUnioASala, _on_estudiante_se_unio)
    dispatcher.subscribe(SalaCompletadaPorEstudiante, _on_sala_completada)
