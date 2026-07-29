import uuid
from dataclasses import dataclass


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
