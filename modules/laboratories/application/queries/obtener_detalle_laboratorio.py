import uuid

from modules.laboratories.application.dtos import LaboratorioDetalleDTO
from modules.laboratories.domain.ports import IEstadoInscripcionProvider, SinInscripcionProvider
from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.shared.domain.exceptions import NotFoundError

_NO_ENCONTRADO_MSG = "Laboratorio no encontrado."


class ObtenerDetalleLaboratorioQuery:
    """
    HV-03: descripción, nivel, temas y cantidad de secciones — nunca
    contenido teórico ni flags (esos campos ni siquiera existen en
    `LaboratorioDetalleDTO`, así el bloqueo se cumple estructuralmente, no
    por una validación que se pueda olvidar en Presentation).

    La visibilidad usa `Laboratorio.es_visible_para` (mismo criterio que
    el catálogo, HV-02/HI-01): un borrador ajeno responde 404, nunca 403
    — no se confirma la existencia de laboratorios que el actor no puede
    ver (mismo criterio anti-enumeración que Authentication, UC-01 E1).
    Además, un estudiante con una asignación vigente para este
    laboratorio (`estado_inscripcion_provider`) también puede verlo aunque
    sea `personalizado` de otro instructor — Laboratories no conoce el
    agregado Asignación directamente (dominio.md §1), por eso esto se
    resuelve vía puerto, igual que el campo `inscrito` del catálogo. Un
    administrador (`es_admin=True`) ve cualquier laboratorio sin importar
    dueño/estado — necesario para revisar un `personalizado` en
    `en_revision` desde la cola de revisión, que no es ni su propio
    laboratorio ni un `predeterminado`.
    """

    def __init__(
        self,
        laboratorio_repository: ILaboratorioRepository,
        estado_inscripcion_provider: IEstadoInscripcionProvider | None = None,
    ):
        self._repo = laboratorio_repository
        self._inscripcion = estado_inscripcion_provider or SinInscripcionProvider()

    def execute(
        self,
        laboratorio_id: uuid.UUID,
        instructor_id: uuid.UUID | None = None,
        estudiante_id: uuid.UUID | None = None,
        es_admin: bool = False,
    ) -> LaboratorioDetalleDTO:
        laboratorio = self._repo.get_by_id(laboratorio_id)
        visible = laboratorio is not None and (
            es_admin
            or laboratorio.es_visible_para(instructor_id)
            or (
                estudiante_id is not None
                and self._inscripcion.esta_inscrito(estudiante_id, laboratorio_id)
            )
        )
        if not visible:
            raise NotFoundError(_NO_ENCONTRADO_MSG)

        secciones = self._repo.get_secciones(laboratorio_id)
        return LaboratorioDetalleDTO(
            id=laboratorio.id,
            nombre=laboratorio.nombre,
            descripcion=laboratorio.descripcion,
            nivel_dificultad=laboratorio.nivel_dificultad.value,
            estado=laboratorio.estado.value,
            temas=laboratorio.temas,
            total_secciones=len(secciones),
            motivo_rechazo=laboratorio.motivo_rechazo,
        )
