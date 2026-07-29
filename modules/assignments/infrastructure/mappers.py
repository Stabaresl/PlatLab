from modules.assignments.domain.entities import Asignacion
from modules.assignments.domain.value_objects import EstadoAsignacion
from modules.assignments.infrastructure.models import AsignacionModel


def asignacion_to_entity(model: AsignacionModel) -> Asignacion:
    return Asignacion(
        id=model.id,
        estudiante_id=model.estudiante_id,
        laboratorio_id=model.laboratorio_id,
        instructor_id=model.instructor_id,
        estado=EstadoAsignacion(model.estado),
        fecha_invitacion=model.fecha_invitacion,
        fecha_vencimiento=model.fecha_vencimiento,
        fecha_respuesta=model.fecha_respuesta,
    )
