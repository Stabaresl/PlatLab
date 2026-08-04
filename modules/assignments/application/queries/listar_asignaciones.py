from modules.assignments.application.dtos import AsignacionListItemDTO, ListarAsignacionesDTO
from modules.assignments.domain.repositories import IAsignacionRepository
from modules.users.domain.repositories import IUserRepository


class ListarAsignacionesQuery:
    """api.md §6 `GET /assignments/`: instructor ve las que creó; estudiante, las suyas."""

    def __init__(self, asignacion_repository: IAsignacionRepository, user_repository: IUserRepository):
        self._repo = asignacion_repository
        self._user_repository = user_repository

    def execute(self, input_dto: ListarAsignacionesDTO) -> list[AsignacionListItemDTO]:
        if input_dto.actor_rol == "instructor":
            asignaciones = self._repo.find_por_instructor(input_dto.actor_id)
        elif input_dto.actor_rol == "estudiante":
            asignaciones = self._repo.find_por_estudiante(input_dto.actor_id)
        else:
            asignaciones = []

        # Un estudiante suele tener pocas asignaciones y de pocos
        # instructores distintos — resolver nombre por id acá, sin
        # necesidad de un método de batch nuevo en IUserRepository (no es
        # el mismo escenario que el N+1 de los dashboards, que escalaba
        # con TODA la plataforma).
        nombres_por_instructor: dict = {}
        for a in asignaciones:
            if a.instructor_id is None or a.instructor_id in nombres_por_instructor:
                continue
            instructor = self._user_repository.get_by_id(a.instructor_id)
            nombres_por_instructor[a.instructor_id] = instructor.nombre_completo if instructor else None

        return [
            AsignacionListItemDTO(
                id=a.id,
                estudiante_id=a.estudiante_id,
                laboratorio_id=a.laboratorio_id,
                estado=a.estado.value,
                fecha_invitacion=a.fecha_invitacion,
                fecha_vencimiento=a.fecha_vencimiento,
                instructor_nombre=nombres_por_instructor.get(a.instructor_id) if a.instructor_id else None,
            )
            for a in asignaciones
        ]
