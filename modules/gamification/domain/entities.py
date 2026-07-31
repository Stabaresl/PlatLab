import uuid
from dataclasses import dataclass, field
from datetime import datetime

from modules.gamification.domain.value_objects import (
    AvatarTipo,
    RarezaCosmetico,
    TipoCosmetico,
    TipoCriterioLogro,
)
from modules.shared.domain.base_entity import BaseEntity

# Umbrales de XP acumulado para subir de nivel — nivel = cuántos umbrales
# superó (nivel 1 en 0 XP). Tabla fija en el dominio a propósito: no hay
# necesidad de que sea configurable en v1 (ver plan, "fuera de v1").
NIVEL_UMBRALES = [0, 100, 250, 450, 700, 1000, 1400, 1900, 2500, 3200, 4000]

# XP otorgado al completar un laboratorio, según su dificultad.
XP_POR_DIFICULTAD = {"basico": 50, "intermedio": 100, "avanzado": 150}


@dataclass(frozen=True)
class AvatarPreset:
    """Un avatar predeterminado — no se persiste, es un catálogo fijo (ver `AVATAR_PRESETS`)."""

    clave: str
    nombre: str
    emoji: str
    color: str


# Catálogo fijo de avatares predeterminados (mismo criterio que
# `NIVEL_UMBRALES`: dato de balance/contenido, no configurable en v1,
# sin tabla ni UI de autoría). `PerfilJugador.avatar_valor` guarda la
# `clave` de uno de estos cuando `avatar_tipo == PRESET`.
AVATAR_PRESETS = [
    AvatarPreset("operador_nocturno", "Operador Nocturno", "🥷", "56,214,245"),
    AvatarPreset("ingeniera_red", "Ingeniera de Red", "👩‍💻", "51,214,159"),
    AvatarPreset("ingeniero_sistemas", "Ingeniero de Sistemas", "👨‍💻", "255,176,32"),
    AvatarPreset("analista_soc", "Analista SOC", "🕵️", "255,71,87"),
    AvatarPreset("unidad_autonoma", "Unidad Autónoma", "🤖", "136,146,163"),
    AvatarPreset("vector_amenaza", "Vector de Amenaza", "👾", "186,85,255"),
    AvatarPreset("explorador_digital", "Explorador Digital", "🧑‍🚀", "236,72,153"),
    AvatarPreset("fantasma_red", "Fantasma de la Red", "👻", "230,230,230"),
]
_AVATAR_PRESET_POR_CLAVE = {p.clave: p for p in AVATAR_PRESETS}


def avatar_preset_valido(clave: str) -> bool:
    return clave in _AVATAR_PRESET_POR_CLAVE


def _nivel_para(xp: int) -> int:
    nivel = 1
    for umbral in NIVEL_UMBRALES:
        if xp >= umbral:
            nivel += 1
        else:
            break
    return nivel - 1 if nivel > 1 else 1


@dataclass(eq=False)
class PerfilJugador(BaseEntity):
    """
    Progresión de un estudiante — 1:1 con `estudiante_id` (id suelto,
    Arquitectura §8: Gamification no depende de Users a nivel de FK).
    """

    estudiante_id: uuid.UUID
    xp: int = 0
    nivel: int = 1
    avatar_tipo: AvatarTipo = AvatarTipo.PRESET
    avatar_valor: str = AVATAR_PRESETS[0].clave
    created_at: datetime = field(default_factory=datetime.utcnow)
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        BaseEntity.__init__(self, id=self.id)

    def agregar_xp(self, cantidad: int) -> None:
        self.xp += cantidad
        self.nivel = _nivel_para(self.xp)

    def xp_para_siguiente_nivel(self) -> int | None:
        """XP total que hace falta acumular para el próximo nivel, o `None` si ya está en el máximo."""
        for umbral in NIVEL_UMBRALES:
            if self.xp < umbral:
                return umbral
        return None


@dataclass(eq=False)
class XpOtorgado(BaseEntity):
    """
    Registro append-only de XP ganado — único por `(estudiante_id,
    laboratorio_id)`: además de idempotencia (un examen reintentable
    dispara `ExamGraded` más de una vez, esto evita duplicar XP), sirve
    como fuente de "cuántos laboratorios distintos completó" sin
    duplicar `HistorialCompletitud` (que vive en Progress).
    """

    estudiante_id: uuid.UUID
    laboratorio_id: uuid.UUID
    xp: int
    fecha: datetime = field(default_factory=datetime.utcnow)
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        BaseEntity.__init__(self, id=self.id)


@dataclass(eq=False)
class Logro(BaseEntity):
    """Catálogo de logros — sembrado por `seed_gamification_catalog`, sin UI de autoría en v1."""

    clave: str
    nombre: str
    descripcion: str
    tipo_criterio: TipoCriterioLogro
    rareza: RarezaCosmetico
    # Umbral N (N_LABORATORIOS) o id de CategoriaRoadmap (CATEGORIA_ROADMAP_COMPLETA) según el tipo; None para PRIMER_LABORATORIO.
    criterio_valor: str | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        BaseEntity.__init__(self, id=self.id)


@dataclass(eq=False)
class LogroDesbloqueado(BaseEntity):
    estudiante_id: uuid.UUID
    logro_id: uuid.UUID
    fecha: datetime = field(default_factory=datetime.utcnow)
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        BaseEntity.__init__(self, id=self.id)


@dataclass(eq=False)
class Cosmetico(BaseEntity):
    """Catálogo de cosméticos — cada uno desbloqueado por un `Logro` puntual (`logro_requerido_id`)."""

    clave: str
    nombre: str
    tipo: TipoCosmetico
    rareza: RarezaCosmetico
    color: str
    logro_requerido_id: uuid.UUID
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        BaseEntity.__init__(self, id=self.id)


@dataclass(eq=False)
class CosmeticoDesbloqueado(BaseEntity):
    estudiante_id: uuid.UUID
    cosmetico_id: uuid.UUID
    equipado: bool = False
    fecha: datetime = field(default_factory=datetime.utcnow)
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        BaseEntity.__init__(self, id=self.id)


@dataclass(eq=False)
class Titulo(BaseEntity):
    """
    Catálogo de títulos (ej. "Cazador de Bugs") — mismo criterio que
    `Cosmetico`, pero sin `tipo`: un título es siempre un único slot
    (un cartel bajo el nombre, no una pieza de vestuario), así que no
    hace falta subdividir por categoría de equipamiento.
    """

    clave: str
    nombre: str
    descripcion: str
    rareza: RarezaCosmetico
    logro_requerido_id: uuid.UUID
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        BaseEntity.__init__(self, id=self.id)


@dataclass(eq=False)
class TituloDesbloqueado(BaseEntity):
    estudiante_id: uuid.UUID
    titulo_id: uuid.UUID
    equipado: bool = False
    fecha: datetime = field(default_factory=datetime.utcnow)
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        BaseEntity.__init__(self, id=self.id)
