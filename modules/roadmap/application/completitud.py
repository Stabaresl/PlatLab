import uuid

from modules.assignments.domain.repositories import IAsignacionRepository
from modules.progress.domain.repositories import IProgresoRepository


def esta_completado_por_estudiante(
    asignacion_repository: IAsignacionRepository,
    progreso_repository: IProgresoRepository,
    estudiante_id: uuid.UUID,
    laboratorio_id: uuid.UUID,
) -> bool:
    """
    Mismo criterio de completitud que usa el resto del código (HE-11 /
    `ObtenerHistorialQuery`, `InscribirseLaboratorioUseCase._esta_terminada`):
    el estudiante tiene una `Asignacion` para ese laboratorio cuyo
    `Progreso` tiene al menos un `HistorialCompletitud` registrado.
    Compartido entre `InscribirseRoadmapUseCase` (gate de prerequisitos)
    y `ListarRoadmapQuery` (estado de cada nodo) — ambos viven en este
    mismo módulo, así que factorizarlo acá no cruza límites de módulo.
    """
    return laboratorio_id in laboratorios_completados_por_estudiante(
        asignacion_repository, progreso_repository, estudiante_id
    )


def laboratorios_completados_por_estudiante(
    asignacion_repository: IAsignacionRepository,
    progreso_repository: IProgresoRepository,
    estudiante_id: uuid.UUID,
) -> set[uuid.UUID]:
    """
    Mismo criterio que `esta_completado_por_estudiante`, pero para TODOS
    los laboratorios del estudiante en 2 consultas — antes el roadmap
    repetía asignaciones+progreso+historial por cada nodo (N+1 medido en
    loadtests/: `/roadmap/` costaba ~6x el catálogo anónimo).
    """
    asignaciones = asignacion_repository.find_por_estudiante(estudiante_id)
    terminadas = progreso_repository.asignaciones_con_historial([a.id for a in asignaciones])
    return {a.laboratorio_id for a in asignaciones if a.id in terminadas}
