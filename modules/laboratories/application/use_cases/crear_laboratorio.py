from modules.laboratories.application.dtos import CrearLaboratorioDTO, LaboratorioResultDTO
from modules.laboratories.domain.entities import Laboratorio
from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.laboratories.domain.value_objects import (
    EstadoLaboratorio,
    NivelDificultad,
    TipoLaboratorio,
)
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ForbiddenError, ValidationError

_SIN_PERMISO_MSG = "No tienes permiso para crear laboratorios."
_DIFICULTAD_INVALIDA_MSG = "Nivel de dificultad inválido."

_TIPO_POR_ROL = {
    "instructor": TipoLaboratorio.PERSONALIZADO,
    "administrador": TipoLaboratorio.PREDETERMINADO,
}


class CrearLaboratorioUseCase(BaseUseCase[CrearLaboratorioDTO, LaboratorioResultDTO]):
    """
    UC-04, api.md §5 `POST /laboratories/`: crea un laboratorio en
    estado `borrador`. `tipo` se infiere del rol del actor — un
    Instructor siempre crea `personalizado` (dueño = él mismo); un
    Administrador crea `predeterminado` (sin dueño instructor).
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        laboratorio_repository: ILaboratorioRepository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._laboratorio_repository = laboratorio_repository

    def _validate(self, input_dto: CrearLaboratorioDTO) -> None:
        if input_dto.actor_rol not in _TIPO_POR_ROL:
            raise ForbiddenError(_SIN_PERMISO_MSG)
        try:
            NivelDificultad(input_dto.nivel_dificultad)
        except ValueError as exc:
            raise ValidationError(_DIFICULTAD_INVALIDA_MSG) from exc

    def _execute_domain_logic(
        self, input_dto: CrearLaboratorioDTO
    ) -> tuple[LaboratorioResultDTO, list[DomainEvent]]:
        tipo = _TIPO_POR_ROL[input_dto.actor_rol]
        laboratorio = Laboratorio(
            nombre=input_dto.nombre,
            descripcion=input_dto.descripcion,
            nivel_dificultad=NivelDificultad(input_dto.nivel_dificultad),
            estado=EstadoLaboratorio.BORRADOR,
            tipo=tipo,
            temas=input_dto.temas,
            instructor_id=(
                input_dto.actor_id if tipo == TipoLaboratorio.PERSONALIZADO else None
            ),
        )
        guardado = self._laboratorio_repository.add(laboratorio)

        result = LaboratorioResultDTO(
            id=guardado.id,
            nombre=guardado.nombre,
            estado=guardado.estado.value,
            tipo=guardado.tipo.value,
        )
        return result, []
