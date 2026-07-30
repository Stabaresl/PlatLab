from modules.lab_environments.domain.entities import EntornoActivo
from modules.lab_environments.domain.value_objects import EstadoEntorno
from modules.lab_environments.infrastructure.models import EntornoActivoModel


def entorno_to_entity(model: EntornoActivoModel) -> EntornoActivo:
    return EntornoActivo(
        id=model.id,
        seccion_id=model.seccion_id,
        progreso_id=model.progreso_id,
        estudiante_id=model.estudiante_id,
        container_id=model.container_id,
        estado=EstadoEntorno(model.estado),
        fecha_inicio=model.fecha_inicio,
        ultima_actividad=model.ultima_actividad,
    )
