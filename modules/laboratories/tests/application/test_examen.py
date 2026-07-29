import uuid

import pytest

from modules.laboratories.application.dtos import AgregarPreguntaDTO, CrearExamenDTO
from modules.laboratories.application.use_cases.agregar_pregunta import AgregarPreguntaUseCase
from modules.laboratories.application.use_cases.crear_examen import CrearExamenUseCase
from modules.laboratories.domain.entities import Laboratorio
from modules.laboratories.domain.value_objects import (
    EstadoLaboratorio,
    NivelDificultad,
    TipoLaboratorio,
)
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.shared.domain.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


def _crear_lab_personalizado(instructor_id):
    return LaboratorioRepository().add(
        Laboratorio(
            nombre=f"Lab {uuid.uuid4()}",
            descripcion="desc",
            nivel_dificultad=NivelDificultad.BASICO,
            estado=EstadoLaboratorio.BORRADOR,
            tipo=TipoLaboratorio.PERSONALIZADO,
            instructor_id=instructor_id,
        )
    )


def _build_crear_examen_use_case():
    return CrearExamenUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        laboratorio_repository=LaboratorioRepository(),
    )


def _build_agregar_pregunta_use_case():
    return AgregarPreguntaUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        laboratorio_repository=LaboratorioRepository(),
    )


@pytest.mark.django_db
def test_crear_examen_exitoso_instructor_dueno():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_personalizado(instructor_id)

    resultado = _build_crear_examen_use_case().execute(
        CrearExamenDTO(laboratorio_id=lab.id, actor_id=instructor_id, actor_rol="instructor")
    )

    assert resultado.laboratorio_id == lab.id


@pytest.mark.django_db
def test_crear_examen_ya_existente_lanza_conflict():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_personalizado(instructor_id)
    dto = CrearExamenDTO(laboratorio_id=lab.id, actor_id=instructor_id, actor_rol="instructor")
    _build_crear_examen_use_case().execute(dto)

    with pytest.raises(ConflictError):
        _build_crear_examen_use_case().execute(dto)


@pytest.mark.django_db
def test_crear_examen_instructor_no_dueno_lanza_forbidden():
    lab = _crear_lab_personalizado(uuid.uuid4())

    with pytest.raises(ForbiddenError):
        _build_crear_examen_use_case().execute(
            CrearExamenDTO(laboratorio_id=lab.id, actor_id=uuid.uuid4(), actor_rol="instructor")
        )


@pytest.mark.django_db
def test_agregar_pregunta_opcion_multiple_exitosa():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_personalizado(instructor_id)
    examen = _build_crear_examen_use_case().execute(
        CrearExamenDTO(laboratorio_id=lab.id, actor_id=instructor_id, actor_rol="instructor")
    )

    resultado = _build_agregar_pregunta_use_case().execute(
        AgregarPreguntaDTO(
            laboratorio_id=lab.id,
            enunciado="¿Cual es la capital?",
            tipo="opcion_multiple",
            respuesta="a",
            actor_id=instructor_id,
            actor_rol="instructor",
            opciones=["a", "b"],
        )
    )

    assert resultado.examen_id == examen.id
    assert resultado.tipo == "opcion_multiple"


@pytest.mark.django_db
def test_agregar_pregunta_abierta_exitosa():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_personalizado(instructor_id)
    _build_crear_examen_use_case().execute(
        CrearExamenDTO(laboratorio_id=lab.id, actor_id=instructor_id, actor_rol="instructor")
    )

    resultado = _build_agregar_pregunta_use_case().execute(
        AgregarPreguntaDTO(
            laboratorio_id=lab.id,
            enunciado="Explica XSS",
            tipo="abierta",
            respuesta="Cross Site Scripting",
            actor_id=instructor_id,
            actor_rol="instructor",
        )
    )

    assert resultado.tipo == "abierta"
    assert resultado.opciones is None


@pytest.mark.django_db
def test_agregar_pregunta_sin_examen_lanza_not_found():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_personalizado(instructor_id)

    with pytest.raises(NotFoundError):
        _build_agregar_pregunta_use_case().execute(
            AgregarPreguntaDTO(
                laboratorio_id=lab.id,
                enunciado="x",
                tipo="abierta",
                respuesta="y",
                actor_id=instructor_id,
                actor_rol="instructor",
            )
        )


@pytest.mark.django_db
def test_agregar_pregunta_tipo_invalido_lanza_validation_error():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_personalizado(instructor_id)
    _build_crear_examen_use_case().execute(
        CrearExamenDTO(laboratorio_id=lab.id, actor_id=instructor_id, actor_rol="instructor")
    )

    with pytest.raises(ValidationError):
        _build_agregar_pregunta_use_case().execute(
            AgregarPreguntaDTO(
                laboratorio_id=lab.id,
                enunciado="x",
                tipo="tipo_invalido",
                respuesta="y",
                actor_id=instructor_id,
                actor_rol="instructor",
            )
        )


@pytest.mark.django_db
def test_agregar_pregunta_opcion_multiple_sin_opciones_lanza_validation_error():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_personalizado(instructor_id)
    _build_crear_examen_use_case().execute(
        CrearExamenDTO(laboratorio_id=lab.id, actor_id=instructor_id, actor_rol="instructor")
    )

    with pytest.raises(ValidationError):
        _build_agregar_pregunta_use_case().execute(
            AgregarPreguntaDTO(
                laboratorio_id=lab.id,
                enunciado="x",
                tipo="opcion_multiple",
                respuesta="a",
                actor_id=instructor_id,
                actor_rol="instructor",
                opciones=None,
            )
        )
