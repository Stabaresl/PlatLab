import uuid

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from modules.shared.domain.exceptions import ValidationError

_LIMITE_TAMANO_KB = 5 * 1024  # 5 MB
_FIRMAS_PERMITIDAS: dict[bytes, str] = {
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
    b"%PDF-": "application/pdf",
}
_TAMANO_EXCEDIDO_MSG = f"El archivo supera el límite de {_LIMITE_TAMANO_KB} KB."
_TIPO_NO_PERMITIDO_MSG = "Tipo de archivo no permitido."


def _detectar_mime(contenido: bytes) -> str:
    """
    seguridad.md §4: valida el tipo MIME real por firma binaria (magic
    bytes) — nunca por la extensión del nombre de archivo ni por el
    `Content-Type` que reporta el cliente (falsificable).
    """
    for firma, mime in _FIRMAS_PERMITIDAS.items():
        if contenido.startswith(firma):
            return mime
    raise ValidationError(_TIPO_NO_PERMITIDO_MSG)


def guardar_adjunto(nombre_archivo: str, contenido: bytes) -> tuple[str, int]:
    """
    HE-12/HA-05: valida el adjunto de un reporte (MIME real + límite de
    tamaño) y lo guarda fuera del webroot (`MEDIA_ROOT` en dev;
    S3/MinIO con `Content-Disposition: attachment` en producción,
    RNF-08.1). Devuelve `(archivo_url, tamano_kb)`.
    """
    tamano_kb = len(contenido) // 1024
    if tamano_kb > _LIMITE_TAMANO_KB:
        raise ValidationError(_TAMANO_EXCEDIDO_MSG)

    _detectar_mime(contenido)

    ruta = f"reports/adjuntos/{uuid.uuid4()}_{nombre_archivo}"
    archivo_guardado = default_storage.save(ruta, ContentFile(contenido))
    return default_storage.url(archivo_guardado), tamano_kb
