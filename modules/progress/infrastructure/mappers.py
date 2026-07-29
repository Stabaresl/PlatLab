from modules.progress.domain.entities import (
    HistorialCompletitud,
    IntentoFlag,
    Progreso,
    ProgresoSeccion,
    ResultadoExamen,
)
from modules.progress.domain.value_objects import EstadoProgresoSeccion
from modules.progress.infrastructure.models import (
    HistorialCompletitudModel,
    IntentoFlagModel,
    ProgresoModel,
    ProgresoSeccionModel,
    ResultadoExamenModel,
)


def progreso_to_entity(model: ProgresoModel) -> Progreso:
    return Progreso(
        id=model.id,
        asignacion_id=model.asignacion_id,
        estudiante_id=model.estudiante_id,
        fecha_inicio=model.fecha_inicio,
        ultima_actividad=model.ultima_actividad,
    )


def progreso_seccion_to_entity(model: ProgresoSeccionModel) -> ProgresoSeccion:
    return ProgresoSeccion(
        id=model.id,
        progreso_id=model.progreso_id,
        seccion_id=model.seccion_id,
        estado=EstadoProgresoSeccion(model.estado),
        fecha_completado=model.fecha_completado,
    )


def intento_flag_to_entity(model: IntentoFlagModel) -> IntentoFlag:
    return IntentoFlag(
        id=model.id,
        progreso_id=model.progreso_id,
        seccion_id=model.seccion_id,
        resultado=model.resultado,
        timestamp=model.timestamp,
    )


def resultado_examen_to_entity(model: ResultadoExamenModel) -> ResultadoExamen:
    return ResultadoExamen(
        id=model.id,
        progreso_id=model.progreso_id,
        examen_id=model.examen_id,
        respuestas=model.respuestas,
        puntaje=float(model.puntaje),
        fecha=model.fecha,
    )


def historial_to_entity(model: HistorialCompletitudModel) -> HistorialCompletitud:
    return HistorialCompletitud(
        id=model.id,
        progreso_id=model.progreso_id,
        numero_intento=model.numero_intento,
        fecha_completado=model.fecha_completado,
        puntaje=float(model.puntaje) if model.puntaje is not None else None,
    )
