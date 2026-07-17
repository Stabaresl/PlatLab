import uuid
from typing import Protocol

from modules.users.domain.entities import ProveedorAutenticacion, User


class IUserRepository(Protocol):
    """
    Puerto de persistencia del agregado User. La implementación real
    (Infrastructure) vive en `infrastructure/repositories.py` y traduce
    hacia/desde el ORM de Django vía `mappers.py`.

    Se usa tanto desde Users como desde Authentication (backend.md §1: "vía
    su Application Service") — Authentication nunca importa el modelo ORM
    directamente, solo consume esta interfaz.
    """

    def get_by_id(self, user_id: uuid.UUID) -> User | None: ...

    def get_by_email(self, email: str) -> User | None: ...

    def get_by_username(self, username: str) -> User | None: ...

    def exists_by_email(self, email: str) -> bool: ...

    def add(self, user: User) -> User: ...

    def update(self, user: User) -> User: ...

    def add_proveedor(self, proveedor: ProveedorAutenticacion) -> ProveedorAutenticacion: ...

    def get_proveedores_by_user_id(self, user_id: uuid.UUID) -> list[ProveedorAutenticacion]: ...

    def get_by_proveedor(
        self, proveedor: str, proveedor_uid: str
    ) -> User | None: ...
