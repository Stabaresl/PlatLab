import uuid

import pytest
from rest_framework.response import Response
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework.views import APIView

from modules.authentication.infrastructure.jwt_service import JWTService


class _DummyProtectedView(APIView):
    """Vista de prueba, no registrada en urls.py — solo para validar la config global."""

    def get(self, request):
        return Response({"ok": True, "user_id": str(request.user.id)})


@pytest.mark.django_db
def test_docs_endpoint_remains_public_after_global_protection():
    client = APIClient()

    response = client.get("/api/v1/docs/")

    assert response.status_code == 200


@pytest.mark.django_db
def test_schema_endpoint_remains_public_after_global_protection():
    client = APIClient()

    response = client.get("/api/v1/schema/")

    assert response.status_code == 200


@pytest.mark.django_db
def test_health_endpoint_remains_public_after_global_protection():
    client = APIClient()

    response = client.get("/api/v1/health/")

    assert response.status_code == 200


def test_default_permission_blocks_unauthenticated_request():
    """
    Prueba de extremo a extremo de la configuración global (settings
    REST_FRAMEWORK): una vista que NO declara permission_classes propio
    queda protegida automáticamente por default.
    """
    factory = APIRequestFactory()
    view = _DummyProtectedView.as_view()

    request = factory.get("/")
    response = view(request)

    assert response.status_code == 401


def test_default_permission_allows_authenticated_request():
    factory = APIRequestFactory()
    view = _DummyProtectedView.as_view()
    tokens = JWTService().generate_token_pair(user_id=uuid.uuid4(), rol="estudiante")

    request = factory.get("/", HTTP_AUTHORIZATION=f"Bearer {tokens.access}")
    response = view(request)

    assert response.status_code == 200
    assert response.data["ok"] is True
