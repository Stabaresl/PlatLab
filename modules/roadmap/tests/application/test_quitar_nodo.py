import uuid

import pytest

from modules.laboratories.domain.entities import Laboratorio
from modules.laboratories.domain.value_objects import (
    EstadoLaboratorio,
    NivelDificultad,
    TipoLaboratorio,
)
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.roadmap.application.dtos import AgregarNodoDTO, QuitarNodoDTO
from modules.roadmap.application.use_cases.agregar_nodo import AgregarNodoUseCase
from modules.roadmap.application.use_cases.quitar_nodo import QuitarNodoUseCase
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
    return QuitarNodoUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
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


@pytest.mark.django_db
def test_admin_quita_nodo_y_cierra_el_hueco():
    categoria = _crear_categoria()
    a, b, c = _crear_lab(), _crear_lab(), _crear_lab()
    _agregar_uc().execute(AgregarNodoDTO(categoria.id, a.id, 0, uuid.uuid4(), "administrador"))
    nodo_b = _agregar_uc().execute(
        AgregarNodoDTO(categoria.id, b.id, 1, uuid.uuid4(), "administrador")
    )
    _agregar_uc().execute(AgregarNodoDTO(categoria.id, c.id, 2, uuid.uuid4(), "administrador"))

    _uc().execute(QuitarNodoDTO(nodo_b.id, uuid.uuid4(), "administrador"))

    nodo_repo = NodoRoadmapRepository()
    orden = [(n.laboratorio_id, n.posicion) for n in nodo_repo.find_por_categoria(categoria.id)]
    assert orden == [(a.id, 0), (c.id, 1)]
    assert nodo_repo.get_by_laboratorio(b.id) is None


@pytest.mark.django_db
def test_instructor_no_puede_quitar_nodo():
    categoria = _crear_categoria()
    lab = _crear_lab()
    nodo = _agregar_uc().execute(
        AgregarNodoDTO(categoria.id, lab.id, 0, uuid.uuid4(), "administrador")
    )

    with pytest.raises(ForbiddenError):
        _uc().execute(QuitarNodoDTO(nodo.id, uuid.uuid4(), "instructor"))


@pytest.mark.django_db
def test_nodo_inexistente_lanza_not_found():
    with pytest.raises(NotFoundError):
        _uc().execute(QuitarNodoDTO(uuid.uuid4(), uuid.uuid4(), "administrador"))
