from modules.assignments.application.dtos import LaboratorioDashboardItemDTO, ObtenerDashboardDTO
from modules.assignments.domain.repositories import IAsignacionRepository
from modules.assignments.domain.value_objects import EstadoAsignacion
from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.progress.domain.repositories import IProgresoRepository
from modules.shared.domain.exceptions import ForbiddenError

_SIN_PERMISO_MSG = "Solo un instructor tiene panel principal."


class ObtenerDashboardQuery:
    """
    HI-06 — panel principal del instructor: sus laboratorios propios con
    métricas rápidas (estudiantes inscritos, % completitud promedio).
    Cruza Laboratories (labs propios), Assignments (asignaciones
    activas por lab) y Progress (% completitud de cada Progreso) —
    puramente de lectura, no usa `BaseUseCase`.
    """

    def __init__(
        self,
        laboratorio_repository: ILaboratorioRepository,
        asignacion_repository: IAsignacionRepository,
        progreso_repository: IProgresoRepository,
    ):
        self._laboratorio_repository = laboratorio_repository
        self._asignacion_repository = asignacion_repository
        self._progreso_repository = progreso_repository

    def execute(self, input_dto: ObtenerDashboardDTO) -> list[LaboratorioDashboardItemDTO]:
        if input_dto.actor_rol != "instructor":
            raise ForbiddenError(_SIN_PERMISO_MSG)

        labs_visibles = self._laboratorio_repository.find_catalogo(
            instructor_id=input_dto.instructor_id
        )
        labs_propios = [
            lab for lab in labs_visibles if lab.instructor_id == input_dto.instructor_id
        ]
        asignaciones = self._asignacion_repository.find_por_instructor(input_dto.instructor_id)
        activas = [a for a in asignaciones if a.estado == EstadoAsignacion.ACTIVA]
        completitud_por_asignacion = self._progreso_repository.get_completitud_por_asignaciones(
            [a.id for a in activas]
        )

        return [
            self._a_dashboard_item(lab, activas, completitud_por_asignacion)
            for lab in labs_propios
        ]

    def _a_dashboard_item(self, lab, activas, completitud_por_asignacion) -> LaboratorioDashboardItemDTO:
        activas_del_lab = [a for a in activas if a.laboratorio_id == lab.id]
        porcentajes = [
            completitud_por_asignacion[a.id]
            for a in activas_del_lab
            if a.id in completitud_por_asignacion
        ]
        promedio = round(sum(porcentajes) / len(porcentajes), 2) if porcentajes else 0.0

        return LaboratorioDashboardItemDTO(
            laboratorio_id=lab.id,
            nombre=lab.nombre,
            estado=lab.estado.value,
            estudiantes_inscritos=len(activas_del_lab),
            porcentaje_completitud_promedio=promedio,
            tipo=lab.tipo.value,
            visible_en_catalogo=lab.visible_en_catalogo,
        )
