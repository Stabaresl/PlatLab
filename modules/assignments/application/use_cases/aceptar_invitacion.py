from modules.assignments.application.dtos import AceptarInvitacionDTO, AsignacionResultDTO
from modules.assignments.domain.events import AssignmentAccepted
from modules.assignments.domain.repositories import IAsignacionRepository
from modules.assignments.domain.value_objects import EstadoAsignacion
from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.progress.domain.entities import Progreso, ProgresoSeccion
from modules.progress.domain.repositories import IProgresoRepository
from modules.progress.domain.value_objects import EstadoProgresoSeccion
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import BusinessRuleViolationError, NotFoundError

_ASIGNACION_NO_ENCONTRADA_MSG = "Invitación no encontrada."
_YA_RESPONDIDA_MSG = "Esta invitación ya fue respondida."


class AceptarInvitacionUseCase(BaseUseCase[AceptarInvitacionDTO, AsignacionResultDTO]):
    """
    UC-06, paso 4-5, api.md §6 `POST /assignments/invitations/{id}/accept/`:
    acepta la invitación (pendiente -> activa) y crea el `Progreso`
    inicial — una `ProgresoSeccion` por cada `Seccion` del laboratorio,
    la primera `en_progreso` y el resto `bloqueada` (dominio.md §3). Todo
    ocurre en la misma transacción (HI-09): si la creación del Progreso
    falla, la aceptación también se revierte.
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

    def _validate(self, input_dto: AceptarInvitacionDTO) -> None:
        asignacion = self._asignacion_repository.get_by_id(input_dto.asignacion_id)
        if asignacion is None or asignacion.estudiante_id != input_dto.estudiante_id:
            raise NotFoundError(_ASIGNACION_NO_ENCONTRADA_MSG)
        if asignacion.estado != EstadoAsignacion.PENDIENTE:
            raise BusinessRuleViolationError(_YA_RESPONDIDA_MSG)

        self._asignacion = asignacion

    def _execute_domain_logic(
        self, input_dto: AceptarInvitacionDTO
    ) -> tuple[AsignacionResultDTO, list[DomainEvent]]:
        asignacion = self._asignacion
        asignacion.aceptar()
        actualizada = self._asignacion_repository.update(asignacion)

        progreso = self._progreso_repository.add(
            Progreso(asignacion_id=actualizada.id, estudiante_id=actualizada.estudiante_id)
        )
        secciones = self._laboratorio_repository.get_secciones(actualizada.laboratorio_id)
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
            id=actualizada.id,
            laboratorio_id=actualizada.laboratorio_id,
            estado=actualizada.estado.value,
        )
        event = AssignmentAccepted(
            asignacion_id=actualizada.id,
            estudiante_id=actualizada.estudiante_id,
            laboratorio_id=actualizada.laboratorio_id,
        )
        return result, [event]
