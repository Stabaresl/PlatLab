import uuid

import pytest

from modules.gamification.application.dtos import QuitarCosmeticoDTO
from modules.gamification.application.use_cases.quitar_cosmetico import QuitarCosmeticoUseCase
from modules.gamification.domain.entities import Cosmetico, CosmeticoDesbloqueado, Logro
from modules.gamification.domain.value_objects import RarezaCosmetico, TipoCosmetico, TipoCriterioLogro
from modules.gamification.infrastructure.repositories import CosmeticoDesbloqueadoRepository, CosmeticoRepository, LogroRepository
from modules.shared.domain.exceptions import ForbiddenError, NotFoundError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


def _uc():
    return QuitarCosmeticoUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        cosmetico_desbloqueado_repository=CosmeticoDesbloqueadoRepository(),
    )


@pytest.mark.django_db
def test_quita_un_cosmetico_equipado():
    logro = LogroRepository().add(
        Logro(
            clave=f"logro-{uuid.uuid4()}",
            nombre="Logro",
            descripcion="desc",
            tipo_criterio=TipoCriterioLogro.PRIMER_LABORATORIO,
            rareza=RarezaCosmetico.COMUN,
        )
    )
    cosmetico = CosmeticoRepository().add(
        Cosmetico(
            clave=f"cosmetico-{uuid.uuid4()}",
            nombre="Cosmético",
            tipo=TipoCosmetico.HOODIE,
            rareza=RarezaCosmetico.COMUN,
            color="0,0,0",
            logro_requerido_id=logro.id,
        )
    )
    estudiante_id = uuid.uuid4()
    desbloqueo = CosmeticoDesbloqueadoRepository().add(
        CosmeticoDesbloqueado(estudiante_id=estudiante_id, cosmetico_id=cosmetico.id, equipado=True)
    )

    resultado = _uc().execute(QuitarCosmeticoDTO(desbloqueo.id, estudiante_id, "estudiante"))

    assert resultado.equipado is False


@pytest.mark.django_db
def test_no_puede_quitar_cosmetico_de_otro_estudiante():
    with pytest.raises(NotFoundError):
        _uc().execute(QuitarCosmeticoDTO(uuid.uuid4(), uuid.uuid4(), "estudiante"))


@pytest.mark.django_db
def test_admin_no_puede_quitar_cosmetico():
    with pytest.raises(ForbiddenError):
        _uc().execute(QuitarCosmeticoDTO(uuid.uuid4(), uuid.uuid4(), "administrador"))
