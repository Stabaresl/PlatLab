import redis
from django.conf import settings


class RedisClient:
    """
    Wrapper sobre redis-py. Usado directamente por `IRefreshTokenRepository`
    (Authentication) para la familia de refresh tokens con TTL, y por
    cualquier otro módulo que necesite cache o almacenamiento efímero.

    Singleton por proceso: reutiliza una sola conexión (redis-py ya maneja
    un connection pool internamente), en vez de abrir una nueva por cada
    instancia de RedisClient.
    """

    _client: redis.Redis | None = None

    def __init__(self, url: str | None = None):
        if RedisClient._client is None:
            RedisClient._client = redis.from_url(
                url or settings.REDIS_URL, decode_responses=True
            )
        self._connection = RedisClient._client

    def get(self, key: str) -> str | None:
        return self._connection.get(key)

    def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        self._connection.set(key, value, ex=ttl_seconds)

    def delete(self, key: str) -> None:
        self._connection.delete(key)

    def exists(self, key: str) -> bool:
        return bool(self._connection.exists(key))

    def expire(self, key: str, ttl_seconds: int) -> None:
        self._connection.expire(key, ttl_seconds)

    @property
    def raw(self) -> redis.Redis:
        """Acceso directo al cliente redis-py para operaciones no cubiertas arriba."""
        return self._connection
