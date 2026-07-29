from modules.shared.domain.exceptions import ForbiddenError
from modules.users.application.dtos import ListarUsuariosDTO, UsuarioListItemDTO
from modules.users.domain.repositories import IUserRepository

_SIN_PERMISO_MSG = "Solo un administrador puede listar usuarios."


class ListarUsuariosQuery:
    """HA-01, api.md §4 `GET /users/?nombre=&rol=&activo=`."""

    def __init__(self, user_repository: IUserRepository):
        self._repo = user_repository

    def execute(self, input_dto: ListarUsuariosDTO) -> list[UsuarioListItemDTO]:
        if input_dto.actor_rol != "administrador":
            raise ForbiddenError(_SIN_PERMISO_MSG)

        usuarios = self._repo.find_all(
            nombre=input_dto.nombre, rol=input_dto.rol, activo=input_dto.activo
        )
        return [
            UsuarioListItemDTO(
                id=u.id,
                email=str(u.email),
                nombre_completo=u.nombre_completo,
                rol=u.rol.value,
                is_active=u.is_active,
            )
            for u in usuarios
        ]
