import uuid

from modules.authentication.domain.exceptions import (
    InvalidCredentialsError,
    TokenReuseDetectedError,
)
from modules.shared.infrastructure.redis_client import RedisClient

_SEVEN_DAYS_SECONDS = 7 * 24 * 60 * 60


class RefreshTokenStore:
    """
    Guarda en Redis la "familia" de refresh tokens de cada sesión
    (seguridad.md §2), con TTL igual a la expiración del refresh (7 días).

    Modelo: cada login crea una `family_id` nueva. Dentro de una familia,
    solo un `jti` (identificador del token) es válido para refrescar en un
    momento dado — al rotar, el anterior deja de ser válido. Si alguien
    presenta un `jti` que ya fue rotado (robado y reusado, o replay), se
    detecta el reuso y se revoca **toda la familia** de inmediato: tanto el
    token robado como el legítimo dejan de servir, forzando un nuevo login.

    Claves en Redis:
    - `refresh:family:{family_id}`      -> jti actualmente válido
    - `refresh:jti:{jti}`               -> family_id al que pertenece
    - `refresh:family_user:{family_id}` -> user_id dueño de la familia
    - `refresh:user:{user_id}`          -> set de family_ids activas del usuario
      (usado por LogoutAllUseCase para revocar todas las sesiones a la vez)
    """

    def __init__(
        self,
        redis_client: RedisClient | None = None,
        ttl_seconds: int = _SEVEN_DAYS_SECONDS,
    ):
        self._redis = redis_client or RedisClient()
        self._ttl = ttl_seconds

    def register_family(self, user_id: uuid.UUID, jti: str) -> str:
        """Crea una nueva familia al hacer login. Devuelve el family_id."""
        family_id = str(uuid.uuid4())

        self._redis.set(f"refresh:family:{family_id}", jti, ttl_seconds=self._ttl)
        self._redis.set(f"refresh:jti:{jti}", family_id, ttl_seconds=self._ttl)
        self._redis.set(f"refresh:family_user:{family_id}", str(user_id), ttl_seconds=self._ttl)

        user_key = f"refresh:user:{user_id}"
        self._redis.raw.sadd(user_key, family_id)
        self._redis.raw.expire(user_key, self._ttl)

        return family_id

    def validate_and_rotate(self, jti: str, new_jti: str) -> str:
        """
        Valida que `jti` sea el token vigente de su familia y lo rota a
        `new_jti`. Devuelve el `family_id`.

        Lanza `InvalidCredentialsError` si el token no se reconoce (nunca
        existió o ya expiró), y `TokenReuseDetectedError` si se reconoce
        pero ya no es el vigente (fue rotado antes) — en ese caso revoca la
        familia completa antes de lanzar la excepción.
        """
        family_id = self._redis.get(f"refresh:jti:{jti}")
        if family_id is None:
            raise InvalidCredentialsError("Refresh token no reconocido o expirado.")

        current_jti = self._redis.get(f"refresh:family:{family_id}")
        if current_jti != jti:
            self.revoke_family(family_id)
            raise TokenReuseDetectedError(
                "Se detectó reutilización de un refresh token; la sesión fue revocada."
            )

        self._redis.set(f"refresh:family:{family_id}", new_jti, ttl_seconds=self._ttl)
        self._redis.set(f"refresh:jti:{new_jti}", family_id, ttl_seconds=self._ttl)
        self._redis.delete(f"refresh:jti:{jti}")

        return family_id

    def revoke_family(self, family_id: str) -> None:
        current_jti = self._redis.get(f"refresh:family:{family_id}")
        family_user = self._redis.get(f"refresh:family_user:{family_id}")

        if current_jti:
            self._redis.delete(f"refresh:jti:{current_jti}")
        self._redis.delete(f"refresh:family:{family_id}")
        self._redis.delete(f"refresh:family_user:{family_id}")

        if family_user:
            self._redis.raw.srem(f"refresh:user:{family_user}", family_id)

    def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        """Usado por LogoutAllUseCase (HE-14): invalida todas las sesiones del usuario."""
        user_key = f"refresh:user:{user_id}"
        family_ids = self._redis.raw.smembers(user_key)

        for family_id in family_ids:
            self.revoke_family(family_id)

        self._redis.delete(user_key)
