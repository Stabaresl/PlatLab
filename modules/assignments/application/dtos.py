import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class InvitarEstudiantesDTO:
    """
    api.md §6 `POST /assignments/invitations/` (UC-06): `estudiantes` es
    una lista de email o username (HI-09) — se resuelve a `User` vía
    `IUserRepository` (id suelto, Arquitectura §8). `fecha_vencimiento`
    es opcional en este sprint; la validación completa de ventana
    (`VentanaVencimiento`) llega en HI-07 (Sprint 5).
    """

    laboratorio_id: uuid.UUID
    estudiantes: list[str]
    actor_id: uuid.UUID
    actor_rol: str
    fecha_vencimiento: datetime | None = None


@dataclass(frozen=True)
class InvitacionResultDTO:
    identificador: str
    resultado: str  # "invitado" | "ya_vigente" | "no_encontrado"
    asignacion_id: uuid.UUID | None = None


@dataclass(frozen=True)
class InvitarEstudiantesResultDTO:
    invitaciones: list[InvitacionResultDTO] = field(default_factory=list)


@dataclass(frozen=True)
class InscribirseLaboratorioDTO:
    """Autoinscripción del estudiante a un laboratorio del catálogo público (sin invitación)."""

    laboratorio_id: uuid.UUID
    actor_id: uuid.UUID
    actor_rol: str


@dataclass(frozen=True)
class AceptarInvitacionDTO:
    asignacion_id: uuid.UUID
    estudiante_id: uuid.UUID


@dataclass(frozen=True)
class RechazarInvitacionDTO:
    asignacion_id: uuid.UUID
    estudiante_id: uuid.UUID


@dataclass(frozen=True)
class AsignacionResultDTO:
    id: uuid.UUID
    laboratorio_id: uuid.UUID
    estado: str


@dataclass(frozen=True)
class ListarAsignacionesDTO:
    """api.md §6 `GET /assignments/`: instructor ve las que creó; estudiante, las suyas."""

    actor_id: uuid.UUID
    actor_rol: str


@dataclass(frozen=True)
class AsignacionListItemDTO:
    id: uuid.UUID
    estudiante_id: uuid.UUID
    laboratorio_id: uuid.UUID
    estado: str
    fecha_invitacion: datetime
    fecha_vencimiento: datetime | None


@dataclass(frozen=True)
class FiltrarEstudiantesDTO:
    """HI-04: filtros combinables, solo estudiantes con labs asignados por ese instructor."""

    instructor_id: uuid.UUID
    actor_rol: str
    nombre: str | None = None
    laboratorio_id: uuid.UUID | None = None


@dataclass(frozen=True)
class EstudianteFiltradoDTO:
    estudiante_id: uuid.UUID
    nombre_completo: str
    laboratorio_id: uuid.UUID
    estado_asignacion: str
    porcentaje_completitud: float


@dataclass(frozen=True)
class ObtenerDashboardDTO:
    """HI-06: panel principal del instructor."""

    instructor_id: uuid.UUID
    actor_rol: str


@dataclass(frozen=True)
class LaboratorioDashboardItemDTO:
    laboratorio_id: uuid.UUID
    nombre: str
    estado: str
    estudiantes_inscritos: int
    porcentaje_completitud_promedio: float
    tipo: str = "personalizado"
    visible_en_catalogo: bool = False
