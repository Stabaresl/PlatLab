import uuid
from typing import Protocol

from modules.lab_environments.domain.entities import EntornoActivo


class IEntornoRepository(Protocol):
    """Puerto de persistencia del agregado EntornoActivo (PostgreSQL vía infrastructure/repositories.py)."""

    def add(self, entorno: EntornoActivo) -> EntornoActivo: ...

    def get_by_id(self, entorno_id: uuid.UUID) -> EntornoActivo | None: ...

    def get_activo_por_seccion(
        self, progreso_id: uuid.UUID, seccion_id: uuid.UUID
    ) -> EntornoActivo | None:
        """El entorno `iniciando`/`activo` más reciente para esa (progreso, sección), si existe."""
        ...

    def update(self, entorno: EntornoActivo) -> EntornoActivo: ...

    def contar_activos(self) -> int:
        """RNF rendimiento: cuenta entornos `iniciando`/`activo` en toda la plataforma."""
        ...

    def contar_activos_por_estudiante(self, estudiante_id: uuid.UUID) -> int:
        """Entornos `iniciando`/`activo` de un estudiante (cupo por estudiante)."""
        ...

    def tocar_actividad(self, entorno_id: uuid.UUID) -> bool:
        """Actualiza solo `ultima_actividad` si sigue activo; False si ya no lo está."""
        ...

    def get_todos_activos(self) -> list[EntornoActivo]:
        """Candidatos a evaluar por el reaper de inactividad (Celery Beat)."""
        ...
