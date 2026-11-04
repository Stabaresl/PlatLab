from modules.rooms.application.dtos import RegistrarCompletitudSalaDTO
from modules.rooms.domain.events import SalaCompletadaPorEstudiante
from modules.rooms.domain.repositories import IParticipanteSalaRepository, ISalaRepository
from modules.rooms.domain.value_objects import EstadoSala
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.tiempo import ahora_utc


class RegistrarCompletitudSalaUseCase(BaseUseCase[RegistrarCompletitudSalaDTO, list[int]]):
    """
    La invocan los listeners de Progress cuando una asignación termina su
    laboratorio. Por cada sala donde esa asignación compite, le asigna el
    siguiente puesto (1.º, 2.º, ...) y emite `SalaCompletadaPorEstudiante`.
    Idempotente: un reintento del examen no vuelve a dar puesto. Una sala
    finalizada ya no reparte puestos.
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        sala_repository: ISalaRepository,
        participante_repository: IParticipanteSalaRepository,
    ):
        super().__init__(unit_of_work, event_dispatcher)
        self._sala_repository = sala_repository
        self._participante_repository = participante_repository

    def _validate(self, input_dto: RegistrarCompletitudSalaDTO) -> None:
        self._participaciones = [
            p for p in self._participante_repository.find_por_asignacion(input_dto.asignacion_id) if p.compite
        ]

    def _execute_domain_logic(self, input_dto: RegistrarCompletitudSalaDTO) -> tuple[list[int], list[DomainEvent]]:
        puestos: list[int] = []
        eventos: list[DomainEvent] = []
        for participante in self._participaciones:
            sala = self._sala_repository.bloquear(participante.sala_id)
            if sala.estado == EstadoSala.FINALIZADA:
                continue
            puesto = self._participante_repository.contar_completados(sala.id) + 1
            participante.posicion_final = puesto
            participante.fecha_completado = ahora_utc()
            self._participante_repository.update(participante)
            puestos.append(puesto)
            eventos.append(
                SalaCompletadaPorEstudiante(
                    sala_id=sala.id,
                    sala_nombre=sala.nombre,
                    estudiante_id=participante.estudiante_id,
                    anfitrion_id=sala.anfitrion_id,
                    posicion=puesto,
                )
            )
        return puestos, eventos
