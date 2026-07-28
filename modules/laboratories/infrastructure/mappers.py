from modules.laboratories.domain.entities import Laboratorio, Seccion
from modules.laboratories.domain.value_objects import (
    EstadoLaboratorio,
    NivelDificultad,
    TipoLaboratorio,
)
from modules.laboratories.infrastructure.models import LaboratorioModel, SeccionModel


def laboratorio_to_entity(model: LaboratorioModel) -> Laboratorio:
    return Laboratorio(
        id=model.id,
        nombre=model.nombre,
        descripcion=model.descripcion,
        nivel_dificultad=NivelDificultad(model.nivel_dificultad),
        estado=EstadoLaboratorio(model.estado),
        tipo=TipoLaboratorio(model.tipo),
        temas=[tema.nombre for tema in model.temas.all()],
        origen_id=model.origen_id,
        instructor_id=model.instructor_id,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def seccion_to_entity(model: SeccionModel) -> Seccion:
    return Seccion(
        id=model.id,
        laboratorio_id=model.laboratorio_id,
        titulo=model.titulo,
        contenido_teorico=model.contenido_teorico,
        orden=model.orden,
        tiene_practica=model.tiene_practica,
    )
