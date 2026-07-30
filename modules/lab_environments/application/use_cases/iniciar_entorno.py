from modules.lab_environments.application.dtos import EntornoResultDTO, IniciarEntornoDTO
from modules.lab_environments.domain.entities import EntornoActivo
from modules.lab_environments.domain.exceptions import (
    EntornoNoDisponibleError,
    EntornoProviderError,
    SeccionNoDisponibleError,
    SeccionSinEntornoRealError,
)
from modules.lab_environments.domain.ports import IContenedorProvider
from modules.lab_environments.domain.repositories import IEntornoRepository
from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.progress.domain.repositories import IProgresoRepository
from modules.progress.domain.value_objects import EstadoProgresoSeccion
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import NotFoundError

_PROGRESO_NO_ENCONTRADO_MSG = "Progreso no encontrado."
_SECCION_NO_ENCONTRADA_MSG = "Sección no encontrada."
_BLOQUEADA_MSG = "Esta sección todavía está bloqueada."
_SIN_ENTORNO_MSG = "Esta sección no tiene un entorno de práctica real configurado."
_SIN_CUPO_MSG = "Todos los entornos de práctica están ocupados en este momento. Reintentá en unos minutos."
_ERROR_PROVIDER_MSG = "No se pudo iniciar el entorno de práctica. Reintentá en unos minutos."


class IniciarEntornoUseCase(BaseUseCase[IniciarEntornoDTO, EntornoResultDTO]):
    """
    Crea (o reconecta a) el contenedor de práctica real de un estudiante
    para una sección puntual — un entorno por (progreso, sección), nunca
    dos a la vez para el mismo par (idempotente: si ya hay uno vivo, lo
    devuelve en vez de crear otro). El arranque del contenedor pasa por
    `IContenedorProvider` ANTES de abrir la transacción (`_validate`): si
    Docker falla, nunca llegamos a escribir en la base — evita persistir
    un `EntornoActivo` "fantasma" sin contenedor real detrás.
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        entorno_repository: IEntornoRepository,
        progreso_repository: IProgresoRepository,
        laboratorio_repository: ILaboratorioRepository,
        contenedor_provider: IContenedorProvider,
        max_concurrentes: int = 5,
        idle_timeout_minutos: int = 20,
        max_lifetime_minutos: int = 120,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._entorno_repository = entorno_repository
        self._progreso_repository = progreso_repository
        self._laboratorio_repository = laboratorio_repository
        self._contenedor_provider = contenedor_provider
        self._max_concurrentes = max_concurrentes
        self._idle_timeout_minutos = idle_timeout_minutos
        self._max_lifetime_minutos = max_lifetime_minutos
        self._entorno_existente = None
        self._container_id: str | None = None

    def _validate(self, input_dto: IniciarEntornoDTO) -> None:
        progreso = self._progreso_repository.get_by_asignacion(input_dto.asignacion_id)
        if progreso is None or not progreso.es_propio_de(input_dto.estudiante_id):
            raise NotFoundError(_PROGRESO_NO_ENCONTRADO_MSG)

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

        if self._entorno_repository.contar_activos() >= self._max_concurrentes:
            raise EntornoNoDisponibleError(_SIN_CUPO_MSG)

        try:
            self._container_id = self._contenedor_provider.iniciar(seccion.imagen_practica)
        except Exception as exc:  # noqa: BLE001 - cualquier falla de Docker se traduce a un error de dominio
            raise EntornoProviderError(_ERROR_PROVIDER_MSG) from exc

        self._progreso = progreso

    def _execute_domain_logic(
        self, input_dto: IniciarEntornoDTO
    ) -> tuple[EntornoResultDTO, list[DomainEvent]]:
        if self._entorno_existente is not None:
            entorno = self._entorno_existente
        else:
            entorno = self._entorno_repository.add(
                EntornoActivo(
                    seccion_id=input_dto.seccion_id,
                    progreso_id=self._progreso.id,
                    estudiante_id=input_dto.estudiante_id,
                    container_id=self._container_id,
                )
            )
            entorno.marcar_activo()
            entorno = self._entorno_repository.update(entorno)

        result = EntornoResultDTO(
            id=entorno.id,
            estado=entorno.estado.value,
            idle_timeout_minutos=self._idle_timeout_minutos,
            max_lifetime_minutos=self._max_lifetime_minutos,
        )
        return result, []
