"""
Autenticación JWT para conexiones WebSocket (Channels no tiene acceso al
header `Authorization` del navegador para WS — el token viaja como query
param `?token=...`, único mecanismo estándar disponible desde el cliente
WebSocket nativo). Reutiliza `JWTService`, mismo servicio que
`JWTAuthentication` (DRF) usa para HTTP — un solo lugar que sabe decodificar
tokens.
"""

import uuid
from urllib.parse import parse_qs

from modules.authentication.infrastructure.authentication import AuthenticatedUser
from modules.authentication.infrastructure.jwt_service import JWTService
from modules.shared.domain.exceptions import UnauthenticatedError


class JWTAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        scope["user"] = None
        query_string = scope.get("query_string", b"").decode()
        token = parse_qs(query_string).get("token", [None])[0]

        if token:
            try:
                claims = JWTService().decode_access_token(token)
                scope["user"] = AuthenticatedUser(id=uuid.UUID(claims["sub"]), rol=claims["rol"])
            except (UnauthenticatedError, ValueError, KeyError):
                scope["user"] = None

        return await self.app(scope, receive, send)
