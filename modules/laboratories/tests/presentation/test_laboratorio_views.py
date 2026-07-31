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


def _crear_lab(**overrides) -> Laboratorio:
    defaults = dict(
        nombre="Lab Vista",
        descripcion="desc",
        nivel_dificultad=NivelDificultad.BASICO,
        estado=EstadoLaboratorio.PUBLICADO,
        tipo=TipoLaboratorio.PREDETERMINADO,
        temas=[],
    )
    defaults.update(overrides)
    return LaboratorioRepository().add(Laboratorio(**defaults))


def _client_autenticado(user_id: uuid.UUID, rol: str) -> APIClient:
    tokens = JWTService().generate_token_pair(user_id=user_id, rol=rol)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens.access}")
    return client


@pytest.mark.django_db
def test_listar_endpoint_publico_no_requiere_auth():
    _crear_lab(nombre=f"Publico {uuid.uuid4()}")

    response = APIClient().get("/api/v1/laboratories/")

    assert response.status_code == 200
    assert "results" in response.data


@pytest.mark.django_db
def test_listar_endpoint_oculta_borradores_a_visitante():
    nombre_borrador = f"Borrador {uuid.uuid4()}"
    _crear_lab(nombre=nombre_borrador, estado=EstadoLaboratorio.BORRADOR)

    response = APIClient().get("/api/v1/laboratories/")

    nombres = [item["nombre"] for item in response.data["results"]]
    assert nombre_borrador not in nombres


@pytest.mark.django_db
def test_listar_endpoint_filtra_por_dificultad():
    nombre_avanzado = f"Avanzado {uuid.uuid4()}"
    nombre_basico = f"Basico {uuid.uuid4()}"
    _crear_lab(nombre=nombre_avanzado, nivel_dificultad=NivelDificultad.AVANZADO)
    _crear_lab(nombre=nombre_basico, nivel_dificultad=NivelDificultad.BASICO)

    response = APIClient().get("/api/v1/laboratories/?dificultad=avanzado")

    nombres = [item["nombre"] for item in response.data["results"]]
    assert nombre_avanzado in nombres
    assert nombre_basico not in nombres


@pytest.mark.django_db
def test_listar_endpoint_dificultad_invalida_retorna_400():
    response = APIClient().get("/api/v1/laboratories/?dificultad=imposible")

    assert response.status_code == 400


@pytest.mark.django_db
def test_listar_endpoint_instructor_ve_su_propio_borrador():
    instructor_id = uuid.uuid4()
    nombre_propio = f"Propio {uuid.uuid4()}"
    _crear_lab(
        nombre=nombre_propio,
        estado=EstadoLaboratorio.BORRADOR,
        tipo=TipoLaboratorio.PERSONALIZADO,
        instructor_id=instructor_id,
    )
    client = _client_autenticado(instructor_id, "instructor")

    response = client.get("/api/v1/laboratories/")

    nombres = [item["nombre"] for item in response.data["results"]]
    assert nombre_propio in nombres


@pytest.mark.django_db
def test_listar_endpoint_instructor_no_ve_borrador_ajeno():
    nombre_ajeno = f"Ajeno {uuid.uuid4()}"
    _crear_lab(
        nombre=nombre_ajeno,
        estado=EstadoLaboratorio.BORRADOR,
        tipo=TipoLaboratorio.PERSONALIZADO,
        instructor_id=uuid.uuid4(),
    )
    client = _client_autenticado(uuid.uuid4(), "instructor")

    response = client.get("/api/v1/laboratories/")

    nombres = [item["nombre"] for item in response.data["results"]]
    assert nombre_ajeno not in nombres


@pytest.mark.django_db
def test_listar_endpoint_estudiante_recibe_campo_inscrito():
    _crear_lab(nombre=f"Inscrito {uuid.uuid4()}")
    client = _client_autenticado(uuid.uuid4(), "estudiante")

    response = client.get("/api/v1/laboratories/")

    resultados = response.data["results"]
    assert len(resultados) > 0
    assert all(item["inscrito"] is False for item in resultados)


@pytest.mark.django_db
def test_listar_endpoint_visitante_no_recibe_inscrito():
    _crear_lab(nombre=f"SinInscrito {uuid.uuid4()}")

    response = APIClient().get("/api/v1/laboratories/")

    resultados = response.data["results"]
    assert len(resultados) > 0
    assert all(item["inscrito"] is None for item in resultados)


@pytest.mark.django_db
def test_retrieve_endpoint_devuelve_detalle_sin_contenido_teorico():
    lab = _crear_lab(nombre=f"Detalle {uuid.uuid4()}")

    response = APIClient().get(f"/api/v1/laboratories/{lab.id}/")

    assert response.status_code == 200
    assert response.data["nombre"] == lab.nombre
    assert "contenido_teorico" not in response.data


@pytest.mark.django_db
def test_retrieve_endpoint_inexistente_retorna_404():
    response = APIClient().get(f"/api/v1/laboratories/{uuid.uuid4()}/")

    assert response.status_code == 404


def test_retrieve_endpoint_id_invalido_retorna_404():
    response = APIClient().get("/api/v1/laboratories/no-es-un-uuid/")

    assert response.status_code == 404


@pytest.mark.django_db
def test_retrieve_endpoint_borrador_ajeno_retorna_404():
    lab = _crear_lab(
        nombre=f"Ajeno Detalle {uuid.uuid4()}",
        estado=EstadoLaboratorio.BORRADOR,
        tipo=TipoLaboratorio.PERSONALIZADO,
        instructor_id=uuid.uuid4(),
    )
    client = _client_autenticado(uuid.uuid4(), "instructor")

    response = client.get(f"/api/v1/laboratories/{lab.id}/")

    assert response.status_code == 404


@pytest.mark.django_db
def test_toc_endpoint_devuelve_solo_titulos():
    lab = _crear_lab(nombre=f"TOC {uuid.uuid4()}")
    LaboratorioRepository().add_seccion(
        Seccion(
            laboratorio_id=lab.id,
            titulo="Seccion 1",
            contenido_teorico="secreto",
            orden=1,
            tiene_practica=False,
        )
    )

    response = APIClient().get(f"/api/v1/laboratories/{lab.id}/toc/")

    assert response.status_code == 200
    assert response.data["secciones"][0]["titulo"] == "Seccion 1"
    assert "contenido_teorico" not in response.data["secciones"][0]


@pytest.mark.django_db
def test_listar_endpoint_es_publico():
    response = APIClient().get("/api/v1/laboratories/")

    assert response.status_code != 403


@pytest.mark.django_db
def test_catalog_visibility_endpoint_instructor_dueno_activa():
    instructor_id = uuid.uuid4()
    lab = _crear_lab(
        nombre="Lab Visibilidad Endpoint",
        tipo=TipoLaboratorio.PERSONALIZADO,
        instructor_id=instructor_id,
    )
    client = _client_autenticado(instructor_id, "instructor")

    response = client.patch(
        f"/api/v1/laboratories/{lab.id}/catalog-visibility/",
        {"visible": True},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["visible_en_catalogo"] is True


@pytest.mark.django_db
def test_catalog_visibility_endpoint_instructor_ajeno_403():
    lab = _crear_lab(
        nombre="Lab Visibilidad Ajeno",
        tipo=TipoLaboratorio.PERSONALIZADO,
        instructor_id=uuid.uuid4(),
    )
    client = _client_autenticado(uuid.uuid4(), "instructor")

    response = client.patch(
        f"/api/v1/laboratories/{lab.id}/catalog-visibility/",
        {"visible": True},
        format="json",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_catalog_visibility_endpoint_requiere_auth():
    lab = _crear_lab(
        nombre="Lab Visibilidad Sin Auth",
        tipo=TipoLaboratorio.PERSONALIZADO,
        instructor_id=uuid.uuid4(),
    )

    response = APIClient().patch(
        f"/api/v1/laboratories/{lab.id}/catalog-visibility/",
        {"visible": True},
        format="json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_published_custom_endpoint_admin_ve_personalizados_publicados():
    _crear_lab(
        nombre="Personalizado Publicado Endpoint",
        tipo=TipoLaboratorio.PERSONALIZADO,
        instructor_id=uuid.uuid4(),
    )
    client = _client_autenticado(uuid.uuid4(), "administrador")

    response = client.get("/api/v1/laboratories/published-custom/")

    assert response.status_code == 200
    nombres = [item["nombre"] for item in response.data]
    assert "Personalizado Publicado Endpoint" in nombres


@pytest.mark.django_db
def test_published_custom_endpoint_instructor_403():
    client = _client_autenticado(uuid.uuid4(), "instructor")

    response = client.get("/api/v1/laboratories/published-custom/")

    assert response.status_code == 403


@pytest.mark.django_db
def test_catalog_visibility_endpoint_invalida_cache_del_listado_sin_filtro():
    """
    Reproduce el bug reportado: el listado sin filtro ("Todos") tiene su
    propia entrada de cache (`CachedLaboratorioRepository`, TTL 60s) —
    sin invalidación explícita, activar la visibilidad de catálogo podía
    tardar hasta 60s en reflejarse ahí, aunque una categoría específica
    (nunca antes cacheada) ya mostrara el resultado fresco.
    """
    instructor_id = uuid.uuid4()
    lab = _crear_lab(
        nombre="Lab Recien Visible",
        tipo=TipoLaboratorio.PERSONALIZADO,
        instructor_id=instructor_id,
    )

    # Precalienta el cache del listado sin filtro ("Todos") ANTES de
    # activar la visibilidad — sin invalidación, este resultado (sin el
    # lab) quedaría servido desde cache hasta por 60s.
    precalentado = APIClient().get("/api/v1/laboratories/")
    assert str(lab.id) not in {u["id"] for u in precalentado.data["results"]}  # sanity check

    client = _client_autenticado(instructor_id, "instructor")
    toggle = client.patch(
        f"/api/v1/laboratories/{lab.id}/catalog-visibility/", {"visible": True}, format="json"
    )
    assert toggle.status_code == 200

    respuesta_sin_filtro = APIClient().get("/api/v1/laboratories/")
    nombres = [item["nombre"] for item in respuesta_sin_filtro.data["results"]]
    assert "Lab Recien Visible" in nombres
