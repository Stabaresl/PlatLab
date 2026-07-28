from modules.shared.domain.exceptions import BusinessRuleViolationError, ForbiddenError


class SeccionBloqueadaError(ForbiddenError):
    """
    UC-02 precondición / dominio.md §3: se intenta acceder a contenido o
    validar una flag de una sección `bloqueada`. El TOC (HE-08) permite
    navegar solo a secciones `completada` o la `en_progreso` actual.
    """


class SeccionNoPerteneceAProgresoError(BusinessRuleViolationError):
    """La sección indicada no forma parte del laboratorio de este Progreso (UC-02 E3)."""
