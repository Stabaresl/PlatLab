import uuid

import pytest

from modules.assignments.domain.entities import Asignacion
from modules.assignments.infrastructure.repositories import AsignacionRepository
from modules.laboratories.domain.entities import Laboratorio
from modules.laboratories.domain.value_objects import (
    EstadoLaboratorio,
    NivelDificultad,
    TipoLaboratorio,
)
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.progress.domain.entities import HistorialCompletitud, Progreso
from modules.progress.infrastructure.repositories import ProgresoRepository
from modules.roadmap.application.dtos import AgregarNodoDTO
from modules.roadmap.application.queries.listar_roadmap import ListarRoadmapQuery
from modules.roadmap.application.use_cases.agregar_nodo import AgregarNodoUseCase
from modules.roadmap.domain.entities import CategoriaRoadmap
from modules.roadmap.infrastructure.repositories import (
    CategoriaRoadmapRepository,
    NodoRoadmapRepository,
)
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


def _agregar_uc():
    return AgregarNodoUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        categoria_repository=CategoriaRoadmapRepository(),
        nodo_repository=NodoRoadmapRepository(),
        laboratorio_repository=LaboratorioRepository(),
    )


def _query():
    return ListarRoadmapQuery(
        categoria_repository=CategoriaRoadmapRepository(),
        nodo_repository=NodoRoadmapRepository(),
        laboratorio_repository=LaboratorioRepository(),
        asignacion_repository=AsignacionRepository(),
        progreso_repository=ProgresoRepository(),
    )


def _crear_categoria():
    return CategoriaRoadmapRepository().add(CategoriaRoadmap(nombre=f"Cat {uuid.uuid4()}"))


def _crear_lab(**overrides) -> Laboratorio:
    defaults = dict(
        nombre=f"Lab {uuid.uuid4()}",
        descripcion="desc",
        nivel_dificultad=NivelDificultad.BASICO,
        estado=EstadoLaboratorio.PUBLICADO,
        tipo=TipoLaboratorio.PREDETERMINADO,
        temas=["redes"],
    )
    defaults.update(overrides)
    return LaboratorioRepository().add(Laboratorio(**defaults))


def _completar_laboratorio_para(estudiante_id, laboratorio_id):
    asignacion_repo = AsignacionRepository()
    progreso_repo = ProgresoRepository()
    asignacion = asignacion_repo.add(
        Asignacion(estudiante_id=estudiante_id, laboratorio_id=laboratorio_id)
    )
    asignacion.aceptar()
    asignacion_repo.update(asignacion)
    progreso = progreso_repo.add(Progreso(asignacion_id=asignacion.id, estudiante_id=estudiante_id))
    progreso_repo.registrar_historial(
        HistorialCompletitud(progreso_id=progreso.id, numero_intento=1, puntaje=90.0)
    )


def _nodo_por_lab(categorias, laboratorio_id):
    for categoria in categorias:
        for nodo in categoria.nodos:
            if nodo.laboratorio_id == laboratorio_id:
                return nodo
    raise AssertionError(f"nodo para {laboratorio_id} no encontrado en el resultado")


@pytest.mark.django_db
def test_visitante_anonimo_no_recibe_estado():
    categoria = _crear_categoria()
    lab = _crear_lab()
    _agregar_uc().execute(AgregarNodoDTO(categoria.id, lab.id, 0, uuid.uuid4(), "administrador"))

    resultado = _query().execute(estudiante_id=None)

    nodo = _nodo_por_lab(resultado, lab.id)
    assert nodo.estado is None
    assert nodo.nombre == lab.nombre
    assert nodo.temas == ["redes"]


@pytest.mark.django_db
def test_primer_nodo_disponible_para_estudiante_sin_progreso():
    categoria = _crear_categoria()
    lab = _crear_lab()
    _agregar_uc().execute(AgregarNodoDTO(categoria.id, lab.id, 0, uuid.uuid4(), "administrador"))

    resultado = _query().execute(estudiante_id=uuid.uuid4())

    assert _nodo_por_lab(resultado, lab.id).estado == "disponible"


@pytest.mark.django_db
def test_segundo_nodo_bloqueado_muestra_prerequisito():
    categoria = _crear_categoria()
    lab_a, lab_b = _crear_lab(nombre="Lab A"), _crear_lab(nombre="Lab B")
    _agregar_uc().execute(AgregarNodoDTO(categoria.id, lab_a.id, 0, uuid.uuid4(), "administrador"))
    _agregar_uc().execute(AgregarNodoDTO(categoria.id, lab_b.id, 1, uuid.uuid4(), "administrador"))

    resultado = _query().execute(estudiante_id=uuid.uuid4())

    nodo_b = _nodo_por_lab(resultado, lab_b.id)
    assert nodo_b.estado == "bloqueado"
    assert [p.nombre for p in nodo_b.prerequisitos] == ["Lab A"]


@pytest.mark.django_db
def test_estado_completado_y_desbloqueo_del_siguiente():
    categoria = _crear_categoria()
    lab_a, lab_b = _crear_lab(), _crear_lab()
    _agregar_uc().execute(AgregarNodoDTO(categoria.id, lab_a.id, 0, uuid.uuid4(), "administrador"))
    _agregar_uc().execute(AgregarNodoDTO(categoria.id, lab_b.id, 1, uuid.uuid4(), "administrador"))
    estudiante_id = uuid.uuid4()
    _completar_laboratorio_para(estudiante_id, lab_a.id)

    resultado = _query().execute(estudiante_id=estudiante_id)

    assert _nodo_por_lab(resultado, lab_a.id).estado == "completado"
    assert _nodo_por_lab(resultado, lab_b.id).estado == "disponible"


@pytest.mark.django_db
def test_categorias_sin_nodos_devuelven_lista_vacia():
    _crear_categoria()

    resultado = _query().execute(estudiante_id=None)

    assert resultado[0].nodos == []
