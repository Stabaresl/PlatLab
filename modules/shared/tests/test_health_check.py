import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_check_returns_200_when_dependencies_are_up():
    client = APIClient()

    response = client.get("/api/v1/health/")

    assert response.status_code == 200
    assert response.data["status"] == "ok"
    assert response.data["checks"]["database"] is True
    assert response.data["checks"]["redis"] is True


@pytest.mark.django_db
def test_health_check_is_public():
    """No requiere autenticación (HV-01: el frontend lo consulta sin login)."""
    client = APIClient()

    response = client.get("/api/v1/health/")

    assert response.status_code != 401
    assert response.status_code != 403