from modules.laboratories.application.dtos import EditarSeccionDTO, SeccionResultDTO
from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.laboratories.domain.value_objects import PasoGuia, TipoLaboratorio
from modules.laboratories.infrastructure.content_sanitizer import sanitizar_contenido_html
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ConflictError, ForbiddenError, NotFoundError

_LAB_NO_ENCONTRADO_MSG = "Laboratorio no encontrado."
_SECCION_NO_ENCONTRADA_MSG = "Sección no encontrada."
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


class EditarSeccionUseCase(BaseUseCase[EditarSeccionDTO, SeccionResultDTO]):
    """
    api.md §5 `PATCH /laboratories/{id}/sections/{section_id}/` — misma
    regla de propiedad que `CrearSeccionUseCase`.
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        laboratorio_repository: ILaboratorioRepository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._laboratorio_repository = laboratorio_repository

    def _validate(self, input_dto: EditarSeccionDTO) -> None:
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
        seccion = next((s for s in secciones if s.id == input_dto.seccion_id), None)
        if seccion is None:
            raise NotFoundError(_SECCION_NO_ENCONTRADA_MSG)

        if input_dto.orden is not None and input_dto.orden != seccion.orden:
            if any(s.orden == input_dto.orden for s in secciones if s.id != seccion.id):
                raise ConflictError(_ORDEN_DUPLICADO_MSG)

        self._seccion = seccion

    def _execute_domain_logic(
        self, input_dto: EditarSeccionDTO
    ) -> tuple[SeccionResultDTO, list[DomainEvent]]:
        seccion = self._seccion
        if input_dto.titulo is not None:
            seccion.titulo = input_dto.titulo
        if input_dto.contenido_teorico is not None:
            seccion.contenido_teorico = sanitizar_contenido_html(input_dto.contenido_teorico)
        if input_dto.orden is not None:
            seccion.orden = input_dto.orden
        if input_dto.tiene_practica is not None:
            seccion.tiene_practica = input_dto.tiene_practica
        if input_dto.objetivos is not None:
            seccion.objetivos = input_dto.objetivos
        if input_dto.duracion_estimada_minutos is not None:
            seccion.duracion_estimada_minutos = input_dto.duracion_estimada_minutos
        if input_dto.pasos_guia is not None:
            seccion.pasos_guia = _sanitizar_pasos(input_dto.pasos_guia)
        if input_dto.entorno_practica is not None:
            seccion.entorno_practica = input_dto.entorno_practica
        if input_dto.imagen_practica is not None:
            seccion.imagen_practica = input_dto.imagen_practica

        actualizada = self._laboratorio_repository.update_seccion(seccion)

        result = SeccionResultDTO(
            id=actualizada.id,
            laboratorio_id=actualizada.laboratorio_id,
            orden=actualizada.orden,
            titulo=actualizada.titulo,
            tiene_practica=actualizada.tiene_practica,
        )
        return result, []
