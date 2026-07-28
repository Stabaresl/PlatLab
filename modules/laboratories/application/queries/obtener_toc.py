import uuid

from modules.laboratories.application.dtos import TOCDTO, SeccionTOCItemDTO
from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.shared.domain.exceptions import NotFoundError

_NO_ENCONTRADO_MSG = "Laboratorio no encontrado."


class ObtenerTOCQuery:
    """
    HV-03: tabla de contenido — solo `orden`/`titulo`/`tiene_practica` por
    sección, nunca `contenido_teorico` (ese campo no existe en
    `SeccionTOCItemDTO`, el bloqueo de contenido es estructural).
    """

    def __init__(self, laboratorio_repository: ILaboratorioRepository):
        self._repo = laboratorio_repository

    def execute(self, laboratorio_id: uuid.UUID, instructor_id: uuid.UUID | None = None) -> TOCDTO:
        laboratorio = self._repo.get_by_id(laboratorio_id)
        if laboratorio is None or not laboratorio.es_visible_para(instructor_id):
            raise NotFoundError(_NO_ENCONTRADO_MSG)

        secciones = self._repo.get_secciones(laboratorio_id)
        items = [
            SeccionTOCItemDTO(orden=s.orden, titulo=s.titulo, tiene_practica=s.tiene_practica)
            for s in secciones
        ]
        return TOCDTO(laboratorio_id=laboratorio_id, secciones=items)
