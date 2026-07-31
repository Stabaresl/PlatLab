import uuid

import pytest

from modules.gamification.application.dtos import CambiarAvatarDTO
from modules.gamification.application.use_cases.cambiar_avatar import CambiarAvatarUseCase
from modules.gamification.infrastructure.repositories import PerfilJugadorRepository
from modules.shared.domain.exceptions import ForbiddenError, ValidationError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


def _uc():
    return CambiarAvatarUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        perfil_repository=PerfilJugadorRepository(),
    )


@pytest.mark.django_db
def test_elige_avatar_preset_crea_perfil_si_no_existia():
    estudiante_id = uuid.uuid4()

    resultado = _uc().execute(
        CambiarAvatarDTO(preset_clave="ingeniera_red", actor_id=estudiante_id, actor_rol="estudiante")
    )

    assert resultado.avatar_tipo == "preset"
    assert resultado.avatar_valor == "ingeniera_red"
    perfil = PerfilJugadorRepository().get_by_estudiante(estudiante_id)
    assert perfil.avatar_valor == "ingeniera_red"


@pytest.mark.django_db
def test_cambia_avatar_de_un_perfil_existente():
    estudiante_id = uuid.uuid4()
    _uc().execute(CambiarAvatarDTO("operador_nocturno", estudiante_id, "estudiante"))

    _uc().execute(CambiarAvatarDTO("fantasma_red", estudiante_id, "estudiante"))

    perfil = PerfilJugadorRepository().get_by_estudiante(estudiante_id)
    assert perfil.avatar_valor == "fantasma_red"


@pytest.mark.django_db
def test_preset_inexistente_lanza_validation_error():
    with pytest.raises(ValidationError):
        _uc().execute(CambiarAvatarDTO("no_existe", uuid.uuid4(), "estudiante"))


@pytest.mark.django_db
def test_instructor_no_puede_elegir_avatar():
    with pytest.raises(ForbiddenError):
        _uc().execute(CambiarAvatarDTO("operador_nocturno", uuid.uuid4(), "instructor"))
