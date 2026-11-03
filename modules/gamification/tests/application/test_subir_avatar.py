import io
import uuid

import pytest
from PIL import Image

from modules.gamification.application.dtos import SubirAvatarDTO
from modules.gamification.application.use_cases.subir_avatar import SubirAvatarUseCase
from modules.gamification.infrastructure.repositories import PerfilJugadorRepository
from modules.shared.domain.exceptions import ForbiddenError, ValidationError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


def _png_valido() -> bytes:
    """
    avatar_storage.py ahora decodifica la imagen de verdad para
    redimensionarla (ver _redimensionar) — a diferencia del resto de la
    suite, acá no alcanza con las firmas mágicas solas.
    """
    buffer = io.BytesIO()
    Image.new("RGB", (20, 20), color="red").save(buffer, format="PNG")
    return buffer.getvalue()


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
            archivo_contenido=_png_valido(),
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


def _imagen(formato: str, tamano: tuple[int, int], **kwargs) -> bytes:
    buffer = io.BytesIO()
    Image.effect_noise(tamano, 80).convert("RGB").save(buffer, format=formato, **kwargs)
    return buffer.getvalue()


@pytest.mark.django_db
def test_acepta_foto_de_celular_grande_y_la_reduce_a_512px():
    """Regresión: el límite era 2 MB y rechazaba casi cualquier foto tomada con el teléfono."""
    from django.core.files.storage import default_storage

    foto = _imagen("JPEG", (3000, 2400), quality=95)
    assert len(foto) > 2 * 1024 * 1024

    resultado = _uc().execute(
        SubirAvatarDTO(
            archivo_nombre="IMG_20261103 foto ñ.jpg",
            archivo_contenido=foto,
            actor_id=uuid.uuid4(),
            actor_rol="estudiante",
        )
    )

    ruta = resultado.avatar_valor.removeprefix("/media/")
    assert ruta.endswith(".jpg") and " " not in ruta and "ñ" not in ruta
    with default_storage.open(ruta) as guardado:
        assert max(Image.open(guardado).size) <= 512


@pytest.mark.django_db
def test_acepta_webp():
    resultado = _uc().execute(
        SubirAvatarDTO(
            archivo_nombre="avatar.webp",
            archivo_contenido=_imagen("WEBP", (300, 300)),
            actor_id=uuid.uuid4(),
            actor_rol="estudiante",
        )
    )

    assert resultado.avatar_valor.endswith(".webp")


@pytest.mark.django_db
def test_rechaza_imagen_que_supera_los_10_mb():
    with pytest.raises(ValidationError):
        _uc().execute(
            SubirAvatarDTO(
                archivo_nombre="enorme.png",
                archivo_contenido=b"\x89PNG\r\n\x1a\n" + b"\x00" * (11 * 1024 * 1024),
                actor_id=uuid.uuid4(),
                actor_rol="estudiante",
            )
        )
