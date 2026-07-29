import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class MarcarLeidaDTO:
    notificacion_id: uuid.UUID
    actor_id: uuid.UUID


@dataclass(frozen=True)
class NotificacionResultDTO:
    id: uuid.UUID
    tipo: str
    mensaje: str
    canal: str
    leida: bool
    entidad_tipo: str | None
    entidad_id: uuid.UUID | None
    fecha_creacion: datetime


@dataclass(frozen=True)
class ListarNotificacionesDTO:
    user_id: uuid.UUID
    leida: bool | None = None
