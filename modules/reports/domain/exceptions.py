from modules.shared.domain.exceptions import BusinessRuleViolationError, ValidationError


class DescriptionTooShortError(ValidationError):
    """UC-09 E1: la descripción del reporte no alcanza el mínimo (10 caracteres)."""


class ReporteYaResueltoError(BusinessRuleViolationError):
    """No se puede cambiar el estado de un reporte que ya está `resuelto`/`no_reproducible`."""
