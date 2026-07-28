from modules.laboratories.application.dtos import EditarLaboratorioDTO, LaboratorioResultDTO
from modules.laboratories.domain.exceptions import CannotEditPredeterminadoError
from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.laboratories.domain.value_objects import NivelDificultad, TipoLaboratorio
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ForbiddenError, NotFoundError, ValidationError

_LAB_NO_ENCONTRADO_MSG = "Laboratorio no encontrado."
_SIN_PERMISO_MSG = "No tienes permiso para editar este laboratorio."
_DIFICULTAD_INVALIDA_MSG = "Nivel de dificultad inválido."


class EditarLaboratorioUseCase(BaseUseCase[EditarLaboratorioDTO, LaboratorioResultDTO]):
    """
    UC-05 E1, api.md §5 `PATCH /laboratories/{id}/`: edita metadatos
    (nombre/descripción/dificultad/temas). Un Instructor solo edita sus
    propios `personalizado`. Un Administrador solo edita
    `predeterminado` (seguridad.md §1 — misma regla de propiedad que
    `DefinirFlagUseCase`).
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        laboratorio_repository: ILaboratorioRepository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._laboratorio_repository = laboratorio_repository

    def _validate(self, input_dto: EditarLaboratorioDTO) -> None:
        laboratorio = self._laboratorio_repository.get_by_id(input_dto.laboratorio_id)
        if laboratorio is None:
            raise NotFoundError(_LAB_NO_ENCONTRADO_MSG)

        if input_dto.actor_rol == "instructor":
            if laboratorio.tipo == TipoLaboratorio.PREDETERMINADO:
                raise CannotEditPredeterminadoError(_SIN_PERMISO_MSG)
            if laboratorio.instructor_id != input_dto.actor_id:
                raise ForbiddenError(_SIN_PERMISO_MSG)
        elif input_dto.actor_rol == "administrador":
            if laboratorio.tipo != TipoLaboratorio.PREDETERMINADO:
                raise ForbiddenError(_SIN_PERMISO_MSG)
        else:
            raise ForbiddenError(_SIN_PERMISO_MSG)

        if input_dto.nivel_dificultad is not None:
            try:
                NivelDificultad(input_dto.nivel_dificultad)
            except ValueError as exc:
                raise ValidationError(_DIFICULTAD_INVALIDA_MSG) from exc

        self._laboratorio = laboratorio

    def _execute_domain_logic(
        self, input_dto: EditarLaboratorioDTO
    ) -> tuple[LaboratorioResultDTO, list[DomainEvent]]:
        laboratorio = self._laboratorio
        if input_dto.nombre is not None:
            laboratorio.nombre = input_dto.nombre
        if input_dto.descripcion is not None:
            laboratorio.descripcion = input_dto.descripcion
        if input_dto.nivel_dificultad is not None:
            laboratorio.nivel_dificultad = NivelDificultad(input_dto.nivel_dificultad)
        if input_dto.temas is not None:
            laboratorio.temas = input_dto.temas

        actualizado = self._laboratorio_repository.update(laboratorio)

        result = LaboratorioResultDTO(
            id=actualizado.id,
            nombre=actualizado.nombre,
            estado=actualizado.estado.value,
            tipo=actualizado.tipo.value,
        )
        return result, []
