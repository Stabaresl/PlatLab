import uuid

from modules.laboratories.application.dtos import LaboratorioDetalleDTO
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
    """

    def __init__(self, laboratorio_repository: ILaboratorioRepository):
        self._repo = laboratorio_repository

    def execute(
        self, laboratorio_id: uuid.UUID, instructor_id: uuid.UUID | None = None
    ) -> LaboratorioDetalleDTO:
        laboratorio = self._repo.get_by_id(laboratorio_id)
        if laboratorio is None or not laboratorio.es_visible_para(instructor_id):
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
        )
