"""
Prueba de punta a punta REAL: abre un WebSocket contra `TerminalConsumer`
(mismo consumer que usa el frontend), autenticado con un JWT real, sobre
un `EntornoActivo` respaldado por un contenedor Docker real — y verifica
que un comando tipeado por el "estudiante" llega de verdad al contenedor y
la salida vuelve por el mismo WebSocket. Sin esto, toda la cadena
(middleware de auth, consumer, ExecSession) podría estar rota igual con
los demás tests en verde (todos mockean o prueban una capa a la vez).

Se salta si Docker no está disponible (ver test_docker_provider.py).
"""

import asyncio
import uuid

import docker as docker_sdk
import pytest
from channels.testing import WebsocketCommunicator

from config.asgi import application
from modules.authentication.infrastructure.jwt_service import JWTService
from modules.laboratories.domain.entities import Laboratorio, Seccion
from modules.laboratories.domain.value_objects import (
    EstadoLaboratorio,
    NivelDificultad,
    TipoLaboratorio,
)
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.lab_environments.domain.entities import EntornoActivo
from modules.lab_environments.domain.value_objects import EstadoEntorno
from modules.lab_environments.infrastructure.docker_provider import DockerContenedorProvider
from modules.lab_environments.infrastructure.repositories import EntornoRepository
from modules.progress.domain.entities import Progreso, ProgresoSeccion
from modules.progress.domain.value_objects import EstadoProgresoSeccion
from modules.progress.infrastructure.repositories import ProgresoRepository

_IMAGEN = "platlab-target-sqli:latest"


def _docker_disponible() -> bool:
    try:
        client = docker_sdk.from_env()
        client.ping()
        client.images.get(_IMAGEN)
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _docker_disponible(), reason="Docker no disponible")


def _preparar_entorno_real():
    estudiante_id = uuid.uuid4()
    lab_repo = LaboratorioRepository()
    lab = lab_repo.add(
        Laboratorio(
            nombre=f"Lab WS {uuid.uuid4()}",
            descripcion="desc",
            nivel_dificultad=NivelDificultad.BASICO,
            estado=EstadoLaboratorio.PUBLICADO,
            tipo=TipoLaboratorio.PREDETERMINADO,
        )
    )
    seccion = lab_repo.add_seccion(
        Seccion(
            laboratorio_id=lab.id,
            titulo="Practica",
            contenido_teorico="...",
            orden=1,
            tiene_practica=True,
            imagen_practica=_IMAGEN,
        )
    )
    progreso_repo = ProgresoRepository()
    progreso = progreso_repo.add(Progreso(asignacion_id=uuid.uuid4(), estudiante_id=estudiante_id))
    progreso_repo.add_secciones(
        [
            ProgresoSeccion(
                progreso_id=progreso.id, seccion_id=seccion.id, estado=EstadoProgresoSeccion.EN_PROGRESO
            )
        ]
    )

    container_id = DockerContenedorProvider().iniciar(_IMAGEN)
    entorno_repo = EntornoRepository()
    entorno = entorno_repo.add(
        EntornoActivo(
            seccion_id=seccion.id,
            progreso_id=progreso.id,
            estudiante_id=estudiante_id,
            container_id=container_id,
            estado=EstadoEntorno.ACTIVO,
        )
    )
    tokens = JWTService().generate_token_pair(user_id=estudiante_id, rol="estudiante")
    return entorno, tokens.access, container_id


@pytest.mark.django_db(transaction=True)
def test_terminal_consumer_ejecuta_comando_real_y_devuelve_la_flag():
    entorno, access_token, container_id = _preparar_entorno_real()

    async def _cuerpo():
        communicator = WebsocketCommunicator(
            application, f"/ws/lab-environments/{entorno.id}/terminal/?token={access_token}"
        )
        connected, _ = await communicator.connect()
        assert connected is True

        payload = (
            b"curl -s http://127.0.0.1:5000/login.php "
            b"--data-urlencode \"username=' OR '1'='1' -- \" "
            b"--data-urlencode 'password=x'\n"
        )
        await communicator.send_to(bytes_data=payload)

        salida = b""
        for _ in range(30):
            try:
                frame = await asyncio.wait_for(communicator.receive_from(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            salida += frame if isinstance(frame, bytes) else frame.encode()
            if b"FLAG{" in salida:
                break

        await communicator.disconnect()
        return salida

    salida = asyncio.run(_cuerpo())
    assert b"FLAG{sql_injection_1s_ez}" in salida

    DockerContenedorProvider().detener(container_id)


@pytest.mark.django_db(transaction=True)
def test_terminal_consumer_rechaza_sin_token():
    entorno, _, container_id = _preparar_entorno_real()

    async def _cuerpo():
        communicator = WebsocketCommunicator(
            application, f"/ws/lab-environments/{entorno.id}/terminal/"
        )
        connected, _ = await communicator.connect()
        await communicator.disconnect()
        return connected

    connected = asyncio.run(_cuerpo())
    assert connected is False

    DockerContenedorProvider().detener(container_id)


@pytest.mark.django_db(transaction=True)
def test_terminal_consumer_rechaza_entorno_de_otro_estudiante():
    entorno, _access_token, container_id = _preparar_entorno_real()
    otro_token = JWTService().generate_token_pair(user_id=uuid.uuid4(), rol="estudiante").access

    async def _cuerpo():
        communicator = WebsocketCommunicator(
            application, f"/ws/lab-environments/{entorno.id}/terminal/?token={otro_token}"
        )
        connected, _ = await communicator.connect()
        await communicator.disconnect()
        return connected

    connected = asyncio.run(_cuerpo())
    assert connected is False

    DockerContenedorProvider().detener(container_id)
