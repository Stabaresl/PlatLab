import uuid

import pytest

from modules.gamification.application.dtos import EquiparCosmeticoDTO
from modules.gamification.application.use_cases.equipar_cosmetico import EquiparCosmeticoUseCase
from modules.gamification.domain.entities import Cosmetico, CosmeticoDesbloqueado, Logro
from modules.gamification.domain.value_objects import RarezaCosmetico, TipoCosmetico, TipoCriterioLogro
from modules.gamification.infrastructure.repositories import CosmeticoDesbloqueadoRepository, CosmeticoRepository, LogroRepository
from modules.shared.domain.exceptions import ForbiddenError, NotFoundError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


def _uc():
    return EquiparCosmeticoUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        cosmetico_desbloqueado_repository=CosmeticoDesbloqueadoRepository(),
        cosmetico_repository=CosmeticoRepository(),
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


def _cosmetico(logro_id, tipo=TipoCosmetico.HOODIE) -> Cosmetico:
    return CosmeticoRepository().add(
        Cosmetico(
            clave=f"cosmetico-{uuid.uuid4()}",
            nombre="Cosmético",
            tipo=tipo,
            rareza=RarezaCosmetico.COMUN,
            color="0,0,0",
            logro_requerido_id=logro_id,
        )
    )


def _desbloquear(estudiante_id, cosmetico_id, equipado=False) -> CosmeticoDesbloqueado:
    return CosmeticoDesbloqueadoRepository().add(
        CosmeticoDesbloqueado(estudiante_id=estudiante_id, cosmetico_id=cosmetico_id, equipado=equipado)
    )


@pytest.mark.django_db
def test_equipa_un_cosmetico_desbloqueado():
    logro = _logro()
    cosmetico = _cosmetico(logro.id)
    estudiante_id = uuid.uuid4()
    desbloqueo = _desbloquear(estudiante_id, cosmetico.id)

    resultado = _uc().execute(
        EquiparCosmeticoDTO(desbloqueo.id, estudiante_id, "estudiante")
    )

    assert resultado.equipado is True


@pytest.mark.django_db
def test_equipar_desequipa_otro_del_mismo_tipo():
    logro = _logro()
    hoodie_a = _cosmetico(logro.id, tipo=TipoCosmetico.HOODIE)
    hoodie_b = _cosmetico(logro.id, tipo=TipoCosmetico.HOODIE)
    estudiante_id = uuid.uuid4()
    desbloqueo_a = _desbloquear(estudiante_id, hoodie_a.id, equipado=True)
    desbloqueo_b = _desbloquear(estudiante_id, hoodie_b.id)

    _uc().execute(EquiparCosmeticoDTO(desbloqueo_b.id, estudiante_id, "estudiante"))

    repo = CosmeticoDesbloqueadoRepository()
    assert repo.get_by_id(desbloqueo_a.id).equipado is False
    assert repo.get_by_id(desbloqueo_b.id).equipado is True


@pytest.mark.django_db
def test_insignias_admiten_varias_equipadas_a_la_vez():
    logro = _logro()
    insignia_a = _cosmetico(logro.id, tipo=TipoCosmetico.INSIGNIA)
    insignia_b = _cosmetico(logro.id, tipo=TipoCosmetico.INSIGNIA)
    estudiante_id = uuid.uuid4()
    desbloqueo_a = _desbloquear(estudiante_id, insignia_a.id, equipado=True)
    desbloqueo_b = _desbloquear(estudiante_id, insignia_b.id)

    _uc().execute(EquiparCosmeticoDTO(desbloqueo_b.id, estudiante_id, "estudiante"))

    repo = CosmeticoDesbloqueadoRepository()
    assert repo.get_by_id(desbloqueo_a.id).equipado is True
    assert repo.get_by_id(desbloqueo_b.id).equipado is True


@pytest.mark.django_db
def test_no_puede_equipar_cosmetico_de_otro_estudiante():
    logro = _logro()
    cosmetico = _cosmetico(logro.id)
    desbloqueo = _desbloquear(uuid.uuid4(), cosmetico.id)

    with pytest.raises(NotFoundError):
        _uc().execute(EquiparCosmeticoDTO(desbloqueo.id, uuid.uuid4(), "estudiante"))


@pytest.mark.django_db
def test_instructor_no_puede_equipar():
    with pytest.raises(ForbiddenError):
        _uc().execute(EquiparCosmeticoDTO(uuid.uuid4(), uuid.uuid4(), "instructor"))
