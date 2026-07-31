import uuid

import pytest

from modules.roadmap.application.queries.listar_categorias import ListarCategoriasQuery
from modules.roadmap.domain.entities import CategoriaRoadmap
from modules.roadmap.infrastructure.repositories import CategoriaRoadmapRepository
from modules.shared.domain.exceptions import ForbiddenError


@pytest.mark.django_db
def test_lista_categorias_ordenadas():
    repo = CategoriaRoadmapRepository()
    repo.add(CategoriaRoadmap(nombre=f"B {uuid.uuid4()}", orden=1))
    repo.add(CategoriaRoadmap(nombre=f"A {uuid.uuid4()}", orden=0))

    resultado = ListarCategoriasQuery(repo).execute(actor_rol="administrador")

    ordenes = [c.orden for c in resultado]
    assert ordenes == sorted(ordenes)


@pytest.mark.django_db
def test_instructor_no_puede_listar_categorias():
    with pytest.raises(ForbiddenError):
        ListarCategoriasQuery(CategoriaRoadmapRepository()).execute(actor_rol="instructor")
