import uuid

from modules.assignments.infrastructure.repositories import AsignacionRepository


class AsignacionInscripcionProvider:
    """
    Implementación real de `IEstadoInscripcionProvider` (el puerto quedó
    como null-object — `SinInscripcionProvider` — desde Sprint 2, a la
    espera de que existiera el módulo Assignments). Ahora que existe,
    "inscrito" se resuelve como "tiene una asignación vigente" (pendiente
    o activa, `AsignacionRepository.existe_vigente`) para ese par
    estudiante/laboratorio.

    Se usa en dos lugares (`presentation/views.py`):
    - `ListarLaboratoriosQuery`: agrega el campo `inscrito` al catálogo
      (HE-02).
    - `ObtenerDetalleLaboratorioQuery`/`ObtenerTOCQuery`: además de
      `Laboratorio.es_visible_para` (que solo contempla predeterminado+
      publicado o el instructor dueño), un estudiante con asignación
      vigente también puede ver el detalle/TOC de un laboratorio
      `personalizado` que le asignaron — antes esto respondía 404 porque
      `es_visible_para` no sabe nada de Assignments (módulo aparte,
      dominio.md §1: Laboratories no depende de Assignments).
    """

    def __init__(self, asignacion_repository: AsignacionRepository | None = None):
        self._repo = asignacion_repository or AsignacionRepository()

    def esta_inscrito(self, estudiante_id: uuid.UUID, laboratorio_id: uuid.UUID) -> bool:
        return self._repo.existe_vigente(estudiante_id, laboratorio_id)
