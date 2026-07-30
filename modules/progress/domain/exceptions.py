from modules.shared.domain.exceptions import BusinessRuleViolationError, ForbiddenError


class SeccionBloqueadaError(ForbiddenError):
    """
    UC-02 precondición / dominio.md §3: se intenta acceder a contenido o
    validar una flag de una sección `bloqueada`. El TOC (HE-08) permite
    navegar solo a secciones `completada` o la `en_progreso` actual.
    """


class SeccionNoPerteneceAProgresoError(BusinessRuleViolationError):
    """La sección indicada no forma parte del laboratorio de este Progreso (UC-02 E3)."""


class SeccionRequierePracticaError(BusinessRuleViolationError):
    """
    UC-02 bis: se intentó completar como "sección teórica" (sin flag) una
    sección con `tiene_practica=True` — esas solo se completan a través
    de `ValidarFlagUseCase` (POST .../flag/).
    """


class AsignacionVencidaError(ForbiddenError):
    """
    RF-32/HI-07: la `Asignación` de este `Progreso` ya venció — no se
    puede seguir avanzando (flags, secciones teóricas, examen). El
    laboratorio queda visible en modo solo-lectura vía
    `ObtenerProgresoQuery` (que expone `vencido`/`fecha_vencimiento`),
    pero ninguna de las acciones de escritura debe aceptarse.
    """
