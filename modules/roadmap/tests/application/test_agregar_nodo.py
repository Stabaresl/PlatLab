import uuid

import pytest

from modules.laboratories.domain.entities import Laboratorio
from modules.laboratories.domain.value_objects import (
    EstadoLaboratorio,
    NivelDificultad,
    TipoLaboratorio,
)
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.roadmap.application.dtos import AgregarNodoDTO
from modules.roadmap.application.use_cases.agregar_nodo import AgregarNodoUseCase
from modules.roadmap.domain.entities import CategoriaRoadmap
from modules.roadmap.infrastructure.repositories import (
    CategoriaRoadmapRepository,
    NodoRoadmapRepository,
)
from modules.shared.domain.exceptions import ConflictError, ForbiddenError, NotFoundError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


def _uc():
    return AgregarNodoUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        categoria_repository=CategoriaRoadmapRepository(),
        nodo_repository=NodoRoadmapRepository(),
        laboratorio_repository=LaboratorioRepository(),
    )


def _crear_categoria(nombre=None):
    repo = CategoriaRoadmapRepository()
    return repo.add(CategoriaRoadmap(nombre=nombre or f"Cat {uuid.uuid4()}"))


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
def test_admin_agrega_nodo_exitosamente():
    categoria = _crear_categoria()
    lab = _crear_lab()

    resultado = _uc().execute(
        AgregarNodoDTO(
            categoria_id=categoria.id,
            laboratorio_id=lab.id,
            posicion=0,
            actor_id=uuid.uuid4(),
            actor_rol="administrador",
        )
    )

    assert resultado.posicion == 0
    assert NodoRoadmapRepository().get_by_laboratorio(lab.id) is not None


@pytest.mark.django_db
def test_insertar_en_medio_desplaza_los_siguientes():
    categoria = _crear_categoria()
    lab_a, lab_b, lab_c = _crear_lab(), _crear_lab(), _crear_lab()
    nodo_repo = NodoRoadmapRepository()

    _uc().execute(
        AgregarNodoDTO(categoria.id, lab_a.id, 0, uuid.uuid4(), "administrador")
    )
    _uc().execute(
        AgregarNodoDTO(categoria.id, lab_b.id, 1, uuid.uuid4(), "administrador")
    )
    _uc().execute(
        AgregarNodoDTO(categoria.id, lab_c.id, 1, uuid.uuid4(), "administrador")
    )

    orden = [(n.laboratorio_id, n.posicion) for n in nodo_repo.find_por_categoria(categoria.id)]
    assert (lab_a.id, 0) in orden
    assert (lab_c.id, 1) in orden
    assert (lab_b.id, 2) in orden


@pytest.mark.django_db
def test_instructor_no_puede_agregar_nodo():
    categoria = _crear_categoria()
    lab = _crear_lab()

    with pytest.raises(ForbiddenError):
        _uc().execute(
            AgregarNodoDTO(categoria.id, lab.id, 0, uuid.uuid4(), "instructor")
        )


@pytest.mark.django_db
def test_categoria_inexistente_lanza_not_found():
    lab = _crear_lab()

    with pytest.raises(NotFoundError):
        _uc().execute(
            AgregarNodoDTO(uuid.uuid4(), lab.id, 0, uuid.uuid4(), "administrador")
        )


@pytest.mark.django_db
def test_laboratorio_personalizado_no_puede_ir_en_roadmap():
    categoria = _crear_categoria()
    lab = _crear_lab(tipo=TipoLaboratorio.PERSONALIZADO, instructor_id=uuid.uuid4())

    with pytest.raises(ForbiddenError):
        _uc().execute(
            AgregarNodoDTO(categoria.id, lab.id, 0, uuid.uuid4(), "administrador")
        )


@pytest.mark.django_db
def test_laboratorio_sin_publicar_no_puede_ir_en_roadmap():
    categoria = _crear_categoria()
    lab = _crear_lab(estado=EstadoLaboratorio.BORRADOR)

    with pytest.raises(ConflictError):
        _uc().execute(
            AgregarNodoDTO(categoria.id, lab.id, 0, uuid.uuid4(), "administrador")
        )


@pytest.mark.django_db
def test_laboratorio_ya_en_roadmap_no_se_puede_agregar_dos_veces():
    categoria = _crear_categoria()
    otra_categoria = _crear_categoria()
    lab = _crear_lab()
    _uc().execute(AgregarNodoDTO(categoria.id, lab.id, 0, uuid.uuid4(), "administrador"))

    with pytest.raises(ConflictError):
        _uc().execute(
            AgregarNodoDTO(otra_categoria.id, lab.id, 0, uuid.uuid4(), "administrador")
        )
