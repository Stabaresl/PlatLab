import uuid

import pytest

from modules.audit.infrastructure.repositories import AuditoriaRepository
from modules.authentication.domain.events import UserLoggedIn
from modules.reports.domain.events import ReportSubmitted
from modules.shared.infrastructure.event_dispatcher import EventDispatcher

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
