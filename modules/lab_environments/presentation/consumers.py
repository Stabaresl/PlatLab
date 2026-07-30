"""
Puente WebSocket <-> `docker exec -it bash` de un `EntornoActivo`. Un
consumer por conexión: al conectar abre una sesión exec nueva sobre el
MISMO contenedor (reconectar no reinicia el contenedor, solo abre otra
shell dentro de él); al desconectar cierra la sesión exec pero deja el
contenedor corriendo (lo apaga el estudiante con "Detener" o el reaper por
inactividad, `application/use_cases/reap_entornos_inactivos.py`).

Verificado en runtime contra un contenedor real (no solo supuesto): ver
`ExecSession` en `infrastructure/docker_provider.py` para el porqué del
split lectura/escritura.
"""

import asyncio
import uuid

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from modules.lab_environments.domain.value_objects import EstadoEntorno
from modules.lab_environments.infrastructure.docker_provider import DockerContenedorProvider
from modules.lab_environments.infrastructure.repositories import EntornoRepository

_READ_CHUNK = 4096
_TOUCH_ACTIVITY_INTERVAL_SECONDS = 20


class TerminalConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.entorno_id = self.scope["url_route"]["kwargs"]["entorno_id"]
        user = self.scope.get("user")
        if user is None:
            await self.close(code=4401)
            return

        self._repo = EntornoRepository()
        self._provider = DockerContenedorProvider()

        try:
            entorno_uuid = uuid.UUID(self.entorno_id)
        except ValueError:
            await self.close(code=4404)
            return

        entorno = await database_sync_to_async(self._repo.get_by_id)(entorno_uuid)
        if entorno is None or not entorno.es_propio_de(user.id):
            await self.close(code=4404)
            return
        if entorno.estado != EstadoEntorno.ACTIVO:
            await self.close(code=4409)
            return

        self._entorno = entorno
        loop = asyncio.get_event_loop()
        try:
            self._sock = await loop.run_in_executor(
                None, self._provider.exec_interactivo, entorno.container_id
            )
        except Exception:
            await self.close(code=4500)
            return

        await self.accept()
        self._last_touch = 0.0
        self._reader_task = asyncio.ensure_future(self._leer_salida())

    async def _leer_salida(self):
        loop = asyncio.get_event_loop()
        try:
            while True:
                data = await loop.run_in_executor(None, self._sock.read, _READ_CHUNK)
                if not data:
                    break
                await self.send(bytes_data=data)
        except Exception:
            pass
        finally:
            await self.close()

    async def receive(self, text_data=None, bytes_data=None):
        payload = bytes_data if bytes_data is not None else (text_data or "").encode()
        if not payload:
            return

        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, self._sock.write, payload)
        except Exception:
            await self.close()
            return

        await self._tocar_actividad_throttled()

    async def _tocar_actividad_throttled(self):
        ahora = asyncio.get_event_loop().time()
        if ahora - self._last_touch < _TOUCH_ACTIVITY_INTERVAL_SECONDS:
            return
        self._last_touch = ahora
        await database_sync_to_async(self._repo.update)(self._entorno)

    async def disconnect(self, close_code):
        reader = getattr(self, "_reader_task", None)
        if reader is not None:
            reader.cancel()
        sock = getattr(self, "_sock", None)
        if sock is not None:
            try:
                sock.close()
            except Exception:
                pass
