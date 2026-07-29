from modules.reports.application.dtos import ListarReportesPropiosDTO, ReporteListItemDTO
from modules.reports.domain.repositories import IReporteRepository


class ListarReportesPropiosQuery:
    """api.md §8 `GET /reports/me/` — el estudiante ve solo los suyos."""

    def __init__(self, reporte_repository: IReporteRepository):
        self._repo = reporte_repository

    def execute(self, input_dto: ListarReportesPropiosDTO) -> list[ReporteListItemDTO]:
        reportes = self._repo.find_por_estudiante(input_dto.estudiante_id)
        return [
            ReporteListItemDTO(
                id=r.id,
                laboratorio_id=r.laboratorio_id,
                estado=r.estado.value,
                descripcion=r.descripcion,
                fecha_creacion=r.fecha_creacion,
                fecha_resolucion=r.fecha_resolucion,
            )
            for r in reportes
        ]
