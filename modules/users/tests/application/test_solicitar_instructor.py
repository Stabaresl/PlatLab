import uuid

import pytest

from modules.shared.domain.exceptions import ConflictError, ForbiddenError, ValidationError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork
from modules.users.application.dtos import SolicitarInstructorDTO
from modules.users.application.use_cases.solicitar_convertirse_en_instructor import (
    SolicitarConvertirseEnInstructorUseCase,
)
from modules.users.domain.entities import SolicitudInstructor, User
from modules.users.domain.value_objects import Email, Rol
from modules.users.infrastructure import openalex_adapter
from modules.users.infrastructure.repositories import SolicitudInstructorRepository, UserRepository

_ORCID_VALIDO = "0000-0000-0000-0000"


def _crear_estudiante(email: str, nombre: str = "Ada Lovelace") -> User:
    return UserRepository().add(
        User(email=Email(email), nombre_completo=nombre, rol=Rol.ESTUDIANTE)
    )


def _uc():
    return SolicitarConvertirseEnInstructorUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        user_repository=UserRepository(),
        solicitud_repository=SolicitudInstructorRepository(),
    )


class _FakeResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json = json_data or {}

    def json(self):
        return self._json

    def raise_for_status(self):
        pass


@pytest.mark.django_db
def test_no_estudiante_lanza_forbidden():
    with pytest.raises(ForbiddenError):
        _uc().execute(
            SolicitarInstructorDTO(
                actor_id=uuid.uuid4(), actor_rol="instructor", orcid=_ORCID_VALIDO, tipo="investigador"
            )
        )


@pytest.mark.django_db
def test_orcid_con_formato_invalido_lanza_validation_error():
    usuario = _crear_estudiante("malorcid@uni.edu")

    with pytest.raises(ValidationError):
        _uc().execute(
            SolicitarInstructorDTO(
                actor_id=usuario.id, actor_rol="estudiante", orcid="no-es-un-orcid", tipo="investigador"
            )
        )


@pytest.mark.django_db
def test_solicitud_pendiente_existente_lanza_conflict():
    usuario = _crear_estudiante("pendiente@uni.edu")
    SolicitudInstructorRepository().add(
        SolicitudInstructor(
            user_id=usuario.id,
            orcid=_ORCID_VALIDO,
            nombre_declarado=usuario.nombre_completo,
            tipo="investigador",
        )
    )

    with pytest.raises(ConflictError):
        _uc().execute(
            SolicitarInstructorDTO(
                actor_id=usuario.id, actor_rol="estudiante", orcid=_ORCID_VALIDO, tipo="investigador"
            )
        )


@pytest.mark.django_db
def test_solicitud_valida_dispara_verificacion_asincrona_y_asciende_a_instructor(monkeypatch):
    """
    Integración end-to-end del evento: `execute()` solo crea la solicitud
    en `pendiente`, pero como los tests corren con `CELERY_TASK_ALWAYS_EAGER`
    (config/settings/test.py), el listener -> tarea -> segundo caso de uso
    corren de forma síncrona antes de que `execute()` retorne — así que al
    volver a consultar el repositorio, la solicitud ya quedó resuelta.
    """
    usuario = _crear_estudiante("valido@uni.edu", nombre="Ada Lovelace")
    monkeypatch.setattr(
        openalex_adapter.requests,
        "get",
        lambda url, params, timeout: _FakeResponse(
            200, {"display_name": "Ada Lovelace", "works_count": 4}
        ),
    )

    resultado = _uc().execute(
        SolicitarInstructorDTO(
            actor_id=usuario.id, actor_rol="estudiante", orcid=_ORCID_VALIDO, tipo="investigador"
        )
    )

    solicitud_final = SolicitudInstructorRepository().get_by_id(resultado.id)
    assert solicitud_final.estado.value == "aprobada"
    usuario_final = UserRepository().get_by_id(usuario.id)
    assert usuario_final.rol == Rol.INSTRUCTOR


@pytest.mark.django_db
def test_solicitud_con_nombre_que_no_coincide_queda_rechazada(monkeypatch):
    usuario = _crear_estudiante("rechazo@uni.edu", nombre="Ada Lovelace")
    monkeypatch.setattr(
        openalex_adapter.requests,
        "get",
        lambda url, params, timeout: _FakeResponse(
            200, {"display_name": "Persona Distinta", "works_count": 4}
        ),
    )

    resultado = _uc().execute(
        SolicitarInstructorDTO(
            actor_id=usuario.id, actor_rol="estudiante", orcid=_ORCID_VALIDO, tipo="investigador"
        )
    )

    solicitud_final = SolicitudInstructorRepository().get_by_id(resultado.id)
    assert solicitud_final.estado.value == "rechazada"
    usuario_final = UserRepository().get_by_id(usuario.id)
    assert usuario_final.rol == Rol.ESTUDIANTE
