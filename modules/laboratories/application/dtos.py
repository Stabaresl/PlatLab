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
