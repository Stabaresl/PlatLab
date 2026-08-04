import io
import uuid

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from PIL import Image

from modules.shared.domain.exceptions import ValidationError

_LIMITE_TAMANO_KB = 2 * 1024  # 2 MB — de sobra para una foto de perfil
_MAX_DIMENSION_PX = 512  # el badge del avatar es chico; nadie necesita servir la foto a resolución original
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


def _redimensionar(contenido: bytes, mime: str) -> bytes:
    """
    Nadie sirve la foto que alguien suba a su resolución original — el
    badge del avatar es chico. Achica al lado más largo <= 512px
    preservando proporción. GIF animado se aplana al primer frame (caso
    raro para una foto de perfil, no vale la pena manejar animación acá).
    """
    try:
        imagen = Image.open(io.BytesIO(contenido))
        imagen.thumbnail((_MAX_DIMENSION_PX, _MAX_DIMENSION_PX))
        buffer = io.BytesIO()
        if mime == "image/jpeg":
            if imagen.mode != "RGB":
                imagen = imagen.convert("RGB")
            imagen.save(buffer, format="JPEG", quality=85, optimize=True)
        elif mime == "image/png":
            imagen.save(buffer, format="PNG", optimize=True)
        else:
            imagen.save(buffer, format="GIF")
        return buffer.getvalue()
    except Exception as exc:  # noqa: BLE001 - cualquier falla de decodificación es "no es una imagen válida"
        raise ValidationError(_TIPO_NO_PERMITIDO_MSG) from exc


def verificar_tamano_declarado(size_bytes: int) -> None:
    """
    Chequea el tamaño que ya declaró el cliente (`UploadedFile.size`, sale
    de la parte multipart, no hace falta leer nada) ANTES de llamar
    `.read()` en la vista — evita bufferizar en memoria un archivo que ya
    se sabe que va a ser rechazado. `guardar_avatar` mantiene su propio
    chequeo como fuente de verdad una vez leído.
    """
    if size_bytes // 1024 > _LIMITE_TAMANO_KB:
        raise ValidationError(_TAMANO_EXCEDIDO_MSG)


def guardar_avatar(nombre_archivo: str, contenido: bytes) -> tuple[str, int]:
    """Valida y guarda una imagen de avatar subida por el estudiante. Devuelve `(archivo_url, tamano_kb)`."""
    tamano_kb = len(contenido) // 1024
    if tamano_kb > _LIMITE_TAMANO_KB:
        raise ValidationError(_TAMANO_EXCEDIDO_MSG)

    mime = _detectar_mime(contenido)
    contenido = _redimensionar(contenido, mime)

    ruta = f"gamification/avatares/{uuid.uuid4()}_{nombre_archivo}"
    archivo_guardado = default_storage.save(ruta, ContentFile(contenido))
    return default_storage.url(archivo_guardado), len(contenido) // 1024
