import pytest
from rest_framework.test import APIClient


def _register(client, email="login_view@uni.edu", password="Segura123"):
    return client.post(
        "/api/v1/auth/register/",
        {
            "email": email,
            "password": password,
            "password_confirm": password,
            "nombre_completo": "Login View Test",
        },
        format="json",
    )


@pytest.mark.django_db
def test_login_endpoint_returns_200_with_tokens():
    client = APIClient()
    _register(client, "login_ok_view@uni.edu", "Segura123")

    response = client.post(
        "/api/v1/auth/login/",
        {"email": "login_ok_view@uni.edu", "password": "Segura123"},
        format="json",
    )

    assert response.status_code == 200
    assert "access" in response.data
    assert "refresh" in response.data
    assert response.data["expires_in"] == 15 * 60
    assert response.data["rol"] == "estudiante"


@pytest.mark.django_db
def test_login_endpoint_returns_401_on_wrong_password():
    client = APIClient()
    _register(client, "login_bad_view@uni.edu", "Segura123")

    response = client.post(
        "/api/v1/auth/login/",
        {"email": "login_bad_view@uni.edu", "password": "Incorrecta1"},
        format="json",
    )

    assert response.status_code == 401
    assert response.data["error"]["code"] == "UNAUTHENTICATED"


@pytest.mark.django_db
def test_login_endpoint_returns_401_on_unknown_email():
    client = APIClient()

    response = client.post(
        "/api/v1/auth/login/",
        {"email": "no_existe_view@uni.edu", "password": "Segura123"},
        format="json",
    )

    assert response.status_code == 401


def test_login_endpoint_is_public():
    client = APIClient()

    response = client.post("/api/v1/auth/login/", {}, format="json")

    assert response.status_code != 403
