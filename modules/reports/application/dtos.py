import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CrearReporteDTO:
    """
    HE-12, api.md §8 `POST /reports/` (UC-09): `archivo_*` son opcionales
    (adjunto único, seguridad.md §4) — si vienen, se validan y guardan
    vía `storage_adapter.guardar_adjunto` antes de persistir.
    """

    estudiante_id: uuid.UUID
    actor_rol: str
    laboratorio_id: uuid.UUID
    descripcion: str
    seccion_id: uuid.UUID | None = None
    archivo_nombre: str | None = None
    archivo_contenido: bytes | None = None


@dataclass(frozen=True)
class ReporteResultDTO:
    id: uuid.UUID
    laboratorio_id: uuid.UUID
    estado: str
    fecha_creacion: datetime


@dataclass(frozen=True)
class CambiarEstadoReporteDTO:
    """api.md §8 `PATCH /reports/{id}/` — solo Admin (UC-09, pasos 2-3/A1)."""

    reporte_id: uuid.UUID
    actor_id: uuid.UUID
    actor_rol: str
    nuevo_estado: str


@dataclass(frozen=True)
class ListarReportesPropiosDTO:
    estudiante_id: uuid.UUID


@dataclass(frozen=True)
class ListarReportesDTO:
    """api.md §8 `GET /reports/?estado=&laboratorio=` — solo Admin."""

    actor_rol: str
    estado: str | None = None
    laboratorio_id: uuid.UUID | None = None


@dataclass(frozen=True)
class ReporteListItemDTO:
    id: uuid.UUID
    laboratorio_id: uuid.UUID
    estado: str
    descripcion: str
    fecha_creacion: datetime
    fecha_resolucion: datetime | None
