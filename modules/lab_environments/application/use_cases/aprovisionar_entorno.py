import uuid

from modules.lab_environments.domain.ports import IContenedorProvider
from modules.lab_environments.domain.repositories import IEntornoRepository
from modules.lab_environments.domain.value_objects import EstadoEntorno


class AprovisionarEntornoUseCase:
    """
    Fase asíncrona de `IniciarEntornoUseCase`: arranca el contenedor
    Docker real de un `EntornoActivo` que ya quedó creado en estado
    `iniciando`. Disparada por Celery (`infrastructure/tasks.py`), no por
    un usuario directamente — mismo criterio que
    `ReapEntornosInactivosUseCase` (sin `actor_id`/`actor_rol`, no hereda
    `BaseUseCase`).
    """

    def __init__(
        self,
        unit_of_work,
        entorno_repository: IEntornoRepository,
        contenedor_provider: IContenedorProvider,
    ):
        self._uow = unit_of_work
        self._entorno_repository = entorno_repository
        self._contenedor_provider = contenedor_provider

    def execute(self, entorno_id: uuid.UUID, imagen: str) -> None:
        entorno = self._entorno_repository.get_by_id(entorno_id)
        if entorno is None or entorno.estado != EstadoEntorno.INICIANDO:
            # Ya se detuvo/quedó en error por otra vía (ej. el estudiante
            # cerró la pestaña y el reaper lo alcanzó primero) — nada que
            # aprovisionar.
            return

        try:
            container_id = self._contenedor_provider.iniciar(imagen)
        except Exception:  # noqa: BLE001 - cualquier falla de Docker deja el entorno en error, no se propaga (corre en un worker, sin quien atrape la excepción)
            with self._uow:
                entorno.marcar_error()
                self._entorno_repository.update(entorno)
                self._uow.commit()
            return

        with self._uow:
            entorno.container_id = container_id
            entorno.marcar_activo()
            self._entorno_repository.update(entorno)
            self._uow.commit()
