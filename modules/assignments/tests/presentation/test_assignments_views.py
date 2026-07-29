import uuid

import pytest
from rest_framework.test import APIClient

from modules.assignments.domain.entities import Asignacion
from modules.assignments.infrastructure.repositories import AsignacionRepository
from modules.authentication.infrastructure.jwt_service import JWTService
from modules.laboratories.domain.entities import Laboratorio
from modules.laboratories.domain.value_objects import (
    EstadoLaboratorio,
    NivelDificultad,
    TipoLaboratorio,
)
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.users.domain.entities import User
from modules.users.domain.value_objects import Email
from modules.users.infrastructure.repositories import UserRepository


def _client_autenticado(user_id: uuid.UUID, rol: str) -> APIClient:
    tokens = JWTService().generate_token_pair(user_id=user_id, rol=rol)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens.access}")
    return client


def _crear_lab_publicado(instructor_id: uuid.UUID) -> Laboratorio:
    return LaboratorioRepository().add(
        Laboratorio(
            nombre=f"Lab Vista Assignments {uuid.uuid4()}",
            descripcion="desc",
            nivel_dificultad=NivelDificultad.BASICO,
            estado=EstadoLaboratorio.PUBLICADO,
            tipo=TipoLaboratorio.PERSONALIZADO,
            instructor_id=instructor_id,
        )
    )


@pytest.mark.django_db
def test_invitar_endpoint_requiere_autenticacion():
    response = APIClient().post(
        "/api/v1/assignments/invitations/",
        {"laboratorio_id": str(uuid.uuid4()), "estudiantes": ["x@uni.edu"]},
        format="json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_invitar_endpoint_instructor_exitoso():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_publicado(instructor_id)
    UserRepository().add(User(email=Email("vista_inv@uni.edu"), nombre_completo="X"))
    client = _client_autenticado(instructor_id, "instructor")

    response = client.post(
        "/api/v1/assignments/invitations/",
        {"laboratorio_id": str(lab.id), "estudiantes": ["vista_inv@uni.edu"]},
        format="json",
    )

    assert response.status_code == 201
    assert response.data["invitaciones"][0]["resultado"] == "invitado"


@pytest.mark.django_db
def test_aceptar_invitacion_endpoint_exitoso():
    instructor_id = uuid.uuid4()
    estudiante_id = uuid.uuid4()
    lab = _crear_lab_publicado(instructor_id)
    asignacion = AsignacionRepository().add(
        Asignacion(estudiante_id=estudiante_id, laboratorio_id=lab.id, instructor_id=instructor_id)
    )
    client = _client_autenticado(estudiante_id, "estudiante")

    response = client.post(f"/api/v1/assignments/invitations/{asignacion.id}/accept/")

    assert response.status_code == 200
    assert response.data["estado"] == "activa"


@pytest.mark.django_db
def test_aceptar_invitacion_endpoint_ajena_retorna_404():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_publicado(instructor_id)
    asignacion = AsignacionRepository().add(
        Asignacion(estudiante_id=uuid.uuid4(), laboratorio_id=lab.id, instructor_id=instructor_id)
    )
    client = _client_autenticado(uuid.uuid4(), "estudiante")

    response = client.post(f"/api/v1/assignments/invitations/{asignacion.id}/accept/")

    assert response.status_code == 404


@pytest.mark.django_db
def test_rechazar_invitacion_endpoint_exitoso():
    instructor_id = uuid.uuid4()
    estudiante_id = uuid.uuid4()
    lab = _crear_lab_publicado(instructor_id)
    asignacion = AsignacionRepository().add(
        Asignacion(estudiante_id=estudiante_id, laboratorio_id=lab.id, instructor_id=instructor_id)
    )
    client = _client_autenticado(estudiante_id, "estudiante")

    response = client.post(f"/api/v1/assignments/invitations/{asignacion.id}/reject/")

    assert response.status_code == 200
    assert response.data["estado"] == "rechazada"


@pytest.mark.django_db
def test_listar_asignaciones_endpoint_estudiante_ve_las_suyas():
    instructor_id = uuid.uuid4()
    estudiante_id = uuid.uuid4()
    lab = _crear_lab_publicado(instructor_id)
    AsignacionRepository().add(
        Asignacion(estudiante_id=estudiante_id, laboratorio_id=lab.id, instructor_id=instructor_id)
    )
    client = _client_autenticado(estudiante_id, "estudiante")

    response = client.get("/api/v1/assignments/")

    assert response.status_code == 200
    assert len(response.data) == 1


@pytest.mark.django_db
def test_dashboard_endpoint_estudiante_retorna_403():
    client = _client_autenticado(uuid.uuid4(), "estudiante")

    response = client.get("/api/v1/assignments/dashboard/")

    assert response.status_code == 403


@pytest.mark.django_db
def test_students_endpoint_instructor_exitoso():
    instructor_id = uuid.uuid4()
    client = _client_autenticado(instructor_id, "instructor")

    response = client.get("/api/v1/assignments/students/")

    assert response.status_code == 200
    assert response.data == []
