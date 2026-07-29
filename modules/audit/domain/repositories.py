import uuid
from datetime import datetime
from typing import Protocol

from modules.audit.domain.entities import RegistroAuditoria


class IAuditoriaRepository(Protocol):
    """
    Puerto de persistencia del agregado RegistroAuditoria. Append-only
    (UC-12): deliberadamente no expone `update` ni `delete`, solo `add`
    y lecturas. La implementación real vive en
    `infrastructure/repositories.py` (PostgreSQL vía `mappers.py`).
    """

    def add(self, registro: RegistroAuditoria) -> RegistroAuditoria: ...

    def find_todos(
        self,
        actor_id: uuid.UUID | None = None,
        accion: str | None = None,
        desde: datetime | None = None,
        hasta: datetime | None = None,
    ) -> list[RegistroAuditoria]:
        """api.md §10 `GET /audit/?actor=&accion=&desde=&hasta=` — solo Admin."""
        ...
