import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class IniciarEntornoDTO:
    """`POST /lab-environments/{assignment_id}/sections/{section_id}/start/`."""

    asignacion_id: uuid.UUID
    seccion_id: uuid.UUID
    estudiante_id: uuid.UUID


@dataclass(frozen=True)
class EntornoResultDTO:
    id: uuid.UUID
    estado: str
    idle_timeout_minutos: int
    max_lifetime_minutos: int


@dataclass(frozen=True)
class DetenerEntornoDTO:
    entorno_id: uuid.UUID
    estudiante_id: uuid.UUID


@dataclass(frozen=True)
class ObtenerEstadoEntornoDTO:
    asignacion_id: uuid.UUID
    seccion_id: uuid.UUID
    estudiante_id: uuid.UUID
