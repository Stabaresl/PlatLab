from modules.lab_environments.application.dtos import ObtenerEstadoEntornoDTO
from modules.lab_environments.domain.entities import EntornoActivo
from modules.lab_environments.domain.repositories import IEntornoRepository
from modules.progress.domain.repositories import IProgresoRepository
from modules.shared.domain.exceptions import NotFoundError

_PROGRESO_NO_ENCONTRADO_MSG = "Progreso no encontrado."


class ObtenerEstadoEntornoQuery:
    """`GET /lab-environments/{assignment_id}/sections/{section_id}/status/`."""

    def __init__(self, entorno_repository: IEntornoRepository, progreso_repository: IProgresoRepository):
        self._entorno_repository = entorno_repository
        self._progreso_repository = progreso_repository

    def execute(self, input_dto: ObtenerEstadoEntornoDTO) -> EntornoActivo | None:
        progreso = self._progreso_repository.get_by_asignacion(input_dto.asignacion_id)
        if progreso is None or not progreso.es_propio_de(input_dto.estudiante_id):
            raise NotFoundError(_PROGRESO_NO_ENCONTRADO_MSG)

        entorno = self._entorno_repository.get_activo_por_seccion(progreso.id, input_dto.seccion_id)
        if entorno is None or not entorno.es_propio_de(input_dto.estudiante_id):
            return None
        return entorno
