from modules.rooms.application.dtos import CambiarEstadoSalaDTO
from modules.rooms.domain.events import EstadoSalaCambiado
from modules.rooms.domain.repositories import ISalaRepository
from modules.rooms.domain.value_objects import EstadoSala
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import NotFoundError, ValidationError

_NO_ENCONTRADA_MSG = "Sala no encontrada."
_ESTADO_INVALIDO_MSG = "Estado inválido: usa abierta, cerrada o finalizada."


class CambiarEstadoSalaUseCase(BaseUseCase[CambiarEstadoSalaDTO, str]):
    """
    El anfitrión (o un admin) abre o cierra los ingresos, o finaliza la sala.
    Cerrar no saca a nadie: quienes ya entraron siguen trabajando. Finalizar
    congela el tablero y deja de dar recompensas.
    """

    def __init__(self, unit_of_work, event_dispatcher, sala_repository: ISalaRepository):
        super().__init__(unit_of_work, event_dispatcher)
        self._sala_repository = sala_repository

    def _validate(self, input_dto: CambiarEstadoSalaDTO) -> None:
        sala = self._sala_repository.get_by_id(input_dto.sala_id)
        # Mismo 404 para "no existe" y "no es tuya": no se confirma que exista.
        if sala is None or (input_dto.actor_rol != "administrador" and sala.anfitrion_id != input_dto.actor_id):
            raise NotFoundError(_NO_ENCONTRADA_MSG)
        try:
            self._nuevo = EstadoSala(input_dto.estado)
        except ValueError as exc:
            raise ValidationError(_ESTADO_INVALIDO_MSG) from exc
        self._sala = sala

    def _execute_domain_logic(self, input_dto: CambiarEstadoSalaDTO) -> tuple[str, list[DomainEvent]]:
        self._sala.cambiar_estado(self._nuevo)
        self._sala_repository.update(self._sala)
        evento = EstadoSalaCambiado(sala_id=self._sala.id, actor_id=input_dto.actor_id, estado=self._nuevo.value)
        return self._nuevo.value, [evento]
