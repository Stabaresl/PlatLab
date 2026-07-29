import uuid

import pytest

from modules.reports.application.dtos import CambiarEstadoReporteDTO, CrearReporteDTO
from modules.reports.application.use_cases.cambiar_estado_reporte import (
    CambiarEstadoReporteUseCase,
)
from modules.reports.application.use_cases.crear_reporte import CrearReporteUseCase
from modules.reports.domain.exceptions import ReporteYaResueltoError
from modules.reports.domain.value_objects import EstadoReporte
from modules.reports.infrastructure.repositories import ReporteRepository
from modules.shared.domain.exceptions import ForbiddenError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


def _crear_reporte():
    return CrearReporteUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        reporte_repository=ReporteRepository(),
    ).execute(
        CrearReporteDTO(
            estudiante_id=uuid.uuid4(),
            actor_rol="estudiante",
            laboratorio_id=uuid.uuid4(),
            descripcion="Descripcion valida de mas de diez caracteres.",
        )
    )


def _build_use_case():
    return CambiarEstadoReporteUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        reporte_repository=ReporteRepository(),
    )


@pytest.mark.django_db
def test_cambiar_estado_a_en_revision_no_es_final():
    reporte = _crear_reporte()

    resultado = _build_use_case().execute(
        CambiarEstadoReporteDTO(
            reporte_id=reporte.id,
            actor_id=uuid.uuid4(),
            actor_rol="administrador",
            nuevo_estado="en_revision",
        )
    )

    assert resultado.estado == EstadoReporte.EN_REVISION.value


@pytest.mark.django_db
def test_cambiar_estado_a_resuelto_es_final():
    reporte = _crear_reporte()

    resultado = _build_use_case().execute(
        CambiarEstadoReporteDTO(
            reporte_id=reporte.id,
            actor_id=uuid.uuid4(),
            actor_rol="administrador",
            nuevo_estado="resuelto",
        )
    )

    assert resultado.estado == EstadoReporte.RESUELTO.value


@pytest.mark.django_db
def test_cambiar_estado_de_resuelto_a_otro_lanza_error():
    reporte = _crear_reporte()
    use_case = _build_use_case()
    use_case.execute(
        CambiarEstadoReporteDTO(
            reporte_id=reporte.id,
            actor_id=uuid.uuid4(),
            actor_rol="administrador",
            nuevo_estado="resuelto",
        )
    )

    with pytest.raises(ReporteYaResueltoError):
        _build_use_case().execute(
            CambiarEstadoReporteDTO(
                reporte_id=reporte.id,
                actor_id=uuid.uuid4(),
                actor_rol="administrador",
                nuevo_estado="en_revision",
            )
        )


@pytest.mark.django_db
def test_cambiar_estado_actor_no_admin_lanza_forbidden():
    reporte = _crear_reporte()

    with pytest.raises(ForbiddenError):
        _build_use_case().execute(
            CambiarEstadoReporteDTO(
                reporte_id=reporte.id,
                actor_id=uuid.uuid4(),
                actor_rol="estudiante",
                nuevo_estado="resuelto",
            )
        )
