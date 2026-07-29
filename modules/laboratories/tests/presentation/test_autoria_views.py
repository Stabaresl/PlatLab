import uuid

import pytest
from django.contrib.auth.hashers import make_password
from rest_framework.test import APIClient

from modules.authentication.infrastructure.jwt_service import JWTService
from modules.laboratories.domain.entities import Flag, Laboratorio, Seccion
from modules.laboratories.domain.value_objects import (
    EstadoLaboratorio,
    NivelDificultad,
    TipoLaboratorio,
)
from modules.laboratories.infrastructure.repositories import LaboratorioRepository


def _client_autenticado(user_id: uuid.UUID, rol: str) -> APIClient:
    tokens = JWTService().generate_token_pair(user_id=user_id, rol=rol)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens.access}")
    return client


def _crear_lab_personalizado(instructor_id: uuid.UUID) -> Laboratorio:
    return LaboratorioRepository().add(
        Laboratorio(
            nombre=f"Lab Vista Autoria {uuid.uuid4()}",
            descripcion="desc",
            nivel_dificultad=NivelDificultad.BASICO,
            estado=EstadoLaboratorio.BORRADOR,
            tipo=TipoLaboratorio.PERSONALIZADO,
            instructor_id=instructor_id,
        )
    )


@pytest.mark.django_db
def test_crear_laboratorio_endpoint_requiere_autenticacion():
    response = APIClient().post(
        "/api/v1/laboratories/",
        {"nombre": "x", "descripcion": "y", "nivel_dificultad": "basico"},
        format="json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_crear_laboratorio_endpoint_instructor_exitoso():
    instructor_id = uuid.uuid4()
    client = _client_autenticado(instructor_id, "instructor")

    response = client.post(
        "/api/v1/laboratories/",
        {"nombre": "Nuevo", "descripcion": "desc", "nivel_dificultad": "basico"},
        format="json",
    )

    assert response.status_code == 201
    assert response.data["tipo"] == "personalizado"


@pytest.mark.django_db
def test_editar_laboratorio_endpoint_ajeno_retorna_403():
    lab = _crear_lab_personalizado(uuid.uuid4())
    client = _client_autenticado(uuid.uuid4(), "instructor")

    response = client.patch(
        f"/api/v1/laboratories/{lab.id}/", {"nombre": "Hackeado"}, format="json"
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_publicar_laboratorio_endpoint_sin_flags_retorna_422_o_400():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_personalizado(instructor_id)
    LaboratorioRepository().add_seccion(
        Seccion(
            laboratorio_id=lab.id,
            titulo="Practica",
            contenido_teorico="...",
            orden=1,
            tiene_practica=True,
        )
    )
    client = _client_autenticado(instructor_id, "instructor")

    response = client.post(f"/api/v1/laboratories/{lab.id}/publish/")

    assert response.status_code >= 400


@pytest.mark.django_db
def test_publicar_laboratorio_endpoint_exitoso():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_personalizado(instructor_id)
    seccion = LaboratorioRepository().add_seccion(
        Seccion(
            laboratorio_id=lab.id,
            titulo="Practica",
            contenido_teorico="...",
            orden=1,
            tiene_practica=True,
        )
    )
    LaboratorioRepository().save_flag(Flag(seccion_id=seccion.id, hash=make_password("FLAG{x}")))
    client = _client_autenticado(instructor_id, "instructor")

    response = client.post(f"/api/v1/laboratories/{lab.id}/publish/")

    assert response.status_code == 200
    assert response.data["estado"] == "publicado"


@pytest.mark.django_db
def test_duplicar_laboratorio_endpoint_estudiante_retorna_403():
    lab = LaboratorioRepository().add(
        Laboratorio(
            nombre=f"Predeterminado {uuid.uuid4()}",
            descripcion="desc",
            nivel_dificultad=NivelDificultad.BASICO,
            estado=EstadoLaboratorio.PUBLICADO,
            tipo=TipoLaboratorio.PREDETERMINADO,
        )
    )
    client = _client_autenticado(uuid.uuid4(), "estudiante")

    response = client.post(f"/api/v1/laboratories/{lab.id}/duplicate/")

    assert response.status_code == 403


@pytest.mark.django_db
def test_crear_seccion_endpoint_exitoso():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_personalizado(instructor_id)
    client = _client_autenticado(instructor_id, "instructor")

    response = client.post(
        f"/api/v1/laboratories/{lab.id}/sections/",
        {"titulo": "Intro", "contenido_teorico": "<p>hola</p>", "orden": 1},
        format="json",
    )

    assert response.status_code == 201
    assert response.data["titulo"] == "Intro"


@pytest.mark.django_db
def test_editar_seccion_endpoint_exitoso():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_personalizado(instructor_id)
    seccion = LaboratorioRepository().add_seccion(
        Seccion(laboratorio_id=lab.id, titulo="Original", contenido_teorico="...", orden=1)
    )
    client = _client_autenticado(instructor_id, "instructor")

    response = client.patch(
        f"/api/v1/laboratories/{lab.id}/sections/{seccion.id}/",
        {"titulo": "Editado"},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["titulo"] == "Editado"
