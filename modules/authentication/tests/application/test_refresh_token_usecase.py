import pytest
from django.contrib.auth.hashers import make_password

from modules.authentication.application.dtos import LoginDTO, RefreshRequestDTO
from modules.authentication.application.use_cases.login import LoginUseCase
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
            nombre_completo="Refresh Test",
            password_hash=make_password(password),
        )
    )
    login_uc = LoginUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        user_repository=UserRepository(),
        jwt_service=JWTService(),
        refresh_token_store=RefreshTokenStore(),
    )
    return login_uc.execute(LoginDTO(email=email, password=password))


def _build_refresh_use_case():
    return RefreshTokenUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        jwt_service=JWTService(),
        refresh_token_store=RefreshTokenStore(),
    )


@pytest.mark.django_db
def test_refresh_con_token_valido_entrega_nuevo_par():
    tokens = _login("refresh_ok@uni.edu")
    uc = _build_refresh_use_case()

    new_tokens = uc.execute(RefreshRequestDTO(refresh=tokens.refresh))

    assert new_tokens.access
    assert new_tokens.refresh
    assert new_tokens.refresh != tokens.refresh
    assert new_tokens.rol == "estudiante"


@pytest.mark.django_db
def test_refresh_token_ya_rotado_lanza_reuse_detected():
    tokens = _login("refresh_reuse@uni.edu")
    uc = _build_refresh_use_case()
    uc.execute(RefreshRequestDTO(refresh=tokens.refresh))  # rota una vez, ok

    with pytest.raises(TokenReuseDetectedError):
        _build_refresh_use_case().execute(RefreshRequestDTO(refresh=tokens.refresh))


@pytest.mark.django_db
def test_refresh_reuso_invalida_tambien_el_token_nuevo():
    tokens = _login("refresh_reuse2@uni.edu")
    uc = _build_refresh_use_case()
    new_tokens = uc.execute(RefreshRequestDTO(refresh=tokens.refresh))

    with pytest.raises(TokenReuseDetectedError):
        _build_refresh_use_case().execute(RefreshRequestDTO(refresh=tokens.refresh))

    # la sesion entera quedo revocada, incluido el token "legitimo" nuevo
    with pytest.raises(InvalidCredentialsError):
        _build_refresh_use_case().execute(RefreshRequestDTO(refresh=new_tokens.refresh))


@pytest.mark.django_db
def test_refresh_token_malformado_lanza_error():
    uc = _build_refresh_use_case()

    with pytest.raises(Exception):  # noqa: B017 — cualquier error de decodificación es válido aquí
        uc.execute(RefreshRequestDTO(refresh="esto-no-es-un-jwt"))
