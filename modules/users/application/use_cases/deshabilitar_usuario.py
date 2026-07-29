from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ForbiddenError, NotFoundError
from modules.users.application.dtos import DeshabilitarUsuarioDTO, UsuarioResultDTO
from modules.users.domain.exceptions import SelfDisableNotAllowedError
from modules.users.domain.repositories import IUserRepository

_USUARIO_NO_ENCONTRADO_MSG = "Usuario no encontrado."
_SIN_PERMISO_MSG = "Solo un administrador puede deshabilitar usuarios."
_AUTO_DESHABILITACION_MSG = "No puedes deshabilitar tu propia cuenta."


class DeshabilitarUsuarioUseCase(BaseUseCase[DeshabilitarUsuarioDTO, UsuarioResultDTO]):
    """
    HA-01, UC-08 A1/E1, api.md §4 `POST /users/{id}/disable/`:
    soft-delete (`is_active=False`) — no borra histórico de progreso ni
    laboratorios creados. Un administrador nunca puede deshabilitarse a
    sí mismo (previene bloqueo total del sistema).
    """

    def __init__(self, unit_of_work, event_dispatcher, user_repository: IUserRepository):
        super().__init__(unit_of_work, event_dispatcher)
        self._user_repository = user_repository

    def _validate(self, input_dto: DeshabilitarUsuarioDTO) -> None:
        if input_dto.actor_rol != "administrador":
            raise ForbiddenError(_SIN_PERMISO_MSG)

        usuario = self._user_repository.get_by_id(input_dto.usuario_id)
        if usuario is None:
            raise NotFoundError(_USUARIO_NO_ENCONTRADO_MSG)
        if usuario.id == input_dto.actor_id:
            raise SelfDisableNotAllowedError(_AUTO_DESHABILITACION_MSG)

        self._usuario = usuario

    def _execute_domain_logic(
        self, input_dto: DeshabilitarUsuarioDTO
    ) -> tuple[UsuarioResultDTO, list[DomainEvent]]:
        usuario = self._usuario
        usuario.is_active = False
        actualizado = self._user_repository.update(usuario)

        result = UsuarioResultDTO(
            id=actualizado.id,
            email=str(actualizado.email),
            nombre_completo=actualizado.nombre_completo,
            rol=actualizado.rol.value,
            is_active=actualizado.is_active,
        )
        return result, []
