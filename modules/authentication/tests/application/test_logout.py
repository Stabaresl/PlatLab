import pytest
from django.contrib.auth.hashers import make_password

from modules.authentication.application.dtos import LoginDTO, LogoutDTO, RefreshRequestDTO
from modules.authentication.application.use_cases.login import LoginUseCase
from modules.authentication.application.use_cases.logout import (
    LogoutAllUseCase,
    LogoutUseCase,
)
from modules.authentication.application.use_cases.refresh_token import RefreshTokenUseCase
from modules.authentication.domain.exceptions import (
    InvalidCredentialsError,
    TokenReuseDetectedError,
)
from modules.authentication.infrastructure.jwt_service import JWTService
from modules.authentication.infrastructure.refresh_token_store import RefreshTokenStore
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork
from modules.users.domain.entities import User
from modules.users.domain.value_objects import Email
from modules.users.infrastructure.repositories import UserRepository


def _login(email: str, password: str = "Segura123"):
    UserRepository().add(
        User(
            email=Email(email),
            nombre_completo="Logout Test",
            password_hash=make_password(password),
        )
    )
    uc = LoginUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        user_repository=UserRepository(),
        jwt_service=JWTService(),
        refresh_token_store=RefreshTokenStore(),
    )
    return uc.execute(LoginDTO(email=email, password=password))


def _logout_uc():
    return LogoutUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        jwt_service=JWTService(),
        refresh_token_store=RefreshTokenStore(),
    )


def _logout_all_uc():
    return LogoutAllUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        jwt_service=JWTService(),
        refresh_token_store=RefreshTokenStore(),
    )


def _refresh_uc():
    return RefreshTokenUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        jwt_service=JWTService(),
        refresh_token_store=RefreshTokenStore(),
    )


@pytest.mark.django_db
def test_logout_invalida_el_refresh_usado():
    tokens = _login("logout_ok@uni.edu")
    _logout_uc().execute(LogoutDTO(refresh=tokens.refresh))

    with pytest.raises((InvalidCredentialsError, TokenReuseDetectedError)):
        _refresh_uc().execute(RefreshRequestDTO(refresh=tokens.refresh))


@pytest.mark.django_db
def test_logout_no_afecta_otras_sesiones_del_usuario():
    email = "logout_multi_session@uni.edu"
    # dos "logins" = dos sesiones (familias) distintas del mismo usuario
    session_a = _login(email)
    UserRepository().get_by_email(email)  # asegura que ya existe, no falla el 2do login
    session_b_uc = LoginUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        user_repository=UserRepository(),
        jwt_service=JWTService(),
        refresh_token_store=RefreshTokenStore(),
    )
    session_b = session_b_uc.execute(LoginDTO(email=email, password="Segura123"))

    _logout_uc().execute(LogoutDTO(refresh=session_a.refresh))

    # sesion A murio
    with pytest.raises((InvalidCredentialsError, TokenReuseDetectedError)):
        _refresh_uc().execute(RefreshRequestDTO(refresh=session_a.refresh))

    # sesion B sigue viva
    new_tokens_b = _refresh_uc().execute(RefreshRequestDTO(refresh=session_b.refresh))
    assert new_tokens_b.access


@pytest.mark.django_db
def test_logout_all_invalida_todas_las_sesiones():
    email = "logout_all@uni.edu"
    session_a = _login(email)
    session_b_uc = LoginUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        user_repository=UserRepository(),
        jwt_service=JWTService(),
        refresh_token_store=RefreshTokenStore(),
    )
    session_b = session_b_uc.execute(LoginDTO(email=email, password="Segura123"))

    _logout_all_uc().execute(LogoutDTO(refresh=session_a.refresh))

    with pytest.raises((InvalidCredentialsError, TokenReuseDetectedError)):
        _refresh_uc().execute(RefreshRequestDTO(refresh=session_a.refresh))
    with pytest.raises((InvalidCredentialsError, TokenReuseDetectedError)):
        _refresh_uc().execute(RefreshRequestDTO(refresh=session_b.refresh))


@pytest.mark.django_db
def test_logout_con_token_malformado_lanza_error():
    with pytest.raises(Exception):  # noqa: B017
        _logout_uc().execute(LogoutDTO(refresh="no-es-un-jwt"))
