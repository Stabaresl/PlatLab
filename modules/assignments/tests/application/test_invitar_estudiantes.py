import uuid
from datetime import datetime, timedelta, timezone

import pytest

from modules.assignments.application.dtos import InvitarEstudiantesDTO
from modules.assignments.application.use_cases.invitar_estudiantes import (
    InvitarEstudiantesUseCase,
)
from modules.assignments.domain.exceptions import InvalidExpirationError
from modules.assignments.infrastructure.repositories import AsignacionRepository
from modules.laboratories.domain.entities import Laboratorio
from modules.laboratories.domain.value_objects import (
    EstadoLaboratorio,
    NivelDificultad,
    TipoLaboratorio,
)
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.shared.domain.exceptions import (
    BusinessRuleViolationError,
    ForbiddenError,
    NotFoundError,
)
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork
from modules.users.domain.entities import User
from modules.users.domain.value_objects import Email
from modules.users.infrastructure.repositories import UserRepository


def _uc():
    return InvitarEstudiantesUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        asignacion_repository=AsignacionRepository(),
        laboratorio_repository=LaboratorioRepository(),
        user_repository=UserRepository(),
    )


def _crear_lab_publicado(instructor_id: uuid.UUID) -> Laboratorio:
    return LaboratorioRepository().add(
        Laboratorio(
            nombre="Lab Invitar",
            descripcion="desc",
            nivel_dificultad=NivelDificultad.BASICO,
            estado=EstadoLaboratorio.PUBLICADO,
            tipo=TipoLaboratorio.PERSONALIZADO,
            instructor_id=instructor_id,
        )
    )


def _crear_estudiante(email: str) -> User:
    return UserRepository().add(User(email=Email(email), nombre_completo="Estudiante"))


@pytest.mark.django_db
def test_invitar_estudiante_por_email_exitoso():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_publicado(instructor_id)
    estudiante = _crear_estudiante("invitado1@uni.edu")

    resultado = _uc().execute(
        InvitarEstudiantesDTO(
            laboratorio_id=lab.id,
            estudiantes=["invitado1@uni.edu"],
            actor_id=instructor_id,
            actor_rol="instructor",
        )
    )

    assert len(resultado.invitaciones) == 1
    item = resultado.invitaciones[0]
    assert item.resultado == "invitado"
    assert item.asignacion_id is not None
    guardada = AsignacionRepository().get_by_id(item.asignacion_id)
    assert guardada.estudiante_id == estudiante.id


@pytest.mark.django_db
def test_invitar_estudiante_no_encontrado_no_falla_completo():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_publicado(instructor_id)

    resultado = _uc().execute(
        InvitarEstudiantesDTO(
            laboratorio_id=lab.id,
            estudiantes=["no_existe@uni.edu"],
            actor_id=instructor_id,
            actor_rol="instructor",
        )
    )

    assert resultado.invitaciones[0].resultado == "no_encontrado"


@pytest.mark.django_db
def test_invitar_estudiante_ya_vigente_no_duplica():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_publicado(instructor_id)
    _crear_estudiante("repetido@uni.edu")
    dto = InvitarEstudiantesDTO(
        laboratorio_id=lab.id,
        estudiantes=["repetido@uni.edu"],
        actor_id=instructor_id,
        actor_rol="instructor",
    )
    _uc().execute(dto)

    resultado = _uc().execute(dto)

    assert resultado.invitaciones[0].resultado == "ya_vigente"


@pytest.mark.django_db
def test_invitar_instructor_ajeno_lanza_forbidden():
    lab = _crear_lab_publicado(uuid.uuid4())

    with pytest.raises(ForbiddenError):
        _uc().execute(
            InvitarEstudiantesDTO(
                laboratorio_id=lab.id,
                estudiantes=["x@uni.edu"],
                actor_id=uuid.uuid4(),
                actor_rol="instructor",
            )
        )


@pytest.mark.django_db
def test_invitar_laboratorio_no_publicado_lanza_business_rule():
    instructor_id = uuid.uuid4()
    lab = LaboratorioRepository().add(
        Laboratorio(
            nombre="Borrador",
            descripcion="desc",
            nivel_dificultad=NivelDificultad.BASICO,
            estado=EstadoLaboratorio.BORRADOR,
            tipo=TipoLaboratorio.PERSONALIZADO,
            instructor_id=instructor_id,
        )
    )

    with pytest.raises(BusinessRuleViolationError):
        _uc().execute(
            InvitarEstudiantesDTO(
                laboratorio_id=lab.id,
                estudiantes=["x@uni.edu"],
                actor_id=instructor_id,
                actor_rol="instructor",
            )
        )


@pytest.mark.django_db
def test_invitar_laboratorio_inexistente_lanza_not_found():
    with pytest.raises(NotFoundError):
        _uc().execute(
            InvitarEstudiantesDTO(
                laboratorio_id=uuid.uuid4(),
                estudiantes=["x@uni.edu"],
                actor_id=uuid.uuid4(),
                actor_rol="instructor",
            )
        )


@pytest.mark.django_db
def test_invitar_fecha_vencimiento_pasada_lanza_invalid_expiration():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_publicado(instructor_id)

    with pytest.raises(InvalidExpirationError):
        _uc().execute(
            InvitarEstudiantesDTO(
                laboratorio_id=lab.id,
                estudiantes=["x@uni.edu"],
                actor_id=instructor_id,
                actor_rol="instructor",
                fecha_vencimiento=datetime.now(timezone.utc) - timedelta(days=1),
            )
        )
