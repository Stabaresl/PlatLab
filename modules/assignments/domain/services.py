from datetime import datetime

from modules.assignments.domain.entities import Asignacion
from modules.assignments.domain.value_objects import VentanaVencimiento


class GestorDeVencimientos:
    """
    RF-32, dominio.md §5, UC-07: evalúa `Asignación`es activas contra su
    `VentanaVencimiento` y las transiciona a `vencida`, revocando
    acceso. Invocado por un proceso externo (Celery Beat,
    `CerrarAsignacionesVencidasJob`), no por acción directa de un actor
    — por eso no es un `BaseUseCase` (no hay `actor_id`/`actor_rol` que
    validar).
    """

    def identificar_vencidas(
        self, asignaciones_activas: list[Asignacion], ahora: datetime | None = None
    ) -> list[Asignacion]:
        vencidas = []
        for asignacion in asignaciones_activas:
            if asignacion.fecha_vencimiento is None:
                continue
            ventana = VentanaVencimiento(fecha=asignacion.fecha_vencimiento)
            if ventana.ya_vencio(ahora):
                asignacion.vencer()
                vencidas.append(asignacion)
        return vencidas
