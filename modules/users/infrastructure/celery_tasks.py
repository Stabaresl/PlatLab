import uuid

import requests
from celery import shared_task

from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork
from modules.users.application.dtos import RegistrarVerificacionOpenAlexDTO
from modules.users.application.use_cases.registrar_verificacion_openalex import (
    RegistrarVerificacionOpenAlexUseCase,
)
from modules.users.domain.value_objects import SolicitudInstructorEstado
from modules.users.infrastructure.openalex_adapter import OpenAlexAdapter
from modules.users.infrastructure.repositories import SolicitudInstructorRepository


@shared_task(
    name="modules.users.infrastructure.celery_tasks.verificar_solicitud_instructor_task",
    autoretry_for=(requests.RequestException,),
    retry_backoff=True,
    max_retries=5,
)
def verificar_solicitud_instructor_task(solicitud_id: str) -> None:
    """
    Encolada por `event_listeners.py` al crear una `SolicitudInstructor` —
    corre en el worker, nunca dentro del request que la creó. Consulta
    OpenAlex y guarda el resultado como evidencia para el admin que va a
    revisar la solicitud (no la aprueba ni la rechaza). Solo reintenta
    ante fallas de red/timeout (`requests.RequestException`): un ORCID no
    encontrado es un resultado válido, no un error. Si OpenAlex no
    responde tras los reintentos, la solicitud queda sin resultado y el
    admin lo ve así en su panel.
    """
    solicitud_repository = SolicitudInstructorRepository()
    solicitud = solicitud_repository.get_by_id(uuid.UUID(solicitud_id))
    if solicitud is None or solicitud.estado != SolicitudInstructorEstado.PENDIENTE:
        return

    resultado = OpenAlexAdapter().verificar(
        orcid=solicitud.orcid, nombre_declarado=solicitud.nombre_declarado
    )

    RegistrarVerificacionOpenAlexUseCase(
        BaseUnitOfWork(), EventDispatcher(), solicitud_repository
    ).execute(RegistrarVerificacionOpenAlexDTO(solicitud_id=solicitud.id, resultado=resultado))
