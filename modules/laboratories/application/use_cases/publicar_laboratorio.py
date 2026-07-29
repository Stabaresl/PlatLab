from modules.laboratories.application.dtos import LaboratorioResultDTO, PublicarLaboratorioDTO
from modules.laboratories.domain.events import LaboratoryPublished
from modules.laboratories.domain.exceptions import PublishValidationError
from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.laboratories.domain.value_objects import EstadoLaboratorio, TipoLaboratorio
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ForbiddenError, NotFoundError

_LAB_NO_ENCONTRADO_MSG = "Laboratorio no encontrado."
_SIN_PERMISO_MSG = "No tienes permiso para publicar este laboratorio."
_FLAGS_FALTANTES_MSG = "Todas las secciones con práctica necesitan una flag antes de publicar."


class PublicarLaboratorioUseCase(BaseUseCase[PublicarLaboratorioDTO, LaboratorioResultDTO]):
    """
    UC-04 paso 6 / E2, api.md §5 `POST /laboratories/{id}/publish/`:
    `borrador` -> `publicado`. Bloquea la publicación si alguna sección
    práctica no tiene flag asociada (indicando cuáles). Misma regla de
    propiedad que `EditarLaboratorioUseCase`.
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        laboratorio_repository: ILaboratorioRepository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._laboratorio_repository = laboratorio_repository

    def _validate(self, input_dto: PublicarLaboratorioDTO) -> None:
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

        secciones_practica = [
            s
            for s in self._laboratorio_repository.get_secciones(input_dto.laboratorio_id)
            if s.tiene_practica
        ]
        faltantes = [
            s
            for s in secciones_practica
            if self._laboratorio_repository.get_flag_by_seccion(s.id) is None
        ]
        if faltantes:
            raise PublishValidationError(
                _FLAGS_FALTANTES_MSG,
                details=[{"seccion_id": str(s.id), "titulo": s.titulo} for s in faltantes],
            )

        self._laboratorio = laboratorio

    def _execute_domain_logic(
        self, input_dto: PublicarLaboratorioDTO
    ) -> tuple[LaboratorioResultDTO, list[DomainEvent]]:
        laboratorio = self._laboratorio
        laboratorio.estado = EstadoLaboratorio.PUBLICADO
        actualizado = self._laboratorio_repository.update(laboratorio)

        result = LaboratorioResultDTO(
            id=actualizado.id,
            nombre=actualizado.nombre,
            estado=actualizado.estado.value,
            tipo=actualizado.tipo.value,
        )
        event = LaboratoryPublished(
            laboratorio_id=actualizado.id, instructor_id=actualizado.instructor_id
        )
        return result, [event]
