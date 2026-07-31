import uuid

import pytest

from modules.roadmap.application.dtos import CrearCategoriaDTO
from modules.roadmap.application.use_cases.crear_categoria import CrearCategoriaUseCase
from modules.roadmap.infrastructure.repositories import CategoriaRoadmapRepository
from modules.shared.domain.exceptions import ConflictError, ForbiddenError, ValidationError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


def _uc():
    return CrearCategoriaUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        categoria_repository=CategoriaRoadmapRepository(),
    )


@pytest.mark.django_db
def test_admin_crea_categoria_exitosamente():
    resultado = _uc().execute(
        CrearCategoriaDTO(
            nombre=f"Redes {uuid.uuid4()}", actor_id=uuid.uuid4(), actor_rol="administrador"
        )
    )

    assert resultado.orden == 0
    assert CategoriaRoadmapRepository().get_by_id(resultado.id) is not None


@pytest.mark.django_db
def test_segunda_categoria_recibe_orden_incremental():
    _uc().execute(
        CrearCategoriaDTO(
            nombre=f"Primera {uuid.uuid4()}", actor_id=uuid.uuid4(), actor_rol="administrador"
        )
    )
    segunda = _uc().execute(
        CrearCategoriaDTO(
            nombre=f"Segunda {uuid.uuid4()}", actor_id=uuid.uuid4(), actor_rol="administrador"
        )
    )

    assert segunda.orden >= 1


@pytest.mark.django_db
def test_instructor_no_puede_crear_categoria():
    with pytest.raises(ForbiddenError):
        _uc().execute(
            CrearCategoriaDTO(
                nombre=f"X {uuid.uuid4()}", actor_id=uuid.uuid4(), actor_rol="instructor"
            )
        )


@pytest.mark.django_db
def test_nombre_vacio_lanza_validation_error():
    with pytest.raises(ValidationError):
        _uc().execute(
            CrearCategoriaDTO(nombre="   ", actor_id=uuid.uuid4(), actor_rol="administrador")
        )


@pytest.mark.django_db
def test_nombre_duplicado_lanza_conflict():
    nombre = f"Duplicada {uuid.uuid4()}"
    _uc().execute(CrearCategoriaDTO(nombre=nombre, actor_id=uuid.uuid4(), actor_rol="administrador"))

    with pytest.raises(ConflictError):
        _uc().execute(
            CrearCategoriaDTO(nombre=nombre, actor_id=uuid.uuid4(), actor_rol="administrador")
        )
