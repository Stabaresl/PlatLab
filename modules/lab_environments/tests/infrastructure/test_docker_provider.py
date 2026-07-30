"""
Tests de integración CONTRA DOCKER REAL (no mocks) — requieren que el
proceso de test tenga acceso a `/var/run/docker.sock` (cierto para `web`/
`worker` en docker-compose.yml) y la imagen `platlab-target-sqli:latest`
ya construida (`docker build` en docker/targets/sqli-login/). Si Docker no
está disponible, se saltan en vez de fallar — no todos los entornos donde
corre la suite completa tienen acceso a un daemon Docker.
"""

import docker as docker_sdk
import pytest

from modules.lab_environments.infrastructure.docker_provider import DockerContenedorProvider

_IMAGEN = "platlab-target-sqli:latest"


def _docker_disponible() -> bool:
    try:
        client = docker_sdk.from_env()
        client.ping()
        client.images.get(_IMAGEN)
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _docker_disponible(),
    reason="Docker no disponible o falta la imagen platlab-target-sqli:latest",
)


def test_iniciar_detener_contenedor_real():
    provider = DockerContenedorProvider()
    container_id = provider.iniciar(_IMAGEN)
    try:
        assert provider.esta_vivo(container_id) is True
    finally:
        provider.detener(container_id)

    assert provider.esta_vivo(container_id) is False


def test_exec_interactivo_ejecuta_comandos_reales_y_devuelve_la_flag():
    provider = DockerContenedorProvider()
    container_id = provider.iniciar(_IMAGEN)
    try:
        sesion = provider.exec_interactivo(container_id)
        try:
            sesion.raw_socket.settimeout(5)
            sesion.write(b"echo ready_marker\n")
            salida = b""
            for _ in range(20):
                salida += sesion.read(4096)
                if b"ready_marker" in salida:
                    break
            assert b"ready_marker" in salida

            payload = (
                b"curl -s http://127.0.0.1:5000/login.php "
                b"--data-urlencode \"username=' OR '1'='1' -- \" "
                b"--data-urlencode 'password=x'\n"
            )
            sesion.write(payload)
            salida = b""
            for _ in range(20):
                salida += sesion.read(4096)
                if b"FLAG{" in salida:
                    break
            assert b"FLAG{sql_injection_1s_ez}" in salida
        finally:
            sesion.close()
    finally:
        provider.detener(container_id)


def test_contenedor_no_tiene_acceso_a_red_externa():
    """RNF de seguridad: `network_disabled` deja al contenedor sin salida a Internet."""
    provider = DockerContenedorProvider()
    container_id = provider.iniciar(_IMAGEN)
    try:
        sesion = provider.exec_interactivo(container_id)
        try:
            sesion.raw_socket.settimeout(8)
            sesion.write(b"curl -s -m 3 http://example.com > /tmp/out 2>&1; echo EXIT:$?\n")
            salida = b""
            for _ in range(30):
                salida += sesion.read(4096)
                if b"EXIT:" in salida:
                    break
            # curl debe fallar (sin red) — nunca "EXIT:0"
            assert b"EXIT:0" not in salida
        finally:
            sesion.close()
    finally:
        provider.detener(container_id)
