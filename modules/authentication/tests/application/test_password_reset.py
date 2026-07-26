import pytest
from django.contrib.auth.hashers import check_password, make_password

from modules.authentication.application.dtos import (
    ConfirmarRecuperacionDTO,
    SolicitarRecuperacionDTO,
)
from modules.authentication.application.use_cases.confirmar_recuperacion import (
    ConfirmarRecuperacionUseCase,
)
from modules.authentication.application.use_cases.solicitar_recuperacion import (
    SolicitarRecuperacionUseCase,
)
from modules.authentication.domain.events import PasswordResetRequested
from modules.authentication.infrastructure.password_reset_store import (
    PasswordResetTokenStore,
)
from modules.authentication.infrastructure.refresh_token_store import RefreshTokenStore
from modules.shared.domain.exceptions import ValidationError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork
from modules.users.domain.entities import User
from modules.users.domain.value_objects import Email
from modules.users.infrastructure.repositories import UserRepository


def _create_user(email: str, password: str = "Original123") -> User:
    return UserRepository().add(
        User(
            email=Email(email),
            nombre_completo="Recuperacion Test",
            password_hash=make_password(password),
        )
    )


def _solicitar_uc(dispatcher=None):
    return SolicitarRecuperacionUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=dispatcher or EventDispatcher(),
        user_repository=UserRepository(),
        password_reset_store=PasswordResetTokenStore(),
    )


def _confirmar_uc():
    return ConfirmarRecuperacionUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        user_repository=UserRepository(),
        password_reset_store=PasswordResetTokenStore(),
        refresh_token_store=RefreshTokenStore(),
    )


@pytest.mark.django_db
def test_solicitar_recuperacion_usuario_existente_dispara_evento_con_token():
    _create_user("solicitar_ok@uni.edu")
    dispatcher = EventDispatcher()
    received = []
    dispatcher.subscribe(PasswordResetRequested, lambda e: received.append(e))

    _solicitar_uc(dispatcher).execute(SolicitarRecuperacionDTO(email="solicitar_ok@uni.edu"))

    assert len(received) == 1
    assert received[0].email == "solicitar_ok@uni.edu"
    assert received[0].token


@pytest.mark.django_db
def test_solicitar_recuperacion_usuario_inexistente_no_dispara_evento_ni_falla():
    dispatcher = EventDispatcher()
    received = []
    dispatcher.subscribe(PasswordResetRequested, lambda e: received.append(e))

    # No debe lanzar excepcion (anti-enumeracion)
    _solicitar_uc(dispatcher).execute(SolicitarRecuperacionDTO(email="no_existe_recup@uni.edu"))

    assert received == []


@pytest.mark.django_db
def test_confirmar_recuperacion_exitoso_actualiza_password():
    user = _create_user("confirmar_ok@uni.edu")
    store = PasswordResetTokenStore()
    token = store.create_token(user.id)

    _confirmar_uc().execute(
        ConfirmarRecuperacionDTO(
            token=token, password="NuevaSegura123", password_confirm="NuevaSegura123"
        )
    )

    updated = UserRepository().get_by_id(user.id)
    assert check_password("NuevaSegura123", updated.password_hash)
    assert not check_password("Original123", updated.password_hash)


@pytest.mark.django_db
def test_confirmar_recuperacion_token_es_de_un_solo_uso():
    user = _create_user("confirmar_reuso@uni.edu")
    store = PasswordResetTokenStore()
    token = store.create_token(user.id)

    _confirmar_uc().execute(
        ConfirmarRecuperacionDTO(
            token=token, password="NuevaSegura123", password_confirm="NuevaSegura123"
        )
    )

    with pytest.raises(ValidationError):
        _confirmar_uc().execute(
            ConfirmarRecuperacionDTO(
                token=token, password="OtraSegura123", password_confirm="OtraSegura123"
            )
        )


@pytest.mark.django_db
def test_confirmar_recuperacion_token_invalido_lanza_validation_error():
    with pytest.raises(ValidationError):
        _confirmar_uc().execute(
            ConfirmarRecuperacionDTO(
                token="token-que-nunca-existio",
                password="NuevaSegura123",
                password_confirm="NuevaSegura123",
            )
        )


@pytest.mark.django_db
def test_confirmar_recuperacion_passwords_no_coinciden():
    user = _create_user("confirmar_mismatch@uni.edu")
    token = PasswordResetTokenStore().create_token(user.id)

    with pytest.raises(ValidationError):
        _confirmar_uc().execute(
            ConfirmarRecuperacionDTO(
                token=token, password="NuevaSegura123", password_confirm="OtraCosa123"
            )
        )


@pytest.mark.django_db
def test_confirmar_recuperacion_password_debil_lanza_validation_error():
    user = _create_user("confirmar_debil@uni.edu")
    token = PasswordResetTokenStore().create_token(user.id)

    with pytest.raises(ValidationError):
        _confirmar_uc().execute(
            ConfirmarRecuperacionDTO(token=token, password="debil", password_confirm="debil")
        )
