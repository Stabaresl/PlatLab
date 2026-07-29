from modules.assignments.domain.repositories import IAsignacionRepository
from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.progress.domain.repositories import IProgresoRepository
from modules.progress.domain.value_objects import EstadoProgresoSeccion
from modules.shared.domain.exceptions import ForbiddenError
from modules.users.application.dtos import (
    DashboardAdminResultDTO,
    LabPopularDTO,
    ObtenerDashboardAdminDTO,
)
from modules.users.domain.repositories import IUserRepository

_SIN_PERMISO_MSG = "Solo un administrador tiene acceso al dashboard."
_TOP_N_POPULARES = 5


class ObtenerDashboardAdminQuery:
    """
    HA-03, RF-28: métricas de plataforma para el administrador — usuarios
    por rol, laboratorios activos, los más populares (por asignaciones
    activas) y la tasa de completitud promedio. Cruza Users,
    Laboratories, Assignments y Progress — puramente de lectura, no usa
    `BaseUseCase` (mismo patrón que `ObtenerDashboardQuery`, HI-06).
    """

    def __init__(
        self,
        user_repository: IUserRepository,
        laboratorio_repository: ILaboratorioRepository,
        asignacion_repository: IAsignacionRepository,
        progreso_repository: IProgresoRepository,
    ):
        self._user_repository = user_repository
        self._laboratorio_repository = laboratorio_repository
        self._asignacion_repository = asignacion_repository
        self._progreso_repository = progreso_repository

    def execute(self, input_dto: ObtenerDashboardAdminDTO) -> DashboardAdminResultDTO:
        if input_dto.actor_rol != "administrador":
            raise ForbiddenError(_SIN_PERMISO_MSG)

        usuarios_por_rol: dict[str, int] = {}
        for usuario in self._user_repository.find_all():
            usuarios_por_rol[usuario.rol.value] = usuarios_por_rol.get(usuario.rol.value, 0) + 1

        labs_publicados = self._laboratorio_repository.find_publicados()
        asignaciones_activas = self._asignacion_repository.find_todas_activas()

        conteo_por_lab: dict = {}
        for asignacion in asignaciones_activas:
            conteo_por_lab[asignacion.laboratorio_id] = (
                conteo_por_lab.get(asignacion.laboratorio_id, 0) + 1
            )

        populares = sorted(
            labs_publicados, key=lambda lab: conteo_por_lab.get(lab.id, 0), reverse=True
        )[:_TOP_N_POPULARES]

        labs_mas_populares = [
            LabPopularDTO(
                laboratorio_id=lab.id,
                nombre=lab.nombre,
                estudiantes_inscritos=conteo_por_lab.get(lab.id, 0),
            )
            for lab in populares
        ]

        return DashboardAdminResultDTO(
            usuarios_por_rol=usuarios_por_rol,
            laboratorios_activos=len(labs_publicados),
            labs_mas_populares=labs_mas_populares,
            tasa_completitud_promedio=self._calcular_tasa_completitud(asignaciones_activas),
        )

    def _calcular_tasa_completitud(self, asignaciones) -> float:
        porcentajes = []
        for asignacion in asignaciones:
            progreso = self._progreso_repository.get_by_asignacion(asignacion.id)
            if progreso is None:
                continue
            secciones = self._progreso_repository.get_secciones(progreso.id)
            if not secciones:
                continue
            completadas = sum(1 for s in secciones if s.estado == EstadoProgresoSeccion.COMPLETADA)
            porcentajes.append(completadas / len(secciones) * 100)

        return round(sum(porcentajes) / len(porcentajes), 2) if porcentajes else 0.0
