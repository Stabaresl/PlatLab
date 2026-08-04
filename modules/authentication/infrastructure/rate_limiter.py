from modules.shared.domain.exceptions import RateLimitedError
from modules.shared.infrastructure.redis_client import RedisClient

_VENTANA_SEGUNDOS = 60
_LIMITE_INTENTOS = 10
_MENSAJE = "Demasiados intentos. Intenta de nuevo en un minuto."


class AuthRateLimiter:
    """
    Mismo patrón que FlagRateLimiter (modules/progress/infrastructure), pero
    llaveado por IP en vez de estudiante_id: login/registro/reset/refresh
    son AllowAny — todavía no hay usuario autenticado con el que limitar.
    Ventana fija de 60s por clave `auth_rate:{accion}:{ip}` en Redis, una
    acción no consume el cupo de otra (un intento de registro fallido no
    debería bloquear el login de alguien más desde la misma red).
    """

    def __init__(self, redis_client: RedisClient | None = None):
        self._redis = redis_client or RedisClient()

    def verificar(self, accion: str, ip: str) -> None:
        clave = f"auth_rate:{accion}:{ip}"
        conteo = self._redis.raw.incr(clave)
        if conteo == 1:
            self._redis.raw.expire(clave, _VENTANA_SEGUNDOS)
        if conteo > _LIMITE_INTENTOS:
            raise RateLimitedError(_MENSAJE)
