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
from modules.progress.domain.entities import Progreso, ProgresoSeccion
from modules.progress.domain.value_objects import EstadoProgresoSeccion
from modules.progress.infrastructure.repositories import ProgresoRepository


def _client_autenticado(user_id: uuid.UUID, rol: str = "estudiante") -> APIClient:
    tokens = JWTService().generate_token_pair(user_id=user_id, rol=rol)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens.access}")
    return client


def _crear_lab_con_seccion(valor_flag: str = "FLAG{correcta}"):
    lab_repo = LaboratorioRepository()
    lab = lab_repo.add(
        Laboratorio(
            nombre=f"Lab Vista Progreso {uuid.uuid4()}",
            descripcion="desc",
            nivel_dificultad=NivelDificultad.BASICO,
            estado=EstadoLaboratorio.PUBLICADO,
            tipo=TipoLaboratorio.PREDETERMINADO,
        )
    )
    seccion = lab_repo.add_seccion(
        Seccion(
            laboratorio_id=lab.id,
            titulo="Seccion Vista",
            contenido_teorico="contenido",
            orden=1,
            tiene_practica=True,
        )
    )
    lab_repo.save_flag(Flag(seccion_id=seccion.id, hash=make_password(valor_flag)))
    return lab, seccion


def _crear_progreso(seccion, estudiante_id, estado=EstadoProgresoSeccion.EN_PROGRESO):
    progreso_repo = ProgresoRepository()
    progreso = progreso_repo.add(
        Progreso(asignacion_id=uuid.uuid4(), estudiante_id=estudiante_id)
    )
    progreso_repo.add_secciones(
        [ProgresoSeccion(progreso_id=progreso.id, seccion_id=seccion.id, estado=estado)]
    )
    return progreso


@pytest.mark.django_db
def test_contenido_seccion_endpoint_requiere_autenticacion():
    _, seccion = _crear_lab_con_seccion()
    progreso = _crear_progreso(seccion, uuid.uuid4())

    response = APIClient().get(
        f"/api/v1/progress/{progreso.asignacion_id}/sections/{seccion.id}/"
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_contenido_seccion_endpoint_devuelve_contenido_al_dueno():
    estudiante_id = uuid.uuid4()
    _, seccion = _crear_lab_con_seccion()
    progreso = _crear_progreso(seccion, estudiante_id)
    client = _client_autenticado(estudiante_id)

    response = client.get(f"/api/v1/progress/{progreso.asignacion_id}/sections/{seccion.id}/")

    assert response.status_code == 200
    assert response.data["contenido_teorico"] == "contenido"


@pytest.mark.django_db
def test_contenido_seccion_endpoint_bloqueada_devuelve_403():
    estudiante_id = uuid.uuid4()
    _, seccion = _crear_lab_con_seccion()
    progreso = _crear_progreso(seccion, estudiante_id, EstadoProgresoSeccion.BLOQUEADA)
    client = _client_autenticado(estudiante_id)

    response = client.get(f"/api/v1/progress/{progreso.asignacion_id}/sections/{seccion.id}/")

    assert response.status_code == 403


@pytest.mark.django_db
def test_contenido_seccion_endpoint_otro_estudiante_devuelve_404():
    _, seccion = _crear_lab_con_seccion()
    progreso = _crear_progreso(seccion, uuid.uuid4())
    client = _client_autenticado(uuid.uuid4())

    response = client.get(f"/api/v1/progress/{progreso.asignacion_id}/sections/{seccion.id}/")

    assert response.status_code == 404


@pytest.mark.django_db
def test_flag_endpoint_correcta_devuelve_correcto_true():
    estudiante_id = uuid.uuid4()
    _, seccion = _crear_lab_con_seccion("FLAG{correcta}")
    progreso = _crear_progreso(seccion, estudiante_id)
    client = _client_autenticado(estudiante_id)

    response = client.post(
        f"/api/v1/progress/{progreso.asignacion_id}/sections/{seccion.id}/flag/",
        {"valor": "FLAG{correcta}"},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["correcto"] is True


@pytest.mark.django_db
def test_flag_endpoint_incorrecta_devuelve_correcto_false():
    estudiante_id = uuid.uuid4()
    _, seccion = _crear_lab_con_seccion("FLAG{correcta}")
    progreso = _crear_progreso(seccion, estudiante_id)
    client = _client_autenticado(estudiante_id)

    response = client.post(
        f"/api/v1/progress/{progreso.asignacion_id}/sections/{seccion.id}/flag/",
        {"valor": "FLAG{incorrecta}"},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["correcto"] is False
    assert response.data["intentos_fallidos"] == 1
    assert "pista" not in response.data


@pytest.mark.django_db
def test_flag_endpoint_rate_limit_bloquea_intento_21():
    estudiante_id = uuid.uuid4()
    _, seccion = _crear_lab_con_seccion("FLAG{correcta}")
    progreso = _crear_progreso(seccion, estudiante_id)
    client = _client_autenticado(estudiante_id)
    url = f"/api/v1/progress/{progreso.asignacion_id}/sections/{seccion.id}/flag/"

    for _ in range(20):
        client.post(url, {"valor": "FLAG{incorrecta}"}, format="json")

    response = client.post(url, {"valor": "FLAG{incorrecta}"}, format="json")

    assert response.status_code == 429


@pytest.mark.django_db
def test_hint_endpoint_sin_fallos_no_muestra_pista():
    estudiante_id = uuid.uuid4()
    _, seccion = _crear_lab_con_seccion()
    progreso = _crear_progreso(seccion, estudiante_id)
    client = _client_autenticado(estudiante_id)

    response = client.get(
        f"/api/v1/progress/{progreso.asignacion_id}/sections/{seccion.id}/hint/"
    )

    assert response.status_code == 200
    assert response.data["pista_disponible"] is False
    assert "pista" not in response.data


@pytest.mark.django_db
def test_history_endpoint_devuelve_lista_vacia_por_defecto():
    estudiante_id = uuid.uuid4()
    _, seccion = _crear_lab_con_seccion()
    progreso = _crear_progreso(seccion, estudiante_id)
    client = _client_autenticado(estudiante_id)

    response = client.get(f"/api/v1/progress/{progreso.asignacion_id}/history/")

    assert response.status_code == 200
    assert response.data == []
