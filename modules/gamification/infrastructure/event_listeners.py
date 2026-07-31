import uuid

from modules.assignments.infrastructure.repositories import AsignacionRepository
from modules.gamification.application.dtos import ProcesarCompletitudDTO
from modules.gamification.application.procesar_completitud import ProcesarCompletitudLaboratorio
from modules.gamification.infrastructure.repositories import (
    CosmeticoDesbloqueadoRepository,
    CosmeticoRepository,
    LogroDesbloqueadoRepository,
    LogroRepository,
    PerfilJugadorRepository,
    TituloDesbloqueadoRepository,
    TituloRepository,
    XpOtorgadoRepository,
)
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.progress.domain.events import ExamGraded, LabCompleted
from modules.progress.infrastructure.repositories import ProgresoRepository
from modules.roadmap.infrastructure.repositories import NodoRoadmapRepository
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


def _resolver_estudiante_y_laboratorio(progreso_id: uuid.UUID) -> tuple[uuid.UUID, uuid.UUID] | None:
    progreso = ProgresoRepository().get_by_id(progreso_id)
    if progreso is None:
        return None
    asignacion = AsignacionRepository().get_by_id(progreso.asignacion_id)
    if asignacion is None:
        return None
    return progreso.estudiante_id, asignacion.laboratorio_id


def _procesar(estudiante_id: uuid.UUID, laboratorio_id: uuid.UUID) -> None:
    ProcesarCompletitudLaboratorio(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        perfil_repository=PerfilJugadorRepository(),
        xp_otorgado_repository=XpOtorgadoRepository(),
        logro_repository=LogroRepository(),
        logro_desbloqueado_repository=LogroDesbloqueadoRepository(),
        cosmetico_repository=CosmeticoRepository(),
        cosmetico_desbloqueado_repository=CosmeticoDesbloqueadoRepository(),
        titulo_repository=TituloRepository(),
        titulo_desbloqueado_repository=TituloDesbloqueadoRepository(),
        laboratorio_repository=LaboratorioRepository(),
        nodo_roadmap_repository=NodoRoadmapRepository(),
    ).execute(ProcesarCompletitudDTO(estudiante_id=estudiante_id, laboratorio_id=laboratorio_id))


def _on_exam_graded(event: ExamGraded) -> None:
    """Un laboratorio CON examen recién cuenta como completado (para XP/logros) al calificarse."""
    resuelto = _resolver_estudiante_y_laboratorio(event.progreso_id)
    if resuelto is None:
        return
    _procesar(*resuelto)


def _on_lab_completed(event: LabCompleted) -> None:
    """
    `LabCompleted` dispara al completar las secciones, sin importar si
    el laboratorio tiene examen — si lo tiene, el otorgamiento real
    espera a `ExamGraded` (acá no hacemos nada, mismo chequeo que ya
    hace `completar_seccion_teorica.py::_registrar_historial_si_no_hay_examen`
    para decidir si crear el `HistorialCompletitud` ahí mismo o no).
    """
    resuelto = _resolver_estudiante_y_laboratorio(event.progreso_id)
    if resuelto is None:
        return
    estudiante_id, laboratorio_id = resuelto
    if LaboratorioRepository().get_examen_by_laboratorio(laboratorio_id) is not None:
        return
    _procesar(estudiante_id, laboratorio_id)


def registrar_listeners(dispatcher: EventDispatcher) -> None:
    dispatcher.subscribe(ExamGraded, _on_exam_graded)
    dispatcher.subscribe(LabCompleted, _on_lab_completed)
