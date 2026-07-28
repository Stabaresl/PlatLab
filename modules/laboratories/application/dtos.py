import uuid
from dataclasses import dataclass, field


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


@dataclass(frozen=True)
class SeccionTOCItemDTO:
    orden: int
    titulo: str
    tiene_practica: bool


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


@dataclass(frozen=True)
class EditarLaboratorioDTO:
    """
    api.md §5 `PATCH /laboratories/{id}/`. Solo metadatos editables
    (nombre/descripción/dificultad/temas) — `tipo`/`estado` cambian solo
    vía `PublicarLaboratorioUseCase`/`DuplicarLaboratorioUseCase`.
    """

    laboratorio_id: uuid.UUID
    actor_id: uuid.UUID
    actor_rol: str
    nombre: str | None = None
    descripcion: str | None = None
    nivel_dificultad: str | None = None
    temas: list[str] | None = None


@dataclass(frozen=True)
class LaboratorioResultDTO:
    id: uuid.UUID
    nombre: str
    estado: str
    tipo: str


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


@dataclass(frozen=True)
class SeccionResultDTO:
    id: uuid.UUID
    laboratorio_id: uuid.UUID
    orden: int
    titulo: str
    tiene_practica: bool
