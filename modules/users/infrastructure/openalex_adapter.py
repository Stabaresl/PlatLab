import unicodedata

import requests
from django.conf import settings

from modules.users.domain.verificacion_academica import ResultadoVerificacionAcademica

_TIMEOUT_SECONDS = 10
_BASE_URL = "https://api.openalex.org/authors/orcid:{orcid}"


def _normalizar(nombre: str) -> set[str]:
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", nombre) if unicodedata.category(c) != "Mn"
    )
    return {token for token in sin_tildes.strip().lower().split() if token}


class OpenAlexAdapter:
    """
    Adapter sobre la API pública de OpenAlex (sin autenticación). Se llama
    únicamente desde `celery_tasks.verificar_solicitud_instructor_task` —
    nunca dentro del request/response que crea la solicitud — para que una
    respuesta lenta de OpenAlex nunca bloquee al servidor web.

    Un 404 (ORCID no encontrado) es un resultado de negocio válido, no un
    error: se retorna `encontrado=False` sin lanzar excepción. Cualquier
    otro fallo (timeout, 5xx, problema de red) sí se propaga, para que el
    `autoretry_for` de la tarea Celery reintente con backoff.
    """

    def verificar(self, orcid: str, nombre_declarado: str) -> ResultadoVerificacionAcademica:
        params = {}
        mailto = getattr(settings, "OPENALEX_MAILTO", "")
        if mailto:
            params["mailto"] = mailto

        response = requests.get(
            _BASE_URL.format(orcid=orcid), params=params, timeout=_TIMEOUT_SECONDS
        )
        if response.status_code == 404:
            return ResultadoVerificacionAcademica(
                encontrado=False, coincide_nombre=False, works_count=0, nombre_openalex=None
            )
        response.raise_for_status()

        data = response.json()
        nombre_openalex = data.get("display_name") or ""
        works_count = int(data.get("works_count") or 0)
        coincide = bool(nombre_openalex) and _normalizar(nombre_openalex) == _normalizar(
            nombre_declarado
        )

        return ResultadoVerificacionAcademica(
            encontrado=True,
            coincide_nombre=coincide,
            works_count=works_count,
            nombre_openalex=nombre_openalex,
        )
