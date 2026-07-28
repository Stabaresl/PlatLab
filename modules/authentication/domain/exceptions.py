from modules.shared.domain.exceptions import ConflictError, UnauthenticatedError


class InvalidCredentialsError(UnauthenticatedError):
    """Credenciales de login inválidas (mensaje genérico, UC-01 E1)."""


class TokenReuseDetectedError(UnauthenticatedError):
    """
    Se detectó el reuso de un refresh token ya rotado — posible robo de
    sesión. Toda la familia de tokens de esa sesión queda invalidada
    (seguridad.md §2).
    """


class AccountLinkingRequiresConfirmationError(ConflictError):
    """
    UC-01 E4 / seguridad.md §3: el email verificado por OAuth ya tiene una
    cuenta creada por otro medio (password u otro proveedor). Nunca se
    vincula automáticamente — previene account takeover. `OAuthLoginUseCase`
    adjunta un `link_token` de un solo uso en `details` para que el usuario
    confirme reautenticándose con su password actual.
    """
