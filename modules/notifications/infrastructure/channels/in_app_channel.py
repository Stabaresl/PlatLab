from modules.notifications.domain.entities import Notificacion
from modules.notifications.domain.repositories import INotificacionRepository


class InAppChannel:
    """Canal in-app (HE-13/UC-11): persiste la `Notificacion` para `GET /notifications/`."""

    def __init__(self, notificacion_repository: INotificacionRepository):
        self._notificacion_repository = notificacion_repository

    def enviar(self, notificacion: Notificacion) -> Notificacion:
        return self._notificacion_repository.add(notificacion)
