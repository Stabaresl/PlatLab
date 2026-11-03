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
    """
    Un administrador aprobó o rechazó la solicitud — insumo de Notifications
    (avisa al estudiante) y Audit (`admin_id` como actor).
    """

    solicitud_id: uuid.UUID
    user_id: uuid.UUID
    aprobada: bool
    motivo_rechazo: str | None
    admin_id: uuid.UUID | None = None


@dataclass(frozen=True, kw_only=True)
class UsuarioDeshabilitado(DomainEvent):
    """
    Un admin deshabilitó la cuenta (HA-01). Authentication lo escucha para
    revocar todas las sesiones del usuario en el acto; Audit, para dejar
    registro (seguridad.md §6: "deshabilitar usuario" es operación sensible).
    """

    user_id: uuid.UUID
    admin_id: uuid.UUID


@dataclass(frozen=True, kw_only=True)
class UsuarioHabilitado(DomainEvent):
    """Un admin reactivó la cuenta (HA-01) — insumo de auditoría."""

    user_id: uuid.UUID
    admin_id: uuid.UUID


@dataclass(frozen=True, kw_only=True)
class RolUsuarioCambiado(DomainEvent):
    """Un admin cambió el rol de un usuario (HA-01, UC-08) — insumo de auditoría."""

    user_id: uuid.UUID
    admin_id: uuid.UUID
    rol_anterior: str
    rol_nuevo: str
