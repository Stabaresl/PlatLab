import uuid
from typing import Protocol

from modules.notifications.domain.entities import Notificacion


class INotificacionRepository(Protocol):
    """
    Puerto de persistencia del agregado Notificacion. La implementación
    real vive en `infrastructure/repositories.py` (PostgreSQL vía
    `mappers.py`) — Application nunca importa el ORM directamente.
    """

    def add(self, notificacion: Notificacion) -> Notificacion: ...

    def get_by_id(self, notificacion_id: uuid.UUID) -> Notificacion | None: ...

    def update(self, notificacion: Notificacion) -> Notificacion: ...

    def find_por_usuario(
        self, user_id: uuid.UUID, leida: bool | None = None
    ) -> list[Notificacion]: ...
