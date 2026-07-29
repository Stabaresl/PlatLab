from modules.shared.domain.exceptions import ConflictError, ValidationError


class DuplicateAssignmentError(ConflictError):
    """
    UC-06 E2: el estudiante ya tiene una asignación vigente (`pendiente`
    o `activa`) a ese mismo laboratorio — no se duplica, se informa el
    estado actual.
    """


class InvalidExpirationError(ValidationError):
    """`fecha_vencimiento` debe ser posterior al momento de la invitación."""
