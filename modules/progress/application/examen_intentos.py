"""
Piezas compartidas del examen final entre la consulta (GET), el inicio y la
entrega: resolver el examen del progreso con sus precondiciones, calcular el
estado de intentos y cerrar un intento abandonado.
"""

import uuid
from collections.abc import Callable
from datetime import datetime

from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.progress.application.dtos import EstadoExamenDTO
from modules.progress.domain.entities import HistorialCompletitud, Progreso, ResultadoExamen
from modules.progress.domain.events import ExamGraded
from modules.progress.domain.repositories import IProgresoRepository
from modules.progress.domain.services import PoliticaDeIntentosExamen
from modules.progress.domain.value_objects import (
    MAX_INTENTOS_EXAMEN,
    PUNTAJE_APROBACION,
    EstadoProgresoSeccion,
)
from modules.shared.domain.exceptions import BusinessRuleViolationError, NotFoundError

PROGRESO_NO_ENCONTRADO_MSG = "Progreso no encontrado."
SECCIONES_INCOMPLETAS_MSG = "Debes completar todas las secciones antes de presentar el examen."
EXAMEN_NO_CONFIGURADO_MSG = "Este laboratorio no tiene examen configurado."

# Marca en `ResultadoExamen.respuestas` de un intento que se cerró porque el
# estudiante salió sin entregar (queda en el historial con puntaje 0).
RESPUESTAS_ABANDONO = {"_abandonado": "salió del examen sin entregarlo"}


def resolver_examen(
    progreso_repository: IProgresoRepository,
    laboratorio_repository: ILaboratorioRepository,
    asignacion_id: uuid.UUID,
    estudiante_id: uuid.UUID,
    verificar_vigencia: Callable[[], None] | None = None,
):
    """
    Progreso propio + examen con preguntas, o la excepción que corresponda.
    `verificar_vigencia` corre justo después de comprobar la propiedad (antes
    que las secciones): un laboratorio vencido se informa como vencido.
    """
    progreso = progreso_repository.get_by_asignacion(asignacion_id)
    if progreso is None or not progreso.es_propio_de(estudiante_id):
        raise NotFoundError(PROGRESO_NO_ENCONTRADO_MSG)
    if verificar_vigencia is not None:
        verificar_vigencia()

    secciones = progreso_repository.get_secciones(progreso.id)
    if not secciones or any(s.estado != EstadoProgresoSeccion.COMPLETADA for s in secciones):
        raise BusinessRuleViolationError(SECCIONES_INCOMPLETAS_MSG)

    primera = laboratorio_repository.get_seccion_by_id(secciones[0].seccion_id)
    examen = laboratorio_repository.get_examen_by_laboratorio(primera.laboratorio_id)
    if examen is None:
        raise BusinessRuleViolationError(EXAMEN_NO_CONFIGURADO_MSG)
    preguntas = laboratorio_repository.get_preguntas(examen.id)
    if not preguntas:
        raise BusinessRuleViolationError(EXAMEN_NO_CONFIGURADO_MSG)
    return progreso, examen, preguntas


def intentos_calificados(progreso_repository: IProgresoRepository, progreso_id: uuid.UUID):
    return [(r.fecha, float(r.puntaje)) for r in progreso_repository.get_resultados_examen(progreso_id)]


def estado_examen(
    progreso_repository: IProgresoRepository,
    progreso: Progreso,
    examen_id: uuid.UUID,
    total_preguntas: int,
    ahora: datetime,
) -> EstadoExamenDTO:
    """
    Estado visible para el estudiante. Un intento que quedó abierto (salió sin
    entregar) ya se cuenta como reprobado: es lo que pasará al volver a iniciar.
    """
    intentos = intentos_calificados(progreso_repository, progreso.id)
    if progreso.tiene_examen_abierto:
        intentos.append((progreso.examen_iniciado_en, 0.0))
    estado = PoliticaDeIntentosExamen().evaluar(intentos, ahora)
    return EstadoExamenDTO(
        examen_id=examen_id,
        total_preguntas=total_preguntas,
        max_intentos=MAX_INTENTOS_EXAMEN,
        puntaje_aprobacion=PUNTAJE_APROBACION,
        intentos_restantes=estado.intentos_restantes,
        bloqueado_hasta=estado.bloqueado_hasta,
        aprobado=estado.aprobado,
        intentos_realizados=estado.intentos_realizados,
        mejor_puntaje=estado.mejor_puntaje,
        intento_abierto=progreso.tiene_examen_abierto,
    )


def registrar_intento(
    progreso_repository: IProgresoRepository,
    progreso_id: uuid.UUID,
    examen_id: uuid.UUID,
    respuestas: dict,
    puntaje: float,
) -> tuple[int, ExamGraded]:
    """Guarda un intento calificado (resultado + historial) y cierra el intento abierto."""
    progreso_repository.registrar_resultado_examen(
        ResultadoExamen(progreso_id=progreso_id, examen_id=examen_id, respuestas=respuestas, puntaje=puntaje)
    )
    numero_intento = len(progreso_repository.get_historial(progreso_id)) + 1
    progreso_repository.registrar_historial(
        HistorialCompletitud(progreso_id=progreso_id, numero_intento=numero_intento, puntaje=puntaje)
    )
    progreso_repository.fijar_examen_iniciado(progreso_id, None)
    return numero_intento, ExamGraded(progreso_id=progreso_id, examen_id=examen_id, puntaje=puntaje)
