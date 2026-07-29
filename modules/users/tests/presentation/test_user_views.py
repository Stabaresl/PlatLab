import uuid

import pytest
from rest_framework.test import APIClient

from modules.authentication.infrastructure.jwt_service import JWTService
from modules.users.domain.entities import User
from modules.users.domain.value_objects import Email, Rol
from modules.users.infrastructure.repositories import UserRepository


def _client_autenticado(user_id: uuid.UUID, rol: str) -> APIClient:
    tokens = JWTService().generate_token_pair(user_id=user_id, rol=rol)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens.access}")
    return client


def _crear_usuario(email: str, rol: Rol = Rol.ESTUDIANTE) -> User:
    return UserRepository().add(User(email=Email(email), nombre_completo="Usuario Vista", rol=rol))


@pytest.mark.django_db
def test_list_endpoint_requiere_autenticacion():
    response = APIClient().get("/api/v1/users/")

    assert response.status_code == 401


@pytest.mark.django_db
def test_list_endpoint_no_admin_retorna_403():
    client = _client_autenticado(uuid.uuid4(), "instructor")

    response = client.get("/api/v1/users/")

    assert response.status_code == 403


@pytest.mark.django_db
def test_list_endpoint_admin_exitoso():
    _crear_usuario(f"vista_lista_{uuid.uuid4()}@uni.edu")
    client = _client_autenticado(uuid.uuid4(), "administrador")

    response = client.get("/api/v1/users/")

    assert response.status_code == 200
    assert len(response.data) >= 1


@pytest.mark.django_db
def test_list_endpoint_sin_filtro_activo_no_oculta_usuarios_activos():
    """
    Regresion: BooleanField de DRF trata un query param ausente como
    `False` (comportamiento HTML-input) salvo que se declare
    `allow_null=True` — sin eso, `GET /users/` sin `?activo=` filtraba
    por error solo deshabilitados, ocultando todos los activos.
    """
    usuario = _crear_usuario(f"vista_sin_filtro_{uuid.uuid4()}@uni.edu")
    client = _client_autenticado(uuid.uuid4(), "administrador")

    response = client.get("/api/v1/users/")

    ids = [item["id"] for item in response.data]
    assert str(usuario.id) in ids


@pytest.mark.django_db
def test_list_endpoint_filtro_activo_false_excluye_activos():
    usuario_activo = _crear_usuario(f"vista_activo_{uuid.uuid4()}@uni.edu")
    client = _client_autenticado(uuid.uuid4(), "administrador")

    response = client.get("/api/v1/users/?activo=false")

    ids = [item["id"] for item in response.data]
    assert str(usuario_activo.id) not in ids


@pytest.mark.django_db
def test_retrieve_endpoint_admin_exitoso():
    usuario = _crear_usuario(f"vista_detalle_{uuid.uuid4()}@uni.edu")
    client = _client_autenticado(uuid.uuid4(), "administrador")

    response = client.get(f"/api/v1/users/{usuario.id}/")

    assert response.status_code == 200
    assert response.data["id"] == str(usuario.id)


@pytest.mark.django_db
def test_partial_update_endpoint_admin_cambia_rol():
    usuario = _crear_usuario(f"vista_editar_{uuid.uuid4()}@uni.edu")
    client = _client_autenticado(uuid.uuid4(), "administrador")

    response = client.patch(f"/api/v1/users/{usuario.id}/", {"rol": "instructor"}, format="json")

    assert response.status_code == 200
    assert response.data["rol"] == "instructor"


@pytest.mark.django_db
def test_disable_endpoint_admin_exitoso():
    usuario = _crear_usuario(f"vista_disable_{uuid.uuid4()}@uni.edu")
    client = _client_autenticado(uuid.uuid4(), "administrador")

    response = client.post(f"/api/v1/users/{usuario.id}/disable/")

    assert response.status_code == 200
    assert response.data["is_active"] is False


@pytest.mark.django_db
def test_disable_endpoint_admin_no_puede_deshabilitarse_a_si_mismo():
    admin = _crear_usuario(f"vista_admin_self_{uuid.uuid4()}@uni.edu", rol=Rol.ADMINISTRADOR)
    client = _client_autenticado(admin.id, "administrador")

    response = client.post(f"/api/v1/users/{admin.id}/disable/")

    assert response.status_code >= 400


@pytest.mark.django_db
def test_enable_endpoint_admin_exitoso():
    usuario = _crear_usuario(f"vista_enable_{uuid.uuid4()}@uni.edu")
    client = _client_autenticado(uuid.uuid4(), "administrador")
    client.post(f"/api/v1/users/{usuario.id}/disable/")

    response = client.post(f"/api/v1/users/{usuario.id}/enable/")

    assert response.status_code == 200
    assert response.data["is_active"] is True
