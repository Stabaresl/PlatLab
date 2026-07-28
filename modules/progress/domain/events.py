import uuid
from dataclasses import dataclass

from modules.shared.domain.domain_event import DomainEvent


@dataclass(frozen=True, kw_only=True)
class FlagValidated(DomainEvent):
    """
    Se dispara en cada intento de flag, correcto o fallido (UC-02) —
    insumo de auditoría (UC-12).
    """

    progreso_id: uuid.UUID
    seccion_id: uuid.UUID
    correcta: bool


@dataclass(frozen=True, kw_only=True)
class SectionCompleted(DomainEvent):
    """Se dispara al completar una sección (HE-07) — desbloquea la siguiente (dominio.md §3)."""

    progreso_id: uuid.UUID
    seccion_id: uuid.UUID


@dataclass(frozen=True, kw_only=True)
class LabCompleted(DomainEvent):
    """
    Se dispara cuando la última `ProgresoSeccion` pasa a `completada` —
    habilita el examen final (dominio.md §3, UC-03). No implica todavía
    un `HistorialCompletitud` (eso lo crea `CalificadorDeExamen` al
    calificar el examen, Sprint 5); es solo la señal de "secciones
    completas".
    """

    progreso_id: uuid.UUID
