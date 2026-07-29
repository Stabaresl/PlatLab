from modules.reports.domain.entities import AdjuntoReporte, Reporte
from modules.reports.domain.value_objects import EstadoReporte
from modules.reports.infrastructure.models import AdjuntoReporteModel, ReporteModel


def reporte_to_entity(model: ReporteModel) -> Reporte:
    return Reporte(
        id=model.id,
        estudiante_id=model.estudiante_id,
        laboratorio_id=model.laboratorio_id,
        seccion_id=model.seccion_id,
        descripcion=model.descripcion,
        estado=EstadoReporte(model.estado),
        fecha_creacion=model.fecha_creacion,
        fecha_resolucion=model.fecha_resolucion,
    )


def adjunto_to_entity(model: AdjuntoReporteModel) -> AdjuntoReporte:
    return AdjuntoReporte(
        id=model.id,
        reporte_id=model.reporte_id,
        archivo_url=model.archivo_url,
        nombre_archivo=model.nombre_archivo,
        tamano_kb=model.tamano_kb,
    )
