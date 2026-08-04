import pytest

from modules.shared.infrastructure.redis_client import RedisClient


@pytest.fixture(autouse=True)
def _limpia_cache_catalogo_gamificacion():
    """
    LogroRepository/CosmeticoRepository/TituloRepository.find_todos()
    ahora cachean en Redis (ver simple_cache.py) — sin este flush, un
    test que crea un logro/cosmético/título directo por repositorio y
    después consulta find_todos() (u otra query que dependa de él) se
    pisaría con lo que haya quedado cacheado de un test anterior.
    """
    redis = RedisClient().raw
    for clave in ("gamification:logros", "gamification:cosmeticos", "gamification:titulos"):
        redis.delete(clave)
    yield
