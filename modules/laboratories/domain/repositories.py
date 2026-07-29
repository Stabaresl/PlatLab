import uuid
from typing import Protocol

from modules.laboratories.domain.entities import Examen, Flag, Laboratorio, Pregunta, Seccion


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
        nombre: str | None = None,
    ) -> list[Laboratorio]:
        """
        Visibilidad ya resuelta a nivel de query (índices `(estado,
        nivel_dificultad)` / `(tipo, instructor_id)`, base-de-datos.md
        §7): predeterminado+publicado siempre; + personalizado propio si
        se pasa `instructor_id` (HI-01). `nivel_dificultad`/`tema`/
        `nombre` (HI-05, coincidencia parcial) filtran además sobre ese
        conjunto ya visible.
        """
        ...

    def get_by_id(self, laboratorio_id: uuid.UUID) -> Laboratorio | None: ...

    def update(self, laboratorio: Laboratorio) -> Laboratorio:
        """Persiste nombre/descripción/dificultad/estado/temas — no crea ni borra filas."""
        ...

    def get_secciones(self, laboratorio_id: uuid.UUID) -> list[Seccion]: ...

    def update_seccion(self, seccion: Seccion) -> Seccion: ...

    def get_seccion_by_id(self, seccion_id: uuid.UUID) -> Seccion | None:
        """
        Busca una `Seccion` por su propio id, sin conocer su
        `laboratorio_id` — necesario para módulos que solo guardan el
        "id suelto" de la sección (ej. Progress, `ProgresoSeccion`).
        """
        ...

    def get_flag_by_seccion(self, seccion_id: uuid.UUID) -> Flag | None: ...

    def save_flag(self, flag: Flag) -> Flag:
        """
        Upsert por `seccion_id` (relación 1:1, UNIQUE en base-de-datos.md):
        crea la flag si la sección no tenía una, o actualiza hash/ayuda si
        ya existía (HE-05, api.md "Definir/actualizar flag").
        """
        ...

    def get_examen_by_laboratorio(self, laboratorio_id: uuid.UUID) -> Examen | None:
        """HE-09/HI-08: relación 1:1 con Laboratorio, opcional en `personalizado` (UC-03 A2)."""
        ...

    def add_examen(self, examen: Examen) -> Examen: ...

    def get_examen_by_id(self, examen_id: uuid.UUID) -> Examen | None: ...

    def add_pregunta(self, pregunta: Pregunta) -> Pregunta: ...

    def get_preguntas(self, examen_id: uuid.UUID) -> list[Pregunta]: ...

    def find_publicados(self) -> list[Laboratorio]:
        """
        HA-03/RF-28: todos los laboratorios publicados de la plataforma
        (predeterminados + personalizados de cualquier instructor), para
        el dashboard admin — a diferencia de `find_catalogo()`, no
        filtra por visibilidad de un actor puntual.
        """
        ...
