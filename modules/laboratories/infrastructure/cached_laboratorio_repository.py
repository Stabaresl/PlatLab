import hashlib
import json
import uuid
from datetime import datetime

from modules.laboratories.domain.entities import Laboratorio, Seccion
from modules.laboratories.domain.value_objects import (
    EstadoLaboratorio,
    NivelDificultad,
    TipoLaboratorio,
)
from modules.shared.infrastructure.redis_client import RedisClient

_CATALOGO_TTL_SECONDS = 60


class CachedLaboratorioRepository:
    """
    Decorator (patrón Decorator, RNF-02.1/02.2) sobre otro
    `ILaboratorioRepository`: cachea `find_catalogo` en Redis por 60s bajo
    una clave derivada de los filtros. El catálogo es de lectura intensiva
    y cambia con poca frecuencia (solo al publicar/editar un laboratorio,
    algo que Sprint 2 todavía no construye). No cachea
    `get_by_id`/`get_secciones` (detalle/TOC): tráfico bastante menor que
    el listado y se prefiere no invalidar cache en más de un lugar todavía.
    """

    def __init__(
        self,
        repositorio,
        redis_client: RedisClient | None = None,
        ttl_seconds: int = _CATALOGO_TTL_SECONDS,
    ):
        self._repo = repositorio
        self._redis = redis_client or RedisClient()
        self._ttl = ttl_seconds

    def find_catalogo(
        self,
        instructor_id: uuid.UUID | None = None,
        nivel_dificultad: str | None = None,
        tema: str | None = None,
    ) -> list[Laboratorio]:
        clave = self._clave_catalogo(instructor_id, nivel_dificultad, tema)
        cacheado = self._redis.get(clave)
        if cacheado is not None:
            return [self._deserializar(item) for item in json.loads(cacheado)]

        resultado = self._repo.find_catalogo(
            instructor_id=instructor_id, nivel_dificultad=nivel_dificultad, tema=tema
        )
        payload = json.dumps([self._serializar(lab) for lab in resultado])
        self._redis.set(clave, payload, ttl_seconds=self._ttl)
        return resultado

    def get_by_id(self, laboratorio_id: uuid.UUID) -> Laboratorio | None:
        return self._repo.get_by_id(laboratorio_id)

    def get_secciones(self, laboratorio_id: uuid.UUID) -> list[Seccion]:
        return self._repo.get_secciones(laboratorio_id)

    def _clave_catalogo(
        self, instructor_id: uuid.UUID | None, nivel_dificultad: str | None, tema: str | None
    ) -> str:
        crudo = f"{instructor_id}:{nivel_dificultad}:{tema}"
        return f"catalogo_labs:{hashlib.sha256(crudo.encode()).hexdigest()}"

    def _serializar(self, laboratorio: Laboratorio) -> dict:
        return {
            "id": str(laboratorio.id),
            "nombre": laboratorio.nombre,
            "descripcion": laboratorio.descripcion,
            "nivel_dificultad": laboratorio.nivel_dificultad.value,
            "estado": laboratorio.estado.value,
            "tipo": laboratorio.tipo.value,
            "temas": laboratorio.temas,
            "origen_id": str(laboratorio.origen_id) if laboratorio.origen_id else None,
            "instructor_id": (
                str(laboratorio.instructor_id) if laboratorio.instructor_id else None
            ),
            "created_at": laboratorio.created_at.isoformat(),
            "updated_at": laboratorio.updated_at.isoformat(),
        }

    def _deserializar(self, data: dict) -> Laboratorio:
        return Laboratorio(
            id=uuid.UUID(data["id"]),
            nombre=data["nombre"],
            descripcion=data["descripcion"],
            nivel_dificultad=NivelDificultad(data["nivel_dificultad"]),
            estado=EstadoLaboratorio(data["estado"]),
            tipo=TipoLaboratorio(data["tipo"]),
            temas=data["temas"],
            origen_id=uuid.UUID(data["origen_id"]) if data["origen_id"] else None,
            instructor_id=(uuid.UUID(data["instructor_id"]) if data["instructor_id"] else None),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )
