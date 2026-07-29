import uuid

import pytest

from modules.reports.application.dtos import CrearReporteDTO
from modules.reports.application.use_cases.crear_reporte import CrearReporteUseCase
from modules.reports.domain.exceptions import DescriptionTooShortError
from modules.reports.domain.value_objects import EstadoReporte
from modules.reports.infrastructure.repositories import ReporteRepository
from modules.shared.domain.exceptions import ForbiddenError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


def _build_use_case():
    return CrearReporteUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        reporte_repository=ReporteRepository(),
    )


@pytest.mark.django_db
def test_crear_reporte_exitoso_queda_abierto():
    resultado = _build_use_case().execute(
        CrearReporteDTO(
            estudiante_id=uuid.uuid4(),
            actor_rol="estudiante",
            laboratorio_id=uuid.uuid4(),
            descripcion="La flag no valida aunque el valor es correcto.",
        )
    )

    assert resultado.estado == EstadoReporte.ABIERTO.value


@pytest.mark.django_db
def test_crear_reporte_descripcion_corta_lanza_error():
    with pytest.raises(DescriptionTooShortError):
        _build_use_case().execute(
            CrearReporteDTO(
                estudiante_id=uuid.uuid4(),
                actor_rol="estudiante",
                laboratorio_id=uuid.uuid4(),
                descripcion="corta",
            )
        )


@pytest.mark.django_db
def test_crear_reporte_actor_no_estudiante_lanza_forbidden():
    with pytest.raises(ForbiddenError):
        _build_use_case().execute(
            CrearReporteDTO(
                estudiante_id=uuid.uuid4(),
                actor_rol="instructor",
                laboratorio_id=uuid.uuid4(),
                descripcion="Descripcion valida de mas de diez caracteres.",
            )
        )
