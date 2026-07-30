from enum import Enum


class EstadoEntorno(str, Enum):
    """
    Ciclo de vida de un `EntornoActivo`: `iniciando` mientras se crea el
    contenedor Docker (puede fallar → `error`), `activo` mientras corre y
    acepta sesiones de terminal, `detenido` una vez apagado (explícito por
    el estudiante o por el reaper de inactividad — RF-32 aplicado acá al
    entorno práctico, mismo criterio que `EstadoAsignacion.VENCIDA`).
    """

    INICIANDO = "iniciando"
    ACTIVO = "activo"
    DETENIDO = "detenido"
    ERROR = "error"
