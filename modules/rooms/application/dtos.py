import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class CrearSalaDTO:
    actor_id: uuid.UUID
    actor_rol: str
    nombre: str
    laboratorio_id: uuid.UUID
    descripcion: str = ""
    capacidad: int = 30
    fecha_fin: datetime | None = None


@dataclass(frozen=True)
class UnirseSalaDTO:
    actor_id: uuid.UUID
    actor_rol: str
    codigo: str


@dataclass(frozen=True)
class CambiarEstadoSalaDTO:
    sala_id: uuid.UUID
    actor_id: uuid.UUID
    actor_rol: str
    estado: str


@dataclass(frozen=True)
class RegistrarCompletitudSalaDTO:
    asignacion_id: uuid.UUID


@dataclass(frozen=True)
class SalaResultDTO:
    id: uuid.UUID
    nombre: str
    descripcion: str
    codigo: str
    laboratorio_id: uuid.UUID
    laboratorio_nombre: str
    laboratorio_nivel: str
    anfitrion_id: uuid.UUID
    anfitrion_nombre: str
    capacidad: int
    participantes: int
    completados: int
    estado: str
    acepta_ingresos: bool
    fecha_fin: datetime | None
    created_at: datetime
    # Solo para el estudiante que la ve desde "mis salas".
    mi_asignacion_id: uuid.UUID | None = None
    mi_posicion_final: int | None = None


@dataclass(frozen=True)
class UnirseSalaResultDTO:
    sala_id: uuid.UUID
    asignacion_id: uuid.UUID
    ya_era_participante: bool
    completado_antes: bool


@dataclass(frozen=True)
class ParticipanteTableroDTO:
    estudiante_id: uuid.UUID
    nombre: str
    puesto: int
    secciones_completadas: int
    secciones_total: int
    porcentaje: int
    mejor_puntaje: float | None
    completado: bool
    completado_antes: bool
    posicion_final: int | None
    fecha_completado: datetime | None
    ultima_actividad: datetime | None
    unido_en: datetime
    es_yo: bool


@dataclass(frozen=True)
class DetalleSalaDTO:
    sala: SalaResultDTO
    es_anfitrion: bool
    participantes: list[ParticipanteTableroDTO] = field(default_factory=list)
    mi_asignacion_id: uuid.UUID | None = None


@dataclass(frozen=True)
class VistaPreviaSalaDTO:
    codigo: str
    nombre: str
    descripcion: str
    laboratorio_nombre: str
    laboratorio_nivel: str
    anfitrion_nombre: str
    capacidad: int
    participantes: int
    acepta_ingresos: bool
    ya_participo: bool
    sala_id: uuid.UUID | None = None


@dataclass(frozen=True)
class LaboratorioParaSalaDTO:
    id: uuid.UUID
    nombre: str
    descripcion: str
    nivel_dificultad: str
    tipo: str
    secciones: int
