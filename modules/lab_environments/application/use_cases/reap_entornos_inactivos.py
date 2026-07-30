from datetime import datetime, timedelta, timezone

from modules.lab_environments.domain.ports import IContenedorProvider
from modules.lab_environments.domain.repositories import IEntornoRepository


class ReapEntornosInactivosUseCase:
    """
    RNF de rendimiento/estabilidad: protege al host de acumular
    contenedores olvidados. Disparado por `CerrarAsignacionesVencidasJob`-
    style Celery Beat (`infrastructure/tasks.py`), no por un usuario — sin
    `actor_id`/`actor_rol`, mismo criterio que
    `CerrarAsignacionesVencidasUseCase`. Dos gatillos independientes:

    - Inactividad: sin comandos en `idle_timeout_minutos` (el estudiante
      se fue sin avisar).
    - Vida máxima: `max_lifetime_minutos` desde que arrancó, sin importar
      actividad (nunca un contenedor corre indefinidamente, aunque el
      estudiante deje una sesión de terminal abierta todo el día).
    """

    def __init__(
        self,
        unit_of_work,
        entorno_repository: IEntornoRepository,
        contenedor_provider: IContenedorProvider,
        idle_timeout_minutos: int = 20,
        max_lifetime_minutos: int = 120,
    ):
        self._uow = unit_of_work
        self._entorno_repository = entorno_repository
        self._contenedor_provider = contenedor_provider
        self._idle_timeout = timedelta(minutes=idle_timeout_minutos)
        self._max_lifetime = timedelta(minutes=max_lifetime_minutos)

    def execute(self) -> int:
        ahora = datetime.now(timezone.utc)
        apagados = 0

        for entorno in self._entorno_repository.get_todos_activos():
            inactivo = ahora - self._como_utc(entorno.ultima_actividad) > self._idle_timeout
            vida_maxima_superada = ahora - self._como_utc(entorno.fecha_inicio) > self._max_lifetime
            if not (inactivo or vida_maxima_superada):
                continue

            with self._uow:
                self._contenedor_provider.detener(entorno.container_id)
                entorno.marcar_detenido()
                self._entorno_repository.update(entorno)
                self._uow.commit()
            apagados += 1

        return apagados

    @staticmethod
    def _como_utc(valor: datetime) -> datetime:
        return valor if valor.tzinfo is not None else valor.replace(tzinfo=timezone.utc)
