import uuid

from modules.shared.domain.exceptions import ForbiddenError, NotFoundError
from modules.users.application.dtos import UsuarioResultDTO
from modules.users.domain.repositories import IUserRepository

_SIN_PERMISO_MSG = "Solo un administrador puede ver el detalle de otros usuarios."
_USUARIO_NO_ENCONTRADO_MSG = "Usuario no encontrado."


class ObtenerUsuarioQuery:
    """HA-01, api.md §4 `GET /users/{id}/` — detalle de usuario, solo Admin."""

    def __init__(self, user_repository: IUserRepository):
        self._repo = user_repository

    def execute(self, usuario_id: uuid.UUID, actor_rol: str) -> UsuarioResultDTO:
        if actor_rol != "administrador":
            raise ForbiddenError(_SIN_PERMISO_MSG)

        usuario = self._repo.get_by_id(usuario_id)
        if usuario is None:
            raise NotFoundError(_USUARIO_NO_ENCONTRADO_MSG)

        return UsuarioResultDTO(
            id=usuario.id,
            email=str(usuario.email),
            nombre_completo=usuario.nombre_completo,
            rol=usuario.rol.value,
            is_active=usuario.is_active,
        )
