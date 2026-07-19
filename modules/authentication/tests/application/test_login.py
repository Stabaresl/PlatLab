import pytest
from django.contrib.auth.hashers import make_password

from modules.authentication.application.dtos import LoginDTO
from modules.authentication.application.use_cases.login import LoginUseCase
from modules.authentication.infrastructure.jwt_service import JWTService
from modules.shared.domain.exceptions import ForbiddenError, UnauthenticatedError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork
from modules.users.domain.entities import User
from modules.users.domain.value_objects import Email
from modules.users.infrastructure.repositories import UserRepository


def _build_use_case(dispatcher=None):
    return LoginUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=dispatcher or EventDispatcher(),
        user_repository=UserRepository(),
        jwt_service=JWTService(),
    )


def _create_user(email: str, password: str, is_active: bool = True) -> User:
    repo = UserRepository()
    return repo.add(
        User(
            email=Email(email),
            nombre_completo="Login Test",
            password_hash=make_password(password),
            is_active=is_active,
        )
    )


@pytest.mark.django_db
def test_login_exitoso_retorna_tokens():
    _create_user("login_ok@uni.edu", "Segura123")
    uc = _build_use_case()

    result = uc.execute(LoginDTO(email="login_ok@uni.edu", password="Segura123"))

    assert result.access
    assert result.refresh
    assert result.rol == "estudiante"
    assert result.expires_in == 15 * 60


@pytest.mark.django_db
def test_login_actualiza_last_login():
    user = _create_user("login_lastlogin@uni.edu", "Segura123")
    assert user.last_login is None

    uc = _build_use_case()
    uc.execute(LoginDTO(email="login_lastlogin@uni.edu", password="Segura123"))

    updated = UserRepository().get_by_id(user.id)
    assert updated.last_login is not None


@pytest.mark.django_db
def test_login_password_incorrecta_lanza_unauthenticated():
    _create_user("login_badpass@uni.edu", "Segura123")
    uc = _build_use_case()

    with pytest.raises(UnauthenticatedError):
        uc.execute(LoginDTO(email="login_badpass@uni.edu", password="Incorrecta1"))


@pytest.mark.django_db
def test_login_email_inexistente_lanza_unauthenticated():
    uc = _build_use_case()

    with pytest.raises(UnauthenticatedError):
        uc.execute(LoginDTO(email="no_existe_login@uni.edu", password="Segura123"))


@pytest.mark.django_db
def test_login_usuario_inactivo_lanza_forbidden():
    _create_user("login_inactivo@uni.edu", "Segura123", is_active=False)
    uc = _build_use_case()

    with pytest.raises(ForbiddenError):
        uc.execute(LoginDTO(email="login_inactivo@uni.edu", password="Segura123"))


@pytest.mark.django_db
def test_login_dispara_evento_user_logged_in():
    from modules.authentication.domain.events import UserLoggedIn

    _create_user("login_evento@uni.edu", "Segura123")
    dispatcher = EventDispatcher()
    received = []
    dispatcher.subscribe(UserLoggedIn, lambda e: received.append(e))

    uc = _build_use_case(dispatcher)
    uc.execute(LoginDTO(email="login_evento@uni.edu", password="Segura123"))

    assert len(received) == 1
