from modules.roadmap.application.dtos import CategoriaResultDTO
from modules.roadmap.domain.repositories import ICategoriaRoadmapRepository
from modules.shared.domain.exceptions import ForbiddenError

_SIN_PERMISO_MSG = "Solo un administrador puede ver el listado de categorías del roadmap."


class ListarCategoriasQuery:
    """Panel admin: listado plano de categorías, para el selector al agregar un nodo."""

    def __init__(self, categoria_repository: ICategoriaRoadmapRepository):
        self._categoria_repository = categoria_repository

    def execute(self, actor_rol: str) -> list[CategoriaResultDTO]:
        if actor_rol != "administrador":
            raise ForbiddenError(_SIN_PERMISO_MSG)
        return [
            CategoriaResultDTO(id=c.id, nombre=c.nombre, orden=c.orden)
            for c in self._categoria_repository.find_todas()
        ]
