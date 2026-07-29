import uuid
from dataclasses import dataclass, field
from datetime import datetime

from modules.notifications.domain.value_objects import CanalNotificacion, TipoNotificacion
from modules.shared.domain.base_entity import BaseEntity


@dataclass(eq=False)
class Notificacion(BaseEntity):
    """
    HE-13, base-de-datos.md "notifications_notificacion". `user_id` es
    id suelto (Arquitectura §8) — Notifications no depende de Users.
    `entidad_tipo`/`entidad_id` habilitan deep-link (ej. "asignacion",
    id de la Asignación) sin acoplarse al módulo dueño de esa entidad.
    """

    user_id: uuid.UUID
    tipo: TipoNotificacion
    mensaje: str
    canal: CanalNotificacion = CanalNotificacion.IN_APP
    leida: bool = False
    entidad_tipo: str | None = None
    entidad_id: uuid.UUID | None = None
    fecha_creacion: datetime = field(default_factory=datetime.utcnow)
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        BaseEntity.__init__(self, id=self.id)

    def marcar_leida(self) -> None:
        self.leida = True
