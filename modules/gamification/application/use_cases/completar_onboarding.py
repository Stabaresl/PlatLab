from modules.gamification.application.dtos import (
    CompletarOnboardingDTO,
    CompletarOnboardingResultDTO,
    LogroDesbloqueadoResultDTO,
)
from modules.gamification.domain.entities import CosmeticoDesbloqueado, LogroDesbloqueado, TituloDesbloqueado
from modules.gamification.domain.events import LogroDesbloqueadoEvent
from modules.gamification.domain.repositories import (
    ICosmeticoDesbloqueadoRepository,
    ICosmeticoRepository,
    ILogroDesbloqueadoRepository,
    ILogroRepository,
    ITituloDesbloqueadoRepository,
    ITituloRepository,
)
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ForbiddenError

_SIN_PERMISO_MSG = "Solo un estudiante tiene progresión de gamificación."
_LOGRO_CLAVE = "primeros_pasos"


class CompletarOnboardingUseCase(BaseUseCase[CompletarOnboardingDTO, CompletarOnboardingResultDTO]):
    """
    Recompensa real (no cosmética) al TERMINAR el tour de bienvenida — no
    al saltarlo, ver `OnboardingTour.tsx::finish`. Desbloquea el logro
    de clave fija `primeros_pasos` (`tipo_criterio=TOUR_COMPLETADO`,
    nunca lo evalúa `ProcesarCompletitudLaboratorio`, solo lo dispara
    esto) y cualquier cosmético/título asociado — mismo mecanismo de
    desbloqueo que `_evaluar_logros`, pero gatillado por completar el
    tour en vez de un laboratorio. Idempotente: si el logro ya estaba
    desbloqueado (el estudiante ya vio el tour antes, o encolan dos
    requests), no hace nada.
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        logro_repository: ILogroRepository,
        logro_desbloqueado_repository: ILogroDesbloqueadoRepository,
        cosmetico_repository: ICosmeticoRepository,
        cosmetico_desbloqueado_repository: ICosmeticoDesbloqueadoRepository,
        titulo_repository: ITituloRepository,
        titulo_desbloqueado_repository: ITituloDesbloqueadoRepository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._logro_repository = logro_repository
        self._logro_desbloqueado_repository = logro_desbloqueado_repository
        self._cosmetico_repository = cosmetico_repository
        self._cosmetico_desbloqueado_repository = cosmetico_desbloqueado_repository
        self._titulo_repository = titulo_repository
        self._titulo_desbloqueado_repository = titulo_desbloqueado_repository

    def _validate(self, input_dto: CompletarOnboardingDTO) -> None:
        if input_dto.actor_rol != "estudiante":
            raise ForbiddenError(_SIN_PERMISO_MSG)

        self._logro = self._logro_repository.get_by_clave(_LOGRO_CLAVE)
        self._ya_desbloqueado = self._logro is not None and self._logro_desbloqueado_repository.existe(
            input_dto.actor_id, self._logro.id
        )

    def _execute_domain_logic(
        self, input_dto: CompletarOnboardingDTO
    ) -> tuple[CompletarOnboardingResultDTO, list[DomainEvent]]:
        if self._logro is None or self._ya_desbloqueado:
            return CompletarOnboardingResultDTO(logro_desbloqueado=None), []

        logro = self._logro
        self._logro_desbloqueado_repository.add(
            LogroDesbloqueado(estudiante_id=input_dto.actor_id, logro_id=logro.id)
        )
        for cosmetico in self._cosmetico_repository.find_por_logro(logro.id):
            if not self._cosmetico_desbloqueado_repository.existe(input_dto.actor_id, cosmetico.id):
                self._cosmetico_desbloqueado_repository.add(
                    CosmeticoDesbloqueado(estudiante_id=input_dto.actor_id, cosmetico_id=cosmetico.id)
                )
        for titulo in self._titulo_repository.find_por_logro(logro.id):
            if not self._titulo_desbloqueado_repository.existe(input_dto.actor_id, titulo.id):
                self._titulo_desbloqueado_repository.add(
                    TituloDesbloqueado(estudiante_id=input_dto.actor_id, titulo_id=titulo.id)
                )

        result = CompletarOnboardingResultDTO(
            logro_desbloqueado=LogroDesbloqueadoResultDTO(logro_id=logro.id, nombre=logro.nombre)
        )
        event = LogroDesbloqueadoEvent(estudiante_id=input_dto.actor_id, logro_id=logro.id, nombre=logro.nombre)
        return result, [event]
