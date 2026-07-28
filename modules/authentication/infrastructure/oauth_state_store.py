import json

from modules.shared.infrastructure.redis_client import RedisClient

_TEN_MINUTES_SECONDS = 10 * 60


class OAuthStateStore:
    """
    Guarda el `state` (CSRF) y el `code_verifier` (PKCE) de un intento de
    login OAuth en curso — 10 minutos de vida, un solo uso. Cumple
    seguridad.md §3: "El backend valida el state recibido contra el
    emitido, para prevenir CSRF sobre el flujo de OAuth".
    """

    def __init__(
        self,
        redis_client: RedisClient | None = None,
        ttl_seconds: int = _TEN_MINUTES_SECONDS,
    ):
        self._redis = redis_client or RedisClient()
        self._ttl = ttl_seconds

    def save(self, state: str, code_verifier: str, proveedor: str) -> None:
        payload = json.dumps({"code_verifier": code_verifier, "proveedor": proveedor})
        self._redis.set(f"oauth_state:{state}", payload, ttl_seconds=self._ttl)

    def consume(self, state: str) -> dict | None:
        """Valida y consume el state (un solo uso, evita replay del callback)."""
        raw = self._redis.get(f"oauth_state:{state}")
        if raw is None:
            return None
        self._redis.delete(f"oauth_state:{state}")
        return json.loads(raw)
