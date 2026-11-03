from modules.lab_environments.application.dtos import EntornoResultDTO, IniciarEntornoDTO
from modules.lab_environments.domain.entities import EntornoActivo
from modules.lab_environments.domain.events import EntornoAprovisionamientoSolicitado
from modules.lab_environments.domain.exceptions import (
    EntornoNoDisponibleError,
    SeccionNoDisponibleError,
    SeccionSinEntornoRealError,
)
from modules.lab_environments.domain.repositories import IEntornoRepository
from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.progress.domain.exceptions import AsignacionVencidaError
from modules.progress.domain.ports import IEstadoAsignacionProvider
from modules.progress.domain.repositories import IProgresoRepository
from modules.progress.domain.value_objects import EstadoProgresoSeccion
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import NotFoundError

_PROGRESO_NO_ENCONTRADO_MSG = "Progreso no encontrado."
_SECCION_NO_ENCONTRADA_MSG = "Sección no encontrada."
_BLOQUEADA_MSG = "Esta sección todavía está bloqueada."
_SIN_ENTORNO_MSG = "Esta sección no tiene un entorno de práctica real configurado."
_SIN_CUPO_MSG = (
    "Todos los entornos de práctica están ocupados en este momento. Reintenta en unos minutos."
)
_CUPO_ESTUDIANTE_MSG = (
    "Ya tienes el máximo de entornos de práctica encendidos. Detén uno antes de iniciar otro."
)
_VENCIDA_MSG = "Este laboratorio venció. Ya no se puede continuar."


class IniciarEntornoUseCase(BaseUseCase[IniciarEntornoDTO, EntornoResultDTO]):
    """
    Solicita (o reconecta a) el entorno de práctica real de un estudiante
    para una sección puntual — un entorno por (progreso, sección), nunca
    dos a la vez para el mismo par (idempotente: si ya hay uno vivo, lo
    devuelve en vez de crear otro).

    El arranque real del contenedor Docker NO pasa por acá: `containers.
    run()` más el poll de HEALTHCHECK puede tardar hasta ~10s
    (`docker_provider.py`), y bloquear un worker web por eso en cada
    arranque no escala con varios estudiantes a la vez (RNF rendimiento).
    Este caso de uso solo valida, crea el `EntornoActivo` en estado
    `iniciando` (sin `container_id` todavía) y dispara
    `EntornoAprovisionamientoSolicitado` — el listener de infraestructura
    encola la tarea de Celery que realmente llama a
    `IContenedorProvider.iniciar()` (ver `infrastructure/tasks.py`,
    `AprovisionarEntornoUseCase`). El frontend hace poll de
    `GET .../status/` hasta ver `estado: "activo"`.
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        entorno_repository: IEntornoRepository,
        progreso_repository: IProgresoRepository,
        laboratorio_repository: ILaboratorioRepository,
        max_concurrentes: int = 5,
        idle_timeout_minutos: int = 20,
        max_lifetime_minutos: int = 120,
        max_por_estudiante: int = 2,
        estado_asignacion_provider: IEstadoAsignacionProvider | None = None,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._entorno_repository = entorno_repository
        self._progreso_repository = progreso_repository
        self._laboratorio_repository = laboratorio_repository
        self._max_concurrentes = max_concurrentes
        self._max_por_estudiante = max_por_estudiante
        self._estado_asignacion_provider = estado_asignacion_provider
        self._idle_timeout_minutos = idle_timeout_minutos
        self._max_lifetime_minutos = max_lifetime_minutos
        self._entorno_existente = None
        self._imagen: str | None = None

    def _validate(self, input_dto: IniciarEntornoDTO) -> None:
        progreso = self._progreso_repository.get_by_asignacion(input_dto.asignacion_id)
        if progreso is None or not progreso.es_propio_de(input_dto.estudiante_id):
            raise NotFoundError(_PROGRESO_NO_ENCONTRADO_MSG)

        # Misma regla que flags/secciones/examen (RF-32): una asignación
        # vencida deja ver el material pero no seguir practicando — antes un
        # estudiante vencido podía seguir levantando contenedores.
        if self._estado_asignacion_provider is not None:
            estado = self._estado_asignacion_provider.obtener_estado(input_dto.asignacion_id)
            if estado is not None and estado.vencida:
                raise AsignacionVencidaError(_VENCIDA_MSG)

        progreso_seccion = self._progreso_repository.get_seccion(progreso.id, input_dto.seccion_id)
        if progreso_seccion is None:
            raise NotFoundError(_SECCION_NO_ENCONTRADA_MSG)
        if progreso_seccion.estado == EstadoProgresoSeccion.BLOQUEADA:
            raise SeccionNoDisponibleError(_BLOQUEADA_MSG)

        seccion = self._laboratorio_repository.get_seccion_by_id(input_dto.seccion_id)
        if seccion is None:
            raise NotFoundError(_SECCION_NO_ENCONTRADA_MSG)
        if not seccion.imagen_practica:
            raise SeccionSinEntornoRealError(_SIN_ENTORNO_MSG)

        existente = self._entorno_repository.get_activo_por_seccion(progreso.id, input_dto.seccion_id)
        if existente is not None and existente.esta_activo():
            self._entorno_existente = existente
            self._progreso = progreso
            return

        # Cupo por estudiante antes que el global: sin esto, un solo
        # estudiante podía abrir un entorno por cada sección práctica y
        # agotar el cupo de toda la plataforma (o de su sala).
        if (
            self._entorno_repository.contar_activos_por_estudiante(input_dto.estudiante_id)
            >= self._max_por_estudiante
        ):
            raise EntornoNoDisponibleError(_CUPO_ESTUDIANTE_MSG)

        if self._entorno_repository.contar_activos() >= self._max_concurrentes:
            raise EntornoNoDisponibleError(_SIN_CUPO_MSG)

        self._imagen = seccion.imagen_practica
        self._progreso = progreso

    def _execute_domain_logic(
        self, input_dto: IniciarEntornoDTO
    ) -> tuple[EntornoResultDTO, list[DomainEvent]]:
        if self._entorno_existente is not None:
            entorno = self._entorno_existente
            eventos: list[DomainEvent] = []
        else:
            entorno = self._entorno_repository.add(
                EntornoActivo(
                    seccion_id=input_dto.seccion_id,
                    progreso_id=self._progreso.id,
                    estudiante_id=input_dto.estudiante_id,
                    container_id="",
                )
            )
            eventos = [
                EntornoAprovisionamientoSolicitado(entorno_id=entorno.id, imagen=self._imagen)
            ]

        result = EntornoResultDTO(
            id=entorno.id,
            estado=entorno.estado.value,
            idle_timeout_minutos=self._idle_timeout_minutos,
            max_lifetime_minutos=self._max_lifetime_minutos,
        )
        return result, eventos
