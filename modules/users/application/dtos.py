import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.users.domain.verificacion_academica import ResultadoVerificacionAcademica


@dataclass(frozen=True)
class ListarUsuariosDTO:
    """HA-01, api.md §4 `GET /users/?nombre=&rol=&activo=` — solo Admin."""

    actor_rol: str
    nombre: str | None = None
    rol: str | None = None
    activo: bool | None = None


@dataclass(frozen=True)
class UsuarioListItemDTO:
    id: uuid.UUID
    email: str
    nombre_completo: str
    rol: str
    is_active: bool


@dataclass(frozen=True)
class ActualizarUsuarioDTO:
    """api.md §4 `PATCH /users/{id}/` — edita rol/datos (no password)."""

    usuario_id: uuid.UUID
    actor_id: uuid.UUID
    actor_rol: str
    nombre_completo: str | None = None
    rol: str | None = None
    username: str | None = None


@dataclass(frozen=True)
class UsuarioResultDTO:
    id: uuid.UUID
    email: str
    nombre_completo: str
    rol: str
    is_active: bool


@dataclass(frozen=True)
class DeshabilitarUsuarioDTO:
    usuario_id: uuid.UUID
    actor_id: uuid.UUID
    actor_rol: str


@dataclass(frozen=True)
class HabilitarUsuarioDTO:
    usuario_id: uuid.UUID
    actor_id: uuid.UUID
    actor_rol: str


@dataclass(frozen=True)
class ObtenerDashboardAdminDTO:
    """HA-03, api.md §4 `GET /users/dashboard/` — solo Admin."""

    actor_rol: str


@dataclass(frozen=True)
class LabPopularDTO:
    laboratorio_id: uuid.UUID
    nombre: str
    estudiantes_inscritos: int


@dataclass(frozen=True)
class DashboardAdminResultDTO:
    usuarios_por_rol: dict[str, int]
    laboratorios_activos: int
    labs_mas_populares: list[LabPopularDTO]
    tasa_completitud_promedio: float


@dataclass(frozen=True)
class SolicitarInstructorDTO:
    actor_id: uuid.UUID
    actor_rol: str
    orcid: str
    tipo: str
    institucion: str = ""
    especialidades: str = ""
    motivacion: str = ""


@dataclass(frozen=True)
class SolicitudInstructorResultDTO:
    id: uuid.UUID
    estado: str
    orcid: str
    motivo_rechazo: str | None = None
    created_at: datetime | None = None


@dataclass(frozen=True)
class RegistrarVerificacionOpenAlexDTO:
    solicitud_id: uuid.UUID
    resultado: ResultadoVerificacionAcademica


@dataclass(frozen=True)
class ResolverSolicitudInstructorDTO:
    """`POST /users/instructor-requests/{id}/approve|reject/` — solo Admin."""

    solicitud_id: uuid.UUID
    actor_id: uuid.UUID
    actor_rol: str
    aprobar: bool
    motivo: str | None = None


@dataclass(frozen=True)
class SolicitudInstructorAdminItemDTO:
    """Item de la cola de revisión: datos de la cuenta + lo declarado + resultado de OpenAlex."""

    id: uuid.UUID
    estado: str
    orcid: str
    tipo: str
    institucion: str
    especialidades: str
    motivacion: str
    nombre_declarado: str
    usuario_id: uuid.UUID
    usuario_email: str | None
    usuario_nombre: str | None
    usuario_desde: datetime | None
    resultado_openalex: dict | None
    motivo_rechazo: str | None
    created_at: datetime | None
    resolved_at: datetime | None
