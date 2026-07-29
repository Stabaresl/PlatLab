import uuid

import pytest

from modules.audit.application.dtos import ConsultarAuditoriaDTO
from modules.audit.application.queries.consultar_auditoria import ConsultarAuditoriaQuery
from modules.audit.domain.entities import RegistroAuditoria
from modules.audit.infrastructure.repositories import AuditoriaRepository
from modules.shared.domain.exceptions import ForbiddenError


@pytest.mark.django_db
def test_consultar_auditoria_admin_ve_registros():
    repo = AuditoriaRepository()
    actor_id = uuid.uuid4()
    repo.add(
        RegistroAuditoria(
            actor_id=actor_id, accion="user_logged_in", entidad_tipo="user", entidad_id=actor_id
        )
    )

    resultado = ConsultarAuditoriaQuery(AuditoriaRepository()).execute(
        ConsultarAuditoriaDTO(actor_rol="administrador", actor_id=actor_id)
    )

    assert len(resultado) == 1
    assert resultado[0].accion == "user_logged_in"


@pytest.mark.django_db
def test_consultar_auditoria_filtra_por_accion():
    repo = AuditoriaRepository()
    actor_id = uuid.uuid4()
    repo.add(
        RegistroAuditoria(
            actor_id=actor_id, accion="user_logged_in", entidad_tipo=None, entidad_id=None
        )
    )
    repo.add(
        RegistroAuditoria(
            actor_id=actor_id, accion="assignment_invited", entidad_tipo=None, entidad_id=None
        )
    )

    resultado = ConsultarAuditoriaQuery(AuditoriaRepository()).execute(
        ConsultarAuditoriaDTO(actor_rol="administrador", accion="assignment_invited")
    )

    assert len(resultado) == 1
    assert resultado[0].accion == "assignment_invited"


@pytest.mark.django_db
def test_consultar_auditoria_no_admin_lanza_forbidden():
    with pytest.raises(ForbiddenError):
        ConsultarAuditoriaQuery(AuditoriaRepository()).execute(
            ConsultarAuditoriaDTO(actor_rol="estudiante")
        )
