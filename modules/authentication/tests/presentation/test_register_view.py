import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_register_endpoint_returns_201_on_success():
    client = APIClient()

    response = client.post(
        "/api/v1/auth/register/",
        {
            "email": "endpoint_test@uni.edu",
            "password": "Segura123",
            "password_confirm": "Segura123",
            "nombre_completo": "Endpoint Test",
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.data["email"] == "endpoint_test@uni.edu"
    assert response.data["rol"] == "estudiante"
    assert response.data["email_verificado"] is False
    assert "id" in response.data


@pytest.mark.django_db
def test_register_endpoint_returns_409_on_duplicate_email():
    client = APIClient()
    payload = {
        "email": "endpoint_dup@uni.edu",
        "password": "Segura123",
        "password_confirm": "Segura123",
        "nombre_completo": "Test",
    }
    client.post("/api/v1/auth/register/", payload, format="json")

    response = client.post("/api/v1/auth/register/", payload, format="json")

    assert response.status_code == 409
    assert response.data["error"]["code"] == "CONFLICT"


@pytest.mark.django_db
def test_register_endpoint_returns_400_on_missing_field():
    client = APIClient()

    response = client.post(
        "/api/v1/auth/register/",
        {"email": "sin_nombre@uni.edu", "password": "Segura123", "password_confirm": "Segura123"},
        format="json",
    )

    assert response.status_code == 400
    assert response.data["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.django_db
def test_register_endpoint_returns_400_on_weak_password():
    client = APIClient()

    response = client.post(
        "/api/v1/auth/register/",
        {
            "email": "debil@uni.edu",
            "password": "debil",
            "password_confirm": "debil",
            "nombre_completo": "Test",
        },
        format="json",
    )

    assert response.status_code == 400
    assert response.data["error"]["code"] == "VALIDATION_ERROR"


def test_register_endpoint_is_public():
    client = APIClient()

    response = client.post("/api/v1/auth/register/", {}, format="json")

    assert response.status_code != 401
