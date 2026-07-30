import uuid
from dataclasses import dataclass

from modules.shared.domain.domain_event import DomainEvent


@dataclass(frozen=True, kw_only=True)
class InstructorVerificationRequested(DomainEvent):
    """
    Se dispara al crear una `SolicitudInstructor` (estado pendiente). El
    listener en `infrastructure/event_listeners.py` encola la verificación
    contra OpenAlex vía Celery — nunca se llama la API externa dentro del
    mismo request/response que crea la solicitud.
    """

    solicitud_id: uuid.UUID
    user_id: uuid.UUID
    orcid: str
    nombre_declarado: str


@dataclass(frozen=True, kw_only=True)
class InstructorVerificationResolved(DomainEvent):
    """Se dispara al aprobar o rechazar una solicitud — insumo de Notifications."""

    solicitud_id: uuid.UUID
    user_id: uuid.UUID
    aprobada: bool
    motivo_rechazo: str | None
