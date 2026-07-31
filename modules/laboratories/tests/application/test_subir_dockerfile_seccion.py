import uuid

import pytest

from modules.laboratories.application.dtos import SubirDockerfileDTO
from modules.laboratories.application.use_cases.subir_dockerfile_seccion import (
    SubirDockerfileSeccionUseCase,
)
from modules.laboratories.domain.entities import Laboratorio, Seccion
from modules.laboratories.domain.value_objects import (
    EstadoLaboratorio,
    NivelDificultad,
    TipoLaboratorio,
)
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.shared.domain.exceptions import ForbiddenError, ValidationError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


def _uc():
    return SubirDockerfileSeccionUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        laboratorio_repository=LaboratorioRepository(),
    )


def _crear_lab_con_seccion(instructor_id: uuid.UUID) -> tuple[Laboratorio, Seccion]:
    repo = LaboratorioRepository()
    lab = repo.add(
        Laboratorio(
            nombre="Lab Dockerfile",
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
def test_subir_dockerfile_exitoso_persiste_y_reemplaza():
    instructor_id = uuid.uuid4()
    lab, seccion = _crear_lab_con_seccion(instructor_id)

    resultado = _uc().execute(
        SubirDockerfileDTO(
            laboratorio_id=lab.id,
            seccion_id=seccion.id,
            archivo_nombre="Dockerfile",
            archivo_contenido=b"FROM python:3.12-slim\n",
            actor_id=instructor_id,
            actor_rol="instructor",
        )
    )
    assert resultado.nombre_archivo == "Dockerfile"

    reemplazo = _uc().execute(
        SubirDockerfileDTO(
            laboratorio_id=lab.id,
            seccion_id=seccion.id,
            archivo_nombre="Dockerfile.v2",
            archivo_contenido=b"FROM python:3.13-slim\n",
            actor_id=instructor_id,
            actor_rol="instructor",
        )
    )

    guardado = LaboratorioRepository().get_dockerfile_by_seccion(seccion.id)
    assert guardado.nombre_archivo == "Dockerfile.v2"
    assert reemplazo.id == resultado.id


@pytest.mark.django_db
def test_subir_dockerfile_excede_limite_lanza_validation_error():
    instructor_id = uuid.uuid4()
    lab, seccion = _crear_lab_con_seccion(instructor_id)
    contenido_grande = b"x" * (4 * 1024 * 1024)

    with pytest.raises(ValidationError):
        _uc().execute(
            SubirDockerfileDTO(
                laboratorio_id=lab.id,
                seccion_id=seccion.id,
                archivo_nombre="context.zip",
                archivo_contenido=contenido_grande,
                actor_id=instructor_id,
                actor_rol="instructor",
            )
        )


@pytest.mark.django_db
def test_subir_dockerfile_instructor_ajeno_lanza_forbidden():
    lab, seccion = _crear_lab_con_seccion(uuid.uuid4())

    with pytest.raises(ForbiddenError):
        _uc().execute(
            SubirDockerfileDTO(
                laboratorio_id=lab.id,
                seccion_id=seccion.id,
                archivo_nombre="Dockerfile",
                archivo_contenido=b"FROM python:3.12-slim\n",
                actor_id=uuid.uuid4(),
                actor_rol="instructor",
            )
        )
