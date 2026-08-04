import pytest

from modules.shared.infrastructure.redis_client import RedisClient


@pytest.fixture(autouse=True)
def _limpia_rate_limit_auth():
    """
    AuthRateLimiter cuenta intentos por IP en Redis, y el test client
    siempre pega desde 127.0.0.1 — sin este flush, los tests de este
    módulo que golpean login/register/refresh/password-reset de verdad
    (a diferencia del resto de la suite, que arma clientes autenticados
    mintiendo un JWT directo con JWTService) se pisarían el contador entre
    sí y fallarían por 429 de forma intermitente.
    """
    redis = RedisClient().raw
    for clave in redis.keys("auth_rate:*"):
        redis.delete(clave)
    yield
