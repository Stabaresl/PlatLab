import uuid

from modules.shared.domain.exceptions import RateLimitedError
from modules.shared.infrastructure.redis_client import RedisClient

_VENTANA_SEGUNDOS = 60
_LIMITE_INTENTOS = 20
_MENSAJE = "Demasiados intentos. Intenta de nuevo en un minuto."


class FlagRateLimiter:
    """
    seguridad.md §5 / api.md §12: 20 intentos/minuto por usuario+sección
    sobre `POST /progress/{assignment_id}/sections/{section_id}/flag/`
    (UC-02 E1, previene scripting/fuerza bruta). Ventana fija de 60s por
    clave `estudiante_id:seccion_id` en Redis — suficiente para el
    límite pedido, sin necesidad de un sliding window.
    """

    def __init__(self, redis_client: RedisClient | None = None):
        self._redis = redis_client or RedisClient()

    def verificar(self, estudiante_id: uuid.UUID, seccion_id: uuid.UUID) -> None:
        clave = f"flag_rate:{estudiante_id}:{seccion_id}"
        conteo = self._redis.raw.incr(clave)
        if conteo == 1:
            self._redis.raw.expire(clave, _VENTANA_SEGUNDOS)
        if conteo > _LIMITE_INTENTOS:
            raise RateLimitedError(_MENSAJE)
