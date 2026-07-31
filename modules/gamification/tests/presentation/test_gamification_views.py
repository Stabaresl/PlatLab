import uuid

import pytest
from rest_framework.test import APIClient

from modules.authentication.infrastructure.jwt_service import JWTService
from modules.gamification.domain.entities import (
    Cosmetico,
    CosmeticoDesbloqueado,
    Logro,
    Titulo,
    TituloDesbloqueado,
)
from modules.gamification.domain.value_objects import RarezaCosmetico, TipoCosmetico, TipoCriterioLogro
from modules.gamification.infrastructure.repositories import (
    CosmeticoDesbloqueadoRepository,
    CosmeticoRepository,
    LogroRepository,
    TituloDesbloqueadoRepository,
    TituloRepository,
)

_PNG_MAGIC_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


def _client_autenticado(user_id: uuid.UUID, rol: str) -> APIClient:
    tokens = JWTService().generate_token_pair(user_id=user_id, rol=rol)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens.access}")
    return client


@pytest.mark.django_db
def test_me_sin_auth_retorna_401():
    response = APIClient().get("/api/v1/gamification/me/")

    assert response.status_code == 401


@pytest.mark.django_db
def test_me_estudiante_devuelve_perfil_vacio_por_defecto():
    client = _client_autenticado(uuid.uuid4(), "estudiante")

    response = client.get("/api/v1/gamification/me/")

    assert response.status_code == 200
    assert response.data["xp"] == 0
    assert response.data["nivel"] == 1
    assert response.data["avatar_tipo"] == "preset"
    assert response.data["avatar_valor"] == "operador_nocturno"


@pytest.mark.django_db
def test_catalogo_es_accesible_para_cualquier_rol_autenticado():
    client = _client_autenticado(uuid.uuid4(), "instructor")

    response = client.get("/api/v1/gamification/catalogo/")

    assert response.status_code == 200
    assert "logros" in response.data
    assert "cosmeticos" in response.data
    assert "titulos" in response.data


@pytest.mark.django_db
def test_equipar_y_quitar_cosmetico_via_http():
    logro = LogroRepository().add(
        Logro(
            clave=f"logro-{uuid.uuid4()}",
            nombre="Logro",
            descripcion="desc",
            tipo_criterio=TipoCriterioLogro.PRIMER_LABORATORIO,
            rareza=RarezaCosmetico.COMUN,
        )
    )
    cosmetico = CosmeticoRepository().add(
        Cosmetico(
            clave=f"cosmetico-{uuid.uuid4()}",
            nombre="Cosmético",
            tipo=TipoCosmetico.HOODIE,
            rareza=RarezaCosmetico.COMUN,
            color="0,0,0",
            logro_requerido_id=logro.id,
        )
    )
    estudiante_id = uuid.uuid4()
    desbloqueo = CosmeticoDesbloqueadoRepository().add(
        CosmeticoDesbloqueado(estudiante_id=estudiante_id, cosmetico_id=cosmetico.id)
    )
    client = _client_autenticado(estudiante_id, "estudiante")

    equipar = client.patch(
        f"/api/v1/gamification/cosmeticos/{desbloqueo.id}/", {"equipado": True}, format="json"
    )
    assert equipar.status_code == 200
    assert equipar.data["equipado"] is True

    quitar = client.patch(
        f"/api/v1/gamification/cosmeticos/{desbloqueo.id}/", {"equipado": False}, format="json"
    )
    assert quitar.status_code == 200
    assert quitar.data["equipado"] is False


@pytest.mark.django_db
def test_equipar_cosmetico_inexistente_retorna_404():
    client = _client_autenticado(uuid.uuid4(), "estudiante")

    response = client.patch(
        f"/api/v1/gamification/cosmeticos/{uuid.uuid4()}/", {"equipado": True}, format="json"
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_avatar_presets_lista_al_menos_ocho_opciones():
    client = _client_autenticado(uuid.uuid4(), "estudiante")

    response = client.get("/api/v1/gamification/avatar-presets/")

    assert response.status_code == 200
    assert len(response.data) >= 8
    claves = {p["clave"] for p in response.data}
    assert "operador_nocturno" in claves


@pytest.mark.django_db
def test_cambiar_avatar_via_http():
    client = _client_autenticado(uuid.uuid4(), "estudiante")

    response = client.patch(
        "/api/v1/gamification/avatar/", {"clave": "unidad_autonoma"}, format="json"
    )

    assert response.status_code == 200
    assert response.data["avatar_valor"] == "unidad_autonoma"


@pytest.mark.django_db
def test_cambiar_avatar_con_clave_invalida_retorna_400():
    client = _client_autenticado(uuid.uuid4(), "estudiante")

    response = client.patch(
        "/api/v1/gamification/avatar/", {"clave": "no_existe"}, format="json"
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_subir_avatar_via_http():
    from django.core.files.uploadedfile import SimpleUploadedFile

    client = _client_autenticado(uuid.uuid4(), "estudiante")
    archivo = SimpleUploadedFile("foto.png", _PNG_MAGIC_BYTES, content_type="image/png")

    response = client.post("/api/v1/gamification/avatar/upload/", {"archivo": archivo}, format="multipart")

    assert response.status_code == 200
    assert response.data["avatar_tipo"] == "subido"
    assert response.data["avatar_valor"].startswith("/media/")


@pytest.mark.django_db
def test_equipar_y_quitar_titulo_via_http():
    logro = LogroRepository().add(
        Logro(
            clave=f"logro-{uuid.uuid4()}",
            nombre="Logro",
            descripcion="desc",
            tipo_criterio=TipoCriterioLogro.PRIMER_LABORATORIO,
            rareza=RarezaCosmetico.COMUN,
        )
    )
    titulo = TituloRepository().add(
        Titulo(
            clave=f"titulo-{uuid.uuid4()}",
            nombre="Cazador de Bugs",
            descripcion="desc",
            rareza=RarezaCosmetico.COMUN,
            logro_requerido_id=logro.id,
        )
    )
    estudiante_id = uuid.uuid4()
    desbloqueo = TituloDesbloqueadoRepository().add(
        TituloDesbloqueado(estudiante_id=estudiante_id, titulo_id=titulo.id)
    )
    client = _client_autenticado(estudiante_id, "estudiante")

    equipar = client.patch(
        f"/api/v1/gamification/titulos/{desbloqueo.id}/", {"equipado": True}, format="json"
    )
    assert equipar.status_code == 200
    assert equipar.data["equipado"] is True

    quitar = client.patch(
        f"/api/v1/gamification/titulos/{desbloqueo.id}/", {"equipado": False}, format="json"
    )
    assert quitar.status_code == 200
    assert quitar.data["equipado"] is False
