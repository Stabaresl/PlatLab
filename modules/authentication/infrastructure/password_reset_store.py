import secrets
import uuid

from modules.shared.infrastructure.redis_client import RedisClient

_FIFTEEN_MINUTES_SECONDS = 15 * 60


class PasswordResetTokenStore:
    """
    Token de recuperación de contraseña de un solo uso, guardado en Redis
    con expiración de 15 minutos (UC-01, flujo A3, paso 2c).

    NOTA: si en el futuro se construye el listener de auditoría para
    eventos de Authentication, el token en sí (`PasswordResetRequested.
    token`) NUNCA debe quedar guardado en el log de auditoría — solo sirve
    para el envío del correo, no es información que deba persistirse.
    """

    def __init__(
        self,
        redis_client: RedisClient | None = None,
        ttl_seconds: int = _FIFTEEN_MINUTES_SECONDS,
    ):
        self._redis = redis_client or RedisClient()
        self._ttl = ttl_seconds

    def create_token(self, user_id: uuid.UUID) -> str:
        token = secrets.token_urlsafe(32)
        self._redis.set(f"pwd_reset:{token}", str(user_id), ttl_seconds=self._ttl)
        return token

    def peek_token(self, token: str) -> uuid.UUID | None:
        """Consulta a qué usuario pertenece el token, sin consumirlo."""
        value = self._redis.get(f"pwd_reset:{token}")
        return uuid.UUID(value) if value else None

    def consume_token(self, token: str) -> uuid.UUID | None:
        """Consulta y elimina el token (un solo uso, UC-01 A3 paso 3c)."""
        value = self._redis.get(f"pwd_reset:{token}")
        if value is None:
            return None
        self._redis.delete(f"pwd_reset:{token}")
        return uuid.UUID(value)
