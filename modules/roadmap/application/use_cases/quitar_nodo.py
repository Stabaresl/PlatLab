from modules.roadmap.application.dtos import QuitarNodoDTO
from modules.roadmap.domain.repositories import INodoRoadmapRepository
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ForbiddenError, NotFoundError

_SIN_PERMISO_MSG = "Solo un administrador puede quitar un laboratorio del roadmap."
_NODO_NO_ENCONTRADO_MSG = "Nodo de roadmap no encontrado."


class QuitarNodoUseCase(BaseUseCase[QuitarNodoDTO, None]):
    """
    Quita un laboratorio del roadmap (vuelve a la pool de "sin asignar")
    y cierra el hueco de posiciones en su categoría
    (`INodoRoadmapRepository.quitar`). No borra el laboratorio ni afecta
    inscripciones/progreso ya existentes de estudiantes.
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        nodo_repository: INodoRoadmapRepository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._nodo_repository = nodo_repository

    def _validate(self, input_dto: QuitarNodoDTO) -> None:
        if input_dto.actor_rol != "administrador":
            raise ForbiddenError(_SIN_PERMISO_MSG)
        if self._nodo_repository.get_by_id(input_dto.nodo_id) is None:
            raise NotFoundError(_NODO_NO_ENCONTRADO_MSG)

    def _execute_domain_logic(
        self, input_dto: QuitarNodoDTO
    ) -> tuple[None, list[DomainEvent]]:
        self._nodo_repository.quitar(input_dto.nodo_id)
        return None, []
