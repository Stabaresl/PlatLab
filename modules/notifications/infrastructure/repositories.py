import uuid

from modules.notifications.domain.entities import Notificacion
from modules.notifications.infrastructure.mappers import notificacion_to_entity
from modules.notifications.infrastructure.models import NotificacionModel


class NotificacionRepository:
    """
    Implementación de `INotificacionRepository`
    (modules.notifications.domain.repositories) sobre PostgreSQL vía el
    ORM de Django — traduce entidad <-> modelo con `mappers.py`.
    """

    def add(self, notificacion: Notificacion) -> Notificacion:
        model = NotificacionModel.objects.create(
            id=notificacion.id,
            user_id=notificacion.user_id,
            tipo=notificacion.tipo.value,
            mensaje=notificacion.mensaje,
            canal=notificacion.canal.value,
            leida=notificacion.leida,
            entidad_tipo=notificacion.entidad_tipo,
            entidad_id=notificacion.entidad_id,
        )
        return notificacion_to_entity(model)

    def get_by_id(self, notificacion_id: uuid.UUID) -> Notificacion | None:
        model = NotificacionModel.objects.filter(id=notificacion_id).first()
        return notificacion_to_entity(model) if model else None

    def update(self, notificacion: Notificacion) -> Notificacion:
        model = NotificacionModel.objects.get(id=notificacion.id)
        model.leida = notificacion.leida
        model.save()
        return notificacion_to_entity(model)

    def find_por_usuario(
        self, user_id: uuid.UUID, leida: bool | None = None
    ) -> list[Notificacion]:
        queryset = NotificacionModel.objects.filter(user_id=user_id)
        if leida is not None:
            queryset = queryset.filter(leida=leida)

        queryset = queryset.order_by("-fecha_creacion")
        return [notificacion_to_entity(m) for m in queryset]
