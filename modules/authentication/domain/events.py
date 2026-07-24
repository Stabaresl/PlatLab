import uuid
from dataclasses import dataclass

from modules.shared.domain.domain_event import DomainEvent


@dataclass(frozen=True, kw_only=True)
class UserRegistered(DomainEvent):
    """
    Se dispara al completar el registro (UC-01, paso 4: "El sistema envía
    correo de verificación"). El envío real del correo lo hace un listener
    suscrito a este evento — todavía no está conectado (se conecta cuando
    se construya el sistema de notificaciones/email de verificación), pero
    el evento ya queda disponible desde ahora sin tener que tocar el caso
    de uso más adelante.
    """

    user_id: uuid.UUID
    email: str
    nombre_completo: str


@dataclass(frozen=True, kw_only=True)
class UserLoggedIn(DomainEvent):
    """Se dispara en cada login exitoso — insumo para auditoría (UC-12)."""

    user_id: uuid.UUID
