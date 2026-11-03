import uuid
from typing import Protocol

from modules.users.domain.entities import ProveedorAutenticacion, SolicitudInstructor, User


class IUserRepository(Protocol):
    """
    Puerto de persistencia del agregado User. La implementación real
    (Infrastructure) vive en `infrastructure/repositories.py` y traduce
    hacia/desde el ORM de Django vía `mappers.py`.

    Se usa tanto desde Users como desde Authentication (backend.md "vía
    Application Service") — Authentication nunca importa el modelo ORM
    directamente, solo consume esta interfaz.
    """

    def get_by_id(self, user_id: uuid.UUID) -> User | None: ...

    def find_all(
        self,
        nombre: str | None = None,
        rol: str | None = None,
        activo: bool | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[User]:
        """HA-01, api.md §4 `GET /users/?nombre=&rol=&activo=`. Paginado en BD si se pasa `limit`."""
        ...

    def contar(
        self, nombre: str | None = None, rol: str | None = None, activo: bool | None = None
    ) -> int: ...

    def contar_por_rol(self) -> dict[str, int]:
        """HA-03: `{rol: total}` en una sola consulta agregada (sin traer usuarios a memoria)."""
        ...

    def get_by_ids(self, user_ids: list[uuid.UUID]) -> dict[uuid.UUID, User]:
        """Batch por id — evita N+1 en listados que resuelven nombres (HI-04)."""
        ...

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


class ISolicitudInstructorRepository(Protocol):
    """Puerto de persistencia de `SolicitudInstructor` (verificación OpenAlex)."""

    def get_by_id(self, solicitud_id: uuid.UUID) -> SolicitudInstructor | None: ...

    def get_pendiente_by_user_id(self, user_id: uuid.UUID) -> SolicitudInstructor | None: ...

    def get_ultima_by_user_id(self, user_id: uuid.UUID) -> SolicitudInstructor | None: ...

    def find_por_estado(self, estado: str | None) -> list[SolicitudInstructor]:
        """Cola de revisión del admin (`estado=None` = todas)."""
        ...

    def add(self, solicitud: SolicitudInstructor) -> SolicitudInstructor: ...

    def update(self, solicitud: SolicitudInstructor) -> SolicitudInstructor: ...
