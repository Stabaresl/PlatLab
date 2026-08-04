import base64
import pickle
from typing import Callable, TypeVar

from modules.shared.infrastructure.redis_client import RedisClient

T = TypeVar("T")


def cachear(
    clave: str,
    calcular: Callable[[], T],
    ttl_seconds: int = 300,
    redis_client: RedisClient | None = None,
) -> T:
    """
    Cache de lectura genérico para datos casi-estáticos (catálogo de
    gamificación: logros/cosméticos/títulos) — a diferencia de
    `CachedLaboratorioRepository` (que sí necesita invalidar al toque
    porque cambia por acción de usuarios: publicar/aprobar/cambiar
    visibilidad), este contenido solo cambia por `seed_gamification_
    catalog` — un TTL corto alcanza, sin necesidad de un esquema de
    invalidación por versión.

    Serializa con `pickle` + base64 (`RedisClient` decodifica todo como
    texto — `decode_responses=True` — y el binario crudo de pickle no
    siempre es UTF-8 válido). La clave nunca sale de Redis (privado, sin
    acceso externo), no hay superficie de deserialización insegura acá —
    evita escribir un to-dict/from-dict a mano por cada entidad.
    """
    redis = redis_client or RedisClient()
    cacheado = redis.get(clave)
    if cacheado is not None:
        return pickle.loads(base64.b64decode(cacheado))

    valor = calcular()
    redis.set(clave, base64.b64encode(pickle.dumps(valor)).decode("ascii"), ttl_seconds=ttl_seconds)
    return valor
