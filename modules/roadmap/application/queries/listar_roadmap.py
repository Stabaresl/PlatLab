import uuid

from modules.assignments.domain.repositories import IAsignacionRepository
from modules.laboratories.domain.entities import Laboratorio
from modules.laboratories.domain.repositories import ILaboratorioRepository
from modules.progress.domain.repositories import IProgresoRepository
from modules.roadmap.application.completitud import esta_completado_por_estudiante
from modules.roadmap.application.dtos import (
    CategoriaRoadmapItemDTO,
    NodoRoadmapItemDTO,
    PrerequisitoDTO,
)
from modules.roadmap.domain.entities import NodoRoadmap
from modules.roadmap.domain.repositories import ICategoriaRoadmapRepository, INodoRoadmapRepository

_ESTADO_COMPLETADO = "completado"
_ESTADO_DISPONIBLE = "disponible"
_ESTADO_BLOQUEADO = "bloqueado"


class ListarRoadmapQuery:
    """
    HV público (sin auth) + estado por-estudiante si hay sesión: árbol
    completo de categorías con sus nodos ordenados, cada uno con los
    datos del laboratorio embebidos y —si se pasa `estudiante_id`— su
    estado (`completado`/`disponible`/`bloqueado`) más los nombres de
    los prerequisitos que le faltan. Compone repos de Roadmap,
    Laboratories, Assignments y Progress directamente (mismo patrón que
    `ObtenerDashboardAdminQuery` en `modules/users`) — de solo lectura,
    no usa `BaseUseCase`.
    """

    def __init__(
        self,
        categoria_repository: ICategoriaRoadmapRepository,
        nodo_repository: INodoRoadmapRepository,
        laboratorio_repository: ILaboratorioRepository,
        asignacion_repository: IAsignacionRepository,
        progreso_repository: IProgresoRepository,
    ):
        self._categoria_repository = categoria_repository
        self._nodo_repository = nodo_repository
        self._laboratorio_repository = laboratorio_repository
        self._asignacion_repository = asignacion_repository
        self._progreso_repository = progreso_repository

    def execute(self, estudiante_id: uuid.UUID | None = None) -> list[CategoriaRoadmapItemDTO]:
        resultado = []
        for categoria in self._categoria_repository.find_todas():
            nodos = self._nodo_repository.find_por_categoria(categoria.id)
            items = self._a_items(nodos, estudiante_id)
            resultado.append(
                CategoriaRoadmapItemDTO(
                    id=categoria.id, nombre=categoria.nombre, orden=categoria.orden, nodos=items
                )
            )
        return resultado

    def _a_items(
        self, nodos: list[NodoRoadmap], estudiante_id: uuid.UUID | None
    ) -> list[NodoRoadmapItemDTO]:
        labs: dict[uuid.UUID, Laboratorio] = {}
        for nodo in nodos:
            laboratorio = self._laboratorio_repository.get_by_id(nodo.laboratorio_id)
            if laboratorio is not None:
                labs[nodo.laboratorio_id] = laboratorio

        completados: dict[uuid.UUID, bool] = {}
        if estudiante_id is not None:
            for nodo in nodos:
                completados[nodo.laboratorio_id] = esta_completado_por_estudiante(
                    self._asignacion_repository,
                    self._progreso_repository,
                    estudiante_id,
                    nodo.laboratorio_id,
                )

        items = []
        for nodo in nodos:
            laboratorio = labs.get(nodo.laboratorio_id)
            if laboratorio is None:
                continue

            anteriores = [n for n in nodos if n.posicion < nodo.posicion]
            prerequisitos = [
                PrerequisitoDTO(laboratorio_id=n.laboratorio_id, nombre=labs[n.laboratorio_id].nombre)
                for n in anteriores
                if n.laboratorio_id in labs
            ]

            estado = None
            if estudiante_id is not None:
                if completados.get(nodo.laboratorio_id):
                    estado = _ESTADO_COMPLETADO
                elif all(completados.get(n.laboratorio_id) for n in anteriores):
                    estado = _ESTADO_DISPONIBLE
                else:
                    estado = _ESTADO_BLOQUEADO

            items.append(
                NodoRoadmapItemDTO(
                    id=nodo.id,
                    laboratorio_id=nodo.laboratorio_id,
                    posicion=nodo.posicion,
                    nombre=laboratorio.nombre,
                    nivel_dificultad=laboratorio.nivel_dificultad.value,
                    temas=laboratorio.temas,
                    prerequisitos=prerequisitos,
                    estado=estado,
                )
            )
        return items
