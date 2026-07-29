from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ForbiddenError, NotFoundError
from modules.users.application.dtos import HabilitarUsuarioDTO, UsuarioResultDTO
from modules.users.domain.repositories import IUserRepository

_USUARIO_NO_ENCONTRADO_MSG = "Usuario no encontrado."
_SIN_PERMISO_MSG = "Solo un administrador puede reactivar usuarios."


class HabilitarUsuarioUseCase(BaseUseCase[HabilitarUsuarioDTO, UsuarioResultDTO]):
    """HA-01, api.md §4 `POST /users/{id}/enable/`: reactiva una cuenta deshabilitada."""

    def __init__(self, unit_of_work, event_dispatcher, user_repository: IUserRepository):
        super().__init__(unit_of_work, event_dispatcher)
        self._user_repository = user_repository

    def _validate(self, input_dto: HabilitarUsuarioDTO) -> None:
        if input_dto.actor_rol != "administrador":
            raise ForbiddenError(_SIN_PERMISO_MSG)

        usuario = self._user_repository.get_by_id(input_dto.usuario_id)
        if usuario is None:
            raise NotFoundError(_USUARIO_NO_ENCONTRADO_MSG)

        self._usuario = usuario

    def _execute_domain_logic(
        self, input_dto: HabilitarUsuarioDTO
    ) -> tuple[UsuarioResultDTO, list[DomainEvent]]:
        usuario = self._usuario
        usuario.is_active = True
        actualizado = self._user_repository.update(usuario)

        result = UsuarioResultDTO(
            id=actualizado.id,
            email=str(actualizado.email),
            nombre_completo=actualizado.nombre_completo,
            rol=actualizado.rol.value,
            is_active=actualizado.is_active,
        )
        return result, []
