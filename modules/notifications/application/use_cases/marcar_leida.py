from modules.notifications.application.dtos import MarcarLeidaDTO, NotificacionResultDTO
from modules.notifications.domain.repositories import INotificacionRepository
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import NotFoundError

_NO_ENCONTRADA_MSG = "Notificación no encontrada."


class MarcarLeidaUseCase(BaseUseCase[MarcarLeidaDTO, NotificacionResultDTO]):
    """
    api.md §9 `PATCH /notifications/{id}/read/`: solo el dueño de la
    notificación puede marcarla como leída (anti-enumeración: "no
    existe" y "existe pero no es propia" devuelven el mismo error).
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        notificacion_repository: INotificacionRepository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._notificacion_repository = notificacion_repository

    def _validate(self, input_dto: MarcarLeidaDTO) -> None:
        notificacion = self._notificacion_repository.get_by_id(input_dto.notificacion_id)
        if notificacion is None or notificacion.user_id != input_dto.actor_id:
            raise NotFoundError(_NO_ENCONTRADA_MSG)
        self._notificacion = notificacion

    def _execute_domain_logic(
        self, input_dto: MarcarLeidaDTO
    ) -> tuple[NotificacionResultDTO, list[DomainEvent]]:
        notificacion = self._notificacion
        notificacion.marcar_leida()
        actualizada = self._notificacion_repository.update(notificacion)

        result = NotificacionResultDTO(
            id=actualizada.id,
            tipo=actualizada.tipo.value,
            mensaje=actualizada.mensaje,
            canal=actualizada.canal.value,
            leida=actualizada.leida,
            entidad_tipo=actualizada.entidad_tipo,
            entidad_id=actualizada.entidad_id,
            fecha_creacion=actualizada.fecha_creacion,
        )
        return result, []
