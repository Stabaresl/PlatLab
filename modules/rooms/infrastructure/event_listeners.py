import uuid

from modules.assignments.infrastructure.repositories import AsignacionRepository
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.progress.domain.events import ExamGraded, LabCompleted
from modules.progress.infrastructure.repositories import ProgresoRepository
from modules.rooms.application.dtos import RegistrarCompletitudSalaDTO
from modules.rooms.application.use_cases.registrar_completitud_sala import RegistrarCompletitudSalaUseCase
from modules.rooms.domain.value_objects import PUNTAJE_APROBACION
from modules.rooms.infrastructure.repositories import ParticipanteSalaRepository, SalaRepository
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


def _registrar(progreso_id: uuid.UUID) -> None:
    progreso = ProgresoRepository().get_by_id(progreso_id)
    if progreso is None:
        return
    participantes = ParticipanteSalaRepository()
    if not participantes.find_por_asignacion(progreso.asignacion_id):
        return  # asignación fuera de cualquier sala: nada que hacer (el caso común)
    RegistrarCompletitudSalaUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        sala_repository=SalaRepository(),
        participante_repository=participantes,
    ).execute(RegistrarCompletitudSalaDTO(asignacion_id=progreso.asignacion_id))


def _on_exam_graded(event: ExamGraded) -> None:
    """En la sala cuenta como terminado al aprobar el examen (no basta con presentarlo)."""
    if event.puntaje >= PUNTAJE_APROBACION:
        _registrar(event.progreso_id)


def _on_lab_completed(event: LabCompleted) -> None:
    """Sin examen, terminar las secciones ya es terminar el laboratorio."""
    progreso = ProgresoRepository().get_by_id(event.progreso_id)
    if progreso is None:
        return
    asignacion = AsignacionRepository().get_by_id(progreso.asignacion_id)
    if asignacion is None or LaboratorioRepository().get_examen_by_laboratorio(asignacion.laboratorio_id):
        return
    _registrar(event.progreso_id)


def registrar_listeners(dispatcher: EventDispatcher) -> None:
    dispatcher.subscribe(ExamGraded, _on_exam_graded)
    dispatcher.subscribe(LabCompleted, _on_lab_completed)
