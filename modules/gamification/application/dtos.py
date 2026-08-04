import uuid
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProcesarCompletitudDTO:
    """Entrada para `ProcesarCompletitudLaboratorio` — la dispara un listener de evento, no HTTP."""

    estudiante_id: uuid.UUID
    laboratorio_id: uuid.UUID


@dataclass(frozen=True)
class LogroDesbloqueadoResultDTO:
    logro_id: uuid.UUID
    nombre: str


@dataclass(frozen=True)
class ProcesarCompletitudResultDTO:
    xp_otorgado: int
    nivel_actual: int
    logros_desbloqueados: list[LogroDesbloqueadoResultDTO] = field(default_factory=list)


@dataclass(frozen=True)
class EquiparCosmeticoDTO:
    cosmetico_desbloqueado_id: uuid.UUID
    actor_id: uuid.UUID
    actor_rol: str


@dataclass(frozen=True)
class QuitarCosmeticoDTO:
    cosmetico_desbloqueado_id: uuid.UUID
    actor_id: uuid.UUID
    actor_rol: str


@dataclass(frozen=True)
class CosmeticoDesbloqueadoResultDTO:
    id: uuid.UUID
    cosmetico_id: uuid.UUID
    equipado: bool


@dataclass(frozen=True)
class LogroPerfilItemDTO:
    id: uuid.UUID
    clave: str
    nombre: str
    descripcion: str
    rareza: str
    desbloqueado: bool
    fecha_desbloqueo: str | None
    # Progreso legible cuando aplica (ej. "7/10 laboratorios"), None si no corresponde o ya está desbloqueado.
    progreso: str | None = None


@dataclass(frozen=True)
class CosmeticoPerfilItemDTO:
    id: uuid.UUID  # id del CosmeticoDesbloqueado, no del Cosmetico — es lo que se usa para equipar/quitar
    cosmetico_id: uuid.UUID
    clave: str
    nombre: str
    tipo: str
    rareza: str
    color: str
    equipado: bool


@dataclass(frozen=True)
class TituloPerfilItemDTO:
    id: uuid.UUID  # id del TituloDesbloqueado — se usa para equipar/quitar
    titulo_id: uuid.UUID
    clave: str
    nombre: str
    descripcion: str
    rareza: str
    equipado: bool


@dataclass(frozen=True)
class AvatarPresetItemDTO:
    clave: str
    nombre: str
    emoji: str
    color: str


@dataclass(frozen=True)
class PerfilJugadorDTO:
    estudiante_id: uuid.UUID
    xp: int
    nivel: int
    xp_para_siguiente_nivel: int | None
    avatar_tipo: str
    avatar_valor: str
    logros: list[LogroPerfilItemDTO]
    cosmeticos: list[CosmeticoPerfilItemDTO]
    titulos: list[TituloPerfilItemDTO]


@dataclass(frozen=True)
class CatalogoLogroItemDTO:
    id: uuid.UUID
    clave: str
    nombre: str
    descripcion: str
    rareza: str


@dataclass(frozen=True)
class CatalogoCosmeticoItemDTO:
    id: uuid.UUID
    clave: str
    nombre: str
    tipo: str
    rareza: str
    color: str
    logro_requerido_id: uuid.UUID


@dataclass(frozen=True)
class CatalogoTituloItemDTO:
    id: uuid.UUID
    clave: str
    nombre: str
    descripcion: str
    rareza: str
    logro_requerido_id: uuid.UUID


@dataclass(frozen=True)
class CambiarAvatarDTO:
    """`PATCH /gamification/avatar/` — elegir un avatar predeterminado."""

    preset_clave: str
    actor_id: uuid.UUID
    actor_rol: str


@dataclass(frozen=True)
class SubirAvatarDTO:
    """`POST /gamification/avatar/upload/` — subir una foto propia como avatar."""

    archivo_nombre: str
    archivo_contenido: bytes
    actor_id: uuid.UUID
    actor_rol: str


@dataclass(frozen=True)
class AvatarResultDTO:
    avatar_tipo: str
    avatar_valor: str


@dataclass(frozen=True)
class EquiparTituloDTO:
    titulo_desbloqueado_id: uuid.UUID
    actor_id: uuid.UUID
    actor_rol: str


@dataclass(frozen=True)
class QuitarTituloDTO:
    titulo_desbloqueado_id: uuid.UUID
    actor_id: uuid.UUID
    actor_rol: str


@dataclass(frozen=True)
class TituloDesbloqueadoResultDTO:
    id: uuid.UUID
    titulo_id: uuid.UUID
    equipado: bool


@dataclass(frozen=True)
class CompletarOnboardingDTO:
    """`POST /gamification/onboarding/completar/` — se llama al terminar el tour, no al saltarlo."""

    actor_id: uuid.UUID
    actor_rol: str


@dataclass(frozen=True)
class CompletarOnboardingResultDTO:
    logro_desbloqueado: LogroDesbloqueadoResultDTO | None
