from django.db import transaction


class BaseUnitOfWork:
    """
    Implementación de `IUnitOfWork` (ver modules.shared.application.ports)
    sobre `django.db.transaction.atomic`.

    Se usa como context manager dentro de `BaseUseCase.execute`:

        with self._uow:
            result, events = self._execute_domain_logic(input_dto)
            self._uow.commit()

    - Si el bloque termina sin excepciones y se llamó a `commit()`, la
      transacción se confirma (Postgres) al salir del `with`.
    - Si el bloque lanza una excepción (ej. una regla de negocio violada
      dentro de un repositorio), Django hace rollback automático de todo lo
      escrito en la transacción — no queda estado parcial.
    - Soporta anidamiento: si ya existe una transacción atómica abierta
      (ej. en un test), Django la trata como savepoint interno en vez de
      abrir una nueva conexión.

    Cada módulo puede tener su propia subclase (`ILaboratorioUnitOfWork`,
    etc.) si necesita exponer repositorios específicos en el `with`, pero
    el mecanismo de atomicidad es siempre este mismo.
    """

    def __enter__(self) -> "BaseUnitOfWork":
        self._atomic = transaction.atomic()
        self._atomic.__enter__()
        self._committed = False
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            # Propaga la excepción; Django hace rollback de la transacción.
            self._atomic.__exit__(exc_type, exc_val, exc_tb)
            return False

        if not self._committed:
            # Se salió del `with` sin llamar a commit() explícitamente:
            # se fuerza rollback para no persistir estado a medias.
            transaction.set_rollback(True)

        self._atomic.__exit__(None, None, None)
        return False

    def commit(self) -> None:
        self._committed = True

    def rollback(self) -> None:
        transaction.set_rollback(True)
        self._committed = False
