import uuid
from dataclasses import dataclass

from modules.shared.domain.domain_event import DomainEvent


@dataclass(frozen=True, kw_only=True)
class ReportSubmitted(DomainEvent):
    """Se dispara al crear un reporte (UC-09, paso 1) — notifica al administrador (HE-13)."""

    reporte_id: uuid.UUID
    estudiante_id: uuid.UUID
    laboratorio_id: uuid.UUID


@dataclass(frozen=True, kw_only=True)
class ReportResolved(DomainEvent):
    """Se dispara al resolver un reporte (UC-09 paso 3/A1) — notifica al estudiante (HE-13)."""

    reporte_id: uuid.UUID
    estudiante_id: uuid.UUID
    estado: str
