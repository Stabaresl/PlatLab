import uuid

from modules.laboratories.application.dtos import TOCDTO, SeccionTOCItemDTO
from modules.laboratories.domain.ports import IEstadoInscripcionProvider, SinInscripcionProvider
from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.shared.domain.exceptions import NotFoundError

_NO_ENCONTRADO_MSG = "Laboratorio no encontrado."


class ObtenerTOCQuery:
    """
    HV-03: tabla de contenido — solo `orden`/`titulo`/`tiene_practica` por
    sección, nunca `contenido_teorico` (ese campo no existe en
    `SeccionTOCItemDTO`, el bloqueo de contenido es estructural). Misma
    regla de visibilidad extendida que `ObtenerDetalleLaboratorioQuery`:
    un estudiante con asignación vigente también puede ver el TOC de un
    `personalizado` ajeno.
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
    ) -> TOCDTO:
        laboratorio = self._repo.get_by_id(laboratorio_id)
        visible = laboratorio is not None and (
            laboratorio.es_visible_para(instructor_id)
            or (
                estudiante_id is not None
                and self._inscripcion.esta_inscrito(estudiante_id, laboratorio_id)
            )
        )
        if not visible:
            raise NotFoundError(_NO_ENCONTRADO_MSG)

        secciones = self._repo.get_secciones(laboratorio_id)
        items = [
            SeccionTOCItemDTO(orden=s.orden, titulo=s.titulo, tiene_practica=s.tiene_practica)
            for s in secciones
        ]
        return TOCDTO(laboratorio_id=laboratorio_id, secciones=items)
