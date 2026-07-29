import uuid
from dataclasses import dataclass, field
from datetime import datetime

from modules.reports.domain.exceptions import DescriptionTooShortError, ReporteYaResueltoError
from modules.reports.domain.value_objects import EstadoReporte
from modules.shared.domain.base_entity import BaseEntity

_DESCRIPCION_MINIMA = 10
_DESCRIPCION_CORTA_MSG = f"La descripción debe tener al menos {_DESCRIPCION_MINIMA} caracteres."
_YA_RESUELTO_MSG = "Este reporte ya fue resuelto."
_ESTADOS_FINALES = (EstadoReporte.RESUELTO, EstadoReporte.NO_REPRODUCIBLE)


@dataclass(eq=False)
class Reporte(BaseEntity):
    """
    HE-12/HA-05, dominio.md, base-de-datos.md "reports_reporte". `id
    suelto` a `estudiante_id`/`laboratorio_id`/`seccion_id`
    (Arquitectura §8) — Reports no depende de Users/Laboratories.
    """

    estudiante_id: uuid.UUID
    laboratorio_id: uuid.UUID
    descripcion: str
    seccion_id: uuid.UUID | None = None
    estado: EstadoReporte = EstadoReporte.ABIERTO
    fecha_creacion: datetime = field(default_factory=datetime.utcnow)
    fecha_resolucion: datetime | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        BaseEntity.__init__(self, id=self.id)
        if len(self.descripcion.strip()) < _DESCRIPCION_MINIMA:
            raise DescriptionTooShortError(_DESCRIPCION_CORTA_MSG)

    def poner_en_revision(self) -> None:
        if self.estado in _ESTADOS_FINALES:
            raise ReporteYaResueltoError(_YA_RESUELTO_MSG)
        self.estado = EstadoReporte.EN_REVISION

    def resolver(self) -> None:
        if self.estado in _ESTADOS_FINALES:
            raise ReporteYaResueltoError(_YA_RESUELTO_MSG)
        self.estado = EstadoReporte.RESUELTO
        self.fecha_resolucion = datetime.utcnow()

    def marcar_no_reproducible(self) -> None:
        if self.estado in _ESTADOS_FINALES:
            raise ReporteYaResueltoError(_YA_RESUELTO_MSG)
        self.estado = EstadoReporte.NO_REPRODUCIBLE
        self.fecha_resolucion = datetime.utcnow()


@dataclass(eq=False)
class AdjuntoReporte(BaseEntity):
    """
    base-de-datos.md "reports_adjunto": 1:0..1 con `Reporte` (un solo
    adjunto por reporte). `archivo_url` apunta a almacenamiento externo
    (S3/MinIO, seguridad.md §4) — nunca se sirve desde el webroot.
    """

    reporte_id: uuid.UUID
    archivo_url: str
    nombre_archivo: str
    tamano_kb: int
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        BaseEntity.__init__(self, id=self.id)
