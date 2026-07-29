from modules.reports.application.dtos import CrearReporteDTO, ReporteResultDTO
from modules.reports.domain.entities import AdjuntoReporte, Reporte
from modules.reports.domain.events import ReportSubmitted
from modules.reports.domain.repositories import IReporteRepository
from modules.reports.infrastructure.storage_adapter import guardar_adjunto
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ForbiddenError

_SIN_PERMISO_MSG = "Solo un estudiante puede reportar un problema."


class CrearReporteUseCase(BaseUseCase[CrearReporteDTO, ReporteResultDTO]):
    """
    HE-12, UC-09 paso 1, api.md §8 `POST /reports/`: crea un reporte en
    estado `abierto`. La validación de descripción mínima vive en
    `Reporte.__post_init__` (Domain, UC-09 E1). El adjunto, si viene, se
    valida y guarda vía `storage_adapter` antes de asociarlo.
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        reporte_repository: IReporteRepository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._reporte_repository = reporte_repository

    def _validate(self, input_dto: CrearReporteDTO) -> None:
        if input_dto.actor_rol != "estudiante":
            raise ForbiddenError(_SIN_PERMISO_MSG)

    def _execute_domain_logic(
        self, input_dto: CrearReporteDTO
    ) -> tuple[ReporteResultDTO, list[DomainEvent]]:
        reporte = Reporte(
            estudiante_id=input_dto.estudiante_id,
            laboratorio_id=input_dto.laboratorio_id,
            descripcion=input_dto.descripcion,
            seccion_id=input_dto.seccion_id,
        )
        guardado = self._reporte_repository.add(reporte)

        if input_dto.archivo_contenido is not None:
            archivo_url, tamano_kb = guardar_adjunto(
                input_dto.archivo_nombre or "adjunto", input_dto.archivo_contenido
            )
            self._reporte_repository.add_adjunto(
                AdjuntoReporte(
                    reporte_id=guardado.id,
                    archivo_url=archivo_url,
                    nombre_archivo=input_dto.archivo_nombre or "adjunto",
                    tamano_kb=tamano_kb,
                )
            )

        result = ReporteResultDTO(
            id=guardado.id,
            laboratorio_id=guardado.laboratorio_id,
            estado=guardado.estado.value,
            fecha_creacion=guardado.fecha_creacion,
        )
        event = ReportSubmitted(
            reporte_id=guardado.id,
            estudiante_id=guardado.estudiante_id,
            laboratorio_id=guardado.laboratorio_id,
        )
        return result, [event]
