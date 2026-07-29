import uuid

import pytest

from modules.notifications.application.dtos import MarcarLeidaDTO
from modules.notifications.application.use_cases.marcar_leida import MarcarLeidaUseCase
from modules.notifications.domain.entities import Notificacion
from modules.notifications.domain.value_objects import TipoNotificacion
from modules.notifications.infrastructure.repositories import NotificacionRepository
from modules.shared.domain.exceptions import NotFoundError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


def _crear_notificacion(user_id):
    return NotificacionRepository().add(
        Notificacion(user_id=user_id, tipo=TipoNotificacion.INVITACION, mensaje="mensaje")
    )


def _build_use_case():
    return MarcarLeidaUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        notificacion_repository=NotificacionRepository(),
    )


@pytest.mark.django_db
def test_marcar_leida_exitoso():
    user_id = uuid.uuid4()
    notificacion = _crear_notificacion(user_id)

    resultado = _build_use_case().execute(
        MarcarLeidaDTO(notificacion_id=notificacion.id, actor_id=user_id)
    )

    assert resultado.leida is True


@pytest.mark.django_db
def test_marcar_leida_de_otro_usuario_lanza_not_found():
    notificacion = _crear_notificacion(uuid.uuid4())

    with pytest.raises(NotFoundError):
        _build_use_case().execute(
            MarcarLeidaDTO(notificacion_id=notificacion.id, actor_id=uuid.uuid4())
        )


@pytest.mark.django_db
def test_marcar_leida_inexistente_lanza_not_found():
    with pytest.raises(NotFoundError):
        _build_use_case().execute(
            MarcarLeidaDTO(notificacion_id=uuid.uuid4(), actor_id=uuid.uuid4())
        )
