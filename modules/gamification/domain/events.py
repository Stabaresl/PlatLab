import uuid
from dataclasses import dataclass

from modules.shared.domain.domain_event import DomainEvent


@dataclass(frozen=True, kw_only=True)
class LogroDesbloqueadoEvent(DomainEvent):
    """Se dispara al desbloquear un logro — insumo de notificaciones/auditoría."""

    estudiante_id: uuid.UUID
    logro_id: uuid.UUID
    nombre: str
