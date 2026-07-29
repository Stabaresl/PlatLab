from modules.notifications.domain.entities import Notificacion
from modules.notifications.domain.value_objects import CanalNotificacion, TipoNotificacion
from modules.notifications.infrastructure.models import NotificacionModel


def notificacion_to_entity(model: NotificacionModel) -> Notificacion:
    return Notificacion(
        id=model.id,
        user_id=model.user_id,
        tipo=TipoNotificacion(model.tipo),
        mensaje=model.mensaje,
        canal=CanalNotificacion(model.canal),
        leida=model.leida,
        entidad_tipo=model.entidad_tipo,
        entidad_id=model.entidad_id,
        fecha_creacion=model.fecha_creacion,
    )
