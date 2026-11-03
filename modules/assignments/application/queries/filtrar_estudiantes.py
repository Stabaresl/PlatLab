from modules.assignments.application.dtos import EstudianteFiltradoDTO, FiltrarEstudiantesDTO
from modules.assignments.domain.repositories import IAsignacionRepository
from modules.progress.domain.repositories import IProgresoRepository
from modules.shared.domain.exceptions import ForbiddenError
from modules.users.domain.repositories import IUserRepository

_SIN_PERMISO_MSG = "Solo un instructor puede filtrar sus estudiantes."


class FiltrarEstudiantesQuery:
    """
    HI-04, api.md §6 `GET /assignments/students/`: estudiantes con labs
    asignados por el instructor, filtrables por nombre y/o laboratorio.
    Incluye `porcentaje_completitud` (secciones completadas / total)
    como indicador rápido de avance.
    """

    def __init__(
        self,
        asignacion_repository: IAsignacionRepository,
        user_repository: IUserRepository,
        progreso_repository: IProgresoRepository,
    ):
        self._asignacion_repository = asignacion_repository
        self._user_repository = user_repository
        self._progreso_repository = progreso_repository

    def execute(self, input_dto: FiltrarEstudiantesDTO) -> list[EstudianteFiltradoDTO]:
        if input_dto.actor_rol != "instructor":
            raise ForbiddenError(_SIN_PERMISO_MSG)

        asignaciones = self._asignacion_repository.find_por_instructor(input_dto.instructor_id)
        if input_dto.laboratorio_id is not None:
            asignaciones = [
                a for a in asignaciones if a.laboratorio_id == input_dto.laboratorio_id
            ]

        # Batch (2 consultas en total) en vez de usuario + progreso +
        # secciones por cada asignación — mismo N+1 que ya se había quitado
        # de los dashboards de instructor/admin.
        estudiantes = self._user_repository.get_by_ids(
            list({a.estudiante_id for a in asignaciones})
        )
        completitud = self._progreso_repository.get_completitud_por_asignaciones(
            [a.id for a in asignaciones]
        )

        resultados = []
        for asignacion in asignaciones:
            estudiante = estudiantes.get(asignacion.estudiante_id)
            if estudiante is None:
                continue
            if (
                input_dto.nombre
                and input_dto.nombre.lower() not in estudiante.nombre_completo.lower()
            ):
                continue

            resultados.append(
                EstudianteFiltradoDTO(
                    estudiante_id=estudiante.id,
                    nombre_completo=estudiante.nombre_completo,
                    laboratorio_id=asignacion.laboratorio_id,
                    estado_asignacion=asignacion.estado.value,
                    porcentaje_completitud=round(completitud.get(asignacion.id, 0.0), 2),
                )
            )
        return resultados
