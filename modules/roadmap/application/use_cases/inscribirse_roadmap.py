from datetime import datetime, timedelta, timezone

from modules.assignments.domain.entities import Asignacion
from modules.assignments.domain.events import AssignmentAccepted
from modules.assignments.domain.repositories import IAsignacionRepository
from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.laboratories.domain.value_objects import EstadoLaboratorio
from modules.progress.domain.entities import Progreso, ProgresoSeccion
from modules.progress.domain.repositories import IProgresoRepository
from modules.progress.domain.value_objects import EstadoProgresoSeccion
from modules.roadmap.application.completitud import esta_completado_por_estudiante
from modules.roadmap.application.dtos import InscribirseRoadmapDTO, InscripcionRoadmapResultDTO
from modules.roadmap.domain.repositories import INodoRoadmapRepository
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import (
    BusinessRuleViolationError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)

# Independiente de `_VIGENCIA_AUTOINSCRIPCION_DIAS` (assignments/inscribirse_laboratorio.py)
# — misma duración, pero es una constante propia de este módulo a
# propósito (no se importa la privada del otro módulo, mismo criterio de
# tolerar esta pequeña duplicación que ya usa el resto del código, ver
# `AceptarInvitacionUseCase` vs `InscribirseLaboratorioUseCase`). Sin
# fecha de vencimiento, `CerrarAsignacionesVencidasJob` nunca barrería
# una inscripción de roadmap abandonada.
_VIGENCIA_INSCRIPCION_ROADMAP_DIAS = 30

_SIN_PERMISO_MSG = "Solo un estudiante puede inscribirse a un laboratorio del roadmap."
_NODO_NO_ENCONTRADO_MSG = "Laboratorio de roadmap no encontrado."
_LAB_NO_DISPONIBLE_MSG = "Este laboratorio no está disponible."
_YA_INSCRITO_MSG = "Ya tenés una inscripción vigente en este laboratorio."
_PRERREQUISITOS_MSG = (
    "Todavía no completaste los laboratorios anteriores de esta pista del roadmap."
)


class InscribirseRoadmapUseCase(
    BaseUseCase[InscribirseRoadmapDTO, InscripcionRoadmapResultDTO]
):
    """
    Autoinscripción a un laboratorio del roadmap — a diferencia de
    `InscribirseLaboratorioUseCase` (catálogo viejo), acá NO aplica el
    límite global de "un solo laboratorio en curso a la vez": el único
    gate es "completaste todos los laboratorios con posición menor en
    esta misma categoría" (prerequisito = nodo anterior en la pista, ver
    `NodoRoadmap`). Reusa la misma tabla `Asignacion`
    (`existe_vigente` evita duplicar inscripción sin importar por qué
    puerta —catálogo o roadmap— haya entrado el estudiante) y dispara el
    evento `AssignmentAccepted` existente (no uno nuevo), para entrar
    gratis a auditoría/notificaciones ya suscritas a ese evento.
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        nodo_repository: INodoRoadmapRepository,
        asignacion_repository: IAsignacionRepository,
        laboratorio_repository: ILaboratorioRepository,
        progreso_repository: IProgresoRepository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._nodo_repository = nodo_repository
        self._asignacion_repository = asignacion_repository
        self._laboratorio_repository = laboratorio_repository
        self._progreso_repository = progreso_repository

    def _validate(self, input_dto: InscribirseRoadmapDTO) -> None:
        if input_dto.actor_rol != "estudiante":
            raise ForbiddenError(_SIN_PERMISO_MSG)

        nodo = self._nodo_repository.get_by_id(input_dto.nodo_id)
        if nodo is None:
            raise NotFoundError(_NODO_NO_ENCONTRADO_MSG)

        laboratorio = self._laboratorio_repository.get_by_id(nodo.laboratorio_id)
        if laboratorio is None or laboratorio.estado != EstadoLaboratorio.PUBLICADO:
            raise NotFoundError(_LAB_NO_DISPONIBLE_MSG)

        if self._asignacion_repository.existe_vigente(input_dto.actor_id, nodo.laboratorio_id):
            raise ConflictError(_YA_INSCRITO_MSG)

        anteriores = [
            n
            for n in self._nodo_repository.find_por_categoria(nodo.categoria_id)
            if n.posicion < nodo.posicion
        ]
        for previo in anteriores:
            completado = esta_completado_por_estudiante(
                self._asignacion_repository,
                self._progreso_repository,
                input_dto.actor_id,
                previo.laboratorio_id,
            )
            if not completado:
                raise BusinessRuleViolationError(_PRERREQUISITOS_MSG)

        self._nodo = nodo
        self._laboratorio = laboratorio

    def _execute_domain_logic(
        self, input_dto: InscribirseRoadmapDTO
    ) -> tuple[InscripcionRoadmapResultDTO, list[DomainEvent]]:
        asignacion = Asignacion(
            estudiante_id=input_dto.actor_id,
            laboratorio_id=self._nodo.laboratorio_id,
            instructor_id=None,
            fecha_vencimiento=datetime.now(timezone.utc)
            + timedelta(days=_VIGENCIA_INSCRIPCION_ROADMAP_DIAS),
        )
        creada = self._asignacion_repository.add(asignacion)
        creada.aceptar()
        guardada = self._asignacion_repository.update(creada)

        progreso = self._progreso_repository.add(
            Progreso(asignacion_id=guardada.id, estudiante_id=guardada.estudiante_id)
        )
        secciones = self._laboratorio_repository.get_secciones(self._nodo.laboratorio_id)
        progreso_secciones = [
            ProgresoSeccion(
                progreso_id=progreso.id,
                seccion_id=seccion.id,
                estado=(
                    EstadoProgresoSeccion.EN_PROGRESO
                    if indice == 0
                    else EstadoProgresoSeccion.BLOQUEADA
                ),
            )
            for indice, seccion in enumerate(secciones)
        ]
        if progreso_secciones:
            self._progreso_repository.add_secciones(progreso_secciones)

        result = InscripcionRoadmapResultDTO(
            id=guardada.id, laboratorio_id=guardada.laboratorio_id, estado=guardada.estado.value
        )
        event = AssignmentAccepted(
            asignacion_id=guardada.id,
            estudiante_id=guardada.estudiante_id,
            laboratorio_id=guardada.laboratorio_id,
        )
        return result, [event]
