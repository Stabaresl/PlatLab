from modules.gamification.application.dtos import AvatarResultDTO, CambiarAvatarDTO
from modules.gamification.domain.entities import PerfilJugador, avatar_preset_valido
from modules.gamification.domain.repositories import IPerfilJugadorRepository
from modules.gamification.domain.value_objects import AvatarTipo
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ForbiddenError, ValidationError

_SIN_PERMISO_MSG = "Solo un estudiante puede elegir un avatar."
_PRESET_INVALIDO_MSG = "Ese avatar predeterminado no existe."


class CambiarAvatarUseCase(BaseUseCase[CambiarAvatarDTO, AvatarResultDTO]):
    """Elige uno de los avatares predeterminados (`AVATAR_PRESETS`) como identidad visual."""

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        perfil_repository: IPerfilJugadorRepository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._perfil_repository = perfil_repository

    def _validate(self, input_dto: CambiarAvatarDTO) -> None:
        if input_dto.actor_rol != "estudiante":
            raise ForbiddenError(_SIN_PERMISO_MSG)
        if not avatar_preset_valido(input_dto.preset_clave):
            raise ValidationError(_PRESET_INVALIDO_MSG)

    def _execute_domain_logic(
        self, input_dto: CambiarAvatarDTO
    ) -> tuple[AvatarResultDTO, list[DomainEvent]]:
        perfil = self._perfil_repository.get_by_estudiante(input_dto.actor_id)
        if perfil is None:
            perfil = self._perfil_repository.add(PerfilJugador(estudiante_id=input_dto.actor_id))

        perfil.avatar_tipo = AvatarTipo.PRESET
        perfil.avatar_valor = input_dto.preset_clave
        actualizado = self._perfil_repository.update(perfil)

        result = AvatarResultDTO(
            avatar_tipo=actualizado.avatar_tipo.value, avatar_valor=actualizado.avatar_valor
        )
        return result, []
