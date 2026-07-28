import pytest
from django.contrib.auth.hashers import make_password

from modules.authentication.application.dtos import ConfirmarVinculacionDTO
from modules.authentication.application.use_cases.confirmar_vinculacion_oauth import (
    ConfirmarVinculacionOAuthUseCase,
)
from modules.authentication.domain.events import OAuthAccountLinked, UserLoggedIn
from modules.authentication.infrastructure.jwt_service import JWTService
from modules.authentication.infrastructure.oauth_link_store import OAuthLinkStore
from modules.authentication.infrastructure.refresh_token_store import RefreshTokenStore
from modules.shared.domain.exceptions import ForbiddenError, UnauthenticatedError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork
from modules.users.domain.entities import ProveedorTipo, User
from modules.users.domain.value_objects import Email
from modules.users.infrastructure.repositories import UserRepository


def _create_user(email: str, password: str = "Segura123", is_active: bool = True) -> User:
    return UserRepository().add(
        User(
            email=Email(email),
            nombre_completo="Vinculacion Test",
            password_hash=make_password(password),
            is_active=is_active,
        )
    )


def _build_use_case(dispatcher=None):
    return ConfirmarVinculacionOAuthUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=dispatcher or EventDispatcher(),
        user_repository=UserRepository(),
        jwt_service=JWTService(),
        refresh_token_store=RefreshTokenStore(),
        oauth_link_store=OAuthLinkStore(),
    )


@pytest.mark.django_db
def test_confirmar_vinculacion_exitosa_vincula_proveedor_y_retorna_tokens():
    user = _create_user("confirmar_vinc_ok@uni.edu")
    link_token = OAuthLinkStore().create_token(
        user_id=user.id, proveedor="google", proveedor_uid="google-uid-confirm-ok"
    )

    tokens = _build_use_case().execute(
        ConfirmarVinculacionDTO(link_token=link_token, password="Segura123")
    )

    assert tokens.access
    proveedores = UserRepository().get_proveedores_by_user_id(user.id)
    assert len(proveedores) == 1
    assert proveedores[0].proveedor == ProveedorTipo.GOOGLE
    assert proveedores[0].proveedor_uid == "google-uid-confirm-ok"


@pytest.mark.django_db
def test_confirmar_vinculacion_token_es_de_un_solo_uso():
    user = _create_user("confirmar_vinc_reuso@uni.edu")
    link_token = OAuthLinkStore().create_token(
        user_id=user.id, proveedor="google", proveedor_uid="google-uid-reuso"
    )

    _build_use_case().execute(ConfirmarVinculacionDTO(link_token=link_token, password="Segura123"))

    with pytest.raises(UnauthenticatedError):
        _build_use_case().execute(
            ConfirmarVinculacionDTO(link_token=link_token, password="Segura123")
        )


@pytest.mark.django_db
def test_confirmar_vinculacion_password_incorrecta_lanza_unauthenticated():
    user = _create_user("confirmar_vinc_badpass@uni.edu")
    link_token = OAuthLinkStore().create_token(
        user_id=user.id, proveedor="google", proveedor_uid="google-uid-badpass"
    )

    with pytest.raises(UnauthenticatedError):
        _build_use_case().execute(
            ConfirmarVinculacionDTO(link_token=link_token, password="Incorrecta1")
        )


@pytest.mark.django_db
def test_confirmar_vinculacion_token_invalido_lanza_unauthenticated():
    with pytest.raises(UnauthenticatedError):
        _build_use_case().execute(
            ConfirmarVinculacionDTO(link_token="token-que-nunca-existio", password="Segura123")
        )


@pytest.mark.django_db
def test_confirmar_vinculacion_usuario_inactivo_lanza_forbidden():
    user = _create_user("confirmar_vinc_inactivo@uni.edu", is_active=False)
    link_token = OAuthLinkStore().create_token(
        user_id=user.id, proveedor="google", proveedor_uid="google-uid-inactivo"
    )

    with pytest.raises(ForbiddenError):
        _build_use_case().execute(
            ConfirmarVinculacionDTO(link_token=link_token, password="Segura123")
        )


@pytest.mark.django_db
def test_confirmar_vinculacion_dispara_eventos_de_vinculacion_y_login():
    user = _create_user("confirmar_vinc_evento@uni.edu")
    link_token = OAuthLinkStore().create_token(
        user_id=user.id, proveedor="github", proveedor_uid="github-uid-evento"
    )
    dispatcher = EventDispatcher()
    vinculados = []
    logins = []
    dispatcher.subscribe(OAuthAccountLinked, lambda e: vinculados.append(e))
    dispatcher.subscribe(UserLoggedIn, lambda e: logins.append(e))

    _build_use_case(dispatcher).execute(
        ConfirmarVinculacionDTO(link_token=link_token, password="Segura123")
    )

    assert len(vinculados) == 1
    assert vinculados[0].proveedor == "github"
    assert len(logins) == 1
