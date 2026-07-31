from modules.gamification.application.dtos import EquiparTituloDTO, TituloDesbloqueadoResultDTO
from modules.gamification.domain.repositories import ITituloDesbloqueadoRepository
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ForbiddenError, NotFoundError

_SIN_PERMISO_MSG = "Solo un estudiante puede equipar un título."
_NO_ENCONTRADO_MSG = "No tenés ese título desbloqueado."


class EquiparTituloUseCase(BaseUseCase[EquiparTituloDTO, TituloDesbloqueadoResultDTO]):
    """Equipa un título ya desbloqueado — siempre un solo slot, desequipa cualquier otro."""

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        titulo_desbloqueado_repository: ITituloDesbloqueadoRepository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._titulo_desbloqueado_repository = titulo_desbloqueado_repository

    def _validate(self, input_dto: EquiparTituloDTO) -> None:
        if input_dto.actor_rol != "estudiante":
            raise ForbiddenError(_SIN_PERMISO_MSG)

        desbloqueo = self._titulo_desbloqueado_repository.get_by_id(
            input_dto.titulo_desbloqueado_id
        )
        if desbloqueo is None or desbloqueo.estudiante_id != input_dto.actor_id:
            raise NotFoundError(_NO_ENCONTRADO_MSG)

        self._desbloqueo = desbloqueo

    def _execute_domain_logic(
        self, input_dto: EquiparTituloDTO
    ) -> tuple[TituloDesbloqueadoResultDTO, list[DomainEvent]]:
        propios = self._titulo_desbloqueado_repository.find_por_estudiante(input_dto.actor_id)
        for otro in propios:
            if otro.id != self._desbloqueo.id and otro.equipado:
                otro.equipado = False
                self._titulo_desbloqueado_repository.update(otro)

        self._desbloqueo.equipado = True
        actualizado = self._titulo_desbloqueado_repository.update(self._desbloqueo)

        result = TituloDesbloqueadoResultDTO(
            id=actualizado.id, titulo_id=actualizado.titulo_id, equipado=actualizado.equipado
        )
        return result, []
