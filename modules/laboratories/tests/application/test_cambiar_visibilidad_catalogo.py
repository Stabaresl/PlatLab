import uuid

import pytest

from modules.laboratories.application.dtos import CambiarVisibilidadCatalogoDTO
from modules.laboratories.application.use_cases.cambiar_visibilidad_catalogo import (
    CambiarVisibilidadCatalogoUseCase,
)
from modules.laboratories.domain.entities import Laboratorio
from modules.laboratories.domain.value_objects import (
    EstadoLaboratorio,
    NivelDificultad,
    TipoLaboratorio,
)
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.shared.domain.exceptions import ConflictError, ForbiddenError, NotFoundError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


def _uc():
    return CambiarVisibilidadCatalogoUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        laboratorio_repository=LaboratorioRepository(),
    )


def _crear_lab(**overrides) -> Laboratorio:
    # `visible_en_catalogo` no lo acepta `add()` (una creación nunca nace ya
    # visible en catálogo) — se aplica después vía `update()`.
    repo = LaboratorioRepository()
    visible_en_catalogo = overrides.pop("visible_en_catalogo", None)
    defaults = dict(
        nombre="Lab Visibilidad",
        descripcion="desc",
        nivel_dificultad=NivelDificultad.BASICO,
        estado=EstadoLaboratorio.PUBLICADO,
        tipo=TipoLaboratorio.PERSONALIZADO,
        instructor_id=uuid.uuid4(),
    )
    defaults.update(overrides)
    lab = repo.add(Laboratorio(**defaults))
    if visible_en_catalogo is not None:
        lab.visible_en_catalogo = visible_en_catalogo
        lab = repo.update(lab)
    return lab


@pytest.mark.django_db
def test_instructor_dueno_activa_visibilidad_de_catalogo():
    lab = _crear_lab()

    resultado = _uc().execute(
        CambiarVisibilidadCatalogoDTO(
            laboratorio_id=lab.id, visible=True, actor_id=lab.instructor_id, actor_rol="instructor"
        )
    )

    assert resultado.visible_en_catalogo is True
    assert LaboratorioRepository().get_by_id(lab.id).visible_en_catalogo is True


@pytest.mark.django_db
def test_instructor_dueno_desactiva_visibilidad_de_catalogo():
    lab = _crear_lab(visible_en_catalogo=True)

    resultado = _uc().execute(
        CambiarVisibilidadCatalogoDTO(
            laboratorio_id=lab.id, visible=False, actor_id=lab.instructor_id, actor_rol="instructor"
        )
    )

    assert resultado.visible_en_catalogo is False


@pytest.mark.django_db
def test_admin_puede_activar_visibilidad_de_cualquier_laboratorio():
    lab = _crear_lab()

    resultado = _uc().execute(
        CambiarVisibilidadCatalogoDTO(
            laboratorio_id=lab.id, visible=True, actor_id=uuid.uuid4(), actor_rol="administrador"
        )
    )

    assert resultado.visible_en_catalogo is True


@pytest.mark.django_db
def test_instructor_ajeno_no_puede_cambiar_visibilidad():
    lab = _crear_lab()

    with pytest.raises(ForbiddenError):
        _uc().execute(
            CambiarVisibilidadCatalogoDTO(
                laboratorio_id=lab.id, visible=True, actor_id=uuid.uuid4(), actor_rol="instructor"
            )
        )


@pytest.mark.django_db
def test_estudiante_no_puede_cambiar_visibilidad():
    lab = _crear_lab()

    with pytest.raises(ForbiddenError):
        _uc().execute(
            CambiarVisibilidadCatalogoDTO(
                laboratorio_id=lab.id, visible=True, actor_id=uuid.uuid4(), actor_rol="estudiante"
            )
        )


@pytest.mark.django_db
def test_no_aplica_a_laboratorio_predeterminado():
    lab = LaboratorioRepository().add(
        Laboratorio(
            nombre="Lab Predeterminado",
            descripcion="desc",
            nivel_dificultad=NivelDificultad.BASICO,
            estado=EstadoLaboratorio.PUBLICADO,
            tipo=TipoLaboratorio.PREDETERMINADO,
        )
    )

    with pytest.raises(ForbiddenError):
        _uc().execute(
            CambiarVisibilidadCatalogoDTO(
                laboratorio_id=lab.id, visible=True, actor_id=uuid.uuid4(), actor_rol="administrador"
            )
        )


@pytest.mark.django_db
def test_no_aplica_si_no_esta_publicado():
    lab = _crear_lab(estado=EstadoLaboratorio.EN_REVISION)

    with pytest.raises(ConflictError):
        _uc().execute(
            CambiarVisibilidadCatalogoDTO(
                laboratorio_id=lab.id, visible=True, actor_id=lab.instructor_id, actor_rol="instructor"
            )
        )


@pytest.mark.django_db
def test_laboratorio_inexistente_lanza_not_found():
    with pytest.raises(NotFoundError):
        _uc().execute(
            CambiarVisibilidadCatalogoDTO(
                laboratorio_id=uuid.uuid4(), visible=True, actor_id=uuid.uuid4(), actor_rol="administrador"
            )
        )
