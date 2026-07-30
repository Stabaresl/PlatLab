import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class EstadoAsignacionInfo:
    vencida: bool
    fecha_vencimiento: datetime | None


class IEstadoAsignacionProvider(Protocol):
    """
    Puerto para que Progress sepa si la Asignación de un Progreso sigue
    vigente, sin depender directamente del módulo Assignments (dominio.md
    §4: agregados separados, "id suelto"). RF-32/HI-07: una asignación
    vencida no debe permitir seguir avanzando el laboratorio (flags,
    secciones teóricas, examen) — aunque el job periódico
    (`CerrarAsignacionesVencidasJob`) todavía no haya corrido sobre ella,
    por eso la implementación real recalcula contra `fecha_vencimiento`
    en vez de confiar solo en el `estado` ya persistido.
    """

    def obtener_estado(self, asignacion_id: uuid.UUID) -> EstadoAsignacionInfo | None: ...
