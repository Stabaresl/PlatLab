import uuid

import pytest

from modules.notifications.application.dtos import ListarNotificacionesDTO
from modules.notifications.application.queries.listar_notificaciones import (
    ListarNotificacionesQuery,
)
from modules.notifications.domain.entities import Notificacion
from modules.notifications.domain.value_objects import TipoNotificacion
from modules.notifications.infrastructure.repositories import NotificacionRepository


@pytest.mark.django_db
def test_listar_notificaciones_solo_las_del_usuario():
    user_id = uuid.uuid4()
    repo = NotificacionRepository()
    repo.add(Notificacion(user_id=user_id, tipo=TipoNotificacion.INVITACION, mensaje="propia"))
    repo.add(
        Notificacion(user_id=uuid.uuid4(), tipo=TipoNotificacion.INVITACION, mensaje="ajena")
    )

    resultado = ListarNotificacionesQuery(NotificacionRepository()).execute(
        ListarNotificacionesDTO(user_id=user_id)
    )

    assert len(resultado) == 1
    assert resultado[0].mensaje == "propia"


@pytest.mark.django_db
def test_listar_notificaciones_filtra_por_leida():
    user_id = uuid.uuid4()
    repo = NotificacionRepository()
    no_leida = repo.add(
        Notificacion(user_id=user_id, tipo=TipoNotificacion.INVITACION, mensaje="no leida")
    )
    leida = repo.add(
        Notificacion(user_id=user_id, tipo=TipoNotificacion.INVITACION, mensaje="leida")
    )
    leida.marcar_leida()
    repo.update(leida)

    resultado = ListarNotificacionesQuery(NotificacionRepository()).execute(
        ListarNotificacionesDTO(user_id=user_id, leida=False)
    )

    assert len(resultado) == 1
    assert resultado[0].id == no_leida.id
