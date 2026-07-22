import uuid

from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication

from modules.authentication.infrastructure.jwt_service import JWTService
from modules.shared.domain.exceptions import UnauthenticatedError


class AuthenticatedUser:
    """
    Representación mínima del usuario autenticado, construida directamente
    desde los claims del JWT — no se consulta la base de datos en cada
    request (esa es justamente la ventaja de JWT sobre sesiones). No es un
    modelo de Django ni de `django.contrib.auth`; el proyecto no usa ese
    sistema de autenticación para su lógica de negocio.
    """

    def __init__(self, id: uuid.UUID, rol: str):
        self.id = id
        self.rol = rol
        self.is_authenticated = True

    def __str__(self) -> str:
        return f"AuthenticatedUser(id={self.id}, rol={self.rol})"


class JWTAuthentication(BaseAuthentication):
    """
    Valida el header `Authorization: Bearer <access_token>` y resuelve
    `request.user` + `request.auth` antes de que la request llegue al
    controlador (backend.md §10). Registrada globalmente en
    `REST_FRAMEWORK.DEFAULT_AUTHENTICATION_CLASSES` — aplica a toda
    request salvo las rutas con `permission_classes = [AllowAny]`
    explícito (api.md: "Público").

    Si no hay header `Authorization`, devuelve `None` (sin credenciales;
    DRF trata la request como anónima — el `permission_classes` de la
    vista decide si eso es aceptable). Si el header existe pero el token
    es inválido/expirado, lanza `AuthenticationFailed` (401) explícito —
    un token roto nunca debe tratarse silenciosamente como "anónimo".
    """

    keyword = "Bearer"

    def authenticate(self, request):
        header = request.headers.get("Authorization")
        if not header:
            return None

        parts = header.split()
        if len(parts) != 2 or parts[0] != self.keyword:
            return None

        token = parts[1]
        try:
            claims = JWTService().decode_access_token(token)
        except UnauthenticatedError as exc:
            raise exceptions.AuthenticationFailed(exc.message) from exc

        user = AuthenticatedUser(id=uuid.UUID(claims["sub"]), rol=claims["rol"])
        return (user, token)

    def authenticate_header(self, request):
        return self.keyword
