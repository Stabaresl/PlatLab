from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.progress.application.dtos import ContenidoSeccionDTO, ObtenerContenidoSeccionDTO
from modules.progress.domain.exceptions import SeccionBloqueadaError
from modules.progress.domain.repositories import IProgresoRepository
from modules.progress.domain.value_objects import EstadoProgresoSeccion
from modules.shared.domain.exceptions import NotFoundError

_PROGRESO_NO_ENCONTRADO_MSG = "Progreso no encontrado."
_SECCION_NO_ENCONTRADA_MSG = "Sección no encontrada."
_BLOQUEADA_MSG = "Esta sección todavía está bloqueada."


class ObtenerContenidoSeccionQuery:
    """
    HE-03/HE-04, UC-02 precondición: expone el contenido teórico de una
    sección solo si `ProgresoSeccion != bloqueada` (dominio.md §3,
    api.md §7: "403 si ProgresoSeccion.estado = bloqueada"). Cruza
    `Progreso` (estado de avance) y `Laboratorio` (contenido real de la
    `Seccion`) — ambos repositorios se inyectan desde Application.
    """

    def __init__(
        self,
        progreso_repository: IProgresoRepository,
        laboratorio_repository: ILaboratorioRepository,
    ):
        self._progreso_repository = progreso_repository
        self._laboratorio_repository = laboratorio_repository

    def execute(self, input_dto: ObtenerContenidoSeccionDTO) -> ContenidoSeccionDTO:
        progreso = self._progreso_repository.get_by_asignacion(input_dto.asignacion_id)
        if progreso is None or not progreso.es_propio_de(input_dto.estudiante_id):
            raise NotFoundError(_PROGRESO_NO_ENCONTRADO_MSG)

        progreso_seccion = self._progreso_repository.get_seccion(
            progreso.id, input_dto.seccion_id
        )
        if progreso_seccion is None:
            raise NotFoundError(_SECCION_NO_ENCONTRADA_MSG)
        if progreso_seccion.estado == EstadoProgresoSeccion.BLOQUEADA:
            raise SeccionBloqueadaError(_BLOQUEADA_MSG)

        seccion = self._laboratorio_repository.get_seccion_by_id(input_dto.seccion_id)
        if seccion is None:
            raise NotFoundError(_SECCION_NO_ENCONTRADA_MSG)

        return ContenidoSeccionDTO(
            seccion_id=seccion.id,
            titulo=seccion.titulo,
            contenido_teorico=seccion.contenido_teorico,
            tiene_practica=seccion.tiene_practica,
            estado=progreso_seccion.estado.value,
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
            entorno_real_disponible=bool(seccion.imagen_practica),
        )
