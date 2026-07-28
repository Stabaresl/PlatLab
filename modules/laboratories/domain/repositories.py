import uuid
from typing import Protocol

from modules.laboratories.domain.entities import Laboratorio, Seccion


class ILaboratorioRepository(Protocol):
    """
    Puerto de persistencia del agregado Laboratorio. La implementación
    real vive en `infrastructure/repositories.py` (PostgreSQL vía
    `mappers.py`) — Application nunca importa el ORM directamente.
    """

    def find_catalogo(
        self,
        instructor_id: uuid.UUID | None = None,
        nivel_dificultad: str | None = None,
        tema: str | None = None,
    ) -> list[Laboratorio]:
        """
        Visibilidad ya resuelta a nivel de query (índices `(estado,
        nivel_dificultad)` / `(tipo, instructor_id)`, base-de-datos.md
        §7): predeterminado+publicado siempre; + personalizado propio si
        se pasa `instructor_id` (HI-01). `nivel_dificultad`/`tema` filtran
        además sobre ese conjunto ya visible.
        """
        ...

    def get_by_id(self, laboratorio_id: uuid.UUID) -> Laboratorio | None: ...

    def get_secciones(self, laboratorio_id: uuid.UUID) -> list[Seccion]: ...
