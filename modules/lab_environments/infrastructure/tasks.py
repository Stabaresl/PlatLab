from celery import shared_task
from django.conf import settings

from modules.lab_environments.application.use_cases.reap_entornos_inactivos import (
    ReapEntornosInactivosUseCase,
)
from modules.lab_environments.infrastructure.docker_provider import DockerContenedorProvider
from modules.lab_environments.infrastructure.repositories import EntornoRepository
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


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
