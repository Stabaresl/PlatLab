import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_login_endpoint_rate_limit_bloquea_intento_11():
    client = APIClient()

    for _ in range(10):
        client.post(
            "/api/v1/auth/login/",
            {"email": "quien_sea@uni.edu", "password": "loquesea"},
            format="json",
        )

    response = client.post(
        "/api/v1/auth/login/",
        {"email": "quien_sea@uni.edu", "password": "loquesea"},
        format="json",
    )

    assert response.status_code == 429


@pytest.mark.django_db
def test_register_endpoint_rate_limit_bloquea_intento_11():
    client = APIClient()

    for i in range(10):
        client.post(
            "/api/v1/auth/register/",
            {
                "email": f"flood_{i}@uni.edu",
                "password": "Segura123",
                "password_confirm": "Segura123",
                "nombre_completo": "Flood Test",
            },
            format="json",
        )

    response = client.post(
        "/api/v1/auth/register/",
        {
            "email": "flood_final@uni.edu",
            "password": "Segura123",
            "password_confirm": "Segura123",
            "nombre_completo": "Flood Test",
        },
        format="json",
    )

    assert response.status_code == 429


@pytest.mark.django_db
def test_rate_limit_de_login_no_bloquea_registro_desde_la_misma_ip():
    client = APIClient()

    for _ in range(10):
        client.post(
            "/api/v1/auth/login/",
            {"email": "otro@uni.edu", "password": "loquesea"},
            format="json",
        )

    response = client.post(
        "/api/v1/auth/register/",
        {
            "email": "no_deberia_bloquearse@uni.edu",
            "password": "Segura123",
            "password_confirm": "Segura123",
            "nombre_completo": "Otra Accion",
        },
        format="json",
    )

    assert response.status_code != 429
