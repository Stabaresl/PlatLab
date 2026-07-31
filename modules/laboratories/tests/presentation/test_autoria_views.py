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
def test_publicar_laboratorio_endpoint_instructor_retorna_403():
    """Cambio de comportamiento: un personalizado ya no se publica directo, pasa por revisión."""
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

    assert response.status_code == 403


@pytest.mark.django_db
def test_submit_review_endpoint_exitoso():
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

    response = client.post(f"/api/v1/laboratories/{lab.id}/submit-review/")

    assert response.status_code == 200
    assert response.data["estado"] == "en_revision"


@pytest.mark.django_db
def test_approve_endpoint_admin_publica_y_reject_endpoint_admin_vuelve_a_borrador():
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
    instructor_client = _client_autenticado(instructor_id, "instructor")
    instructor_client.post(f"/api/v1/laboratories/{lab.id}/submit-review/")

    admin_client = _client_autenticado(uuid.uuid4(), "administrador")
    response = admin_client.post(f"/api/v1/laboratories/{lab.id}/reject/", {"motivo": "Falta contenido"}, format="json")

    assert response.status_code == 200
    assert response.data["estado"] == "borrador"

    instructor_client.post(f"/api/v1/laboratories/{lab.id}/submit-review/")
    response = admin_client.post(f"/api/v1/laboratories/{lab.id}/approve/")

    assert response.status_code == 200
    assert response.data["estado"] == "publicado"


@pytest.mark.django_db
def test_review_queue_endpoint_solo_admin():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_personalizado(instructor_id)
    seccion = LaboratorioRepository().add_seccion(
        Seccion(laboratorio_id=lab.id, titulo="Teoria", contenido_teorico="...", orden=1)
    )
    instructor_client = _client_autenticado(instructor_id, "instructor")
    instructor_client.post(f"/api/v1/laboratories/{lab.id}/submit-review/")

    estudiante_response = _client_autenticado(uuid.uuid4(), "estudiante").get(
        "/api/v1/laboratories/review-queue/"
    )
    assert estudiante_response.status_code == 403

    admin_response = _client_autenticado(uuid.uuid4(), "administrador").get(
        "/api/v1/laboratories/review-queue/"
    )
    assert admin_response.status_code == 200
    assert any(item["id"] == str(lab.id) for item in admin_response.data)


@pytest.mark.django_db
def test_preview_seccion_endpoint_y_check_flag():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_personalizado(instructor_id)
    seccion = LaboratorioRepository().add_seccion(
        Seccion(
            laboratorio_id=lab.id,
            titulo="Practica",
            contenido_teorico="<p>contenido</p>",
            orden=1,
            tiene_practica=True,
        )
    )
    LaboratorioRepository().save_flag(Flag(seccion_id=seccion.id, hash=make_password("FLAG{x}")))
    admin_client = _client_autenticado(uuid.uuid4(), "administrador")

    preview = admin_client.get(f"/api/v1/laboratories/{lab.id}/sections/{seccion.id}/preview/")
    assert preview.status_code == 200
    assert preview.data["titulo"] == "Practica"

    check_ok = admin_client.post(
        f"/api/v1/laboratories/{lab.id}/sections/{seccion.id}/preview/check-flag/",
        {"valor": "FLAG{x}"},
        format="json",
    )
    assert check_ok.status_code == 200
    assert check_ok.data["correcto"] is True

    check_mal = admin_client.post(
        f"/api/v1/laboratories/{lab.id}/sections/{seccion.id}/preview/check-flag/",
        {"valor": "FLAG{no}"},
        format="json",
    )
    assert check_mal.data["correcto"] is False


@pytest.mark.django_db
def test_admin_puede_ver_detalle_y_toc_de_personalizado_en_revision():
    """
    Regresión: la cola de revisión del admin llama primero a `GET
    /laboratories/{id}/` y `GET /laboratories/{id}/toc/` (LabPreviewPage)
    antes de mostrar el contenido por sección — sin el bypass de admin en
    `es_visible_para`, ambos devolvían 404 ("Laboratorio no encontrado")
    para cualquier personalizado ajeno en revisión.
    """
    instructor_id = uuid.uuid4()
    lab = _crear_lab_personalizado(instructor_id)
    LaboratorioRepository().add_seccion(
        Seccion(laboratorio_id=lab.id, titulo="Intro", contenido_teorico="...", orden=1)
    )
    instructor_client = _client_autenticado(instructor_id, "instructor")
    instructor_client.post(f"/api/v1/laboratories/{lab.id}/submit-review/")

    admin_client = _client_autenticado(uuid.uuid4(), "administrador")

    detalle = admin_client.get(f"/api/v1/laboratories/{lab.id}/")
    assert detalle.status_code == 200
    assert detalle.data["estado"] == "en_revision"

    toc = admin_client.get(f"/api/v1/laboratories/{lab.id}/toc/")
    assert toc.status_code == 200
    assert len(toc.data["secciones"]) == 1


@pytest.mark.django_db
def test_preview_seccion_endpoint_estudiante_retorna_403():
    instructor_id = uuid.uuid4()
    lab = _crear_lab_personalizado(instructor_id)
    seccion = LaboratorioRepository().add_seccion(
        Seccion(laboratorio_id=lab.id, titulo="Teoria", contenido_teorico="...", orden=1)
    )
    client = _client_autenticado(uuid.uuid4(), "estudiante")

    response = client.get(f"/api/v1/laboratories/{lab.id}/sections/{seccion.id}/preview/")

    assert response.status_code == 403


@pytest.mark.django_db
def test_subir_dockerfile_endpoint_exitoso():
    from django.core.files.uploadedfile import SimpleUploadedFile

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
    client = _client_autenticado(instructor_id, "instructor")
    archivo = SimpleUploadedFile("Dockerfile", b"FROM python:3.12-slim\nCMD [\"true\"]")

    response = client.post(
        f"/api/v1/laboratories/{lab.id}/sections/{seccion.id}/dockerfile/",
        {"archivo": archivo},
        format="multipart",
    )

    assert response.status_code == 201
    assert response.data["nombre_archivo"] == "Dockerfile"


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
def test_crear_seccion_endpoint_markdown_con_html_embebido_se_sanea_end_to_end():
    """Markdown -> HTML (serializer) -> saneo (caso de uso): un <script> embebido no sobrevive."""
    instructor_id = uuid.uuid4()
    lab = _crear_lab_personalizado(instructor_id)
    client = _client_autenticado(instructor_id, "instructor")

    response = client.post(
        f"/api/v1/laboratories/{lab.id}/sections/",
        {
            "titulo": "Intro",
            "contenido_teorico": "## Título\n\n<script>alert(1)</script>",
            "orden": 1,
        },
        format="json",
    )

    assert response.status_code == 201
    guardada = LaboratorioRepository().get_seccion_by_id(uuid.UUID(response.data["id"]))
    assert "<h2>Título</h2>" in guardada.contenido_teorico
    assert "<script>" not in guardada.contenido_teorico


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
