import uuid

import pytest

from modules.assignments.domain.events import AssignmentInvited
from modules.notifications.domain.value_objects import TipoNotificacion
from modules.notifications.infrastructure.repositories import NotificacionRepository
from modules.shared.infrastructure.event_dispatcher import EventDispatcher

# `NotificationsConfig.ready()` ya suscribió los listeners reales al
# `EventDispatcher` (singleton) al arrancar Django para esta sesión de
# tests (`CELERY_TASK_ALWAYS_EAGER=True`, config/settings/test.py) — acá
# solo se dispara el evento real y se confirma el efecto de punta a punta.


@pytest.mark.django_db
def test_assignment_invited_crea_notificacion_in_app():
    estudiante_id = uuid.uuid4()
    asignacion_id = uuid.uuid4()

    EventDispatcher().dispatch(
        AssignmentInvited(
            asignacion_id=asignacion_id,
            estudiante_id=estudiante_id,
            laboratorio_id=uuid.uuid4(),
        )
    )

    notificaciones = NotificacionRepository().find_por_usuario(estudiante_id)
    assert len(notificaciones) == 1
    assert notificaciones[0].tipo == TipoNotificacion.INVITACION
    assert notificaciones[0].entidad_id == asignacion_id
