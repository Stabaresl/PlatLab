import uuid

import pytest

from modules.gamification.application.dtos import EquiparTituloDTO
from modules.gamification.application.use_cases.equipar_titulo import EquiparTituloUseCase
from modules.gamification.domain.entities import Logro, Titulo, TituloDesbloqueado
from modules.gamification.domain.value_objects import RarezaCosmetico, TipoCriterioLogro
from modules.gamification.infrastructure.repositories import (
    LogroRepository,
    TituloDesbloqueadoRepository,
    TituloRepository,
)
from modules.shared.domain.exceptions import ForbiddenError, NotFoundError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


def _uc():
    return EquiparTituloUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        titulo_desbloqueado_repository=TituloDesbloqueadoRepository(),
    )


def _logro() -> Logro:
    return LogroRepository().add(
        Logro(
            clave=f"logro-{uuid.uuid4()}",
            nombre="Logro",
            descripcion="desc",
            tipo_criterio=TipoCriterioLogro.PRIMER_LABORATORIO,
            rareza=RarezaCosmetico.COMUN,
        )
    )


def _titulo(logro_id) -> Titulo:
    return TituloRepository().add(
        Titulo(
            clave=f"titulo-{uuid.uuid4()}",
            nombre="Título",
            descripcion="desc",
            rareza=RarezaCosmetico.COMUN,
            logro_requerido_id=logro_id,
        )
    )


def _desbloquear(estudiante_id, titulo_id, equipado=False) -> TituloDesbloqueado:
    return TituloDesbloqueadoRepository().add(
        TituloDesbloqueado(estudiante_id=estudiante_id, titulo_id=titulo_id, equipado=equipado)
    )


@pytest.mark.django_db
def test_equipa_un_titulo_desbloqueado():
    logro = _logro()
    titulo = _titulo(logro.id)
    estudiante_id = uuid.uuid4()
    desbloqueo = _desbloquear(estudiante_id, titulo.id)

    resultado = _uc().execute(EquiparTituloDTO(desbloqueo.id, estudiante_id, "estudiante"))

    assert resultado.equipado is True


@pytest.mark.django_db
def test_equipar_desequipa_el_titulo_anterior():
    logro = _logro()
    titulo_a, titulo_b = _titulo(logro.id), _titulo(logro.id)
    estudiante_id = uuid.uuid4()
    desbloqueo_a = _desbloquear(estudiante_id, titulo_a.id, equipado=True)
    desbloqueo_b = _desbloquear(estudiante_id, titulo_b.id)

    _uc().execute(EquiparTituloDTO(desbloqueo_b.id, estudiante_id, "estudiante"))

    repo = TituloDesbloqueadoRepository()
    assert repo.get_by_id(desbloqueo_a.id).equipado is False
    assert repo.get_by_id(desbloqueo_b.id).equipado is True


@pytest.mark.django_db
def test_no_puede_equipar_titulo_de_otro_estudiante():
    logro = _logro()
    titulo = _titulo(logro.id)
    desbloqueo = _desbloquear(uuid.uuid4(), titulo.id)

    with pytest.raises(NotFoundError):
        _uc().execute(EquiparTituloDTO(desbloqueo.id, uuid.uuid4(), "estudiante"))


@pytest.mark.django_db
def test_instructor_no_puede_equipar_titulo():
    with pytest.raises(ForbiddenError):
        _uc().execute(EquiparTituloDTO(uuid.uuid4(), uuid.uuid4(), "instructor"))
