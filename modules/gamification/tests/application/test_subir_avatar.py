import uuid

import pytest

from modules.gamification.application.dtos import SubirAvatarDTO
from modules.gamification.application.use_cases.subir_avatar import SubirAvatarUseCase
from modules.gamification.infrastructure.repositories import PerfilJugadorRepository
from modules.shared.domain.exceptions import ForbiddenError, ValidationError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork

_PNG_MAGIC_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


def _uc():
    return SubirAvatarUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        perfil_repository=PerfilJugadorRepository(),
    )


@pytest.mark.django_db
def test_sube_avatar_valido_y_actualiza_perfil():
    estudiante_id = uuid.uuid4()

    resultado = _uc().execute(
        SubirAvatarDTO(
            archivo_nombre="foto.png",
            archivo_contenido=_PNG_MAGIC_BYTES,
            actor_id=estudiante_id,
            actor_rol="estudiante",
        )
    )

    assert resultado.avatar_tipo == "subido"
    assert resultado.avatar_valor.startswith("/media/gamification/avatares/")
    perfil = PerfilJugadorRepository().get_by_estudiante(estudiante_id)
    assert perfil.avatar_valor == resultado.avatar_valor


@pytest.mark.django_db
def test_archivo_que_no_es_imagen_lanza_validation_error():
    with pytest.raises(ValidationError):
        _uc().execute(
            SubirAvatarDTO(
                archivo_nombre="malware.exe",
                archivo_contenido=b"MZ\x90\x00" + b"\x00" * 50,
                actor_id=uuid.uuid4(),
                actor_rol="estudiante",
            )
        )


@pytest.mark.django_db
def test_archivo_demasiado_grande_lanza_validation_error():
    contenido = b"\x89PNG\r\n\x1a\n" + b"\x00" * (3 * 1024 * 1024)
    with pytest.raises(ValidationError):
        _uc().execute(
            SubirAvatarDTO(
                archivo_nombre="grande.png",
                archivo_contenido=contenido,
                actor_id=uuid.uuid4(),
                actor_rol="estudiante",
            )
        )


@pytest.mark.django_db
def test_admin_no_puede_subir_avatar():
    with pytest.raises(ForbiddenError):
        _uc().execute(
            SubirAvatarDTO(
                archivo_nombre="foto.png",
                archivo_contenido=_PNG_MAGIC_BYTES,
                actor_id=uuid.uuid4(),
                actor_rol="administrador",
            )
        )
