import uuid

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from modules.shared.domain.exceptions import ValidationError

_LIMITE_TAMANO_KB = 3 * 1024  # 3 MB — Dockerfile suelto o .zip de contexto de build
_TAMANO_EXCEDIDO_MSG = f"El archivo supera el límite de {_LIMITE_TAMANO_KB} KB."


def guardar_dockerfile(nombre_archivo: str, contenido: bytes) -> tuple[str, int]:
    """
    Guarda el Dockerfile/contexto de build que sube un instructor para el
    entorno real de una sección — a diferencia de `reports.guardar_adjunto`,
    no hay una firma binaria confiable para validar "es un Dockerfile
    legítimo" (puede ser texto plano o un .zip), así que solo se valida el
    tamaño. Nunca se ejecuta ni se construye nada con este archivo
    automáticamente: un admin lo revisa manualmente antes de decidir si
    hace `docker build` fuera de la app (seguridad.md — DooD ya expone el
    host vía `/var/run/docker.sock`, un build automático de contenido no
    confiable sería una vía directa de compromiso).
    """
    tamano_kb = len(contenido) // 1024
    if tamano_kb > _LIMITE_TAMANO_KB:
        raise ValidationError(_TAMANO_EXCEDIDO_MSG)

    ruta = f"laboratories/dockerfiles/{uuid.uuid4()}_{nombre_archivo}"
    archivo_guardado = default_storage.save(ruta, ContentFile(contenido))
    return default_storage.url(archivo_guardado), tamano_kb
