import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from modules.shared.domain.base_entity import BaseEntity
from modules.shared.domain.tiempo import ahora_utc
from modules.users.domain.value_objects import Email, Rol, SolicitudInstructorEstado


class ProveedorTipo(str, Enum):
    EMAIL = "email"
    GOOGLE = "google"
    GITHUB = "github"


@dataclass(eq=False)
class User(BaseEntity):
    """
    Entidad raíz del agregado User (dominio.md §4). No conoce Django ni la
    base de datos — el mapeo hacia/desde el modelo ORM ocurre en
    `infrastructure/mappers.py` (tarea posterior).
    """

    email: Email
    nombre_completo: str
    rol: Rol = Rol.ESTUDIANTE
    username: str | None = None
    password_hash: str | None = None
    is_active: bool = True
    date_joined: datetime = field(default_factory=ahora_utc)
    last_login: datetime | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        BaseEntity.__init__(self, id=self.id)


@dataclass(eq=False)
class ProveedorAutenticacion(BaseEntity):
    """Método de acceso vinculado a un User (dominio.md §1)."""

    user_id: uuid.UUID
    proveedor: ProveedorTipo
    proveedor_uid: str
    created_at: datetime = field(default_factory=ahora_utc)
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        BaseEntity.__init__(self, id=self.id)


@dataclass(eq=False)
class SolicitudInstructor(BaseEntity):
    """
    Solicitud de un estudiante para convertirse en instructor. OpenAlex
    (`IVerificadorAcademicoProvider`) aporta evidencia — si el ORCID existe,
    si el nombre coincide, cuántas publicaciones tiene — que queda en
    `resultado_verificacion`; la decisión la toma un administrador
    (`ResolverSolicitudInstructorUseCase`), porque OpenAlex no puede probar
    que quien escribe el ORCID sea su dueño.
    """

    user_id: uuid.UUID
    orcid: str
    nombre_declarado: str
    tipo: str
    institucion: str = ""
    especialidades: str = ""
    motivacion: str = ""
    estado: SolicitudInstructorEstado = SolicitudInstructorEstado.PENDIENTE
    motivo_rechazo: str | None = None
    resultado_verificacion: dict | None = None
    created_at: datetime = field(default_factory=ahora_utc)
    resolved_at: datetime | None = None
    revisada_por_id: uuid.UUID | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        BaseEntity.__init__(self, id=self.id)
