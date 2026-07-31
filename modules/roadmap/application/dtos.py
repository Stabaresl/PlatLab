import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class CrearCategoriaDTO:
    """`POST /roadmap/categorias/` — solo admin."""

    nombre: str
    actor_id: uuid.UUID
    actor_rol: str


@dataclass(frozen=True)
class CategoriaResultDTO:
    id: uuid.UUID
    nombre: str
    orden: int


@dataclass(frozen=True)
class AgregarNodoDTO:
    """`POST /roadmap/nodos/` — solo admin. Inserta el laboratorio en `posicion`, desplazando el resto."""

    categoria_id: uuid.UUID
    laboratorio_id: uuid.UUID
    posicion: int
    actor_id: uuid.UUID
    actor_rol: str


@dataclass(frozen=True)
class ReordenarNodoDTO:
    """`PATCH /roadmap/nodos/{id}/` — solo admin. Mueve el nodo, misma categoría o cruzando a otra."""

    nodo_id: uuid.UUID
    categoria_id: uuid.UUID
    posicion: int
    actor_id: uuid.UUID
    actor_rol: str


@dataclass(frozen=True)
class QuitarNodoDTO:
    """`DELETE /roadmap/nodos/{id}/` — solo admin."""

    nodo_id: uuid.UUID
    actor_id: uuid.UUID
    actor_rol: str


@dataclass(frozen=True)
class NodoResultDTO:
    id: uuid.UUID
    categoria_id: uuid.UUID
    laboratorio_id: uuid.UUID
    posicion: int


@dataclass(frozen=True)
class InscribirseRoadmapDTO:
    """`POST /roadmap/nodos/{id}/inscribirse/` — solo estudiante, bloqueado por prerequisitos."""

    nodo_id: uuid.UUID
    actor_id: uuid.UUID
    actor_rol: str


@dataclass(frozen=True)
class InscripcionRoadmapResultDTO:
    id: uuid.UUID
    laboratorio_id: uuid.UUID
    estado: str


@dataclass(frozen=True)
class PrerequisitoDTO:
    laboratorio_id: uuid.UUID
    nombre: str


@dataclass(frozen=True)
class NodoRoadmapItemDTO:
    """
    Nodo enriquecido para lectura (`ListarRoadmapQuery`): datos del
    laboratorio embebidos + estado calculado por-estudiante (nunca
    persistido — ver `NodoRoadmap` en `domain/entities.py`).
    """

    id: uuid.UUID
    laboratorio_id: uuid.UUID
    posicion: int
    nombre: str
    nivel_dificultad: str
    temas: list[str]
    prerequisitos: list[PrerequisitoDTO]
    # None = visitante anónimo (sin sesión, no aplica estado de progreso).
    estado: str | None = None


@dataclass(frozen=True)
class CategoriaRoadmapItemDTO:
    id: uuid.UUID
    nombre: str
    orden: int
    nodos: list[NodoRoadmapItemDTO] = field(default_factory=list)


@dataclass(frozen=True)
class ListarRoadmapDTO:
    estudiante_id: uuid.UUID | None = None


@dataclass(frozen=True)
class LaboratorioSinRoadmapItemDTO:
    id: uuid.UUID
    nombre: str
    nivel_dificultad: str
    temas: list[str]


@dataclass(frozen=True)
class LaboratorioEnRoadmapItemDTO:
    """Item de `NodoRoadmap` "crudo" (sin estado por-estudiante) para vistas admin."""

    nodo_id: uuid.UUID
    categoria_id: uuid.UUID
    laboratorio_id: uuid.UUID
    posicion: int
    nombre: str
    created_at: datetime
