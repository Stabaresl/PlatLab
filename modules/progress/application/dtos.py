import uuid
from dataclasses import dataclass, field
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
    # Objetivos de aprendizaje y duración estimada — encabezado estilo AWS
    # Academy antes del contenido.
    objetivos: list[str] = field(default_factory=list)
    duracion_estimada_minutos: int = 15
    # Guía siempre disponible una vez desbloqueada la sección (no gatillada
    # por intentos fallidos, a diferencia de la ayuda progresiva de la Flag)
    # — pasos numerados que pueden abrirse en una pestaña aparte y quedan
    # disponibles durante la práctica (ver ResolverLaboratorioPage en el
    # frontend). [{"orden", "titulo", "instrucciones", "comando_sugerido"}, ...]
    pasos_guia: list[dict] = field(default_factory=list)
    # Consola simulada (estilo HackerRank/TryHackMe, sin ejecución real) —
    # {"prompt": str, "banner": str, "comandos": [{"comando": str, "salida": str}]}
    entorno_practica: dict | None = None
    # True si además hay un entorno REAL (contenedor Docker por estudiante,
    # módulo lab_environments) configurado para esta sección — nunca se
    # expone la imagen Docker en sí al estudiante, solo la disponibilidad.
    entorno_real_disponible: bool = False


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
class CompletarSeccionTeoricaDTO:
    """
    UC-02 bis, `POST /progress/{assignment_id}/sections/{section_id}/complete/`
    — completa una sección sin práctica (`tiene_practica=False`), que no
    tiene flag que validar y por lo tanto no puede avanzar vía `.../flag/`.
    """

    asignacion_id: uuid.UUID
    seccion_id: uuid.UUID
    estudiante_id: uuid.UUID


@dataclass(frozen=True)
class CompletarSeccionTeoricaResultDTO:
    seccion_desbloqueada: uuid.UUID | None = None


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
    vencido: bool = False
    fecha_vencimiento: datetime | None = None
    resumen_cierre: str | None = None
