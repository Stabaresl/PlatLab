from modules.shared.domain.exceptions import UnauthenticatedError


class InvalidCredentialsError(UnauthenticatedError):
    """Credenciales de login inválidas (mensaje genérico, UC-01 E1)."""


class TokenReuseDetectedError(UnauthenticatedError):
    """
    Se detectó el reuso de un refresh token ya rotado — posible robo de
    sesión. Toda la familia de tokens de esa sesión queda invalidada
    (seguridad.md §2).
    """
