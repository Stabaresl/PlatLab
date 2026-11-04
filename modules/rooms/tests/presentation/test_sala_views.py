import uuid

import pytest
from rest_framework.test import APIClient

from modules.authentication.infrastructure.jwt_service import JWTService
from modules.laboratories.domain.entities import Laboratorio, Seccion
from modules.laboratories.domain.value_objects import EstadoLaboratorio, NivelDificultad, TipoLaboratorio
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.shared.infrastructure.redis_client import RedisClient
from modules.users.domain.entities import User
from modules.users.domain.value_objects import Email, Rol
from modules.users.infrastructure.repositories import UserRepository


def _usuario(rol: Rol) -> User:
    return UserRepository().add(User(email=Email(f"{uuid.uuid4().hex[:10]}@uni.edu"), nombre_completo="Vista", rol=rol))


def _cliente(usuario: User) -> APIClient:
    tokens = JWTService().generate_token_pair(user_id=usuario.id, rol=usuario.rol.value)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens.access}")
    return client


def _lab() -> Laboratorio:
    repo = LaboratorioRepository()
    lab = repo.add(
        Laboratorio(
            nombre=f"Lab {uuid.uuid4().hex[:6]}",
            descripcion="d",
            nivel_dificultad=NivelDificultad.BASICO,
            estado=EstadoLaboratorio.PUBLICADO,
            tipo=TipoLaboratorio.PREDETERMINADO,
        )
    )
    repo.add_seccion(Seccion(laboratorio_id=lab.id, titulo="S1", contenido_teorico="<p>x</p>", orden=1))
    return lab


@pytest.fixture(autouse=True)
def _limpiar_rate_limit():
    redis = RedisClient().raw
    for clave in redis.scan_iter("sala_codigo_rate:*"):
        redis.delete(clave)


@pytest.mark.django_db
def test_flujo_completo_crear_previsualizar_unirse_y_ver_tablero():
    instructor, estudiante = _usuario(Rol.INSTRUCTOR), _usuario(Rol.ESTUDIANTE)
    lab = _lab()
    prof = _cliente(instructor)

    disponibles = prof.get("/api/v1/salas/laboratorios-disponibles/")
    assert disponibles.status_code == 200
    assert str(lab.id) in {item["id"] for item in disponibles.data}

    creada = prof.post(
        "/api/v1/salas/", {"nombre": "Clase lunes", "laboratorio_id": str(lab.id), "capacidad": 25}, format="json"
    )
    assert creada.status_code == 201
    codigo, sala_id = creada.data["codigo"], creada.data["id"]

    alumno = _cliente(estudiante)
    preview = alumno.get(f"/api/v1/salas/codigo/{codigo}/")
    assert preview.status_code == 200 and preview.data["acepta_ingresos"] is True

    unido = alumno.post("/api/v1/salas/unirse/", {"codigo": codigo}, format="json")
    assert unido.status_code == 201
    assert alumno.post("/api/v1/salas/unirse/", {"codigo": codigo}, format="json").status_code == 200

    tablero = prof.get(f"/api/v1/salas/{sala_id}/")
    assert tablero.status_code == 200
    assert tablero.data["es_anfitrion"] is True
    assert len(tablero.data["tablero"]) == 1
    assert tablero.data["tablero"][0]["secciones_total"] == 1

    mias = alumno.get("/api/v1/salas/")
    assert mias.data[0]["mi_asignacion_id"] == unido.data["asignacion_id"]


@pytest.mark.django_db
def test_estudiante_no_crea_y_extrano_no_ve_el_tablero():
    lab = _lab()
    alumno = _cliente(_usuario(Rol.ESTUDIANTE))
    assert (
        alumno.post("/api/v1/salas/", {"nombre": "x", "laboratorio_id": str(lab.id)}, format="json").status_code == 403
    )

    creada = _cliente(_usuario(Rol.INSTRUCTOR)).post(
        "/api/v1/salas/", {"nombre": "Privada", "laboratorio_id": str(lab.id)}, format="json"
    )
    assert alumno.get(f"/api/v1/salas/{creada.data['id']}/").status_code == 404
    assert alumno.get("/api/v1/salas/no-es-uuid/").status_code == 404


@pytest.mark.django_db
def test_cambiar_estado_solo_anfitrion_y_valores_validos():
    lab = _lab()
    anfitrion = _cliente(_usuario(Rol.INSTRUCTOR))
    sala = anfitrion.post("/api/v1/salas/", {"nombre": "S", "laboratorio_id": str(lab.id)}, format="json").data

    otro = _cliente(_usuario(Rol.INSTRUCTOR))
    assert otro.post(f"/api/v1/salas/{sala['id']}/estado/", {"estado": "cerrada"}, format="json").status_code == 404
    assert (
        anfitrion.post(f"/api/v1/salas/{sala['id']}/estado/", {"estado": "pausada"}, format="json").status_code == 400
    )
    r = anfitrion.post(f"/api/v1/salas/{sala['id']}/estado/", {"estado": "cerrada"}, format="json")
    assert r.status_code == 200 and r.data["estado"] == "cerrada"


@pytest.mark.django_db
def test_codigos_limitados_por_minuto():
    alumno = _cliente(_usuario(Rol.ESTUDIANTE))
    respuestas = [alumno.get("/api/v1/salas/codigo/AAAAAA/").status_code for _ in range(16)]
    assert respuestas[:15] == [404] * 15
    assert respuestas[15] == 429
