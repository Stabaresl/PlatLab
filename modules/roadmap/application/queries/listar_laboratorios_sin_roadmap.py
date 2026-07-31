from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.laboratories.domain.value_objects import EstadoLaboratorio, TipoLaboratorio
from modules.roadmap.application.dtos import LaboratorioSinRoadmapItemDTO
from modules.roadmap.domain.repositories import INodoRoadmapRepository
from modules.shared.domain.exceptions import ForbiddenError

_SIN_PERMISO_MSG = "Solo un administrador puede ver la pool de laboratorios sin roadmap."


class ListarLaboratoriosSinRoadmapQuery:
    """
    Panel admin: laboratorios `predeterminado`+`publicado` que todavía
    no tienen un nodo en ningún roadmap — la "pool" desde la que se
    arrastra hacia una categoría (`AgregarNodoUseCase`).
    """

    def __init__(
        self,
        laboratorio_repository: ILaboratorioRepository,
        nodo_repository: INodoRoadmapRepository,
    ):
        self._laboratorio_repository = laboratorio_repository
        self._nodo_repository = nodo_repository

    def execute(self, actor_rol: str) -> list[LaboratorioSinRoadmapItemDTO]:
        if actor_rol != "administrador":
            raise ForbiddenError(_SIN_PERMISO_MSG)

        asignados = self._nodo_repository.find_laboratorio_ids_asignados()
        candidatos = self._laboratorio_repository.find_catalogo()
        return [
            LaboratorioSinRoadmapItemDTO(
                id=lab.id,
                nombre=lab.nombre,
                nivel_dificultad=lab.nivel_dificultad.value,
                temas=lab.temas,
            )
            for lab in candidatos
            if lab.tipo == TipoLaboratorio.PREDETERMINADO
            and lab.estado == EstadoLaboratorio.PUBLICADO
            and lab.id not in asignados
        ]
