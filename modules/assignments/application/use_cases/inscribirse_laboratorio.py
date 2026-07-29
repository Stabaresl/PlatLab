from modules.assignments.application.dtos import AsignacionResultDTO, InscribirseLaboratorioDTO
from modules.assignments.domain.entities import Asignacion
from modules.assignments.domain.events import AssignmentAccepted
from modules.assignments.domain.repositories import IAsignacionRepository
from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.laboratories.domain.value_objects import EstadoLaboratorio, TipoLaboratorio
from modules.progress.domain.entities import Progreso, ProgresoSeccion
from modules.progress.domain.repositories import IProgresoRepository
from modules.progress.domain.value_objects import EstadoProgresoSeccion
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import (
    BusinessRuleViolationError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)

_SIN_PERMISO_MSG = "Solo un estudiante puede autoinscribirse a un laboratorio."
_LAB_NO_ENCONTRADO_MSG = "Laboratorio no encontrado."
_YA_INSCRITO_MSG = "Ya tenés una inscripción vigente en este laboratorio."
_LAB_EN_CURSO_MSG = (
    "Tenés un laboratorio en curso sin terminar. Completá el examen final antes de "
    "inscribirte en uno nuevo."
)


class InscribirseLaboratorioUseCase(BaseUseCase[InscribirseLaboratorioDTO, AsignacionResultDTO]):
    """
    Autoinscripción directa desde el catálogo público (`/laboratorios`),
    sin invitación de instructor — a diferencia de `InvitarEstudiantesUseCase`
    (UC-06), acá el actor es el propio estudiante y solo aplica a
    laboratorios `predeterminado` + `publicado` (los únicos que el catálogo
    público expone, `Laboratorio.es_visible_para`; un `personalizado` sigue
    siendo privado de su instructor y solo se asigna por invitación).

    Regla de producto (no existía antes): un estudiante no puede tener más
    de un laboratorio "en curso" a la vez. Se considera "en curso" una
    asignación `pendiente`/`activa` cuyo `Progreso` todavía no tiene ningún
    intento de examen registrado (mismo criterio de completitud que HE-11 /
    `ObtenerHistorialQuery` y que ya usa el Dashboard del estudiante en el
    frontend: historial vacío = no terminado). Si existe una así, bloquea
    la autoinscripción con `BusinessRuleViolationError` en vez de dejar que
    el estudiante acumule laboratorios sin terminar.

    Al igual que `AceptarInvitacionUseCase`, otorga acceso inmediato
    (`activa`, no `pendiente` — no hay a quién "aceptarle" una invitación
    que uno mismo se dio) e inicializa el `Progreso` en el mismo paso.
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        asignacion_repository: IAsignacionRepository,
        laboratorio_repository: ILaboratorioRepository,
        progreso_repository: IProgresoRepository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._asignacion_repository = asignacion_repository
        self._laboratorio_repository = laboratorio_repository
        self._progreso_repository = progreso_repository

    def _validate(self, input_dto: InscribirseLaboratorioDTO) -> None:
        if input_dto.actor_rol != "estudiante":
            raise ForbiddenError(_SIN_PERMISO_MSG)

        laboratorio = self._laboratorio_repository.get_by_id(input_dto.laboratorio_id)
        if (
            laboratorio is None
            or laboratorio.estado != EstadoLaboratorio.PUBLICADO
            or laboratorio.tipo != TipoLaboratorio.PREDETERMINADO
        ):
            # Mismo criterio anti-enumeración que HV-03: nunca se confirma la
            # existencia de un laboratorio que el catálogo público no expone.
            raise NotFoundError(_LAB_NO_ENCONTRADO_MSG)

        if self._asignacion_repository.existe_vigente(
            input_dto.actor_id, input_dto.laboratorio_id
        ):
            raise ConflictError(_YA_INSCRITO_MSG)

        vigentes = [
            a
            for a in self._asignacion_repository.find_por_estudiante(input_dto.actor_id)
            if a.esta_vigente()
        ]
        for asignacion in vigentes:
            if not self._esta_terminada(asignacion):
                raise BusinessRuleViolationError(_LAB_EN_CURSO_MSG)

        self._laboratorio = laboratorio

    def _esta_terminada(self, asignacion: Asignacion) -> bool:
        progreso = self._progreso_repository.get_by_asignacion(asignacion.id)
        if progreso is None:
            return False
        return len(self._progreso_repository.get_historial(progreso.id)) > 0

    def _execute_domain_logic(
        self, input_dto: InscribirseLaboratorioDTO
    ) -> tuple[AsignacionResultDTO, list[DomainEvent]]:
        asignacion = Asignacion(
            estudiante_id=input_dto.actor_id,
            laboratorio_id=input_dto.laboratorio_id,
            instructor_id=None,
        )
        creada = self._asignacion_repository.add(asignacion)
        # `add()` solo persiste el estado inicial (pendiente) — la transición a
        # `activa` (con `fecha_respuesta`) pasa siempre por `update()`, igual que
        # en `AceptarInvitacionUseCase`. Acá no hay invitación previa que
        # aceptar: la autoinscripción y la aceptación son el mismo instante.
        creada.aceptar()
        guardada = self._asignacion_repository.update(creada)

        progreso = self._progreso_repository.add(
            Progreso(asignacion_id=guardada.id, estudiante_id=guardada.estudiante_id)
        )
        secciones = self._laboratorio_repository.get_secciones(input_dto.laboratorio_id)
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

        result = AsignacionResultDTO(
            id=guardada.id, laboratorio_id=guardada.laboratorio_id, estado=guardada.estado.value
        )
        event = AssignmentAccepted(
            asignacion_id=guardada.id,
            estudiante_id=guardada.estudiante_id,
            laboratorio_id=guardada.laboratorio_id,
        )
        return result, [event]
