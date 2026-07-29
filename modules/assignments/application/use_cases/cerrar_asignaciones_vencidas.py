from modules.assignments.domain.events import AssignmentExpired
from modules.assignments.domain.repositories import IAsignacionRepository
from modules.assignments.domain.services import GestorDeVencimientos


class CerrarAsignacionesVencidasUseCase:
    """
    RF-32, UC-07: orquesta `GestorDeVencimientos` sobre las asignaciones
    activas con fecha de vencimiento. Sin `actor_id`/`actor_rol` (lo
    dispara `CerrarAsignacionesVencidasJob` vía Celery Beat, no un
    usuario) — por eso no extiende `BaseUseCase`, que exige un DTO de
    entrada con actor.
    """

    def __init__(
        self,
        unit_of_work,
        event_dispatcher,
        asignacion_repository: IAsignacionRepository,
    ):
        self._uow = unit_of_work
        self._event_dispatcher = event_dispatcher
        self._asignacion_repository = asignacion_repository

    def execute(self) -> int:
        activas = self._asignacion_repository.find_activas_con_vencimiento()

        with self._uow:
            vencidas = GestorDeVencimientos().identificar_vencidas(activas)
            for asignacion in vencidas:
                self._asignacion_repository.update(asignacion)
            self._uow.commit()

        for asignacion in vencidas:
            self._event_dispatcher.dispatch(
                AssignmentExpired(
                    asignacion_id=asignacion.id, estudiante_id=asignacion.estudiante_id
                )
            )
        return len(vencidas)
