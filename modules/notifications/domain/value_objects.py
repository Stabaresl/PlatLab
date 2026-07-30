from enum import Enum


class TipoNotificacion(str, Enum):
    """
    HE-13, base-de-datos.md "notifications_notificacion". `VENCIMIENTO_PROXIMO`
    (aviso 24h antes, UC-11) queda definido para uso futuro — este
    sprint solo implementa el cierre real (`ACCESO_VENCIDO`, vía
    `AssignmentExpired`/RF-32), no el job de aviso previo.
    """

    INVITACION = "invitacion"
    VENCIMIENTO_PROXIMO = "vencimiento_proximo"
    REPORTE_RESUELTO = "reporte_resuelto"
    LABORATORIO_PUBLICADO = "laboratorio_publicado"
    ACCESO_VENCIDO = "acceso_vencido"
    INSTRUCTOR_APROBADO = "instructor_aprobado"
    INSTRUCTOR_RECHAZADO = "instructor_rechazado"
    LABORATORIO_APROBADO = "laboratorio_aprobado"
    LABORATORIO_RECHAZADO = "laboratorio_rechazado"


class CanalNotificacion(str, Enum):
    IN_APP = "in_app"
    EMAIL = "email"
