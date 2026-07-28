import uuid

import pytest
from rest_framework.test import APIClient

from modules.authentication.infrastructure.jwt_service import JWTService
from modules.laboratories.domain.entities import Laboratorio, Seccion
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


def _crear_lab_con_seccion_practica(instructor_id: uuid.UUID) -> tuple[Laboratorio, Seccion]:
    repo = LaboratorioRepository()
    lab = repo.add(
        Laboratorio(
            nombre=f"Lab Flag View {uuid.uuid4()}",
            descripcion="desc",
            nivel_dificultad=NivelDificultad.BASICO,
            estado=EstadoLaboratorio.BORRADOR,
            tipo=TipoLaboratorio.PERSONALIZADO,
            instructor_id=instructor_id,
        )
    )
    seccion = repo.add_seccion(
        Seccion(
            laboratorio_id=lab.id,
            titulo="Practica 1",
            contenido_teorico="...",
            orden=1,
            tiene_practica=True,
        )
    )
    return lab, seccion


@pytest.mark.django_db
def test_definir_flag_endpoint_requiere_autenticacion():
    lab, seccion = _crear_lab_con_seccion_practica(uuid.uuid4())

    response = APIClient().put(
        f"/api/v1/laboratories/{lab.id}/sections/{seccion.id}/flag/",
        {"valor": "FLAG{x}"},
        format="json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_definir_flag_endpoint_instructor_propio_devuelve_200_sin_exponer_valor():
    instructor_id = uuid.uuid4()
    lab, seccion = _crear_lab_con_seccion_practica(instructor_id)
    client = _client_autenticado(instructor_id, "instructor")

    response = client.put(
        f"/api/v1/laboratories/{lab.id}/sections/{seccion.id}/flag/",
        {"valor": "FLAG{secreta}", "pista": "una pista"},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["seccion_id"] == str(seccion.id)
    assert "valor" not in response.data
    assert "hash" not in response.data


@pytest.mark.django_db
def test_definir_flag_endpoint_instructor_ajeno_devuelve_403():
    lab, seccion = _crear_lab_con_seccion_practica(uuid.uuid4())
    client = _client_autenticado(uuid.uuid4(), "instructor")

    response = client.put(
        f"/api/v1/laboratories/{lab.id}/sections/{seccion.id}/flag/",
        {"valor": "FLAG{x}"},
        format="json",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_definir_flag_endpoint_estudiante_devuelve_403():
    lab, seccion = _crear_lab_con_seccion_practica(uuid.uuid4())
    client = _client_autenticado(uuid.uuid4(), "estudiante")

    response = client.put(
        f"/api/v1/laboratories/{lab.id}/sections/{seccion.id}/flag/",
        {"valor": "FLAG{x}"},
        format="json",
    )

    assert response.status_code == 403
