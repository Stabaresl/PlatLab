from modules.laboratories.application.dtos import (
    ContenidoSeccionPreviewDTO,
    ObtenerContenidoSeccionPreviewDTO,
)
from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.shared.domain.exceptions import ForbiddenError, NotFoundError

_LAB_NO_ENCONTRADO_MSG = "Laboratorio no encontrado."
_SECCION_NO_ENCONTRADA_MSG = "Sección no encontrada."
_SIN_PERMISO_MSG = "No tienes permiso para previsualizar este laboratorio."


class ObtenerContenidoSeccionPreviewQuery:
    """
    Vista previa de admin/instructor dueño: mismo contenido que
    `ObtenerContenidoSeccionQuery` (Progress), pero sin depender de un
    `Progreso`/asignación real — todo visible, sin importar el estado del
    laboratorio, para poder revisarlo antes de aprobarlo.
    """

    def __init__(self, laboratorio_repository: ILaboratorioRepository):
        self._repo = laboratorio_repository

    def execute(
        self, input_dto: ObtenerContenidoSeccionPreviewDTO
    ) -> ContenidoSeccionPreviewDTO:
        laboratorio = self._repo.get_by_id(input_dto.laboratorio_id)
        if laboratorio is None:
            raise NotFoundError(_LAB_NO_ENCONTRADO_MSG)

        es_admin = input_dto.actor_rol == "administrador"
        es_dueno = (
            input_dto.actor_rol == "instructor"
            and laboratorio.instructor_id == input_dto.actor_id
        )
        if not (es_admin or es_dueno):
            raise ForbiddenError(_SIN_PERMISO_MSG)

        seccion = self._repo.get_seccion_by_id(input_dto.seccion_id)
        if seccion is None or seccion.laboratorio_id != laboratorio.id:
            raise NotFoundError(_SECCION_NO_ENCONTRADA_MSG)

        dockerfile = self._repo.get_dockerfile_by_seccion(seccion.id)

        return ContenidoSeccionPreviewDTO(
            seccion_id=seccion.id,
            titulo=seccion.titulo,
            contenido_teorico=seccion.contenido_teorico,
            tiene_practica=seccion.tiene_practica,
            objetivos=seccion.objetivos,
            duracion_estimada_minutos=seccion.duracion_estimada_minutos,
            pasos_guia=[
                {
                    "orden": p.orden,
                    "titulo": p.titulo,
                    "instrucciones": p.instrucciones,
                    "comando_sugerido": p.comando_sugerido,
                }
                for p in seccion.pasos_guia
            ],
            entorno_practica=(
                {
                    "prompt": seccion.entorno_practica.prompt,
                    "banner": seccion.entorno_practica.banner,
                    "comandos": [
                        {"comando": c.comando, "salida": c.salida}
                        for c in seccion.entorno_practica.comandos
                    ],
                }
                if seccion.entorno_practica
                else None
            ),
            tiene_dockerfile=dockerfile is not None,
            dockerfile_url=dockerfile.archivo_url if dockerfile else None,
        )
