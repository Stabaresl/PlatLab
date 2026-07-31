from modules.roadmap.domain.entities import CategoriaRoadmap, NodoRoadmap
from modules.roadmap.infrastructure.models import CategoriaRoadmapModel, NodoRoadmapModel


def categoria_to_entity(model: CategoriaRoadmapModel) -> CategoriaRoadmap:
    return CategoriaRoadmap(
        id=model.id,
        nombre=model.nombre,
        orden=model.orden,
        created_at=model.created_at,
    )


def nodo_to_entity(model: NodoRoadmapModel) -> NodoRoadmap:
    return NodoRoadmap(
        id=model.id,
        categoria_id=model.categoria_id,
        laboratorio_id=model.laboratorio_id,
        posicion=model.posicion,
        created_at=model.created_at,
    )
