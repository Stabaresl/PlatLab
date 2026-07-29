import uuid
from typing import Protocol

from modules.reports.domain.entities import AdjuntoReporte, Reporte


class IReporteRepository(Protocol):
    """
    Puerto de persistencia del agregado Reporte. La implementación real
    vive en `infrastructure/repositories.py` (PostgreSQL vía
    `mappers.py`) — Application nunca importa el ORM directamente.
    """

    def get_by_id(self, reporte_id: uuid.UUID) -> Reporte | None: ...

    def add(self, reporte: Reporte) -> Reporte: ...

    def update(self, reporte: Reporte) -> Reporte: ...

    def add_adjunto(self, adjunto: AdjuntoReporte) -> AdjuntoReporte: ...

    def get_adjunto(self, reporte_id: uuid.UUID) -> AdjuntoReporte | None: ...

    def find_por_estudiante(self, estudiante_id: uuid.UUID) -> list[Reporte]: ...

    def find_todos(
        self,
        estado: str | None = None,
        laboratorio_id: uuid.UUID | None = None,
    ) -> list[Reporte]:
        """HA-05, api.md §8 `GET /reports/?estado=&laboratorio=` — solo Admin."""
        ...
