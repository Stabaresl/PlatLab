import uuid
from dataclasses import dataclass, field
from datetime import datetime

from modules.laboratories.domain.value_objects import EntornoPractica, PasoGuia


@dataclass(frozen=True)
class ListarLaboratoriosFiltroDTO:
    """
    `instructor_id`/`estudiante_id` no son "filtros" que elija el cliente:
    los resuelve la vista a partir de `request.user` (HI-01/HE-02) — nunca
    llegan como query param arbitrario, para que un visitante no pueda
    hacerse pasar por instructor cambiando la URL.
    """

    dificultad: str | None = None
    tema: str | None = None
    nombre: str | None = None
    instructor_id: uuid.UUID | None = None
    estudiante_id: uuid.UUID | None = None


@dataclass(frozen=True)
class LaboratorioListItemDTO:
    id: uuid.UUID
    nombre: str
    descripcion: str
    nivel_dificultad: str
    estado: str
    temas: list[str] = field(default_factory=list)
    inscrito: bool | None = None


@dataclass(frozen=True)
class LaboratorioDetalleDTO:
    id: uuid.UUID
    nombre: str
    descripcion: str
    nivel_dificultad: str
    estado: str
    temas: list[str]
    total_secciones: int
    motivo_rechazo: str | None = None


@dataclass(frozen=True)
class SeccionTOCItemDTO:
    id: uuid.UUID
    orden: int
    titulo: str
    tiene_practica: bool
    duracion_estimada_minutos: int


@dataclass(frozen=True)
class TOCDTO:
    laboratorio_id: uuid.UUID
    secciones: list[SeccionTOCItemDTO]


@dataclass(frozen=True)
class DefinirFlagDTO:
    """
    api.md §5 `PUT /laboratories/{id}/sections/{section_id}/flag/` —
    write-only: `valor` nunca se persiste en claro ni se retorna.
    `actor_id`/`actor_rol` los resuelve la vista desde `request.user`,
    igual que `instructor_id` en el catálogo (nunca un query param).
    """

    laboratorio_id: uuid.UUID
    seccion_id: uuid.UUID
    valor: str
    actor_id: uuid.UUID
    actor_rol: str
    pista: str | None = None
    paso_a_paso: str | None = None


@dataclass(frozen=True)
class DefinirFlagResultDTO:
    id: uuid.UUID
    seccion_id: uuid.UUID


@dataclass(frozen=True)
class CrearLaboratorioDTO:
    """
    api.md §5 `POST /laboratories/` (UC-04): `tipo` no lo elige el
    cliente, se infiere de `actor_rol` (Instructor→personalizado,
    Admin→predeterminado), igual que `instructor_id`/`estudiante_id` en
    el catálogo.
    """

    nombre: str
    descripcion: str
    nivel_dificultad: str
    actor_id: uuid.UUID
    actor_rol: str
    temas: list[str] = field(default_factory=list)
    resumen_cierre: str = ""


@dataclass(frozen=True)
class EditarLaboratorioDTO:
    """
    api.md §5 `PATCH /laboratories/{id}/`. Solo metadatos editables
    (nombre/descripción/dificultad/temas/resumen_cierre) — `tipo`/`estado`
    cambian solo vía `PublicarLaboratorioUseCase`/`DuplicarLaboratorioUseCase`.
    """

    laboratorio_id: uuid.UUID
    actor_id: uuid.UUID
    actor_rol: str
    nombre: str | None = None
    descripcion: str | None = None
    nivel_dificultad: str | None = None
    temas: list[str] | None = None
    resumen_cierre: str | None = None


@dataclass(frozen=True)
class LaboratorioResultDTO:
    id: uuid.UUID
    nombre: str
    estado: str
    tipo: str
    visible_en_catalogo: bool = False


@dataclass(frozen=True)
class CrearSeccionDTO:
    """api.md §5 `POST /laboratories/{id}/sections/` (UC-04, paso 2)."""

    laboratorio_id: uuid.UUID
    titulo: str
    contenido_teorico: str
    orden: int
    actor_id: uuid.UUID
    actor_rol: str
    tiene_practica: bool = False
    objetivos: list[str] = field(default_factory=list)
    duracion_estimada_minutos: int = 15
    pasos_guia: list[PasoGuia] = field(default_factory=list)
    entorno_practica: EntornoPractica | None = None
    imagen_practica: str | None = None


@dataclass(frozen=True)
class EditarSeccionDTO:
    """api.md §5 `PATCH /laboratories/{id}/sections/{section_id}/`."""

    laboratorio_id: uuid.UUID
    seccion_id: uuid.UUID
    actor_id: uuid.UUID
    actor_rol: str
    titulo: str | None = None
    contenido_teorico: str | None = None
    orden: int | None = None
    tiene_practica: bool | None = None
    objetivos: list[str] | None = None
    duracion_estimada_minutos: int | None = None
    pasos_guia: list[PasoGuia] | None = None
    entorno_practica: EntornoPractica | None = None
    imagen_practica: str | None = None


@dataclass(frozen=True)
class SeccionResultDTO:
    id: uuid.UUID
    laboratorio_id: uuid.UUID
    orden: int
    titulo: str
    tiene_practica: bool


@dataclass(frozen=True)
class PublicarLaboratorioDTO:
    """api.md §5 `POST /laboratories/{id}/publish/` (UC-04, paso 6)."""

    laboratorio_id: uuid.UUID
    actor_id: uuid.UUID
    actor_rol: str


@dataclass(frozen=True)
class DuplicarLaboratorioDTO:
    """api.md §5 `POST /laboratories/{id}/duplicate/` (UC-05) — solo Instructor."""

    laboratorio_id: uuid.UUID
    actor_id: uuid.UUID
    actor_rol: str


@dataclass(frozen=True)
class CrearExamenDTO:
    """HE-09/HI-08, api.md §5 `POST /laboratories/{id}/exam/`. Examen 1:1 con Laboratorio."""

    laboratorio_id: uuid.UUID
    actor_id: uuid.UUID
    actor_rol: str


@dataclass(frozen=True)
class ExamenResultDTO:
    id: uuid.UUID
    laboratorio_id: uuid.UUID


@dataclass(frozen=True)
class AgregarPreguntaDTO:
    """
    api.md §5 `POST /laboratories/{id}/exam/questions/`. `respuesta` es
    write-only (nunca se persiste en claro, mismo patrón que
    `DefinirFlagDTO.valor`): para `opcion_multiple` es el identificador
    de la opción correcta, para `abierta` el texto esperado.
    """

    laboratorio_id: uuid.UUID
    enunciado: str
    tipo: str
    respuesta: str
    actor_id: uuid.UUID
    actor_rol: str
    opciones: list[str] | None = None


@dataclass(frozen=True)
class PreguntaResultDTO:
    id: uuid.UUID
    examen_id: uuid.UUID
    enunciado: str
    tipo: str
    opciones: list[str] | None


@dataclass(frozen=True)
class SolicitarRevisionLaboratorioDTO:
    """`POST /laboratories/{id}/submit-review/` — instructor manda su personalizado a revisión."""

    laboratorio_id: uuid.UUID
    actor_id: uuid.UUID
    actor_rol: str


@dataclass(frozen=True)
class AprobarLaboratorioDTO:
    """`POST /laboratories/{id}/approve/` — admin aprueba (en_revision -> publicado)."""

    laboratorio_id: uuid.UUID
    actor_id: uuid.UUID
    actor_rol: str


@dataclass(frozen=True)
class RechazarLaboratorioDTO:
    """`POST /laboratories/{id}/reject/` — admin rechaza (en_revision -> borrador + motivo)."""

    laboratorio_id: uuid.UUID
    motivo: str
    actor_id: uuid.UUID
    actor_rol: str


@dataclass(frozen=True)
class LaboratorioEnRevisionItemDTO:
    id: uuid.UUID
    nombre: str
    instructor_id: uuid.UUID | None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class SubirDockerfileDTO:
    """`POST /laboratories/{id}/sections/{section_id}/dockerfile/` — multipart."""

    laboratorio_id: uuid.UUID
    seccion_id: uuid.UUID
    archivo_nombre: str
    archivo_contenido: bytes
    actor_id: uuid.UUID
    actor_rol: str


@dataclass(frozen=True)
class DockerfileResultDTO:
    id: uuid.UUID
    seccion_id: uuid.UUID
    archivo_url: str
    nombre_archivo: str
    tamano_kb: int


@dataclass(frozen=True)
class ObtenerContenidoSeccionPreviewDTO:
    laboratorio_id: uuid.UUID
    seccion_id: uuid.UUID
    actor_id: uuid.UUID
    actor_rol: str


@dataclass(frozen=True)
class ContenidoSeccionPreviewDTO:
    seccion_id: uuid.UUID
    titulo: str
    contenido_teorico: str
    tiene_practica: bool
    objetivos: list[str]
    duracion_estimada_minutos: int
    pasos_guia: list[dict]
    entorno_practica: dict | None
    tiene_dockerfile: bool
    dockerfile_url: str | None


@dataclass(frozen=True)
class VerificarFlagPreviewDTO:
    laboratorio_id: uuid.UUID
    seccion_id: uuid.UUID
    valor: str
    actor_id: uuid.UUID
    actor_rol: str


@dataclass(frozen=True)
class CambiarVisibilidadCatalogoDTO:
    """`PATCH /laboratories/{id}/catalog-visibility/` — opt-in de un `personalizado` al catálogo público."""

    laboratorio_id: uuid.UUID
    visible: bool
    actor_id: uuid.UUID
    actor_rol: str


@dataclass(frozen=True)
class LaboratorioPersonalizadoPublicadoItemDTO:
    """`GET /laboratories/published-custom/` — gestión admin de visibilidad de catálogo."""

    id: uuid.UUID
    nombre: str
    instructor_id: uuid.UUID | None
    visible_en_catalogo: bool
