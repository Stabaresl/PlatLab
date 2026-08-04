import uuid
from typing import Protocol

from modules.progress.domain.entities import (
    HistorialCompletitud,
    IntentoFlag,
    Progreso,
    ProgresoSeccion,
    ResultadoExamen,
)


class IProgresoRepository(Protocol):
    """
    Puerto de persistencia del agregado Progreso. La implementación real
    vive en `infrastructure/repositories.py` (PostgreSQL vía
    `mappers.py`) — Application nunca importa el ORM directamente.
    Métodos deliberadamente finos: la atomicidad de un intento completo
    (registrar intento + actualizar secciones + historial) la garantiza
    `BaseUnitOfWork` alrededor de la secuencia de llamadas, no un único
    método "save" monolítico (HE-07).
    """

    def get_by_asignacion(self, asignacion_id: uuid.UUID) -> Progreso | None: ...

    def get_by_id(self, progreso_id: uuid.UUID) -> Progreso | None:
        """UC-12: resuelve `estudiante_id` a partir de `progreso_id` (ej. para auditoría)."""
        ...

    def add(self, progreso: Progreso) -> Progreso: ...

    def tocar_actividad(self, progreso_id: uuid.UUID) -> None:
        """Actualiza `ultima_actividad` (HE-07, soporta reanudación RNF-03.3)."""
        ...

    def get_secciones(self, progreso_id: uuid.UUID) -> list[ProgresoSeccion]: ...

    def get_completitud_por_asignaciones(
        self, asignacion_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, float]:
        """
        Batch: % de secciones completadas, indexado por `asignacion_id`
        — evita el N+1 de llamar `get_by_asignacion()` +
        `get_secciones()` dentro de un loop (dashboard.md HI-06/HA-03,
        `ObtenerDashboardQuery`/`ObtenerDashboardAdminQuery`). Una
        asignación sin progreso o sin secciones registradas todavía no
        aparece en el dict devuelto.
        """
        ...

    def get_seccion(
        self, progreso_id: uuid.UUID, seccion_id: uuid.UUID
    ) -> ProgresoSeccion | None: ...

    def add_secciones(self, secciones: list[ProgresoSeccion]) -> list[ProgresoSeccion]:
        """Crea el set inicial de `ProgresoSeccion` (una por Sección del laboratorio asignado)."""
        ...

    def actualizar_seccion(self, seccion: ProgresoSeccion) -> ProgresoSeccion: ...

    def registrar_intento(self, intento: IntentoFlag) -> IntentoFlag: ...

    def contar_fallos(self, progreso_id: uuid.UUID, seccion_id: uuid.UUID) -> int:
        """
        HE-06: cuenta los `IntentoFlag` fallidos de esa sección
        (índice compuesto `(progreso_id, seccion_id, timestamp)`,
        base-de-datos.md) sin traer todos los intentos a memoria.
        """
        ...

    def registrar_historial(self, historial: HistorialCompletitud) -> HistorialCompletitud: ...

    def get_historial(self, progreso_id: uuid.UUID) -> list[HistorialCompletitud]: ...

    def registrar_resultado_examen(self, resultado: ResultadoExamen) -> ResultadoExamen:
        """HE-09/HI-08: examen reintentable — cada envío crea una fila nueva, nunca sobrescribe."""
        ...

    def get_resultados_examen(self, progreso_id: uuid.UUID) -> list[ResultadoExamen]: ...
