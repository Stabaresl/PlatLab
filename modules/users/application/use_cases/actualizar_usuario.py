from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ForbiddenError, NotFoundError, ValidationError
from modules.users.application.dtos import ActualizarUsuarioDTO, UsuarioResultDTO
from modules.users.domain.exceptions import SelfDisableNotAllowedError
from modules.users.domain.repositories import IUserRepository
from modules.users.domain.value_objects import Rol

_USUARIO_NO_ENCONTRADO_MSG = "Usuario no encontrado."
_SIN_PERMISO_MSG = "Solo un administrador puede editar usuarios."
_ROL_INVALIDO_MSG = "Rol inválido."
_AUTO_DESTITUCION_MSG = "No puedes quitarte tu propio rol de administrador."


class ActualizarUsuarioUseCase(BaseUseCase[ActualizarUsuarioDTO, UsuarioResultDTO]):
    """
    HA-01, UC-08, api.md §4 `PATCH /users/{id}/`: edita datos/rol. Un
    Administrador nunca puede quitarse su propio rol de administrador
    (UC-08 E1) — la misma regla de auto-protección que
    `DeshabilitarUsuarioUseCase`.
    """

    def __init__(self, unit_of_work, event_dispatcher, user_repository: IUserRepository):
        super().__init__(unit_of_work, event_dispatcher)
        self._user_repository = user_repository

    def _validate(self, input_dto: ActualizarUsuarioDTO) -> None:
        if input_dto.actor_rol != "administrador":
            raise ForbiddenError(_SIN_PERMISO_MSG)

        usuario = self._user_repository.get_by_id(input_dto.usuario_id)
        if usuario is None:
            raise NotFoundError(_USUARIO_NO_ENCONTRADO_MSG)

        if input_dto.rol is not None:
            try:
                nuevo_rol = Rol(input_dto.rol)
            except ValueError as exc:
                raise ValidationError(_ROL_INVALIDO_MSG) from exc

            if (
                usuario.id == input_dto.actor_id
                and usuario.rol == Rol.ADMINISTRADOR
                and nuevo_rol != Rol.ADMINISTRADOR
            ):
                raise SelfDisableNotAllowedError(_AUTO_DESTITUCION_MSG)

        self._usuario = usuario

    def _execute_domain_logic(
        self, input_dto: ActualizarUsuarioDTO
    ) -> tuple[UsuarioResultDTO, list[DomainEvent]]:
        usuario = self._usuario
        if input_dto.nombre_completo is not None:
            usuario.nombre_completo = input_dto.nombre_completo
        if input_dto.username is not None:
            usuario.username = input_dto.username
        if input_dto.rol is not None:
            usuario.rol = Rol(input_dto.rol)

        actualizado = self._user_repository.update(usuario)

        result = UsuarioResultDTO(
            id=actualizado.id,
            email=str(actualizado.email),
            nombre_completo=actualizado.nombre_completo,
            rol=actualizado.rol.value,
            is_active=actualizado.is_active,
        )
        return result, []
