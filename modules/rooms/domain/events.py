import uuid
from dataclasses import dataclass

from modules.shared.domain.domain_event import DomainEvent


@dataclass(frozen=True, kw_only=True)
class SalaCreada(DomainEvent):
    """Un instructor/admin abrió una sala — insumo de auditoría."""

    sala_id: uuid.UUID
    anfitrion_id: uuid.UUID
    laboratorio_id: uuid.UUID


@dataclass(frozen=True, kw_only=True)
class EstadoSalaCambiado(DomainEvent):
    sala_id: uuid.UUID
    actor_id: uuid.UUID
    estado: str


@dataclass(frozen=True, kw_only=True)
class EstudianteSeUnioASala(DomainEvent):
    sala_id: uuid.UUID
    estudiante_id: uuid.UUID
    anfitrion_id: uuid.UUID


@dataclass(frozen=True, kw_only=True)
class SalaCompletadaPorEstudiante(DomainEvent):
    """
    Un participante terminó el laboratorio de la sala (secciones + examen
    aprobado). Gamification otorga la recompensa según `posicion` y
    Notifications le avisa al estudiante.
    """

    sala_id: uuid.UUID
    sala_nombre: str
    estudiante_id: uuid.UUID
    anfitrion_id: uuid.UUID
    posicion: int
