from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.progress.application.dtos import (
    ObtenerProgresoDTO,
    ProgresoOverviewDTO,
    SeccionProgresoItemDTO,
)
from modules.progress.domain.ports import IEstadoAsignacionProvider
from modules.progress.domain.repositories import IProgresoRepository
from modules.progress.domain.value_objects import EstadoProgresoSeccion
from modules.shared.domain.exceptions import NotFoundError

_PROGRESO_NO_ENCONTRADO_MSG = "Progreso no encontrado."


class ObtenerProgresoQuery:
    """
    `GET /progress/{assignment_id}/`: resumen de avance para poder
    renderizar la vista de "resolver laboratorio" en el frontend —
    secciones en orden con su estado (`bloqueada`/`en_progreso`/
    `completada`, id incluido — a diferencia del TOC público de
    Laboratories, HV-03, que no expone `id` porque es para navegantes sin
    inscripción) y si el examen ya está disponible para enviar.

    `Progreso` no guarda `laboratorio_id` directamente (dominio.md §4: se
    resuelve vía la primera `Seccion` de su lista, mismo truco que ya usa
    `EnviarExamenUseCase`) — evita que Progress dependa de Assignments
    solo para esto.
    """

    def __init__(
        self,
        progreso_repository: IProgresoRepository,
        laboratorio_repository: ILaboratorioRepository,
        estado_asignacion_provider: IEstadoAsignacionProvider | None = None,
    ):
        self._progreso_repository = progreso_repository
        self._laboratorio_repository = laboratorio_repository
        self._estado_asignacion_provider = estado_asignacion_provider

    def execute(self, input_dto: ObtenerProgresoDTO) -> ProgresoOverviewDTO:
        progreso = self._progreso_repository.get_by_asignacion(input_dto.asignacion_id)
        if progreso is None or not progreso.es_propio_de(input_dto.estudiante_id):
            raise NotFoundError(_PROGRESO_NO_ENCONTRADO_MSG)

        progreso_secciones = self._progreso_repository.get_secciones(progreso.id)
        if not progreso_secciones:
            raise NotFoundError(_PROGRESO_NO_ENCONTRADO_MSG)

        primera_seccion = self._laboratorio_repository.get_seccion_by_id(
            progreso_secciones[0].seccion_id
        )
        laboratorio_id = primera_seccion.laboratorio_id
        laboratorio = self._laboratorio_repository.get_by_id(laboratorio_id)
        secciones_lab = self._laboratorio_repository.get_secciones(laboratorio_id)

        estado_por_seccion = {ps.seccion_id: ps.estado for ps in progreso_secciones}
        secciones_dto = [
            SeccionProgresoItemDTO(
                id=s.id,
                orden=s.orden,
                titulo=s.titulo,
                tiene_practica=s.tiene_practica,
                estado=estado_por_seccion.get(s.id, EstadoProgresoSeccion.BLOQUEADA).value,
            )
            for s in secciones_lab
        ]
        secciones_completas = bool(secciones_dto) and all(
            s.estado == EstadoProgresoSeccion.COMPLETADA.value for s in secciones_dto
        )

        examen = self._laboratorio_repository.get_examen_by_laboratorio(laboratorio_id)
        historial = self._progreso_repository.get_historial(progreso.id)

        vencido = False
        fecha_vencimiento = None
        if self._estado_asignacion_provider is not None:
            estado_asignacion = self._estado_asignacion_provider.obtener_estado(
                input_dto.asignacion_id
            )
            if estado_asignacion is not None:
                vencido = estado_asignacion.vencida
                fecha_vencimiento = estado_asignacion.fecha_vencimiento

        return ProgresoOverviewDTO(
            asignacion_id=input_dto.asignacion_id,
            laboratorio_id=laboratorio_id,
            laboratorio_nombre=laboratorio.nombre if laboratorio else "",
            secciones=secciones_dto,
            secciones_completas=secciones_completas,
            examen_disponible=examen is not None,
            intentos_examen=len(historial),
            vencido=vencido,
            fecha_vencimiento=fecha_vencimiento,
        )
