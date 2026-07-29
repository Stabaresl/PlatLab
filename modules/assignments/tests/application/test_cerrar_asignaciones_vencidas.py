import uuid
from datetime import datetime, timedelta, timezone

import pytest

from modules.assignments.application.use_cases.cerrar_asignaciones_vencidas import (
    CerrarAsignacionesVencidasUseCase,
)
from modules.assignments.domain.entities import Asignacion
from modules.assignments.domain.value_objects import EstadoAsignacion
from modules.assignments.infrastructure.repositories import AsignacionRepository
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


def _build_use_case():
    return CerrarAsignacionesVencidasUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        asignacion_repository=AsignacionRepository(),
    )


@pytest.mark.django_db
def test_cierra_asignaciones_vencidas_y_no_toca_las_vigentes():
    repo = AsignacionRepository()
    ahora = datetime.now(timezone.utc)

    vencida = repo.add(
        Asignacion(
            estudiante_id=uuid.uuid4(),
            laboratorio_id=uuid.uuid4(),
            estado=EstadoAsignacion.ACTIVA,
            fecha_vencimiento=ahora - timedelta(minutes=5),
        )
    )
    vigente = repo.add(
        Asignacion(
            estudiante_id=uuid.uuid4(),
            laboratorio_id=uuid.uuid4(),
            estado=EstadoAsignacion.ACTIVA,
            fecha_vencimiento=ahora + timedelta(days=1),
        )
    )

    cantidad = _build_use_case().execute()

    assert cantidad == 1
    assert repo.get_by_id(vencida.id).estado == EstadoAsignacion.VENCIDA
    assert repo.get_by_id(vigente.id).estado == EstadoAsignacion.ACTIVA


@pytest.mark.django_db
def test_no_cierra_nada_si_no_hay_vencidas():
    cantidad = _build_use_case().execute()
    assert cantidad == 0
