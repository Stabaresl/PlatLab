import uuid

import pytest
from django.contrib.auth.hashers import make_password

from modules.laboratories.application.dtos import PublicarLaboratorioDTO
from modules.laboratories.application.use_cases.publicar_laboratorio import (
    PublicarLaboratorioUseCase,
)
from modules.laboratories.domain.entities import Flag, Laboratorio, Seccion
from modules.laboratories.domain.exceptions import PublishValidationError
from modules.laboratories.domain.value_objects import (
    EstadoLaboratorio,
    NivelDificultad,
    TipoLaboratorio,
)
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.shared.domain.exceptions import ForbiddenError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


def _uc():
    return PublicarLaboratorioUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        laboratorio_repository=LaboratorioRepository(),
    )


def _crear_lab_predeterminado_con_seccion_practica() -> tuple[Laboratorio, Seccion]:
    repo = LaboratorioRepository()
    lab = repo.add(
        Laboratorio(
            nombre="Lab Publicar",
            descripcion="desc",
            nivel_dificultad=NivelDificultad.BASICO,
            estado=EstadoLaboratorio.BORRADOR,
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
    return lab, seccion


def _crear_lab_personalizado_con_seccion_practica(instructor_id: uuid.UUID) -> tuple[Laboratorio, Seccion]:
    repo = LaboratorioRepository()
    lab = repo.add(
        Laboratorio(
            nombre="Lab Publicar",
            descripcion="desc",
            nivel_dificultad=NivelDificultad.BASICO,
            estado=EstadoLaboratorio.BORRADOR,
            tipo=TipoLaboratorio.PERSONALIZADO,
            instructor_id=instructor_id,
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
    return lab, seccion


@pytest.mark.django_db
def test_publicar_laboratorio_admin_con_todas_las_flags_exitoso():
    lab, seccion = _crear_lab_predeterminado_con_seccion_practica()
    LaboratorioRepository().save_flag(
        Flag(seccion_id=seccion.id, hash=make_password("FLAG{x}"))
    )

    resultado = _uc().execute(
        PublicarLaboratorioDTO(
            laboratorio_id=lab.id, actor_id=uuid.uuid4(), actor_rol="administrador"
        )
    )

    assert resultado.estado == "publicado"


@pytest.mark.django_db
def test_publicar_laboratorio_admin_seccion_practica_sin_flag_lanza_publish_validation_error():
    lab, seccion = _crear_lab_predeterminado_con_seccion_practica()

    with pytest.raises(PublishValidationError) as exc_info:
        _uc().execute(
            PublicarLaboratorioDTO(
                laboratorio_id=lab.id, actor_id=uuid.uuid4(), actor_rol="administrador"
            )
        )

    assert str(seccion.id) in [d["seccion_id"] for d in exc_info.value.details]


@pytest.mark.django_db
def test_publicar_laboratorio_instructor_ya_no_puede_publicar_directamente():
    """
    Cambio de comportamiento: un personalizado ya no se publica directo
    por acá — pasa por `SolicitarRevisionLaboratorioUseCase` +
    `AprobarLaboratorioUseCase`.
    """
    instructor_id = uuid.uuid4()
    lab, seccion = _crear_lab_personalizado_con_seccion_practica(instructor_id)
    LaboratorioRepository().save_flag(
        Flag(seccion_id=seccion.id, hash=make_password("FLAG{x}"))
    )

    with pytest.raises(ForbiddenError):
        _uc().execute(
            PublicarLaboratorioDTO(
                laboratorio_id=lab.id, actor_id=instructor_id, actor_rol="instructor"
            )
        )


@pytest.mark.django_db
def test_publicar_laboratorio_admin_no_puede_publicar_personalizado():
    instructor_id = uuid.uuid4()
    lab, _ = _crear_lab_personalizado_con_seccion_practica(instructor_id)

    with pytest.raises(ForbiddenError):
        _uc().execute(
            PublicarLaboratorioDTO(
                laboratorio_id=lab.id, actor_id=uuid.uuid4(), actor_rol="administrador"
            )
        )
