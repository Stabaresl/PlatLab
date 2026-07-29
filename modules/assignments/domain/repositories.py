import uuid
from typing import Protocol

from modules.assignments.domain.entities import Asignacion


class IAsignacionRepository(Protocol):
    """
    Puerto de persistencia del agregado Asignación. La implementación
    real vive en `infrastructure/repositories.py` (PostgreSQL vía
    `mappers.py`) — Application nunca importa el ORM directamente.
    """

    def get_by_id(self, asignacion_id: uuid.UUID) -> Asignacion | None: ...

    def add(self, asignacion: Asignacion) -> Asignacion: ...

    def update(self, asignacion: Asignacion) -> Asignacion: ...

    def existe_vigente(self, estudiante_id: uuid.UUID, laboratorio_id: uuid.UUID) -> bool:
        """UC-06 E2: True si ya existe una asignación `pendiente` o `activa` para ese par."""
        ...

    def find_por_instructor(self, instructor_id: uuid.UUID) -> list[Asignacion]: ...

    def find_por_estudiante(self, estudiante_id: uuid.UUID) -> list[Asignacion]: ...

    def find_activas_con_vencimiento(self) -> list[Asignacion]:
        """RF-32: candidatas a evaluar por `GestorDeVencimientos` (activa, con fecha límite)."""
        ...
