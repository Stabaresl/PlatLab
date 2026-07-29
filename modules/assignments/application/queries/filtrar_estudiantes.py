from modules.assignments.application.dtos import EstudianteFiltradoDTO, FiltrarEstudiantesDTO
from modules.assignments.domain.entities import Asignacion
from modules.assignments.domain.repositories import IAsignacionRepository
from modules.progress.domain.repositories import IProgresoRepository
from modules.progress.domain.value_objects import EstadoProgresoSeccion
from modules.users.domain.repositories import IUserRepository


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
        asignaciones = self._asignacion_repository.find_por_instructor(input_dto.instructor_id)
        if input_dto.laboratorio_id is not None:
            asignaciones = [
                a for a in asignaciones if a.laboratorio_id == input_dto.laboratorio_id
            ]

        resultados = []
        for asignacion in asignaciones:
            estudiante = self._user_repository.get_by_id(asignacion.estudiante_id)
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
                    porcentaje_completitud=self._porcentaje_completitud(asignacion),
                )
            )
        return resultados

    def _porcentaje_completitud(self, asignacion: Asignacion) -> float:
        progreso = self._progreso_repository.get_by_asignacion(asignacion.id)
        if progreso is None:
            return 0.0

        secciones = self._progreso_repository.get_secciones(progreso.id)
        if not secciones:
            return 0.0

        completadas = sum(1 for s in secciones if s.estado == EstadoProgresoSeccion.COMPLETADA)
        return round(completadas / len(secciones) * 100, 2)
