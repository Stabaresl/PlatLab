from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.laboratories.domain.value_objects import EstadoLaboratorio, TipoLaboratorio
from modules.roadmap.application.dtos import AgregarNodoDTO, NodoResultDTO
from modules.roadmap.domain.repositories import ICategoriaRoadmapRepository, INodoRoadmapRepository
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ConflictError, ForbiddenError, NotFoundError

_SIN_PERMISO_MSG = "Solo un administrador puede agregar laboratorios al roadmap."
_CATEGORIA_NO_ENCONTRADA_MSG = "Categoría de roadmap no encontrada."
_LAB_NO_ENCONTRADO_MSG = "Laboratorio no encontrado."
_SOLO_PREDETERMINADO_MSG = (
    "Solo un laboratorio predeterminado (creado por un administrador) puede ir en el roadmap — "
    "los personalizados de instructores se asignan por invitación o catálogo, no por roadmap."
)
_DEBE_ESTAR_PUBLICADO_MSG = "Solo un laboratorio publicado se puede agregar al roadmap."
_YA_EN_ROADMAP_MSG = "Este laboratorio ya está en el roadmap — quitalo de su nodo actual antes de reasignarlo."


class AgregarNodoUseCase(BaseUseCase[AgregarNodoDTO, NodoResultDTO]):
    """
    Un admin arrastra un laboratorio propio (predeterminado, publicado)
    hacia una categoría del roadmap en una posición puntual — inserta el
    nodo ahí, desplazando los existentes (`INodoRoadmapRepository.insertar_en_posicion`).
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        categoria_repository: ICategoriaRoadmapRepository,
        nodo_repository: INodoRoadmapRepository,
        laboratorio_repository: ILaboratorioRepository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._categoria_repository = categoria_repository
        self._nodo_repository = nodo_repository
        self._laboratorio_repository = laboratorio_repository

    def _validate(self, input_dto: AgregarNodoDTO) -> None:
        if input_dto.actor_rol != "administrador":
            raise ForbiddenError(_SIN_PERMISO_MSG)

        if self._categoria_repository.get_by_id(input_dto.categoria_id) is None:
            raise NotFoundError(_CATEGORIA_NO_ENCONTRADA_MSG)

        laboratorio = self._laboratorio_repository.get_by_id(input_dto.laboratorio_id)
        if laboratorio is None:
            raise NotFoundError(_LAB_NO_ENCONTRADO_MSG)
        if laboratorio.tipo != TipoLaboratorio.PREDETERMINADO:
            raise ForbiddenError(_SOLO_PREDETERMINADO_MSG)
        if laboratorio.estado != EstadoLaboratorio.PUBLICADO:
            raise ConflictError(_DEBE_ESTAR_PUBLICADO_MSG)

        if self._nodo_repository.get_by_laboratorio(input_dto.laboratorio_id) is not None:
            raise ConflictError(_YA_EN_ROADMAP_MSG)

    def _execute_domain_logic(
        self, input_dto: AgregarNodoDTO
    ) -> tuple[NodoResultDTO, list[DomainEvent]]:
        nodo = self._nodo_repository.insertar_en_posicion(
            categoria_id=input_dto.categoria_id,
            laboratorio_id=input_dto.laboratorio_id,
            posicion=input_dto.posicion,
        )
        result = NodoResultDTO(
            id=nodo.id,
            categoria_id=nodo.categoria_id,
            laboratorio_id=nodo.laboratorio_id,
            posicion=nodo.posicion,
        )
        return result, []
