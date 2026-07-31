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
    asignaciones = [
        a for a in asignacion_repository.find_por_estudiante(estudiante_id) if a.laboratorio_id == laboratorio_id
    ]
    for asignacion in asignaciones:
        progreso = progreso_repository.get_by_asignacion(asignacion.id)
        if progreso is None:
            continue
        if len(progreso_repository.get_historial(progreso.id)) > 0:
            return True
    return False
