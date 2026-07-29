from modules.shared.domain.exceptions import BusinessRuleViolationError


class SelfDisableNotAllowedError(BusinessRuleViolationError):
    """
    UC-08 E1 / api.md §4: un Administrador no puede deshabilitarse ni
    quitarse su propio rol de administrador a sí mismo — previene un
    bloqueo total del sistema (nadie con permisos de admin restante).
    """
