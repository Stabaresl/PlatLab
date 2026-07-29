import uuid

import pytest
from django.contrib.auth.hashers import make_password

from modules.laboratories.application.dtos import DuplicarLaboratorioDTO
from modules.laboratories.application.use_cases.duplicar_laboratorio import (
    DuplicarLaboratorioUseCase,
)
from modules.laboratories.domain.entities import Flag, Laboratorio, Seccion
from modules.laboratories.domain.value_objects import (
    EstadoLaboratorio,
    NivelDificultad,
    TipoLaboratorio,
)
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.shared.domain.exceptions import ForbiddenError, NotFoundError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


def _uc():
    return DuplicarLaboratorioUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        laboratorio_repository=LaboratorioRepository(),
    )


def _crear_predeterminado_con_seccion_y_flag() -> Laboratorio:
    repo = LaboratorioRepository()
    lab = repo.add(
        Laboratorio(
            nombre="Predeterminado Origen",
            descripcion="desc",
            nivel_dificultad=NivelDificultad.BASICO,
            estado=EstadoLaboratorio.PUBLICADO,
            tipo=TipoLaboratorio.PREDETERMINADO,
        )
    )
    seccion = repo.add_seccion(
        Seccion(
            laboratorio_id=lab.id,
            titulo="Practica",
            contenido_teorico="...",
            orden=1,
            tiene_practica=True,
        )
    )
    repo.save_flag(Flag(seccion_id=seccion.id, hash=make_password("FLAG{original}")))
    return lab


@pytest.mark.django_db
def test_duplicar_laboratorio_instructor_crea_copia_con_secciones_y_flags():
    instructor_id = uuid.uuid4()
    original = _crear_predeterminado_con_seccion_y_flag()

    resultado = _uc().execute(
        DuplicarLaboratorioDTO(
            laboratorio_id=original.id, actor_id=instructor_id, actor_rol="instructor"
        )
    )

    assert resultado.tipo == "personalizado"
    repo = LaboratorioRepository()
    copia = repo.get_by_id(resultado.id)
    assert copia.instructor_id == instructor_id
    assert copia.origen_id == original.id

    secciones_copia = repo.get_secciones(copia.id)
    assert len(secciones_copia) == 1
    flag_copia = repo.get_flag_by_seccion(secciones_copia[0].id)
    assert flag_copia is not None

    original_intacto = repo.get_by_id(original.id)
    assert original_intacto.tipo == TipoLaboratorio.PREDETERMINADO


@pytest.mark.django_db
def test_duplicar_laboratorio_administrador_lanza_forbidden():
    original = _crear_predeterminado_con_seccion_y_flag()

    with pytest.raises(ForbiddenError):
        _uc().execute(
            DuplicarLaboratorioDTO(
                laboratorio_id=original.id, actor_id=uuid.uuid4(), actor_rol="administrador"
            )
        )


@pytest.mark.django_db
def test_duplicar_laboratorio_inexistente_lanza_not_found():
    with pytest.raises(NotFoundError):
        _uc().execute(
            DuplicarLaboratorioDTO(
                laboratorio_id=uuid.uuid4(), actor_id=uuid.uuid4(), actor_rol="instructor"
            )
        )
