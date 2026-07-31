import uuid
from typing import Protocol

from modules.roadmap.domain.entities import CategoriaRoadmap, NodoRoadmap


class ICategoriaRoadmapRepository(Protocol):
    """Puerto de persistencia de `CategoriaRoadmap`. Implementación real en `infrastructure/repositories.py`."""

    def add(self, categoria: CategoriaRoadmap) -> CategoriaRoadmap: ...

    def get_by_id(self, categoria_id: uuid.UUID) -> CategoriaRoadmap | None: ...

    def get_by_nombre(self, nombre: str) -> CategoriaRoadmap | None: ...

    def find_todas(self) -> list[CategoriaRoadmap]:
        """Ordenadas por `orden` — el orden estable de las pistas en la página."""
        ...

    def siguiente_orden(self) -> int:
        """`max(orden) + 1` entre las categorías existentes (0 si no hay ninguna)."""
        ...


class INodoRoadmapRepository(Protocol):
    """
    Puerto de persistencia de `NodoRoadmap`. Los métodos de reindex
    (`insertar_en_posicion`/`mover`/`quitar`) son responsables de la
    atomicidad del shift de posiciones — deben tomar el lock
    (`select_for_update`) sobre los nodos de la categoría afectada antes
    de reordenar, ver `infrastructure/repositories.py`.
    """

    def get_by_id(self, nodo_id: uuid.UUID) -> NodoRoadmap | None: ...

    def get_by_laboratorio(self, laboratorio_id: uuid.UUID) -> NodoRoadmap | None: ...

    def find_por_categoria(self, categoria_id: uuid.UUID) -> list[NodoRoadmap]:
        """Ordenados por `posicion` ascendente."""
        ...

    def find_todos(self) -> list[NodoRoadmap]: ...

    def find_laboratorio_ids_asignados(self) -> set[uuid.UUID]:
        """Todos los `laboratorio_id` que ya tienen un nodo — para la pool de "sin asignar"."""
        ...

    def insertar_en_posicion(
        self, categoria_id: uuid.UUID, laboratorio_id: uuid.UUID, posicion: int
    ) -> NodoRoadmap:
        """
        Crea un nodo en `posicion`, desplazando (+1) los nodos existentes
        de esa categoría con `posicion >=` la nueva — bajo lock de esa
        categoría.
        """
        ...

    def mover(self, nodo_id: uuid.UUID, categoria_id: uuid.UUID, posicion: int) -> NodoRoadmap:
        """
        Mueve un nodo existente a `(categoria_id, posicion)` — misma
        categoría o cruzando a otra — reindexando el hueco que deja y el
        destino que ocupa, bajo lock de ambas categorías afectadas.
        """
        ...

    def quitar(self, nodo_id: uuid.UUID) -> None:
        """Borra el nodo y cierra el hueco (reindexa los que quedan en esa categoría)."""
        ...
