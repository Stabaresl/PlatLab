from modules.laboratories.application.dtos import (
    CambiarVisibilidadCatalogoDTO,
    LaboratorioResultDTO,
)
from modules.laboratories.domain.events import LaboratoryCatalogVisibilityChanged
from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.laboratories.domain.value_objects import EstadoLaboratorio, TipoLaboratorio
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ConflictError, ForbiddenError, NotFoundError

_LAB_NO_ENCONTRADO_MSG = "Laboratorio no encontrado."
_SIN_PERMISO_MSG = "Solo el instructor dueño del laboratorio o un administrador pueden cambiar su visibilidad en el catálogo."
_SOLO_PERSONALIZADO_MSG = (
    "Un laboratorio predeterminado ya es público — la visibilidad de catálogo solo "
    "aplica a laboratorios personalizados."
)
_DEBE_ESTAR_PUBLICADO_MSG = (
    "Solo un laboratorio publicado se puede exponer en el catálogo público."
)


class CambiarVisibilidadCatalogoUseCase(
    BaseUseCase[CambiarVisibilidadCatalogoDTO, LaboratorioResultDTO]
):
    """
    Opt-in de un `personalizado` ya `publicado` al catálogo público (HV-02
    ampliado): por defecto, un `personalizado` solo se asigna por
    invitación directa del instructor (`InvitarEstudiantesUseCase`) — este
    caso de uso permite que su instructor dueño (o un admin, con la misma
    potestad que tiene sobre cualquier laboratorio) decida además hacerlo
    autoinscribible desde `/laboratorios`, sin perder la invitación directa
    como mecanismo alternativo.
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        laboratorio_repository: ILaboratorioRepository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._laboratorio_repository = laboratorio_repository

    def _validate(self, input_dto: CambiarVisibilidadCatalogoDTO) -> None:
        laboratorio = self._laboratorio_repository.get_by_id(input_dto.laboratorio_id)
        if laboratorio is None:
            raise NotFoundError(_LAB_NO_ENCONTRADO_MSG)

        es_dueno = (
            input_dto.actor_rol == "instructor"
            and laboratorio.instructor_id == input_dto.actor_id
        )
        es_admin = input_dto.actor_rol == "administrador"
        if not (es_dueno or es_admin):
            raise ForbiddenError(_SIN_PERMISO_MSG)

        if laboratorio.tipo != TipoLaboratorio.PERSONALIZADO:
            raise ForbiddenError(_SOLO_PERSONALIZADO_MSG)
        if laboratorio.estado != EstadoLaboratorio.PUBLICADO:
            raise ConflictError(_DEBE_ESTAR_PUBLICADO_MSG)

        self._laboratorio = laboratorio

    def _execute_domain_logic(
        self, input_dto: CambiarVisibilidadCatalogoDTO
    ) -> tuple[LaboratorioResultDTO, list[DomainEvent]]:
        laboratorio = self._laboratorio
        laboratorio.visible_en_catalogo = input_dto.visible
        actualizado = self._laboratorio_repository.update(laboratorio)

        result = LaboratorioResultDTO(
            id=actualizado.id,
            nombre=actualizado.nombre,
            estado=actualizado.estado.value,
            tipo=actualizado.tipo.value,
            visible_en_catalogo=actualizado.visible_en_catalogo,
        )
        event = LaboratoryCatalogVisibilityChanged(
            laboratorio_id=actualizado.id,
            instructor_id=actualizado.instructor_id,
            actor_id=input_dto.actor_id,
            visible=actualizado.visible_en_catalogo,
        )
        return result, [event]
