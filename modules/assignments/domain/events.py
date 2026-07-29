import uuid
from dataclasses import dataclass

from modules.shared.domain.domain_event import DomainEvent


@dataclass(frozen=True, kw_only=True)
class AssignmentInvited(DomainEvent):
    """Se dispara al crear una invitación (UC-06) — insumo de Notificaciones (UC-11)."""

    asignacion_id: uuid.UUID
    estudiante_id: uuid.UUID
    laboratorio_id: uuid.UUID


@dataclass(frozen=True, kw_only=True)
class AssignmentAccepted(DomainEvent):
    """
    Se dispara al aceptar una invitación (UC-06, paso 5). La creación
    del `Progreso` inicial la hace `AceptarInvitacionUseCase`
    directamente (misma transacción, HI-09) — este evento es para
    listeners downstream (notificaciones, auditoría), no el mecanismo
    que crea el Progreso.
    """

    asignacion_id: uuid.UUID
    estudiante_id: uuid.UUID
    laboratorio_id: uuid.UUID


@dataclass(frozen=True, kw_only=True)
class AssignmentRejected(DomainEvent):
    """Se dispara al rechazar una invitación (UC-06 A1)."""

    asignacion_id: uuid.UUID
    estudiante_id: uuid.UUID


@dataclass(frozen=True, kw_only=True)
class AssignmentExpired(DomainEvent):
    """
    Se dispara cuando `GestorDeVencimientos` (Sprint 5, UC-07) revoca un
    acceso vencido. Definido ya, mismo patrón que otros eventos
    "reservados" (ej. `PasswordResetRequested`) para no tener que tocar
    este archivo cuando se construya ese job.
    """

    asignacion_id: uuid.UUID
    estudiante_id: uuid.UUID
