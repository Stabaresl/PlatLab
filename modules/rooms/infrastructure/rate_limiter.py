import uuid

from modules.shared.domain.exceptions import RateLimitedError
from modules.shared.infrastructure.redis_client import RedisClient

_VENTANA_SEGUNDOS = 60
_LIMITE = 15
_MENSAJE = "Demasiados intentos con códigos de sala. Espera un minuto e inténtalo de nuevo."


class CodigoSalaRateLimiter:
    """
    Unirse y previsualizar por código: 15 por minuto por usuario. Los códigos
    son de 6 caracteres; sin límite se podrían probar en bucle hasta dar con
    una sala ajena.
    """

    def __init__(self, redis_client: RedisClient | None = None):
        self._redis = redis_client or RedisClient()

    def verificar(self, usuario_id: uuid.UUID) -> None:
        clave = f"sala_codigo_rate:{usuario_id}"
        conteo = self._redis.raw.incr(clave)
        if conteo == 1:
            self._redis.raw.expire(clave, _VENTANA_SEGUNDOS)
        if conteo > _LIMITE:
            raise RateLimitedError(_MENSAJE)
