import json
import secrets
import uuid

from modules.shared.infrastructure.redis_client import RedisClient

_TEN_MINUTES_SECONDS = 10 * 60


class OAuthLinkStore:
    """
    Token de un solo uso para confirmar la vinculación de un
    `ProveedorAutenticacion` pendiente a un `User` existente (UC-01 E4,
    `VinculadorDeCuenta`) — mismo criterio que `PasswordResetTokenStore`
    (10 minutos de vida, consumo único).
    """

    def __init__(
        self,
        redis_client: RedisClient | None = None,
        ttl_seconds: int = _TEN_MINUTES_SECONDS,
    ):
        self._redis = redis_client or RedisClient()
        self._ttl = ttl_seconds

    def create_token(self, user_id: uuid.UUID, proveedor: str, proveedor_uid: str) -> str:
        token = secrets.token_urlsafe(32)
        payload = json.dumps(
            {"user_id": str(user_id), "proveedor": proveedor, "proveedor_uid": proveedor_uid}
        )
        self._redis.set(f"oauth_link:{token}", payload, ttl_seconds=self._ttl)
        return token

    def consume_token(self, token: str) -> dict | None:
        raw = self._redis.get(f"oauth_link:{token}")
        if raw is None:
            return None
        self._redis.delete(f"oauth_link:{token}")
        data = json.loads(raw)
        data["user_id"] = uuid.UUID(data["user_id"])
        return data
