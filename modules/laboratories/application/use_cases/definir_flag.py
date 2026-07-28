from django.contrib.auth.hashers import make_password

from modules.laboratories.application.dtos import DefinirFlagDTO, DefinirFlagResultDTO
from modules.laboratories.domain.entities import Flag
from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.laboratories.domain.value_objects import AyudaProgresiva
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import (
    BusinessRuleViolationError,
    ForbiddenError,
    NotFoundError,
)

_LAB_NO_ENCONTRADO_MSG = "Laboratorio no encontrado."
_SECCION_NO_ENCONTRADA_MSG = "Sección no encontrada."
_SIN_PERMISO_MSG = "No tienes permiso para editar este laboratorio."
_SIN_PRACTICA_MSG = "Solo las secciones con práctica pueden tener flag."


class DefinirFlagUseCase(BaseUseCase[DefinirFlagDTO, DefinirFlagResultDTO]):
    """
    HE-05 / api.md §5 `PUT .../flag/`: define o actualiza (upsert, 1:1)
    la flag de una sección práctica. Solo el instructor dueño del
    laboratorio o un Administrador pueden hacerlo (seguridad.md §1). El
    valor real nunca se persiste — solo su hash (RNF de seguridad.md §4,
    misma utilidad que `password_hash` de User).
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        laboratorio_repository: ILaboratorioRepository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._laboratorio_repository = laboratorio_repository

    def _validate(self, input_dto: DefinirFlagDTO) -> None:
        if input_dto.actor_rol not in ("instructor", "administrador"):
            raise ForbiddenError(_SIN_PERMISO_MSG)

        laboratorio = self._laboratorio_repository.get_by_id(input_dto.laboratorio_id)
        if laboratorio is None:
            raise NotFoundError(_LAB_NO_ENCONTRADO_MSG)

        if input_dto.actor_rol == "instructor" and laboratorio.instructor_id != input_dto.actor_id:
            raise ForbiddenError(_SIN_PERMISO_MSG)

        secciones = self._laboratorio_repository.get_secciones(input_dto.laboratorio_id)
        seccion = next((s for s in secciones if s.id == input_dto.seccion_id), None)
        if seccion is None:
            raise NotFoundError(_SECCION_NO_ENCONTRADA_MSG)
        if not seccion.tiene_practica:
            raise BusinessRuleViolationError(_SIN_PRACTICA_MSG)

    def _execute_domain_logic(
        self, input_dto: DefinirFlagDTO
    ) -> tuple[DefinirFlagResultDTO, list[DomainEvent]]:
        flag = Flag(
            seccion_id=input_dto.seccion_id,
            hash=make_password(input_dto.valor),
            ayuda=AyudaProgresiva(pista=input_dto.pista, paso_a_paso=input_dto.paso_a_paso),
        )
        guardada = self._laboratorio_repository.save_flag(flag)

        result = DefinirFlagResultDTO(id=guardada.id, seccion_id=guardada.seccion_id)
        return result, []
