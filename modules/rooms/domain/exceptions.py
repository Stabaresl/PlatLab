from modules.shared.domain.exceptions import (
    BusinessRuleViolationError,
    ConflictError,
    NotFoundError,
)


class SalaNoEncontradaError(NotFoundError):
    def __init__(self, message: str = "No encontramos una sala con ese código. Revísalo con tu instructor."):
        super().__init__(message)


class SalaSinIngresosError(BusinessRuleViolationError):
    def __init__(self, message: str = "Esta sala ya no recibe participantes."):
        super().__init__(message)


class SalaLlenaError(ConflictError):
    def __init__(self, capacidad: int):
        super().__init__(f"La sala está llena ({capacidad}/{capacidad}). Pídele al anfitrión que amplíe el cupo.")
