import uuid
from dataclasses import dataclass

from modules.shared.domain.domain_event import DomainEvent


@dataclass(frozen=True, kw_only=True)
class LaboratoryPublished(DomainEvent):
    """Se dispara al publicar un laboratorio (UC-04) — insumo de auditoría (UC-12)."""

    laboratorio_id: uuid.UUID
    instructor_id: uuid.UUID | None


@dataclass(frozen=True, kw_only=True)
class LaboratoryDuplicated(DomainEvent):
    """Se dispara al duplicar un laboratorio predeterminado (UC-05)."""

    laboratorio_id: uuid.UUID
    origen_id: uuid.UUID
    instructor_id: uuid.UUID
