from modules.roadmap.application.dtos import NodoResultDTO, ReordenarNodoDTO
from modules.roadmap.domain.repositories import ICategoriaRoadmapRepository, INodoRoadmapRepository
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ForbiddenError, NotFoundError

_SIN_PERMISO_MSG = "Solo un administrador puede reordenar el roadmap."
_NODO_NO_ENCONTRADO_MSG = "Nodo de roadmap no encontrado."
_CATEGORIA_NO_ENCONTRADA_MSG = "Categoría de roadmap no encontrada."


class ReordenarNodoUseCase(BaseUseCase[ReordenarNodoDTO, NodoResultDTO]):
    """
    Mueve un nodo a una nueva posición — misma categoría (reordenar) o
    cruzando a otra (mover de pista). Reindexa ambos extremos afectados
    (`INodoRoadmapRepository.mover`).

    Importante: mover un nodo cambia retroactivamente qué prerequisitos
    hacen falta para desbloquear los laboratorios que quedan después de
    él en su categoría — un estudiante puede ver un laboratorio
    recién-bloqueado o recién-desbloqueado tras un reordenamiento. Es
    consecuencia esperada de que "prerequisito = nodo anterior en la
    misma pista" (ver `InscribirseRoadmapUseCase`), no un bug.
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        categoria_repository: ICategoriaRoadmapRepository,
        nodo_repository: INodoRoadmapRepository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._categoria_repository = categoria_repository
        self._nodo_repository = nodo_repository

    def _validate(self, input_dto: ReordenarNodoDTO) -> None:
        if input_dto.actor_rol != "administrador":
            raise ForbiddenError(_SIN_PERMISO_MSG)
        if self._nodo_repository.get_by_id(input_dto.nodo_id) is None:
            raise NotFoundError(_NODO_NO_ENCONTRADO_MSG)
        if self._categoria_repository.get_by_id(input_dto.categoria_id) is None:
            raise NotFoundError(_CATEGORIA_NO_ENCONTRADA_MSG)

    def _execute_domain_logic(
        self, input_dto: ReordenarNodoDTO
    ) -> tuple[NodoResultDTO, list[DomainEvent]]:
        nodo = self._nodo_repository.mover(
            nodo_id=input_dto.nodo_id,
            categoria_id=input_dto.categoria_id,
            posicion=input_dto.posicion,
        )
        result = NodoResultDTO(
            id=nodo.id,
            categoria_id=nodo.categoria_id,
            laboratorio_id=nodo.laboratorio_id,
            posicion=nodo.posicion,
        )
        return result, []
