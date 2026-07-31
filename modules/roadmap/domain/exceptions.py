from modules.shared.domain.exceptions import ValidationError


class PosicionInvalidaError(ValidationError):
    """La posición de un `NodoRoadmap` debe ser un entero >= 0."""
