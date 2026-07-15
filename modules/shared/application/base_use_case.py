from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from modules.shared.application.ports import IEventDispatcher, IUnitOfWork
from modules.shared.domain.domain_event import DomainEvent

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")


class BaseUseCase(ABC, Generic[TInput, TOutput]):
    """
    Template Method para todo caso de uso de escritura (no aplica a Queries
    de solo lectura, que no necesitan UnitOfWork ni eventos).

    Flujo fijo, igual para los 8 módulos:
      1. Validar entrada       (_validate)
      2. Ejecutar lógica de dominio, dentro de una transacción atómica
         (_execute_domain_logic), que devuelve el resultado + los eventos
         de dominio a despachar.
      3. Persistir vía Unit of Work (commit automático al salir del `with`
         sin excepciones; rollback automático si algo falla).
      4. Despachar los eventos de dominio recolectados (ej. dispara
         notificaciones, auditoría) — solo si la transacción fue exitosa.

    Cada caso de uso concreto (ej. `AceptarInvitacionUseCase`) implementa
    únicamente `_validate` y `_execute_domain_logic`; nunca sobrescribe
    `execute`.
    """

    def __init__(self, unit_of_work: IUnitOfWork, event_dispatcher: IEventDispatcher):
        self._uow = unit_of_work
        self._event_dispatcher = event_dispatcher

    def execute(self, input_dto: TInput) -> TOutput:
        self._validate(input_dto)

        with self._uow:
            result, events = self._execute_domain_logic(input_dto)
            self._uow.commit()

        self._dispatch_events(events)
        return result

    @abstractmethod
    def _validate(self, input_dto: TInput) -> None:
        """
        Valida reglas de negocio previas a ejecutar (ej. propiedad del
        recurso, estado requerido). Lanza una excepción de
        `modules.shared.domain.exceptions` si algo no cumple.
        """
        raise NotImplementedError

    @abstractmethod
    def _execute_domain_logic(self, input_dto: TInput) -> tuple[TOutput, list[DomainEvent]]:
        """
        Ejecuta la lógica de dominio propiamente dicha y devuelve el
        resultado a retornar junto con los eventos de dominio generados
        (ej. `AssignmentAccepted`). No hace commit ni despacha eventos
        directamente — eso lo controla `execute`.
        """
        raise NotImplementedError

    def _dispatch_events(self, events: list[DomainEvent]) -> None:
        for event in events:
            self._event_dispatcher.dispatch(event)
