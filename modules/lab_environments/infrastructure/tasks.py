import uuid

from celery import shared_task
from django.conf import settings

from modules.lab_environments.application.use_cases.aprovisionar_entorno import (
    AprovisionarEntornoUseCase,
)
from modules.lab_environments.application.use_cases.reap_entornos_inactivos import (
    ReapEntornosInactivosUseCase,
)
from modules.lab_environments.infrastructure.docker_provider import DockerContenedorProvider
from modules.lab_environments.infrastructure.repositories import EntornoRepository
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


@shared_task(
    name="modules.lab_environments.infrastructure.tasks.aprovisionar_entorno_task",
    time_limit=30,
    max_retries=0,
)
def aprovisionar_entorno_task(entorno_id: str, imagen: str) -> None:
    """
    Encolada por `event_listeners.py` al crear un `EntornoActivo` en
    estado `iniciando` (RF rendimiento — ver `IniciarEntornoUseCase`, que
    ya no bloquea el request web con `containers.run()`). Sin reintentos:
    si Docker falla acá, `AprovisionarEntornoUseCase` deja el entorno en
    `error`; reintentar solo repetiría la misma falla (imagen inexistente,
    host sin cupo) — el estudiante ve el error y puede volver a intentar
    desde el botón, que crea un pedido nuevo.
    """
    AprovisionarEntornoUseCase(
        unit_of_work=BaseUnitOfWork(),
        entorno_repository=EntornoRepository(),
        contenedor_provider=DockerContenedorProvider(),
    ).execute(uuid.UUID(entorno_id), imagen)


@shared_task(name="modules.lab_environments.infrastructure.tasks.reap_idle_environments_task")
def reap_idle_environments_task() -> int:
    """
    Disparada por Celery Beat (`config/celery.py`) cada 2 minutos — apaga
    contenedores de práctica inactivos o que superaron su vida máxima
    (RNF de rendimiento: sin esto, contenedores olvidados se acumulan y
    degradan al host). Devuelve la cantidad de entornos apagados.
    """
    use_case = ReapEntornosInactivosUseCase(
        unit_of_work=BaseUnitOfWork(),
        entorno_repository=EntornoRepository(),
        contenedor_provider=DockerContenedorProvider(),
        idle_timeout_minutos=settings.LAB_ENV_IDLE_MINUTES,
        max_lifetime_minutos=settings.LAB_ENV_MAX_LIFETIME_MINUTES,
    )
    return use_case.execute()
