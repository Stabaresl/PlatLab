from celery import shared_task

from modules.assignments.application.use_cases.cerrar_asignaciones_vencidas import (
    CerrarAsignacionesVencidasUseCase,
)
from modules.assignments.infrastructure.repositories import AsignacionRepository
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


@shared_task(name="modules.assignments.infrastructure.tasks.cerrar_asignaciones_vencidas_task")
def cerrar_asignaciones_vencidas_task() -> int:
    """
    RF-32, UC-07: `CerrarAsignacionesVencidasJob` — disparada por Celery
    Beat (`config/celery.py`) cada 15 minutos. Devuelve la cantidad de
    asignaciones cerradas (visible en los logs del worker).
    """
    use_case = CerrarAsignacionesVencidasUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        asignacion_repository=AsignacionRepository(),
    )
    return use_case.execute()
