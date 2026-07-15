import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    """
    Clase base para todo evento de dominio (AssignmentAccepted,
    LaboratoryPublished, FlagValidated, etc.). Cada módulo define sus propios
    eventos heredando de esta clase; el EventDispatcher (Infrastructure) los
    despacha a los listeners registrados por tipo.
    """
    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
