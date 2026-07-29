from modules.assignments.application.dtos import AsignacionResultDTO, RechazarInvitacionDTO
from modules.assignments.domain.events import AssignmentRejected
from modules.assignments.domain.repositories import IAsignacionRepository
from modules.assignments.domain.value_objects import EstadoAsignacion
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import BusinessRuleViolationError, NotFoundError

_ASIGNACION_NO_ENCONTRADA_MSG = "Invitación no encontrada."
_YA_RESPONDIDA_MSG = "Esta invitación ya fue respondida."


class RechazarInvitacionUseCase(BaseUseCase[RechazarInvitacionDTO, AsignacionResultDTO]):
    """UC-06 A1, api.md §6 `POST /assignments/invitations/{id}/reject/`."""

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        asignacion_repository: IAsignacionRepository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._asignacion_repository = asignacion_repository

    def _validate(self, input_dto: RechazarInvitacionDTO) -> None:
        asignacion = self._asignacion_repository.get_by_id(input_dto.asignacion_id)
        if asignacion is None or asignacion.estudiante_id != input_dto.estudiante_id:
            raise NotFoundError(_ASIGNACION_NO_ENCONTRADA_MSG)
        if asignacion.estado != EstadoAsignacion.PENDIENTE:
            raise BusinessRuleViolationError(_YA_RESPONDIDA_MSG)

        self._asignacion = asignacion

    def _execute_domain_logic(
        self, input_dto: RechazarInvitacionDTO
    ) -> tuple[AsignacionResultDTO, list[DomainEvent]]:
        asignacion = self._asignacion
        asignacion.rechazar()
        actualizada = self._asignacion_repository.update(asignacion)

        result = AsignacionResultDTO(
            id=actualizada.id,
            laboratorio_id=actualizada.laboratorio_id,
            estado=actualizada.estado.value,
        )
        event = AssignmentRejected(
            asignacion_id=actualizada.id, estudiante_id=actualizada.estudiante_id
        )
        return result, [event]
