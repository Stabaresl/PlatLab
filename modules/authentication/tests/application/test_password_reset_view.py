import pytest
from rest_framework.test import APIClient

from modules.authentication.infrastructure.password_reset_store import (
    PasswordResetTokenStore,
)
from modules.users.infrastructure.repositories import UserRepository


def _register(client, email="reset_view@uni.edu", password="Original123"):
    return client.post(
        "/api/v1/auth/register/",
        {
            "email": email,
            "password": password,
            "password_confirm": password,
            "nombre_completo": "Reset View Test",
        },
        format="json",
    )


@pytest.mark.django_db
def test_password_reset_endpoint_returns_200_regardless_of_existing_email():
    client = APIClient()
    _register(client, "reset_exists@uni.edu")

    resp_existente = client.post(
        "/api/v1/auth/password-reset/", {"email": "reset_exists@uni.edu"}, format="json"
    )
    resp_inexistente = client.post(
        "/api/v1/auth/password-reset/", {"email": "reset_no_existe@uni.edu"}, format="json"
    )

    assert resp_existente.status_code == 200
    assert resp_inexistente.status_code == 200
    assert resp_existente.data == resp_inexistente.data


def test_password_reset_endpoint_is_public():
    client = APIClient()

    response = client.post("/api/v1/auth/password-reset/", {}, format="json")

    assert response.status_code != 401


@pytest.mark.django_db
def test_password_reset_confirm_endpoint_returns_200_and_updates_password():
    client = APIClient()
    _register(client, "reset_confirm_view@uni.edu")
    user = UserRepository().get_by_email("reset_confirm_view@uni.edu")
    token = PasswordResetTokenStore().create_token(user.id)

    response = client.post(
        "/api/v1/auth/password-reset/confirm/",
        {"token": token, "password": "NuevaSegura123", "password_confirm": "NuevaSegura123"},
        format="json",
    )

    assert response.status_code == 200

    login_response = client.post(
        "/api/v1/auth/login/",
        {"email": "reset_confirm_view@uni.edu", "password": "NuevaSegura123"},
        format="json",
    )
    assert login_response.status_code == 200


@pytest.mark.django_db
def test_password_reset_confirm_endpoint_returns_400_on_invalid_token():
    client = APIClient()

    response = client.post(
        "/api/v1/auth/password-reset/confirm/",
        {
            "token": "token-invalido",
            "password": "NuevaSegura123",
            "password_confirm": "NuevaSegura123",
        },
        format="json",
    )

    assert response.status_code == 400
    assert response.data["error"]["code"] == "VALIDATION_ERROR"


def test_password_reset_confirm_endpoint_is_public():
    client = APIClient()

    response = client.post("/api/v1/auth/password-reset/confirm/", {}, format="json")

    assert response.status_code != 401
