from modules.reports.application.dtos import ListarReportesDTO, ReporteListItemDTO
from modules.reports.domain.repositories import IReporteRepository
from modules.shared.domain.exceptions import ForbiddenError

_SIN_PERMISO_MSG = "Solo un administrador puede listar todos los reportes."


class ListarReportesQuery:
    """HA-05, api.md §8 `GET /reports/?estado=&laboratorio=` — solo Admin."""

    def __init__(self, reporte_repository: IReporteRepository):
        self._repo = reporte_repository

    def execute(self, input_dto: ListarReportesDTO) -> list[ReporteListItemDTO]:
        if input_dto.actor_rol != "administrador":
            raise ForbiddenError(_SIN_PERMISO_MSG)

        reportes = self._repo.find_todos(
            estado=input_dto.estado, laboratorio_id=input_dto.laboratorio_id
        )
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
