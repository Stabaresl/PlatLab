import uuid

import requests
from celery import shared_task

from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork
from modules.users.application.dtos import ProcesarVerificacionInstructorDTO
from modules.users.application.use_cases.procesar_verificacion_instructor import (
    ProcesarVerificacionInstructorUseCase,
)
from modules.users.domain.value_objects import SolicitudInstructorEstado
from modules.users.infrastructure.openalex_adapter import OpenAlexAdapter
from modules.users.infrastructure.repositories import SolicitudInstructorRepository, UserRepository


@shared_task(
    name="modules.users.infrastructure.celery_tasks.verificar_solicitud_instructor_task",
    autoretry_for=(requests.RequestException,),
    retry_backoff=True,
    max_retries=5,
)
def verificar_solicitud_instructor_task(solicitud_id: str) -> None:
    """
    Encolada por `event_listeners.py` al crear una `SolicitudInstructor` —
    corre en el worker, nunca dentro del request que la creó. Solo
    reintenta ante fallas de red/timeout hacia OpenAlex
    (`requests.RequestException`); un ORCID no encontrado o un nombre que
    no coincide no es un error de red, es un rechazo legítimo, así que no
    se reintenta.
    """
    solicitud_repository = SolicitudInstructorRepository()
    solicitud = solicitud_repository.get_by_id(uuid.UUID(solicitud_id))
    if solicitud is None or solicitud.estado != SolicitudInstructorEstado.PENDIENTE:
        return

    resultado = OpenAlexAdapter().verificar(
        orcid=solicitud.orcid, nombre_declarado=solicitud.nombre_declarado
    )

    use_case = ProcesarVerificacionInstructorUseCase(
        BaseUnitOfWork(),
        EventDispatcher(),
        solicitud_repository,
        UserRepository(),
    )
    use_case.execute(
        ProcesarVerificacionInstructorDTO(solicitud_id=solicitud.id, resultado=resultado)
    )
