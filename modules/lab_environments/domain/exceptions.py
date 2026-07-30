from modules.shared.domain.exceptions import BusinessRuleViolationError, ForbiddenError, RateLimitedError


class SeccionSinEntornoRealError(BusinessRuleViolationError):
    """La sección no tiene `imagen_practica` configurada — no hay entorno real que iniciar."""


class SeccionNoDisponibleError(ForbiddenError):
    """La `ProgresoSeccion` asociada está `bloqueada` — no se puede abrir un entorno todavía."""


class EntornoNoDisponibleError(RateLimitedError):
    """
    Se alcanzó `LAB_ENV_MAX_CONCURRENTES` — protege al host de sobrecarga
    (RNF de rendimiento): en vez de degradar todos los entornos activos,
    se rechaza el nuevo pedido con una señal clara de "reintentá en unos
    minutos" (mapea a 429, igual que el rate limiting de flags).
    """


class EntornoProviderError(BusinessRuleViolationError):
    """El motor de contenedores (Docker) falló al iniciar/detener un entorno."""
