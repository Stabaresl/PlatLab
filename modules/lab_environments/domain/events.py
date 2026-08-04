import uuid
from dataclasses import dataclass

from modules.shared.domain.domain_event import DomainEvent


@dataclass(frozen=True, kw_only=True)
class EntornoAprovisionamientoSolicitado(DomainEvent):
    """
    Se creó un `EntornoActivo` en estado `iniciando` — todavía sin
    contenedor real detrás. El listener de infraestructura (ver
    `infrastructure/event_listeners.py`) encola la tarea de Celery que
    llama a `IContenedorProvider.iniciar()` fuera del ciclo
    request/response: `containers.run()` más el poll de HEALTHCHECK puede
    tardar hasta ~10s, y con varios estudiantes arrancando a la vez eso
    agota el pool de workers web (RNF rendimiento).
    """

    entorno_id: uuid.UUID
    imagen: str
