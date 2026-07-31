from modules.laboratories.application.dtos import DockerfileResultDTO, SubirDockerfileDTO
from modules.laboratories.domain.entities import DockerfileSeccion
from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.laboratories.domain.value_objects import TipoLaboratorio
from modules.laboratories.infrastructure.dockerfile_storage import guardar_dockerfile
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ForbiddenError, NotFoundError

_LAB_NO_ENCONTRADO_MSG = "Laboratorio no encontrado."
_SECCION_NO_ENCONTRADA_MSG = "Sección no encontrada."
_SIN_PERMISO_MSG = "No tienes permiso para editar este laboratorio."


class SubirDockerfileSeccionUseCase(BaseUseCase[SubirDockerfileDTO, DockerfileResultDTO]):
    """
    Guarda el Dockerfile/contexto de build de una sección práctica —
    reemplaza el anterior si ya existía uno (1:1). Nunca dispara un build:
    solo queda disponible para que un admin lo revise manualmente desde la
    cola de revisión (`preview_seccion`).
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        laboratorio_repository: ILaboratorioRepository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._laboratorio_repository = laboratorio_repository

    def _validate(self, input_dto: SubirDockerfileDTO) -> None:
        laboratorio = self._laboratorio_repository.get_by_id(input_dto.laboratorio_id)
        if laboratorio is None:
            raise NotFoundError(_LAB_NO_ENCONTRADO_MSG)

        if input_dto.actor_rol == "instructor":
            if laboratorio.instructor_id != input_dto.actor_id:
                raise ForbiddenError(_SIN_PERMISO_MSG)
        elif input_dto.actor_rol == "administrador":
            if laboratorio.tipo != TipoLaboratorio.PREDETERMINADO:
                raise ForbiddenError(_SIN_PERMISO_MSG)
        else:
            raise ForbiddenError(_SIN_PERMISO_MSG)

        secciones = self._laboratorio_repository.get_secciones(input_dto.laboratorio_id)
        if not any(s.id == input_dto.seccion_id for s in secciones):
            raise NotFoundError(_SECCION_NO_ENCONTRADA_MSG)

    def _execute_domain_logic(
        self, input_dto: SubirDockerfileDTO
    ) -> tuple[DockerfileResultDTO, list[DomainEvent]]:
        archivo_url, tamano_kb = guardar_dockerfile(
            input_dto.archivo_nombre, input_dto.archivo_contenido
        )
        dockerfile = DockerfileSeccion(
            seccion_id=input_dto.seccion_id,
            archivo_url=archivo_url,
            nombre_archivo=input_dto.archivo_nombre,
            tamano_kb=tamano_kb,
        )
        guardado = self._laboratorio_repository.save_dockerfile(dockerfile)

        result = DockerfileResultDTO(
            id=guardado.id,
            seccion_id=guardado.seccion_id,
            archivo_url=guardado.archivo_url,
            nombre_archivo=guardado.nombre_archivo,
            tamano_kb=guardado.tamano_kb,
        )
        return result, []
