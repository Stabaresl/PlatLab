import uuid

import pytest

from modules.audit.infrastructure.repositories import AuditoriaRepository
from modules.authentication.domain.events import UserLoggedIn
from modules.gamification.domain.events import LogroDesbloqueadoEvent
from modules.laboratories.domain.events import (
    LaboratoryApproved,
    LaboratoryCatalogVisibilityChanged,
    LaboratoryRejected,
    LaboratoryReviewRequested,
)
from modules.reports.domain.events import ReportSubmitted
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.users.domain.events import InstructorVerificationRequested, InstructorVerificationResolved

# `AuditConfig.ready()` ya suscribió los listeners reales al
# `EventDispatcher` (singleton) al arrancar Django para esta sesión de
# tests — acá solo se dispara el evento real y se confirma el efecto.


@pytest.mark.django_db
def test_user_logged_in_registra_auditoria():
    user_id = uuid.uuid4()

    EventDispatcher().dispatch(UserLoggedIn(user_id=user_id))

    registros = AuditoriaRepository().find_todos(actor_id=user_id)
    assert len(registros) == 1
    assert registros[0].accion == "user_logged_in"


@pytest.mark.django_db
def test_report_submitted_registra_auditoria_con_entidad():
    estudiante_id = uuid.uuid4()
    reporte_id = uuid.uuid4()

    EventDispatcher().dispatch(
        ReportSubmitted(
            reporte_id=reporte_id, estudiante_id=estudiante_id, laboratorio_id=uuid.uuid4()
        )
    )

    registros = AuditoriaRepository().find_todos(actor_id=estudiante_id)
    assert len(registros) == 1
    assert registros[0].entidad_tipo == "reporte"
    assert registros[0].entidad_id == reporte_id


@pytest.mark.django_db
def test_laboratory_review_requested_registra_auditoria_con_instructor_como_actor():
    instructor_id = uuid.uuid4()
    laboratorio_id = uuid.uuid4()

    EventDispatcher().dispatch(
        LaboratoryReviewRequested(laboratorio_id=laboratorio_id, instructor_id=instructor_id)
    )

    registros = AuditoriaRepository().find_todos(actor_id=instructor_id)
    assert len(registros) == 1
    assert registros[0].accion == "laboratory_review_requested"
    assert registros[0].entidad_id == laboratorio_id


@pytest.mark.django_db
def test_laboratory_approved_registra_al_admin_como_actor_no_al_instructor():
    admin_id = uuid.uuid4()
    instructor_id = uuid.uuid4()
    laboratorio_id = uuid.uuid4()

    EventDispatcher().dispatch(
        LaboratoryApproved(
            laboratorio_id=laboratorio_id, instructor_id=instructor_id, admin_id=admin_id
        )
    )

    registros_admin = AuditoriaRepository().find_todos(actor_id=admin_id)
    assert len(registros_admin) == 1
    assert registros_admin[0].accion == "laboratory_approved"

    registros_instructor = AuditoriaRepository().find_todos(actor_id=instructor_id)
    assert len(registros_instructor) == 0


@pytest.mark.django_db
def test_laboratory_rejected_registra_al_admin_como_actor():
    admin_id = uuid.uuid4()
    laboratorio_id = uuid.uuid4()

    EventDispatcher().dispatch(
        LaboratoryRejected(
            laboratorio_id=laboratorio_id,
            instructor_id=uuid.uuid4(),
            admin_id=admin_id,
            motivo="Falta contenido",
        )
    )

    registros = AuditoriaRepository().find_todos(actor_id=admin_id)
    assert len(registros) == 1
    assert registros[0].accion == "laboratory_rejected"


@pytest.mark.django_db
def test_laboratory_catalog_visibility_changed_registra_accion_segun_visible():
    actor_id = uuid.uuid4()
    laboratorio_id = uuid.uuid4()

    EventDispatcher().dispatch(
        LaboratoryCatalogVisibilityChanged(
            laboratorio_id=laboratorio_id,
            instructor_id=uuid.uuid4(),
            actor_id=actor_id,
            visible=True,
        )
    )

    registros = AuditoriaRepository().find_todos(actor_id=actor_id)
    assert len(registros) == 1
    assert registros[0].accion == "laboratory_catalog_visibility_enabled"
    assert registros[0].entidad_id == laboratorio_id


@pytest.mark.django_db
def test_logro_desbloqueado_registra_auditoria():
    estudiante_id = uuid.uuid4()
    logro_id = uuid.uuid4()

    EventDispatcher().dispatch(
        LogroDesbloqueadoEvent(estudiante_id=estudiante_id, logro_id=logro_id, nombre="Primer Hackeo")
    )

    registros = AuditoriaRepository().find_todos(actor_id=estudiante_id)
    assert len(registros) == 1
    assert registros[0].accion == "logro_desbloqueado"
    assert registros[0].entidad_id == logro_id


@pytest.mark.django_db
def test_instructor_verification_requested_registra_auditoria():
    user_id = uuid.uuid4()
    solicitud_id = uuid.uuid4()

    EventDispatcher().dispatch(
        InstructorVerificationRequested(
            solicitud_id=solicitud_id, user_id=user_id, orcid="0000-0000-0000-0000", nombre_declarado="Test"
        )
    )

    registros = AuditoriaRepository().find_todos(actor_id=user_id)
    assert len(registros) == 1
    assert registros[0].accion == "instructor_verification_requested"
    assert registros[0].entidad_id == solicitud_id


@pytest.mark.django_db
def test_instructor_verification_resolved_registra_sin_actor_humano():
    solicitud_id = uuid.uuid4()

    EventDispatcher().dispatch(
        InstructorVerificationResolved(
            solicitud_id=solicitud_id, user_id=uuid.uuid4(), aprobada=True, motivo_rechazo=None
        )
    )

    registros = AuditoriaRepository().find_todos(accion="instructor_verification_approved")
    assert len(registros) == 1
    assert registros[0].entidad_id == solicitud_id
    assert registros[0].actor_id is None
