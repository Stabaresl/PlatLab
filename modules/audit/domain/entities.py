import uuid
from dataclasses import dataclass, field
from datetime import datetime

from modules.shared.domain.base_entity import BaseEntity
from modules.shared.domain.tiempo import ahora_utc


@dataclass(eq=False)
class RegistroAuditoria(BaseEntity):
    """
    UC-12/RF-33: registro de una operación sensible (login, cambio de
    rol, CRUD de laboratorio, deshabilitación de usuario, acceso a
    flags, etc.). Append-only por diseño — ni esta entidad ni
    `IAuditoriaRepository` exponen un método para editar o borrar un
    registro ya creado.

    `ip` queda reservado para cuando exista un punto de entrada que
    capture la IP del request (ningún caso de uso ni evento de dominio
    la transporta todavía) — por ahora siempre viaja en `None`.
    """

    actor_id: uuid.UUID | None
    accion: str
    entidad_tipo: str | None
    entidad_id: uuid.UUID | None
    ip: str | None = None
    # Detalle opcional de la acción (base-de-datos.md §audit: jsonb), ej.
    # `{"rol_anterior": ..., "rol_nuevo": ...}`. Nunca secretos (tokens, flags).
    metadata: dict | None = None
    timestamp: datetime = field(default_factory=ahora_utc)
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        BaseEntity.__init__(self, id=self.id)
