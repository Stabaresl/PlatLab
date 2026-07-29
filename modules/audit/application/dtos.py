import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ConsultarAuditoriaDTO:
    """api.md §10 `GET /audit/?actor=&accion=&desde=&hasta=` — solo Admin."""

    actor_rol: str
    actor_id: uuid.UUID | None = None
    accion: str | None = None
    desde: datetime | None = None
    hasta: datetime | None = None


@dataclass(frozen=True)
class RegistroAuditoriaItemDTO:
    id: uuid.UUID
    actor_id: uuid.UUID | None
    accion: str
    entidad_tipo: str | None
    entidad_id: uuid.UUID | None
    timestamp: datetime
