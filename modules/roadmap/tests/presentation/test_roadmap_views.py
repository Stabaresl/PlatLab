import uuid

import pytest
from rest_framework.test import APIClient

from modules.authentication.infrastructure.jwt_service import JWTService
from modules.laboratories.domain.entities import Laboratorio
from modules.laboratories.domain.value_objects import (
    EstadoLaboratorio,
    NivelDificultad,
    TipoLaboratorio,
)
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.roadmap.domain.entities import CategoriaRoadmap
from modules.roadmap.infrastructure.repositories import CategoriaRoadmapRepository


def _crear_lab(**overrides) -> Laboratorio:
    defaults = dict(
        nombre=f"Lab Vista {uuid.uuid4()}",
        descripcion="desc",
        nivel_dificultad=NivelDificultad.BASICO,
        estado=EstadoLaboratorio.PUBLICADO,
        tipo=TipoLaboratorio.PREDETERMINADO,
    )
    defaults.update(overrides)
    return LaboratorioRepository().add(Laboratorio(**defaults))


def _crear_categoria():
    return CategoriaRoadmapRepository().add(CategoriaRoadmap(nombre=f"Cat Vista {uuid.uuid4()}"))


def _client_autenticado(user_id: uuid.UUID, rol: str) -> APIClient:
    tokens = JWTService().generate_token_pair(user_id=user_id, rol=rol)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens.access}")
    return client


@pytest.mark.django_db
def test_get_roadmap_es_publico():
    response = APIClient().get("/api/v1/roadmap/")

    assert response.status_code == 200


@pytest.mark.django_db
def test_post_categorias_sin_auth_retorna_401():
    response = APIClient().post("/api/v1/roadmap/categorias/", {"nombre": "X"}, format="json")

    assert response.status_code == 401


@pytest.mark.django_db
def test_post_categorias_estudiante_retorna_403():
    client = _client_autenticado(uuid.uuid4(), "estudiante")

    response = client.post("/api/v1/roadmap/categorias/", {"nombre": "X"}, format="json")

    assert response.status_code == 403


@pytest.mark.django_db
def test_flujo_completo_admin_agrega_nodo_y_aparece_en_publico():
    admin = _client_autenticado(uuid.uuid4(), "administrador")
    lab = _crear_lab()

    categoria_resp = admin.post(
        "/api/v1/roadmap/categorias/", {"nombre": f"Cat HTTP {uuid.uuid4()}"}, format="json"
    )
    assert categoria_resp.status_code == 201
    categoria_id = categoria_resp.data["id"]

    nodo_resp = admin.post(
        "/api/v1/roadmap/nodos/",
        {"categoria_id": categoria_id, "laboratorio_id": str(lab.id), "posicion": 0},
        format="json",
    )
    assert nodo_resp.status_code == 201
    nodo_id = nodo_resp.data["id"]

    publico = APIClient().get("/api/v1/roadmap/")
    categorias = {c["id"]: c for c in publico.data}
    assert categoria_id in categorias
    assert categorias[categoria_id]["nodos"][0]["laboratorio_id"] == str(lab.id)

    reorder_resp = admin.patch(
        f"/api/v1/roadmap/nodos/{nodo_id}/",
        {"categoria_id": categoria_id, "posicion": 0},
        format="json",
    )
    assert reorder_resp.status_code == 200

    delete_resp = admin.delete(f"/api/v1/roadmap/nodos/{nodo_id}/")
    assert delete_resp.status_code == 204

    publico_tras_borrar = APIClient().get("/api/v1/roadmap/")
    categorias_tras_borrar = {c["id"]: c for c in publico_tras_borrar.data}
    assert categorias_tras_borrar[categoria_id]["nodos"] == []


@pytest.mark.django_db
def test_estudiante_se_inscribe_al_primer_nodo_vía_http():
    admin = _client_autenticado(uuid.uuid4(), "administrador")
    estudiante = _client_autenticado(uuid.uuid4(), "estudiante")
    lab = _crear_lab()

    categoria_resp = admin.post(
        "/api/v1/roadmap/categorias/", {"nombre": f"Cat HTTP Enroll {uuid.uuid4()}"}, format="json"
    )
    categoria_id = categoria_resp.data["id"]
    nodo_resp = admin.post(
        "/api/v1/roadmap/nodos/",
        {"categoria_id": categoria_id, "laboratorio_id": str(lab.id), "posicion": 0},
        format="json",
    )
    nodo_id = nodo_resp.data["id"]

    inscribirse_resp = estudiante.post(f"/api/v1/roadmap/nodos/{nodo_id}/inscribirse/")

    assert inscribirse_resp.status_code == 201
    assert inscribirse_resp.data["laboratorio_id"] == str(lab.id)


@pytest.mark.django_db
def test_admin_puede_no_enviar_posicion_y_se_agrega_al_final():
    admin = _client_autenticado(uuid.uuid4(), "administrador")
    lab_a, lab_b = _crear_lab(), _crear_lab()
    categoria_id = admin.post(
        "/api/v1/roadmap/categorias/", {"nombre": f"Cat Append {uuid.uuid4()}"}, format="json"
    ).data["id"]

    admin.post(
        "/api/v1/roadmap/nodos/",
        {"categoria_id": categoria_id, "laboratorio_id": str(lab_a.id)},
        format="json",
    )
    segundo = admin.post(
        "/api/v1/roadmap/nodos/",
        {"categoria_id": categoria_id, "laboratorio_id": str(lab_b.id)},
        format="json",
    )

    assert segundo.data["posicion"] == 1
