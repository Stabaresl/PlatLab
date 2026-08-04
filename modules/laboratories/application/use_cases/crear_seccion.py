from modules.laboratories.application.dtos import CrearSeccionDTO, SeccionResultDTO
from modules.laboratories.domain.entities import Seccion
from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.laboratories.domain.services import validar_imagen_practica_permitida
from modules.laboratories.domain.value_objects import PasoGuia, TipoLaboratorio
from modules.laboratories.infrastructure.content_sanitizer import sanitizar_contenido_html
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ConflictError, ForbiddenError, NotFoundError

_LAB_NO_ENCONTRADO_MSG = "Laboratorio no encontrado."
_SIN_PERMISO_MSG = "No tienes permiso para editar este laboratorio."
_ORDEN_DUPLICADO_MSG = "Ya existe una sección con ese orden en este laboratorio."


def _sanitizar_pasos(pasos: list[PasoGuia]) -> list[PasoGuia]:
    return [
        PasoGuia(
            orden=p.orden,
            titulo=p.titulo,
            instrucciones=sanitizar_contenido_html(p.instrucciones),
            comando_sugerido=p.comando_sugerido,
        )
        for p in pasos
    ]


class CrearSeccionUseCase(BaseUseCase[CrearSeccionDTO, SeccionResultDTO]):
    """
    UC-04 paso 2, api.md §5 `POST /laboratories/{id}/sections/`. Misma
    regla de propiedad que `DefinirFlagUseCase` (seguridad.md §1):
    Instructor solo en sus propios `personalizado`, Administrador solo
    en `predeterminado`. Sanitiza `contenido_teorico` (UC-04 E1, XSS).
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        laboratorio_repository: ILaboratorioRepository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._laboratorio_repository = laboratorio_repository

    def _validate(self, input_dto: CrearSeccionDTO) -> None:
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
        if any(s.orden == input_dto.orden for s in secciones):
            raise ConflictError(_ORDEN_DUPLICADO_MSG)

        validar_imagen_practica_permitida(input_dto.imagen_practica)

    def _execute_domain_logic(
        self, input_dto: CrearSeccionDTO
    ) -> tuple[SeccionResultDTO, list[DomainEvent]]:
        seccion = Seccion(
            laboratorio_id=input_dto.laboratorio_id,
            titulo=input_dto.titulo,
            contenido_teorico=sanitizar_contenido_html(input_dto.contenido_teorico),
            orden=input_dto.orden,
            tiene_practica=input_dto.tiene_practica,
            objetivos=input_dto.objetivos,
            duracion_estimada_minutos=input_dto.duracion_estimada_minutos,
            pasos_guia=_sanitizar_pasos(input_dto.pasos_guia),
            entorno_practica=input_dto.entorno_practica,
            imagen_practica=input_dto.imagen_practica,
        )
        guardada = self._laboratorio_repository.add_seccion(seccion)

        result = SeccionResultDTO(
            id=guardada.id,
            laboratorio_id=guardada.laboratorio_id,
            orden=guardada.orden,
            titulo=guardada.titulo,
            tiene_practica=guardada.tiene_practica,
        )
        return result, []
