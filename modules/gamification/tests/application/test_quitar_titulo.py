import uuid

import pytest

from modules.gamification.application.dtos import QuitarTituloDTO
from modules.gamification.application.use_cases.quitar_titulo import QuitarTituloUseCase
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
    return QuitarTituloUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        titulo_desbloqueado_repository=TituloDesbloqueadoRepository(),
    )


@pytest.mark.django_db
def test_quita_un_titulo_equipado():
    logro = LogroRepository().add(
        Logro(
            clave=f"logro-{uuid.uuid4()}",
            nombre="Logro",
            descripcion="desc",
            tipo_criterio=TipoCriterioLogro.PRIMER_LABORATORIO,
            rareza=RarezaCosmetico.COMUN,
        )
    )
    titulo = TituloRepository().add(
        Titulo(
            clave=f"titulo-{uuid.uuid4()}",
            nombre="Título",
            descripcion="desc",
            rareza=RarezaCosmetico.COMUN,
            logro_requerido_id=logro.id,
        )
    )
    estudiante_id = uuid.uuid4()
    desbloqueo = TituloDesbloqueadoRepository().add(
        TituloDesbloqueado(estudiante_id=estudiante_id, titulo_id=titulo.id, equipado=True)
    )

    resultado = _uc().execute(QuitarTituloDTO(desbloqueo.id, estudiante_id, "estudiante"))

    assert resultado.equipado is False


@pytest.mark.django_db
def test_no_puede_quitar_titulo_de_otro_estudiante():
    with pytest.raises(NotFoundError):
        _uc().execute(QuitarTituloDTO(uuid.uuid4(), uuid.uuid4(), "estudiante"))


@pytest.mark.django_db
def test_admin_no_puede_quitar_titulo():
    with pytest.raises(ForbiddenError):
        _uc().execute(QuitarTituloDTO(uuid.uuid4(), uuid.uuid4(), "administrador"))
