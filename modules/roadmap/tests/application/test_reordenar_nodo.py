import uuid

import pytest

from modules.laboratories.domain.entities import Laboratorio
from modules.laboratories.domain.value_objects import (
    EstadoLaboratorio,
    NivelDificultad,
    TipoLaboratorio,
)
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.roadmap.application.dtos import AgregarNodoDTO, ReordenarNodoDTO
from modules.roadmap.application.use_cases.agregar_nodo import AgregarNodoUseCase
from modules.roadmap.application.use_cases.reordenar_nodo import ReordenarNodoUseCase
from modules.roadmap.domain.entities import CategoriaRoadmap
from modules.roadmap.infrastructure.repositories import (
    CategoriaRoadmapRepository,
    NodoRoadmapRepository,
)
from modules.shared.domain.exceptions import ForbiddenError, NotFoundError
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


def _uc():
    return ReordenarNodoUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        categoria_repository=CategoriaRoadmapRepository(),
        nodo_repository=NodoRoadmapRepository(),
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
    )
    defaults.update(overrides)
    return LaboratorioRepository().add(Laboratorio(**defaults))


def _orden(categoria_id):
    return [(n.laboratorio_id, n.posicion) for n in NodoRoadmapRepository().find_por_categoria(categoria_id)]


@pytest.mark.django_db
def test_admin_mueve_nodo_dentro_de_la_misma_categoria():
    categoria = _crear_categoria()
    a, b, c = _crear_lab(), _crear_lab(), _crear_lab()
    n_a = _agregar_uc().execute(AgregarNodoDTO(categoria.id, a.id, 0, uuid.uuid4(), "administrador"))
    _agregar_uc().execute(AgregarNodoDTO(categoria.id, b.id, 1, uuid.uuid4(), "administrador"))
    _agregar_uc().execute(AgregarNodoDTO(categoria.id, c.id, 2, uuid.uuid4(), "administrador"))

    _uc().execute(
        ReordenarNodoDTO(n_a.id, categoria.id, 2, uuid.uuid4(), "administrador")
    )

    orden = _orden(categoria.id)
    assert (b.id, 0) in orden
    assert (c.id, 1) in orden
    assert (a.id, 2) in orden


@pytest.mark.django_db
def test_admin_mueve_nodo_a_otra_categoria():
    origen = _crear_categoria()
    destino = _crear_categoria()
    lab = _crear_lab()
    otro_en_origen = _crear_lab()
    nodo = _agregar_uc().execute(
        AgregarNodoDTO(origen.id, lab.id, 0, uuid.uuid4(), "administrador")
    )
    _agregar_uc().execute(
        AgregarNodoDTO(origen.id, otro_en_origen.id, 1, uuid.uuid4(), "administrador")
    )

    _uc().execute(ReordenarNodoDTO(nodo.id, destino.id, 0, uuid.uuid4(), "administrador"))

    assert _orden(origen.id) == [(otro_en_origen.id, 0)]
    assert _orden(destino.id) == [(lab.id, 0)]


@pytest.mark.django_db
def test_instructor_no_puede_reordenar():
    categoria = _crear_categoria()
    lab = _crear_lab()
    nodo = _agregar_uc().execute(
        AgregarNodoDTO(categoria.id, lab.id, 0, uuid.uuid4(), "administrador")
    )

    with pytest.raises(ForbiddenError):
        _uc().execute(ReordenarNodoDTO(nodo.id, categoria.id, 0, uuid.uuid4(), "instructor"))


@pytest.mark.django_db
def test_nodo_inexistente_lanza_not_found():
    categoria = _crear_categoria()

    with pytest.raises(NotFoundError):
        _uc().execute(
            ReordenarNodoDTO(uuid.uuid4(), categoria.id, 0, uuid.uuid4(), "administrador")
        )
