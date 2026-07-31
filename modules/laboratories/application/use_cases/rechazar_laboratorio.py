from modules.laboratories.application.dtos import LaboratorioResultDTO, RechazarLaboratorioDTO
from modules.laboratories.domain.events import LaboratoryRejected
from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.laboratories.domain.value_objects import EstadoLaboratorio, TipoLaboratorio
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError

_LAB_NO_ENCONTRADO_MSG = "Laboratorio no encontrado."
_SIN_PERMISO_MSG = "Solo un administrador puede rechazar laboratorios."
_SOLO_PERSONALIZADO_MSG = "Solo un laboratorio personalizado pasa por este flujo de revisión."
_ESTADO_INVALIDO_MSG = "Solo un laboratorio en revisión se puede rechazar."
_MOTIVO_REQUERIDO_MSG = "Debes indicar el motivo del rechazo."


class RechazarLaboratorioUseCase(BaseUseCase[RechazarLaboratorioDTO, LaboratorioResultDTO]):
    """
    Admin, `en_revision` → `borrador` + `motivo_rechazo`. No existe un
    estado `rechazado` separado — el instructor ve el motivo, corrige, y
    vuelve a mandar a revisión (`SolicitarRevisionLaboratorioUseCase`,
    que limpia `motivo_rechazo`).
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        laboratorio_repository: ILaboratorioRepository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._laboratorio_repository = laboratorio_repository

    def _validate(self, input_dto: RechazarLaboratorioDTO) -> None:
        if input_dto.actor_rol != "administrador":
            raise ForbiddenError(_SIN_PERMISO_MSG)
        if not input_dto.motivo or not input_dto.motivo.strip():
            raise ValidationError(_MOTIVO_REQUERIDO_MSG)

        laboratorio = self._laboratorio_repository.get_by_id(input_dto.laboratorio_id)
        if laboratorio is None:
            raise NotFoundError(_LAB_NO_ENCONTRADO_MSG)
        if laboratorio.tipo != TipoLaboratorio.PERSONALIZADO:
            raise ForbiddenError(_SOLO_PERSONALIZADO_MSG)
        if laboratorio.estado != EstadoLaboratorio.EN_REVISION:
            raise ConflictError(_ESTADO_INVALIDO_MSG)

        self._laboratorio = laboratorio

    def _execute_domain_logic(
        self, input_dto: RechazarLaboratorioDTO
    ) -> tuple[LaboratorioResultDTO, list[DomainEvent]]:
        laboratorio = self._laboratorio
        laboratorio.estado = EstadoLaboratorio.BORRADOR
        laboratorio.motivo_rechazo = input_dto.motivo.strip()
        actualizado = self._laboratorio_repository.update(laboratorio)

        result = LaboratorioResultDTO(
            id=actualizado.id,
            nombre=actualizado.nombre,
            estado=actualizado.estado.value,
            tipo=actualizado.tipo.value,
        )
        event = LaboratoryRejected(
            laboratorio_id=actualizado.id,
            instructor_id=actualizado.instructor_id,
            admin_id=input_dto.actor_id,
            motivo=actualizado.motivo_rechazo,
        )
        return result, [event]
