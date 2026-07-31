import uuid

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from modules.shared.domain.exceptions import ValidationError

_LIMITE_TAMANO_KB = 2 * 1024  # 2 MB — de sobra para una foto de perfil
_FIRMAS_PERMITIDAS: dict[bytes, str] = {
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
}
_TAMANO_EXCEDIDO_MSG = f"La imagen supera el límite de {_LIMITE_TAMANO_KB} KB."
_TIPO_NO_PERMITIDO_MSG = "Solo se permiten imágenes PNG, JPEG o GIF."


def _detectar_mime(contenido: bytes) -> str:
    """Mismo criterio que `reports/infrastructure/storage_adapter.py::_detectar_mime` — MIME real por magic bytes, nunca por extensión/Content-Type del cliente."""
    for firma, mime in _FIRMAS_PERMITIDAS.items():
        if contenido.startswith(firma):
            return mime
    raise ValidationError(_TIPO_NO_PERMITIDO_MSG)


def guardar_avatar(nombre_archivo: str, contenido: bytes) -> tuple[str, int]:
    """Valida y guarda una imagen de avatar subida por el estudiante. Devuelve `(archivo_url, tamano_kb)`."""
    tamano_kb = len(contenido) // 1024
    if tamano_kb > _LIMITE_TAMANO_KB:
        raise ValidationError(_TAMANO_EXCEDIDO_MSG)

    _detectar_mime(contenido)

    ruta = f"gamification/avatares/{uuid.uuid4()}_{nombre_archivo}"
    archivo_guardado = default_storage.save(ruta, ContentFile(contenido))
    return default_storage.url(archivo_guardado), tamano_kb
