import io
import uuid

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from PIL import Image, ImageOps

from modules.shared.domain.exceptions import ValidationError

# 10 MB: una foto de celular típica pesa 3-12 MB. Antes el límite era 2 MB
# y rechazaba casi cualquier foto tomada con el teléfono — da igual el peso
# original, la imagen se reduce a 512 px y se re-codifica antes de guardar.
_LIMITE_TAMANO_KB = 10 * 1024
_MAX_DIMENSION_PX = 512  # el badge del avatar es chico; nadie necesita servir la foto a resolución original
# Tope de píxeles antes de decodificar: una "imagen-bomba" de pocos KB que
# se expande a gigapíxeles agotaría la RAM del servidor (Pillow solo avisa
# por encima de ~89 MP). 40 MP cubre cualquier cámara de celular actual.
_MAX_PIXELES = 40_000_000
_FIRMAS_PERMITIDAS: dict[bytes, str] = {
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
}
# WebP: contenedor RIFF con "WEBP" en el byte 8 — no entra en el chequeo de
# prefijo simple de arriba.
_EXTENSION_POR_FORMATO = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}
_TAMANO_EXCEDIDO_MSG = f"La imagen supera el límite de {_LIMITE_TAMANO_KB // 1024} MB."
_TIPO_NO_PERMITIDO_MSG = "Solo se permiten imágenes PNG, JPEG, WebP o GIF."


def _detectar_mime(contenido: bytes) -> str:
    """
    Mismo criterio que `reports/infrastructure/storage_adapter.py::_detectar_mime`:
    MIME real por magic bytes, nunca por extensión/Content-Type del cliente.
    """
    if contenido[:4] == b"RIFF" and contenido[8:12] == b"WEBP":
        return "image/webp"
    for firma, mime in _FIRMAS_PERMITIDAS.items():
        if contenido.startswith(firma):
            return mime
    raise ValidationError(_TIPO_NO_PERMITIDO_MSG)


def _redimensionar(contenido: bytes, mime: str) -> tuple[bytes, str]:
    """
    Nadie sirve la foto que alguien suba a su resolución original — el
    badge del avatar es chico. Achica al lado más largo <= 512px
    preservando proporción y devuelve `(bytes, extensión)`.

    - Aplica la rotación EXIF (las fotos verticales del celular llegan
      "acostadas" con una etiqueta de orientación; sin esto se veían
      giradas).
    - Re-codificar descarta los metadatos EXIF (incluida la ubicación GPS
      de la foto) — no se publica dónde se tomó.
    - GIF se aplana al primer frame y se guarda como PNG.
    """
    try:
        imagen = Image.open(io.BytesIO(contenido))
        ancho, alto = imagen.size
        if ancho * alto > _MAX_PIXELES:
            raise ValidationError("La imagen tiene demasiada resolución.")
        imagen = ImageOps.exif_transpose(imagen)
        imagen.thumbnail((_MAX_DIMENSION_PX, _MAX_DIMENSION_PX))
        buffer = io.BytesIO()
        if mime == "image/jpeg":
            if imagen.mode != "RGB":
                imagen = imagen.convert("RGB")
            imagen.save(buffer, format="JPEG", quality=85, optimize=True)
            formato = "JPEG"
        elif mime == "image/webp":
            imagen.save(buffer, format="WEBP", quality=85)
            formato = "WEBP"
        else:
            if imagen.mode not in ("RGB", "RGBA", "L", "LA"):
                imagen = imagen.convert("RGBA")
            imagen.save(buffer, format="PNG", optimize=True)
            formato = "PNG"
        return buffer.getvalue(), _EXTENSION_POR_FORMATO[formato]
    except ValidationError:
        raise
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
    contenido, extension = _redimensionar(contenido, mime)

    # Nombre generado, nunca el del cliente: el original podía traer
    # espacios/acentos (URLs con %20/%C3%B1) o intentos de path traversal.
    ruta = f"gamification/avatares/{uuid.uuid4().hex}.{extension}"
    archivo_guardado = default_storage.save(ruta, ContentFile(contenido))
    return default_storage.url(archivo_guardado), len(contenido) // 1024
