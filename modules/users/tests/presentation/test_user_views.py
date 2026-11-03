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

    ids = [item["id"] for item in response.data["results"]]
    assert str(usuario.id) in ids


@pytest.mark.django_db
def test_list_endpoint_filtro_activo_false_excluye_activos():
    usuario_activo = _crear_usuario(f"vista_activo_{uuid.uuid4()}@uni.edu")
    client = _client_autenticado(uuid.uuid4(), "administrador")

    response = client.get("/api/v1/users/?activo=false")

    ids = [item["id"] for item in response.data["results"]]
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


@pytest.mark.django_db
def test_deshabilitar_usuario_se_audita_y_revoca_sus_sesiones():
    """Regresión: deshabilitar no quedaba auditado ni cortaba las sesiones abiertas."""
    from django.contrib.auth.hashers import make_password

    from modules.audit.infrastructure.models import RegistroAuditoriaModel
    from modules.users.domain.entities import User
    from modules.users.domain.value_objects import Email

    victima = UserRepository().add(
        User(
            email=Email(f"v-{uuid.uuid4().hex[:8]}@uni.edu"),
            nombre_completo="V",
            password_hash=make_password("Segura123"),
        )
    )
    login = APIClient().post(
        "/api/v1/auth/login/", {"email": str(victima.email), "password": "Segura123"}, format="json"
    )
    refresh = login.data["refresh"]
    admin_id = uuid.uuid4()

    response = _client_autenticado(admin_id, "administrador").post(f"/api/v1/users/{victima.id}/disable/")

    assert response.status_code == 200
    assert RegistroAuditoriaModel.objects.filter(
        accion="user_disabled", actor_id=admin_id, entidad_id=victima.id
    ).exists()
    assert APIClient().post("/api/v1/auth/refresh/", {"refresh": refresh}, format="json").status_code == 401


# --- Revisión de solicitudes de instructor (admin) -----------------------------


def _solicitud_pendiente_de(usuario: User):
    from modules.users.domain.entities import SolicitudInstructor
    from modules.users.infrastructure.repositories import SolicitudInstructorRepository

    return SolicitudInstructorRepository().add(
        SolicitudInstructor(
            user_id=usuario.id,
            orcid="0000-0002-1825-0097",
            nombre_declarado=usuario.nombre_completo,
            tipo="docente",
            institucion="Universidad de Prueba",
        )
    )


@pytest.mark.django_db
def test_listar_solicitudes_instructor_admin_ve_datos_del_inscrito():
    usuario = _crear_usuario(f"sol_lista_{uuid.uuid4()}@uni.edu")
    solicitud = _solicitud_pendiente_de(usuario)
    client = _client_autenticado(uuid.uuid4(), "administrador")

    response = client.get("/api/v1/users/instructor-requests/")

    assert response.status_code == 200
    item = next(i for i in response.data if i["id"] == str(solicitud.id))
    assert item["usuario"]["email"] == str(usuario.email)
    assert item["orcid_url"] == "https://orcid.org/0000-0002-1825-0097"
    assert item["institucion"] == "Universidad de Prueba"
    assert item["openalex"] is None


@pytest.mark.django_db
def test_listar_solicitudes_instructor_estudiante_recibe_403():
    client = _client_autenticado(uuid.uuid4(), "estudiante")

    response = client.get("/api/v1/users/instructor-requests/")

    assert response.status_code == 403


@pytest.mark.django_db
def test_aprobar_solicitud_instructor_endpoint():
    usuario = _crear_usuario(f"sol_aprobar_{uuid.uuid4()}@uni.edu")
    solicitud = _solicitud_pendiente_de(usuario)
    admin = _crear_usuario(f"sol_admin_{uuid.uuid4()}@uni.edu", Rol.ADMINISTRADOR)
    client = _client_autenticado(admin.id, "administrador")

    response = client.post(f"/api/v1/users/instructor-requests/{solicitud.id}/approve/")

    assert response.status_code == 200
    assert response.data["estado"] == "aprobada"
    assert UserRepository().get_by_id(usuario.id).rol == Rol.INSTRUCTOR


@pytest.mark.django_db
def test_rechazar_solicitud_instructor_sin_motivo_retorna_400():
    usuario = _crear_usuario(f"sol_rechazar_{uuid.uuid4()}@uni.edu")
    solicitud = _solicitud_pendiente_de(usuario)
    client = _client_autenticado(uuid.uuid4(), "administrador")

    sin_motivo = client.post(f"/api/v1/users/instructor-requests/{solicitud.id}/reject/", {}, format="json")
    con_motivo = client.post(
        f"/api/v1/users/instructor-requests/{solicitud.id}/reject/",
        {"motivo": "No encontramos publicaciones asociadas a tu ORCID."},
        format="json",
    )

    assert sin_motivo.status_code == 400
    assert con_motivo.status_code == 200
    assert con_motivo.data["estado"] == "rechazada"


@pytest.mark.django_db
def test_resolver_solicitud_con_id_invalido_retorna_404():
    client = _client_autenticado(uuid.uuid4(), "administrador")

    response = client.post("/api/v1/users/instructor-requests/no-es-uuid/approve/")

    assert response.status_code == 404
