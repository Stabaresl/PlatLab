import pytest
from rest_framework.test import APIClient


def _register_and_login(client, email="refresh_view@uni.edu", password="Segura123"):
    client.post(
        "/api/v1/auth/register/",
        {
            "email": email,
            "password": password,
            "password_confirm": password,
            "nombre_completo": "Refresh View Test",
        },
        format="json",
    )
    login_response = client.post(
        "/api/v1/auth/login/", {"email": email, "password": password}, format="json"
    )
    return login_response.data


@pytest.mark.django_db
def test_refresh_endpoint_returns_200_with_new_tokens():
    client = APIClient()
    tokens = _register_and_login(client, "refresh_ok_view@uni.edu")

    response = client.post(
        "/api/v1/auth/refresh/", {"refresh": tokens["refresh"]}, format="json"
    )

    assert response.status_code == 200
    assert response.data["access"]
    assert response.data["refresh"] != tokens["refresh"]


@pytest.mark.django_db
def test_refresh_endpoint_returns_401_on_reused_token():
    client = APIClient()
    tokens = _register_and_login(client, "refresh_reuse_view@uni.edu")
    client.post("/api/v1/auth/refresh/", {"refresh": tokens["refresh"]}, format="json")

    response = client.post(
        "/api/v1/auth/refresh/", {"refresh": tokens["refresh"]}, format="json"
    )

    assert response.status_code == 401
    assert response.data["error"]["code"] == "UNAUTHENTICATED"


@pytest.mark.django_db
def test_refresh_endpoint_returns_401_on_garbage_token():
    client = APIClient()

    response = client.post(
        "/api/v1/auth/refresh/", {"refresh": "no-es-un-jwt-valido"}, format="json"
    )

    assert response.status_code == 401


def test_refresh_endpoint_is_public():
    client = APIClient()

    response = client.post("/api/v1/auth/refresh/", {}, format="json")

    assert response.status_code != 403


@pytest.mark.django_db
def test_logout_endpoint_revoca_el_refresh_en_el_servidor():
    """Regresión: no existía ruta de logout — el refresh seguía valiendo 7 días tras "Salir"."""
    from django.contrib.auth.hashers import make_password

    from modules.users.domain.entities import User
    from modules.users.domain.value_objects import Email
    from modules.users.infrastructure.repositories import UserRepository

    UserRepository().add(
        User(email=Email("logout_view@uni.edu"), nombre_completo="L", password_hash=make_password("Segura123"))
    )
    client = APIClient()
    tokens = client.post(
        "/api/v1/auth/login/", {"email": "logout_view@uni.edu", "password": "Segura123"}, format="json"
    ).data

    assert client.post("/api/v1/auth/logout/", {"refresh": tokens["refresh"]}, format="json").status_code == 204
    assert client.post("/api/v1/auth/refresh/", {"refresh": tokens["refresh"]}, format="json").status_code == 401
