from modules.laboratories.application.dtos import AprobarLaboratorioDTO, LaboratorioResultDTO
from modules.laboratories.domain.events import LaboratoryApproved
from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.laboratories.domain.services import validar_laboratorio_publicable
from modules.laboratories.domain.value_objects import EstadoLaboratorio, TipoLaboratorio
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ConflictError, ForbiddenError, NotFoundError

_LAB_NO_ENCONTRADO_MSG = "Laboratorio no encontrado."
_SIN_PERMISO_MSG = "Solo un administrador puede aprobar laboratorios."
_SOLO_PERSONALIZADO_MSG = "Solo un laboratorio personalizado pasa por este flujo de aprobación."
_ESTADO_INVALIDO_MSG = "Solo un laboratorio en revisión se puede aprobar."


class AprobarLaboratorioUseCase(BaseUseCase[AprobarLaboratorioDTO, LaboratorioResultDTO]):
    """Admin, `en_revision` → `publicado`. Cierra el flujo de revisión que abre `SolicitarRevisionLaboratorioUseCase`."""

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        laboratorio_repository: ILaboratorioRepository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._laboratorio_repository = laboratorio_repository

    def _validate(self, input_dto: AprobarLaboratorioDTO) -> None:
        if input_dto.actor_rol != "administrador":
            raise ForbiddenError(_SIN_PERMISO_MSG)

        laboratorio = self._laboratorio_repository.get_by_id(input_dto.laboratorio_id)
        if laboratorio is None:
            raise NotFoundError(_LAB_NO_ENCONTRADO_MSG)
        if laboratorio.tipo != TipoLaboratorio.PERSONALIZADO:
            raise ForbiddenError(_SOLO_PERSONALIZADO_MSG)
        if laboratorio.estado != EstadoLaboratorio.EN_REVISION:
            raise ConflictError(_ESTADO_INVALIDO_MSG)

        secciones = self._laboratorio_repository.get_secciones(input_dto.laboratorio_id)
        flags_por_seccion = {
            s.id: self._laboratorio_repository.get_flag_by_seccion(s.id) for s in secciones
        }
        validar_laboratorio_publicable(secciones, flags_por_seccion)

        self._laboratorio = laboratorio

    def _execute_domain_logic(
        self, input_dto: AprobarLaboratorioDTO
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
        event = LaboratoryApproved(
            laboratorio_id=actualizado.id,
            instructor_id=actualizado.instructor_id,
            admin_id=input_dto.actor_id,
        )
        return result, [event]
