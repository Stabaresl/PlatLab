from modules.laboratories.application.dtos import CrearExamenDTO, ExamenResultDTO
from modules.laboratories.domain.entities import Examen
from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.laboratories.domain.value_objects import TipoLaboratorio
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ConflictError, ForbiddenError, NotFoundError

_LAB_NO_ENCONTRADO_MSG = "Laboratorio no encontrado."
_SIN_PERMISO_MSG = "No tienes permiso para editar este laboratorio."
_EXAMEN_YA_EXISTE_MSG = "Este laboratorio ya tiene un examen."


class CrearExamenUseCase(BaseUseCase[CrearExamenDTO, ExamenResultDTO]):
    """
    HE-09/HI-08, api.md §5 `POST /laboratories/{id}/exam/`: crea el
    examen final de un laboratorio (relación 1:1). Misma regla de
    propiedad que `CrearSeccionUseCase` (seguridad.md §1).
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        laboratorio_repository: ILaboratorioRepository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._laboratorio_repository = laboratorio_repository

    def _validate(self, input_dto: CrearExamenDTO) -> None:
        laboratorio = self._laboratorio_repository.get_by_id(input_dto.laboratorio_id)
        if laboratorio is None:
            raise NotFoundError(_LAB_NO_ENCONTRADO_MSG)

        if input_dto.actor_rol == "instructor":
            if laboratorio.instructor_id != input_dto.actor_id:
                raise ForbiddenError(_SIN_PERMISO_MSG)
        elif input_dto.actor_rol == "administrador":
            if laboratorio.tipo != TipoLaboratorio.PREDETERMINADO:
                raise ForbiddenError(_SIN_PERMISO_MSG)
        else:
            raise ForbiddenError(_SIN_PERMISO_MSG)

        if self._laboratorio_repository.get_examen_by_laboratorio(input_dto.laboratorio_id):
            raise ConflictError(_EXAMEN_YA_EXISTE_MSG)

    def _execute_domain_logic(
        self, input_dto: CrearExamenDTO
    ) -> tuple[ExamenResultDTO, list[DomainEvent]]:
        examen = Examen(laboratorio_id=input_dto.laboratorio_id)
        guardado = self._laboratorio_repository.add_examen(examen)

        result = ExamenResultDTO(id=guardado.id, laboratorio_id=guardado.laboratorio_id)
        return result, []
