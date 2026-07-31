from modules.laboratories.application.dtos import LaboratorioPersonalizadoPublicadoItemDTO
from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.laboratories.domain.value_objects import TipoLaboratorio
from modules.shared.domain.exceptions import ForbiddenError

_SIN_PERMISO_MSG = "Solo un administrador puede gestionar la visibilidad de catálogo."


class ListarLaboratoriosPersonalizadosPublicadosQuery:
    """
    Panel admin de gestión de catálogo: todos los `personalizado`
    `publicado` de cualquier instructor (a diferencia de `find_catalogo`,
    que solo expone los propios de un instructor puntual), con su estado
    actual de `visible_en_catalogo` — para que un admin pueda activar/
    desactivar la visibilidad de catálogo de cualquiera, no solo la suya.
    """

    def __init__(self, laboratorio_repository: ILaboratorioRepository):
        self._repo = laboratorio_repository

    def execute(self, actor_rol: str) -> list[LaboratorioPersonalizadoPublicadoItemDTO]:
        if actor_rol != "administrador":
            raise ForbiddenError(_SIN_PERMISO_MSG)

        return [
            LaboratorioPersonalizadoPublicadoItemDTO(
                id=lab.id,
                nombre=lab.nombre,
                instructor_id=lab.instructor_id,
                visible_en_catalogo=lab.visible_en_catalogo,
            )
            for lab in self._repo.find_publicados()
            if lab.tipo == TipoLaboratorio.PERSONALIZADO
        ]
