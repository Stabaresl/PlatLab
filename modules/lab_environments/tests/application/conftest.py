import pytest

import modules.lab_environments.infrastructure.tasks as lab_tasks


class FakeContenedorProvider:
    """Doble de prueba — no toca Docker real, para tests rápidos y deterministas."""

    def __init__(self, falla_al_iniciar: bool = False):
        self.iniciados: list[str] = []
        self.detenidos: list[str] = []
        self._falla = falla_al_iniciar
        self._contador = 0

    def iniciar(self, imagen: str) -> str:
        if self._falla:
            raise RuntimeError("docker no disponible (simulado)")
        self._contador += 1
        container_id = f"fake-container-{self._contador}"
        self.iniciados.append(container_id)
        return container_id

    def detener(self, container_id: str) -> None:
        self.detenidos.append(container_id)

    def esta_vivo(self, container_id: str) -> bool:
        return container_id in self.iniciados and container_id not in self.detenidos


@pytest.fixture
def fake_docker(monkeypatch):
    """
    CELERY_TASK_ALWAYS_EAGER (config/settings/test.py) hace que
    `aprovisionar_entorno_task` corra síncrono, disparada por el listener
    de `infrastructure/event_listeners.py`, dentro del mismo
    `IniciarEntornoUseCase.execute()` que crea el evento — sin este
    parche, cualquier test que arranque un `EntornoActivo` nuevo
    terminaría llamando a Docker real. Mismo criterio que
    `test_solicitar_instructor.py` con `openalex_adapter.requests.get`:
    se deja correr la cadena real (evento -> tarea -> caso de uso), solo
    se reemplaza la dependencia externa real.
    """
    provider = FakeContenedorProvider()
    monkeypatch.setattr(lab_tasks, "DockerContenedorProvider", lambda: provider)
    return provider
