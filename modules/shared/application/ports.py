from typing import Protocol

from modules.shared.domain.domain_event import DomainEvent


class IUnitOfWork(Protocol):
    """
    Puerto de persistencia atómica. La implementación real (Infrastructure,
    tarea Sprint 0 #7) envuelve una transacción de PostgreSQL. Se usa como
    context manager: si el bloque `with` falla, hace rollback automático.
    """

    def __enter__(self) -> "IUnitOfWork": ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


class IEventDispatcher(Protocol):
    """
    Puerto de despacho de eventos de dominio. La implementación real
    (Infrastructure, tarea Sprint 0 #6) invoca los listeners registrados
    para cada tipo de evento.
    """

    def dispatch(self, event: DomainEvent) -> None: ...
