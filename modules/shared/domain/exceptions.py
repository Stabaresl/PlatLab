class DomainError(Exception):
    """Excepción base de la que heredan todas las excepciones de dominio."""
    code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, details: list[dict] | None = None):
        self.message = message
        self.details = details or []
        super().__init__(message)


class BusinessRuleViolationError(DomainError):
    """
    Se viola una regla de negocio (ej. publicar sin flag, examen sin
    secciones completas). Mapea a HTTP 422.
    """
    code = "BUSINESS_RULE_VIOLATION"


class NotFoundError(DomainError):
    """Recurso inexistente. Mapea a HTTP 404."""
    code = "NOT_FOUND"


class ConflictError(DomainError):
    """
    Conflicto de estado (ej. asignación duplicada, email ya registrado).
    Mapea a HTTP 409.
    """
    code = "CONFLICT"


class ValidationError(DomainError):
    """Datos de entrada inválidos. Mapea a HTTP 400."""
    code = "VALIDATION_ERROR"


class ForbiddenError(DomainError):
    """
    Autenticado pero sin permiso (rol o propiedad, ej. instructor editando
    laboratorio ajeno). Mapea a HTTP 403.
    """
    code = "FORBIDDEN"


class UnauthenticatedError(DomainError):
    """Token ausente, inválido o expirado. Mapea a HTTP 401."""
    code = "UNAUTHENTICATED"
