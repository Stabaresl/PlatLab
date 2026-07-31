from modules.gamification.application.dtos import CosmeticoDesbloqueadoResultDTO, QuitarCosmeticoDTO
from modules.gamification.domain.repositories import ICosmeticoDesbloqueadoRepository
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ForbiddenError, NotFoundError

_SIN_PERMISO_MSG = "Solo un estudiante puede quitarse un cosmético."
_NO_ENCONTRADO_MSG = "No tenés ese cosmético desbloqueado."


class QuitarCosmeticoUseCase(BaseUseCase[QuitarCosmeticoDTO, CosmeticoDesbloqueadoResultDTO]):
    """Desequipa un cosmético (vuelve al inventario, sin perder el desbloqueo)."""

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        cosmetico_desbloqueado_repository: ICosmeticoDesbloqueadoRepository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._cosmetico_desbloqueado_repository = cosmetico_desbloqueado_repository

    def _validate(self, input_dto: QuitarCosmeticoDTO) -> None:
        if input_dto.actor_rol != "estudiante":
            raise ForbiddenError(_SIN_PERMISO_MSG)

        desbloqueo = self._cosmetico_desbloqueado_repository.get_by_id(
            input_dto.cosmetico_desbloqueado_id
        )
        if desbloqueo is None or desbloqueo.estudiante_id != input_dto.actor_id:
            raise NotFoundError(_NO_ENCONTRADO_MSG)

        self._desbloqueo = desbloqueo

    def _execute_domain_logic(
        self, input_dto: QuitarCosmeticoDTO
    ) -> tuple[CosmeticoDesbloqueadoResultDTO, list[DomainEvent]]:
        self._desbloqueo.equipado = False
        actualizado = self._cosmetico_desbloqueado_repository.update(self._desbloqueo)

        result = CosmeticoDesbloqueadoResultDTO(
            id=actualizado.id, cosmetico_id=actualizado.cosmetico_id, equipado=actualizado.equipado
        )
        return result, []
