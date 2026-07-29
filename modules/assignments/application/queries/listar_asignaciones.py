from modules.assignments.application.dtos import AsignacionListItemDTO, ListarAsignacionesDTO
from modules.assignments.domain.repositories import IAsignacionRepository


class ListarAsignacionesQuery:
    """api.md §6 `GET /assignments/`: instructor ve las que creó; estudiante, las suyas."""

    def __init__(self, asignacion_repository: IAsignacionRepository):
        self._repo = asignacion_repository

    def execute(self, input_dto: ListarAsignacionesDTO) -> list[AsignacionListItemDTO]:
        if input_dto.actor_rol == "instructor":
            asignaciones = self._repo.find_por_instructor(input_dto.actor_id)
        elif input_dto.actor_rol == "estudiante":
            asignaciones = self._repo.find_por_estudiante(input_dto.actor_id)
        else:
            asignaciones = []

        return [
            AsignacionListItemDTO(
                id=a.id,
                estudiante_id=a.estudiante_id,
                laboratorio_id=a.laboratorio_id,
                estado=a.estado.value,
                fecha_invitacion=a.fecha_invitacion,
                fecha_vencimiento=a.fecha_vencimiento,
            )
            for a in asignaciones
        ]
