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
from modules.shared.domain.exceptions import UnauthenticatedError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork
from modules.users.domain.entities import User
from modules.users.domain.value_objects import Email, Rol
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
        user_repository=UserRepository(),
    )


@pytest.mark.django_db
def test_refresh_de_usuario_deshabilitado_falla_y_revoca_la_sesion():
    """Regresión: un usuario deshabilitado seguía renovando su sesión indefinidamente."""
    tokens = _login("refresh_disabled@uni.edu")
    repo = UserRepository()
    user = repo.get_by_email("refresh_disabled@uni.edu")
    user.is_active = False
    repo.update(user)

    with pytest.raises(UnauthenticatedError):
        _build_refresh_use_case().execute(RefreshRequestDTO(refresh=tokens.refresh))

    # aunque lo reactiven, ese refresh ya quedó revocado
    user.is_active = True
    repo.update(user)
    with pytest.raises(InvalidCredentialsError):
        _build_refresh_use_case().execute(RefreshRequestDTO(refresh=tokens.refresh))


@pytest.mark.django_db
def test_refresh_refleja_cambio_de_rol_sin_volver_a_iniciar_sesion():
    """Regresión: el rol se copiaba del token viejo (ej. ascenso a instructor no se aplicaba)."""
    tokens = _login("refresh_rol@uni.edu")
    repo = UserRepository()
    user = repo.get_by_email("refresh_rol@uni.edu")
    user.rol = Rol.INSTRUCTOR
    repo.update(user)

    nuevos = _build_refresh_use_case().execute(RefreshRequestDTO(refresh=tokens.refresh))

    assert nuevos.rol == "instructor"
    assert JWTService().decode_access_token(nuevos.access)["rol"] == "instructor"


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
