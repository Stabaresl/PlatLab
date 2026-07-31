from modules.roadmap.application.dtos import CategoriaResultDTO, CrearCategoriaDTO
from modules.roadmap.domain.entities import CategoriaRoadmap
from modules.roadmap.domain.repositories import ICategoriaRoadmapRepository
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ConflictError, ForbiddenError, ValidationError

_SIN_PERMISO_MSG = "Solo un administrador puede crear categorías de roadmap."
_NOMBRE_VACIO_MSG = "El nombre de la categoría no puede estar vacío."
_NOMBRE_DUPLICADO_MSG = "Ya existe una categoría de roadmap con ese nombre."


class CrearCategoriaUseCase(BaseUseCase[CrearCategoriaDTO, CategoriaResultDTO]):
    """`POST /roadmap/categorias/` — un admin crea una pista nueva del roadmap."""

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        categoria_repository: ICategoriaRoadmapRepository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._categoria_repository = categoria_repository

    def _validate(self, input_dto: CrearCategoriaDTO) -> None:
        if input_dto.actor_rol != "administrador":
            raise ForbiddenError(_SIN_PERMISO_MSG)
        if not input_dto.nombre.strip():
            raise ValidationError(_NOMBRE_VACIO_MSG)
        if self._categoria_repository.get_by_nombre(input_dto.nombre.strip()) is not None:
            raise ConflictError(_NOMBRE_DUPLICADO_MSG)

    def _execute_domain_logic(
        self, input_dto: CrearCategoriaDTO
    ) -> tuple[CategoriaResultDTO, list[DomainEvent]]:
        orden = self._categoria_repository.siguiente_orden()
        categoria = self._categoria_repository.add(
            CategoriaRoadmap(nombre=input_dto.nombre.strip(), orden=orden)
        )
        result = CategoriaResultDTO(id=categoria.id, nombre=categoria.nombre, orden=categoria.orden)
        return result, []
