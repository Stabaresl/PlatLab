"""
Implementación real de `IContenedorProvider` sobre el motor de Docker del
host (Docker-outside-of-Docker: el contenedor `web`/`worker` habla con el
Docker del host, no directo por el socket sino a través del servicio
`docker-proxy` — ver docker-compose.yml — que solo expone las llamadas de
API que este módulo necesita). Cada entorno es un contenedor descartable,
aislado de red (`network_disabled`) y con límites de CPU/memoria/PIDs — un
estudiante no puede degradar a los demás ni salir a Internet desde el
contenedor.

`docker.from_env()` recoge `DOCKER_HOST=tcp://docker-proxy:2375` del
entorno automáticamente — no hay nada Docker-específico que resolver acá.

Nota de seguridad: el proxy reduce la superficie de API alcanzable, pero no
valida el *contenido* de las llamadas que sí deja pasar (un `POST
/containers/create` con `privileged: true` seguiría siendo posible con
acceso directo al proxy). Aceptable para desarrollo/pruebas en una máquina
propia; antes de exponer esto a estudiantes reales por Internet hace falta
un ejecutor separado del backend (host/VM dedicado) y sandboxing más fuerte
(gVisor/Kata) — no resuelto en esta iteración.
"""

import time

import docker
from docker.errors import DockerException, NotFound

_MEM_LIMIT = "256m"
_NANO_CPUS = 500_000_000  # 0.5 CPU
_PIDS_LIMIT = 128
_READY_TIMEOUT_SECONDS = 10
_READY_POLL_INTERVAL_SECONDS = 0.25
_READY_FALLBACK_SLEEP_SECONDS = 0.5


class DockerContenedorProvider:
    """Implementación de `IContenedorProvider` (ver domain/ports.py)."""

    def __init__(self, client: "docker.DockerClient | None" = None):
        self._client = client or docker.from_env()

    def iniciar(self, imagen: str) -> str:
        try:
            container = self._client.containers.run(
                imagen,
                detach=True,
                mem_limit=_MEM_LIMIT,
                nano_cpus=_NANO_CPUS,
                pids_limit=_PIDS_LIMIT,
                network_disabled=True,
                security_opt=["no-new-privileges"],
                cap_drop=["ALL"],
                tmpfs={"/tmp": "size=32m"},
                labels={"platlab.lab-environment": "true"},
            )
        except DockerException as exc:
            raise RuntimeError(f"No se pudo iniciar el contenedor ({imagen}): {exc}") from exc

        self._esperar_listo(container)
        return container.id

    def _esperar_listo(self, container) -> None:
        """
        Carrera real observada en pruebas: si se abre una sesión `exec`
        apenas arranca el contenedor, el proceso objetivo (ej. el server
        HTTP de `app.py`) puede no haber terminado de bindear su puerto
        todavía — el comando del estudiante se pierde en silencio. Si la
        imagen define `HEALTHCHECK` (recomendado para imágenes propias),
        se espera a que reporte `healthy`; si no define uno, se usa un
        margen fijo corto como resguardo.
        """
        deadline = time.monotonic() + _READY_TIMEOUT_SECONDS
        vio_healthcheck = False
        while time.monotonic() < deadline:
            container.reload()
            health = container.attrs.get("State", {}).get("Health")
            if health is None:
                break
            vio_healthcheck = True
            if health.get("Status") == "healthy":
                return
            time.sleep(_READY_POLL_INTERVAL_SECONDS)

        if not vio_healthcheck:
            time.sleep(_READY_FALLBACK_SLEEP_SECONDS)

    def detener(self, container_id: str) -> None:
        try:
            container = self._client.containers.get(container_id)
        except NotFound:
            return
        try:
            container.remove(force=True)
        except NotFound:
            pass

    def esta_vivo(self, container_id: str) -> bool:
        try:
            container = self._client.containers.get(container_id)
        except NotFound:
            return False
        return container.status == "running"

    def exec_interactivo(self, container_id: str):
        """
        Abre una sesión `docker exec -it bash` sobre el contenedor y
        devuelve el socket duplex crudo (usado por
        `presentation/consumers.py` para puentear stdin/stdout con el
        WebSocket del frontend). No pertenece a `IContenedorProvider`
        (ese puerto es agnóstico de "cómo se ve" una sesión interactiva) —
        el consumer depende de esta clase concreta, no del puerto de
        dominio, porque streaming de terminal es un detalle de
        infraestructura de punta a punta.

        `docker-py` devuelve un `socket.SocketIO` (wrapper de solo
        lectura) para `exec_start(socket=True)` sobre una conexión unix
        socket — verificado en runtime, no supuesto: para escribir hay
        que usar el socket crudo subyacente (`.raw_socket`), la propia
        `SocketIO` solo sirve para leer. Devolvemos ambos ya resueltos
        para que el consumer no tenga que conocer este detalle.
        """
        container = self._client.containers.get(container_id)
        exec_id = self._client.api.exec_create(
            container.id,
            "bash",
            stdin=True,
            tty=True,
            stdout=True,
            stderr=True,
        )["Id"]
        sock = self._client.api.exec_start(exec_id, tty=True, socket=True)
        raw_socket = getattr(sock, "_sock", sock)
        return ExecSession(read_stream=sock, raw_socket=raw_socket)


class ExecSession:
    """
    Envoltorio delgado sobre la sesión exec devuelta por docker-py: separa
    explícitamente el lado de lectura (`read_stream.read(n)`) del lado de
    escritura (`raw_socket.sendall(data)`) — ver nota en `exec_interactivo`.
    """

    def __init__(self, read_stream, raw_socket):
        self.read_stream = read_stream
        self.raw_socket = raw_socket

    def read(self, n: int) -> bytes:
        return self.read_stream.read(n) or b""

    def write(self, data: bytes) -> None:
        self.raw_socket.sendall(data)

    def close(self) -> None:
        try:
            self.read_stream.close()
        except Exception:
            pass
