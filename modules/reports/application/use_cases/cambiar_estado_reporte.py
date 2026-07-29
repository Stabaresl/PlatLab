from modules.reports.application.dtos import CambiarEstadoReporteDTO, ReporteResultDTO
from modules.reports.domain.events import ReportResolved
from modules.reports.domain.repositories import IReporteRepository
from modules.reports.domain.value_objects import EstadoReporte
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ForbiddenError, NotFoundError, ValidationError

_SIN_PERMISO_MSG = "Solo un administrador puede cambiar el estado de un reporte."
_REPORTE_NO_ENCONTRADO_MSG = "Reporte no encontrado."
_ESTADO_INVALIDO_MSG = "Estado inválido."
_ESTADOS_TERMINALES = (EstadoReporte.RESUELTO, EstadoReporte.NO_REPRODUCIBLE)
_TRANSICIONES = {
    EstadoReporte.EN_REVISION: "poner_en_revision",
    EstadoReporte.RESUELTO: "resolver",
    EstadoReporte.NO_REPRODUCIBLE: "marcar_no_reproducible",
}


class CambiarEstadoReporteUseCase(BaseUseCase[CambiarEstadoReporteDTO, ReporteResultDTO]):
    """
    HA-05, UC-09 pasos 2-3/A1, api.md §8 `PATCH /reports/{id}/`: cambia
    el estado de un reporte. Solo Administrador (seguridad.md §1).
    Notifica al estudiante (HE-13) únicamente al llegar a un estado
    terminal (`resuelto`/`no_reproducible`), no al pasar por
    `en_revision`.
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        reporte_repository: IReporteRepository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._reporte_repository = reporte_repository

    def _validate(self, input_dto: CambiarEstadoReporteDTO) -> None:
        if input_dto.actor_rol != "administrador":
            raise ForbiddenError(_SIN_PERMISO_MSG)

        reporte = self._reporte_repository.get_by_id(input_dto.reporte_id)
        if reporte is None:
            raise NotFoundError(_REPORTE_NO_ENCONTRADO_MSG)

        try:
            self._nuevo_estado = EstadoReporte(input_dto.nuevo_estado)
        except ValueError as exc:
            raise ValidationError(_ESTADO_INVALIDO_MSG) from exc

        self._reporte = reporte

    def _execute_domain_logic(
        self, input_dto: CambiarEstadoReporteDTO
    ) -> tuple[ReporteResultDTO, list[DomainEvent]]:
        reporte = self._reporte
        metodo = getattr(reporte, _TRANSICIONES[self._nuevo_estado])
        metodo()
        actualizado = self._reporte_repository.update(reporte)

        result = ReporteResultDTO(
            id=actualizado.id,
            laboratorio_id=actualizado.laboratorio_id,
            estado=actualizado.estado.value,
            fecha_creacion=actualizado.fecha_creacion,
        )
        events: list[DomainEvent] = []
        if actualizado.estado in _ESTADOS_TERMINALES:
            events.append(
                ReportResolved(
                    reporte_id=actualizado.id,
                    estudiante_id=actualizado.estudiante_id,
                    estado=actualizado.estado.value,
                )
            )
        return result, events
