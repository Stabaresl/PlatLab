from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_default_exception_handler

from modules.shared.domain.exceptions import DomainError

_STATUS_BY_CODE = {
    "VALIDATION_ERROR": 400,
    "UNAUTHENTICATED": 401,
    "FORBIDDEN": 403,
    "NOT_FOUND": 404,
    "CONFLICT": 409,
    "BUSINESS_RULE_VIOLATION": 422,
    "RATE_LIMITED": 429,
    "INTERNAL_ERROR": 500,
}


def custom_exception_handler(exc, context):
    """
    Reemplaza el exception handler por defecto de DRF (ver
    REST_FRAMEWORK.EXCEPTION_HANDLER en settings). Traduce:

    - Excepciones de dominio (`modules.shared.domain.exceptions.DomainError`
      y subclases) al formato estándar de api.md §2.
    - `ValidationError` propio de DRF (el que lanza `serializer.is_valid
      (raise_exception=True)`) al mismo formato, para que el frontend nunca
      tenga que distinguir "¿esto vino de un serializer o de un caso de
      uso?" — la forma de la respuesta es siempre la misma.
    - Cualquier otra excepción (404 de Django, permisos de DRF, etc.) se
      delega al handler por defecto de DRF, sin tocarla.
    """
    if isinstance(exc, DomainError):
        status_code = _STATUS_BY_CODE.get(exc.code, 500)
        return Response(
            {"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
            status=status_code,
        )

    if isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
        return Response(
            {
                "error": {
                    "code": "UNAUTHENTICATED",
                    "message": str(exc.detail) if hasattr(exc, "detail") else str(exc),
                    "details": [],
                }
            },
            status=401,
        )

    if isinstance(exc, DRFValidationError):
        return Response(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "La solicitud contiene datos inválidos.",
                    "details": _flatten_drf_errors(exc.detail),
                }
            },
            status=400,
        )

    return drf_default_exception_handler(exc, context)


def _flatten_drf_errors(detail) -> list[dict]:
    if isinstance(detail, dict):
        return [
            {"field": field, "message": str(msg)}
            for field, msgs in detail.items()
            for msg in (msgs if isinstance(msgs, list) else [msgs])
        ]
    if isinstance(detail, list):
        return [{"field": "non_field_errors", "message": str(msg)} for msg in detail]
    return [{"field": "non_field_errors", "message": str(detail)}]
