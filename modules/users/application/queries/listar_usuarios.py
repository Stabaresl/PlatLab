from modules.shared.domain.exceptions import ForbiddenError
from modules.users.application.dtos import ListarUsuariosDTO, UsuarioListItemDTO
from modules.users.domain.repositories import IUserRepository

_SIN_PERMISO_MSG = "Solo un administrador puede listar usuarios."


class ListarUsuariosQuery:
    """HA-01, api.md §4 `GET /users/?nombre=&rol=&activo=`."""

    def __init__(self, user_repository: IUserRepository):
        self._repo = user_repository

    def execute(self, input_dto: ListarUsuariosDTO) -> list[UsuarioListItemDTO]:
        return self.execute_paginado(input_dto, limit=None, offset=0)[0]

    def execute_paginado(
        self, input_dto: ListarUsuariosDTO, limit: int | None, offset: int
    ) -> tuple[list[UsuarioListItemDTO], int]:
        if input_dto.actor_rol != "administrador":
            raise ForbiddenError(_SIN_PERMISO_MSG)

        filtros = {"nombre": input_dto.nombre, "rol": input_dto.rol, "activo": input_dto.activo}
        usuarios = self._repo.find_all(**filtros, limit=limit, offset=offset)
        total = self._repo.contar(**filtros) if limit is not None else len(usuarios)
        return self._a_items(usuarios), total

    def _a_items(self, usuarios) -> list[UsuarioListItemDTO]:
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
