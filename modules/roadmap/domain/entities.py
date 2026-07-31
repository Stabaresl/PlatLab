import uuid
from dataclasses import dataclass, field
from datetime import datetime

from modules.roadmap.domain.exceptions import PosicionInvalidaError
from modules.shared.domain.base_entity import BaseEntity


@dataclass(eq=False)
class CategoriaRoadmap(BaseEntity):
    """
    Una "pista" del roadmap (ej. "Seguridad Web") — agrupa `NodoRoadmap`
    en un camino ordenado. Solo un admin la crea (`CrearCategoriaUseCase`).
    `orden` es el orden estable de las pistas en la página (no
    reordenable en esta versión — se asigna `max(orden)+1` al crear).
    """

    nombre: str
    orden: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        BaseEntity.__init__(self, id=self.id)


@dataclass(eq=False)
class NodoRoadmap(BaseEntity):
    """
    Un laboratorio ubicado dentro de una `CategoriaRoadmap`, en una
    `posicion` (entero denso 0..N-1 por categoría, elegido por un admin
    vía drag-and-drop — no se deriva de `nivel_dificultad`). `categoria_id`/
    `laboratorio_id` son "id suelto" (Arquitectura §8): Roadmap no
    depende de Laboratories a nivel de entidad, solo referencia su id.

    El estado "completado/disponible/bloqueado" de un nodo para un
    estudiante puntual NO vive acá — es derivado en tiempo de lectura
    (`ListarRoadmapQuery`), nunca persistido.
    """

    categoria_id: uuid.UUID
    laboratorio_id: uuid.UUID
    posicion: int
    created_at: datetime = field(default_factory=datetime.utcnow)
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        BaseEntity.__init__(self, id=self.id)
        if self.posicion < 0:
            raise PosicionInvalidaError("La posición de un nodo no puede ser negativa.")
