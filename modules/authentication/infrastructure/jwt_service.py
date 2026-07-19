import uuid

from django.conf import settings
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from modules.authentication.application.dtos import TokenPairDTO
from modules.shared.domain.exceptions import UnauthenticatedError


class JWTService:
    """
    Wrapper sobre `djangorestframework-simplejwt`. Genera el par de tokens
    (access + refresh) con los claims mínimos requeridos (seguridad.md §2:
    `sub`, `rol`, `exp`, `jti`) y valida tokens recibidos, traduciendo
    cualquier error de SimpleJWT a `UnauthenticatedError` (dominio) — el
    resto del sistema nunca importa `rest_framework_simplejwt` directamente,
    solo este servicio.

    No depende de un modelo `User` de Django (el proyecto no usa
    `django.contrib.auth` para su lógica de negocio) — los claims se
    setean manualmente sobre un token "anónimo" en vez de usar
    `RefreshToken.for_user(...)`.
    """

    def generate_token_pair(self, user_id: uuid.UUID, rol: str) -> TokenPairDTO:
        refresh = RefreshToken()
        refresh["sub"] = str(user_id)
        refresh["rol"] = rol

        access = refresh.access_token
        access["sub"] = str(user_id)
        access["rol"] = rol

        return TokenPairDTO(
            access=str(access),
            refresh=str(refresh),
            expires_in=int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()),
            rol=rol,
        )

    def decode_access_token(self, token: str) -> dict:
        try:
            validated = AccessToken(token)
        except TokenError as exc:
            raise UnauthenticatedError("Token de acceso inválido o expirado.") from exc
        return dict(validated.payload)

    def decode_refresh_token(self, token: str) -> dict:
        try:
            validated = RefreshToken(token)
        except TokenError as exc:
            raise UnauthenticatedError("Refresh token inválido o expirado.") from exc
        return dict(validated.payload)
