import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ObtenerContenidoSeccionDTO:
    """
    api.md §7 `GET /progress/{assignment_id}/sections/{section_id}/` —
    `asignacion_id` es el identificador público de la URL; se resuelve a
    `Progreso` internamente (1:1, `get_by_asignacion`).
    """

    asignacion_id: uuid.UUID
    seccion_id: uuid.UUID
    estudiante_id: uuid.UUID


@dataclass(frozen=True)
class ContenidoSeccionDTO:
    seccion_id: uuid.UUID
    titulo: str
    contenido_teorico: str
    tiene_practica: bool
    estado: str


@dataclass(frozen=True)
class ValidarFlagDTO:
    """api.md §7 `POST .../flag/` (UC-02) — DTO de entrada `{ "valor": "..." }`."""

    asignacion_id: uuid.UUID
    seccion_id: uuid.UUID
    valor: str
    estudiante_id: uuid.UUID


@dataclass(frozen=True)
class ValidarFlagResultDTO:
    """api.md §7 — forma de la respuesta `POST .../flag/`."""

    correcto: bool
    intentos_fallidos: int
    seccion_desbloqueada: uuid.UUID | None = None
    pista_disponible: bool = False
    pista: str | None = None
    paso_a_paso_disponible: bool = False
    paso_a_paso: str | None = None


@dataclass(frozen=True)
class ObtenerPistaDTO:
    asignacion_id: uuid.UUID
    seccion_id: uuid.UUID
    estudiante_id: uuid.UUID


@dataclass(frozen=True)
class PistaDTO:
    """api.md §7 `GET .../hint/` — solo devuelve ayuda ya desbloqueada (HE-06)."""

    intentos_fallidos: int
    pista_disponible: bool
    pista: str | None
    paso_a_paso_disponible: bool
    paso_a_paso: str | None


@dataclass(frozen=True)
class ObtenerHistorialDTO:
    asignacion_id: uuid.UUID
    estudiante_id: uuid.UUID


@dataclass(frozen=True)
class HistorialItemDTO:
    numero_intento: int
    fecha_completado: datetime
    puntaje: float | None


@dataclass(frozen=True)
class EnviarExamenDTO:
    """
    HE-09/HI-08, api.md §7 `POST /progress/{assignment_id}/exam/` (UC-03).
    `respuestas` es `{pregunta_id: respuesta}` — validado contra las
    `Pregunta` reales del examen antes de calificar (seguridad.md §4).
    """

    asignacion_id: uuid.UUID
    estudiante_id: uuid.UUID
    respuestas: dict[str, str]


@dataclass(frozen=True)
class EnviarExamenResultDTO:
    puntaje: float
    correctas: int
    total: int
    numero_intento: int


@dataclass(frozen=True)
class ObtenerExamenDTO:
    """`GET /progress/{assignment_id}/exam/` — preguntas para responder (nunca la respuesta)."""

    asignacion_id: uuid.UUID
    estudiante_id: uuid.UUID


@dataclass(frozen=True)
class PreguntaExamenItemDTO:
    id: uuid.UUID
    enunciado: str
    tipo: str
    opciones: list[str] | None


@dataclass(frozen=True)
class ExamenParaResolverDTO:
    examen_id: uuid.UUID
    preguntas: list[PreguntaExamenItemDTO]


@dataclass(frozen=True)
class ObtenerProgresoDTO:
    """`GET /progress/{assignment_id}/` — resumen para poder resolver el laboratorio."""

    asignacion_id: uuid.UUID
    estudiante_id: uuid.UUID


@dataclass(frozen=True)
class SeccionProgresoItemDTO:
    id: uuid.UUID
    orden: int
    titulo: str
    tiene_practica: bool
    estado: str


@dataclass(frozen=True)
class ProgresoOverviewDTO:
    asignacion_id: uuid.UUID
    laboratorio_id: uuid.UUID
    laboratorio_nombre: str
    secciones: list[SeccionProgresoItemDTO]
    secciones_completas: bool
    examen_disponible: bool
    intentos_examen: int
