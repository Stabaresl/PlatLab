import pytest
from django.contrib.auth.hashers import check_password

from modules.authentication.application.dtos import RegistroDTO
from modules.authentication.application.use_cases.registrar_usuario import (
    RegistrarUsuarioUseCase,
)
from modules.shared.domain.exceptions import ConflictError, ValidationError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork
from modules.users.infrastructure.repositories import UserRepository


def _build_use_case():
    return RegistrarUsuarioUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        user_repository=UserRepository(),
    )


@pytest.mark.django_db
def test_registrar_usuario_exitoso_crea_usuario_estudiante():
    uc = _build_use_case()
    dto = RegistroDTO(
        email="nuevo_estudiante@uni.edu",
        password="Segura123",
        password_confirm="Segura123",
        nombre_completo="Ana Perez",
    )

    result = uc.execute(dto)

    assert result.email == "nuevo_estudiante@uni.edu"
    assert result.rol == "estudiante"
    assert result.email_verificado is False

    saved = UserRepository().get_by_email("nuevo_estudiante@uni.edu")
    assert saved is not None
    assert check_password("Segura123", saved.password_hash)


@pytest.mark.django_db
def test_registrar_usuario_email_duplicado_lanza_conflict():
    uc = _build_use_case()
    dto = RegistroDTO(
        email="duplicado@uni.edu",
        password="Segura123",
        password_confirm="Segura123",
        nombre_completo="Primero",
    )
    uc.execute(dto)

    with pytest.raises(ConflictError):
        _build_use_case().execute(dto)


@pytest.mark.django_db
def test_registrar_usuario_passwords_no_coinciden():
    uc = _build_use_case()
    dto = RegistroDTO(
        email="mismatch@uni.edu",
        password="Segura123",
        password_confirm="OtraCosa123",
        nombre_completo="Test",
    )

    with pytest.raises(ValidationError):
        uc.execute(dto)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "password",
    ["corta1A", "sinmayuscula123", "SinNumeroAqui"],
)
def test_registrar_usuario_password_no_cumple_politica(password):
    uc = _build_use_case()
    dto = RegistroDTO(
        email="politica@uni.edu",
        password=password,
        password_confirm=password,
        nombre_completo="Test",
    )

    with pytest.raises(ValidationError):
        uc.execute(dto)


@pytest.mark.django_db
def test_registrar_usuario_email_invalido():
    uc = _build_use_case()
    dto = RegistroDTO(
        email="no-es-un-email",
        password="Segura123",
        password_confirm="Segura123",
        nombre_completo="Test",
    )

    with pytest.raises(ValidationError):
        uc.execute(dto)


@pytest.mark.django_db
def test_registrar_usuario_dispara_evento_user_registered():
    dispatcher = EventDispatcher()
    received = []
    from modules.authentication.domain.events import UserRegistered

    dispatcher.subscribe(UserRegistered, lambda e: received.append(e))

    uc = RegistrarUsuarioUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=dispatcher,
        user_repository=UserRepository(),
    )
    dto = RegistroDTO(
        email="evento@uni.edu",
        password="Segura123",
        password_confirm="Segura123",
        nombre_completo="Evento Test",
    )

    uc.execute(dto)

    assert len(received) == 1
    assert received[0].email == "evento@uni.edu"
