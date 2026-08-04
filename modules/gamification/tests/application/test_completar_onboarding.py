import uuid

import pytest

from modules.gamification.application.dtos import CompletarOnboardingDTO
from modules.gamification.application.use_cases.completar_onboarding import (
    CompletarOnboardingUseCase,
)
from modules.gamification.domain.entities import Logro, Titulo
from modules.gamification.domain.value_objects import RarezaCosmetico, TipoCriterioLogro
from modules.gamification.infrastructure.repositories import (
    CosmeticoDesbloqueadoRepository,
    CosmeticoRepository,
    LogroDesbloqueadoRepository,
    LogroRepository,
    TituloDesbloqueadoRepository,
    TituloRepository,
)
from modules.shared.domain.exceptions import ForbiddenError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


def _uc():
    return CompletarOnboardingUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        logro_repository=LogroRepository(),
        logro_desbloqueado_repository=LogroDesbloqueadoRepository(),
        cosmetico_repository=CosmeticoRepository(),
        cosmetico_desbloqueado_repository=CosmeticoDesbloqueadoRepository(),
        titulo_repository=TituloRepository(),
        titulo_desbloqueado_repository=TituloDesbloqueadoRepository(),
    )


def _crear_logro_primeros_pasos() -> Logro:
    return LogroRepository().add(
        Logro(
            clave="primeros_pasos",
            nombre="Primeros Pasos",
            descripcion="desc",
            tipo_criterio=TipoCriterioLogro.TOUR_COMPLETADO,
            rareza=RarezaCosmetico.COMUN,
        )
    )


@pytest.mark.django_db
def test_completar_onboarding_desbloquea_el_logro_primeros_pasos():
    estudiante_id = uuid.uuid4()
    logro = _crear_logro_primeros_pasos()

    resultado = _uc().execute(
        CompletarOnboardingDTO(actor_id=estudiante_id, actor_rol="estudiante")
    )

    assert resultado.logro_desbloqueado is not None
    assert resultado.logro_desbloqueado.logro_id == logro.id
    assert LogroDesbloqueadoRepository().existe(estudiante_id, logro.id)


@pytest.mark.django_db
def test_completar_onboarding_tambien_desbloquea_el_titulo_asociado():
    estudiante_id = uuid.uuid4()
    logro = _crear_logro_primeros_pasos()
    titulo = TituloRepository().add(
        Titulo(
            clave="recluta",
            nombre="Recluta",
            descripcion="desc",
            rareza=RarezaCosmetico.COMUN,
            logro_requerido_id=logro.id,
        )
    )

    _uc().execute(CompletarOnboardingDTO(actor_id=estudiante_id, actor_rol="estudiante"))

    assert TituloDesbloqueadoRepository().existe(estudiante_id, titulo.id)


@pytest.mark.django_db
def test_completar_onboarding_es_idempotente():
    estudiante_id = uuid.uuid4()
    _crear_logro_primeros_pasos()
    uc = _uc()
    primero = uc.execute(CompletarOnboardingDTO(actor_id=estudiante_id, actor_rol="estudiante"))

    segundo = _uc().execute(CompletarOnboardingDTO(actor_id=estudiante_id, actor_rol="estudiante"))

    assert primero.logro_desbloqueado is not None
    assert segundo.logro_desbloqueado is None


@pytest.mark.django_db
def test_completar_onboarding_sin_logro_sembrado_no_falla():
    estudiante_id = uuid.uuid4()

    resultado = _uc().execute(
        CompletarOnboardingDTO(actor_id=estudiante_id, actor_rol="estudiante")
    )

    assert resultado.logro_desbloqueado is None


@pytest.mark.django_db
def test_admin_no_puede_completar_onboarding():
    with pytest.raises(ForbiddenError):
        _uc().execute(CompletarOnboardingDTO(actor_id=uuid.uuid4(), actor_rol="administrador"))
