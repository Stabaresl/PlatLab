from modules.progress.application.dtos import HistorialItemDTO, ObtenerHistorialDTO
from modules.progress.domain.repositories import IProgresoRepository
from modules.shared.domain.exceptions import NotFoundError

_PROGRESO_NO_ENCONTRADO_MSG = "Progreso no encontrado."


class ObtenerHistorialQuery:
    """HE-10/HE-11, api.md §7 `GET .../history/`: historial de completitudes del laboratorio."""

    def __init__(self, progreso_repository: IProgresoRepository):
        self._progreso_repository = progreso_repository

    def execute(self, input_dto: ObtenerHistorialDTO) -> list[HistorialItemDTO]:
        progreso = self._progreso_repository.get_by_asignacion(input_dto.asignacion_id)
        if progreso is None or not progreso.es_propio_de(input_dto.estudiante_id):
            raise NotFoundError(_PROGRESO_NO_ENCONTRADO_MSG)

        historial = self._progreso_repository.get_historial(progreso.id)
        return [
            HistorialItemDTO(
                numero_intento=h.numero_intento,
                fecha_completado=h.fecha_completado,
                puntaje=h.puntaje,
            )
            for h in historial
        ]
