import pytest
from django.contrib.auth.hashers import make_password
from rest_framework.test import APIClient

from modules.authentication.application.dtos import OAuthProfileDTO
from modules.authentication.infrastructure.oauth_adapters import GoogleOAuthAdapter
from modules.authentication.infrastructure.oauth_link_store import OAuthLinkStore
from modules.users.domain.entities import User
from modules.users.domain.value_objects import Email
from modules.users.infrastructure.repositories import UserRepository


def _authorize(client, provider="google"):
    return client.get(f"/api/v1/auth/oauth/{provider}/authorize/")


def _mock_profile(monkeypatch, email, uid, proveedor="google"):
    profile = OAuthProfileDTO(
        proveedor=proveedor,
        proveedor_uid=uid,
        email=email,
        nombre_completo="OAuth View Test",
        email_verificado=True,
    )
    monkeypatch.setattr(
        GoogleOAuthAdapter, "fetch_profile", lambda self, code, code_verifier: profile
    )


@pytest.mark.django_db
def test_oauth_authorize_endpoint_returns_authorize_url_and_state():
    response = _authorize(APIClient())

    assert response.status_code == 200
    assert response.data["authorize_url"].startswith("https://accounts.google.com/")
    assert response.data["state"]


def test_oauth_authorize_endpoint_unsupported_provider_returns_404():
    response = _authorize(APIClient(), provider="facebook")
    assert response.status_code == 404


@pytest.mark.django_db
def test_oauth_authorize_endpoint_is_public():
    response = _authorize(APIClient())
    assert response.status_code != 403


@pytest.mark.django_db
def test_oauth_callback_endpoint_returns_tokens_for_new_user(monkeypatch):
    _mock_profile(monkeypatch, "oauth_view_nuevo@uni.edu", "google-uid-view-nuevo")
    client = APIClient()
    state = _authorize(client).data["state"]

    response = client.post(
        "/api/v1/auth/oauth/google/callback/",
        {"code": "code-x", "state": state},
        format="json",
    )

    assert response.status_code == 200
    assert "access" in response.data
    assert response.data["rol"] == "estudiante"


@pytest.mark.django_db
def test_oauth_callback_endpoint_collision_returns_409_with_link_token(monkeypatch):
    UserRepository().add(
        User(
            email=Email("oauth_view_colision@uni.edu"),
            nombre_completo="Password Owner",
            password_hash=make_password("Segura123"),
        )
    )
    _mock_profile(monkeypatch, "oauth_view_colision@uni.edu", "google-uid-view-colision")
    client = APIClient()
    state = _authorize(client).data["state"]

    response = client.post(
        "/api/v1/auth/oauth/google/callback/",
        {"code": "code-x", "state": state},
        format="json",
    )

    assert response.status_code == 409
    assert response.data["error"]["details"][0]["link_token"]


@pytest.mark.django_db
def test_oauth_callback_endpoint_invalid_state_returns_401():
    client = APIClient()

    response = client.post(
        "/api/v1/auth/oauth/google/callback/",
        {"code": "code-x", "state": "state-que-nunca-existio"},
        format="json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_oauth_confirm_link_endpoint_completes_linking():
    user = UserRepository().add(
        User(
            email=Email("oauth_view_confirm@uni.edu"),
            nombre_completo="Password Owner",
            password_hash=make_password("Segura123"),
        )
    )
    link_token = OAuthLinkStore().create_token(
        user_id=user.id, proveedor="google", proveedor_uid="google-uid-view-confirm"
    )

    response = APIClient().post(
        "/api/v1/auth/oauth/confirm-link/",
        {"link_token": link_token, "password": "Segura123"},
        format="json",
    )

    assert response.status_code == 200
    assert "access" in response.data


def test_oauth_confirm_link_endpoint_is_public():
    response = APIClient().post("/api/v1/auth/oauth/confirm-link/", {}, format="json")
    assert response.status_code != 403
