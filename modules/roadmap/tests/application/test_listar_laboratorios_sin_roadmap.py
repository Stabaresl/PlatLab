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
from modules.roadmap.application.queries.listar_laboratorios_sin_roadmap import (
    ListarLaboratoriosSinRoadmapQuery,
)
from modules.roadmap.application.use_cases.agregar_nodo import AgregarNodoUseCase
from modules.roadmap.domain.entities import CategoriaRoadmap
from modules.roadmap.infrastructure.repositories import (
    CategoriaRoadmapRepository,
    NodoRoadmapRepository,
)
from modules.shared.domain.exceptions import ForbiddenError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


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
def test_excluye_laboratorios_ya_en_un_nodo():
    lab_libre = _crear_lab(nombre=f"Libre {uuid.uuid4()}")
    lab_asignado = _crear_lab(nombre=f"Asignado {uuid.uuid4()}")
    categoria = CategoriaRoadmapRepository().add(CategoriaRoadmap(nombre=f"Cat {uuid.uuid4()}"))
    AgregarNodoUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        categoria_repository=CategoriaRoadmapRepository(),
        nodo_repository=NodoRoadmapRepository(),
        laboratorio_repository=LaboratorioRepository(),
    ).execute(AgregarNodoDTO(categoria.id, lab_asignado.id, 0, uuid.uuid4(), "administrador"))

    resultado = ListarLaboratoriosSinRoadmapQuery(
        laboratorio_repository=LaboratorioRepository(), nodo_repository=NodoRoadmapRepository()
    ).execute(actor_rol="administrador")

    ids = {item.id for item in resultado}
    assert lab_libre.id in ids
    assert lab_asignado.id not in ids


@pytest.mark.django_db
def test_excluye_personalizados_y_borradores():
    personalizado = _crear_lab(tipo=TipoLaboratorio.PERSONALIZADO, instructor_id=uuid.uuid4())
    borrador = _crear_lab(estado=EstadoLaboratorio.BORRADOR)

    resultado = ListarLaboratoriosSinRoadmapQuery(
        laboratorio_repository=LaboratorioRepository(), nodo_repository=NodoRoadmapRepository()
    ).execute(actor_rol="administrador")

    ids = {item.id for item in resultado}
    assert personalizado.id not in ids
    assert borrador.id not in ids


@pytest.mark.django_db
def test_estudiante_no_puede_ver_la_pool():
    with pytest.raises(ForbiddenError):
        ListarLaboratoriosSinRoadmapQuery(
            laboratorio_repository=LaboratorioRepository(), nodo_repository=NodoRoadmapRepository()
        ).execute(actor_rol="estudiante")
