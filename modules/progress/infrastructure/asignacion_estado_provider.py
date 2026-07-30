import uuid

from modules.assignments.domain.value_objects import EstadoAsignacion, VentanaVencimiento
from modules.assignments.infrastructure.repositories import AsignacionRepository
from modules.progress.domain.ports import EstadoAsignacionInfo


class AsignacionEstadoProvider:
    """Implementación real de `IEstadoAsignacionProvider` (ver domain/ports.py)."""

    def __init__(self, asignacion_repository: AsignacionRepository | None = None):
        self._repo = asignacion_repository or AsignacionRepository()

    def obtener_estado(self, asignacion_id: uuid.UUID) -> EstadoAsignacionInfo | None:
        asignacion = self._repo.get_by_id(asignacion_id)
        if asignacion is None:
            return None

        vencida = asignacion.estado == EstadoAsignacion.VENCIDA
        if not vencida and asignacion.fecha_vencimiento is not None:
            vencida = VentanaVencimiento(fecha=asignacion.fecha_vencimiento).ya_vencio()

        return EstadoAsignacionInfo(vencida=vencida, fecha_vencimiento=asignacion.fecha_vencimiento)
