import uuid
from dataclasses import dataclass, field
from datetime import datetime

from modules.rooms.domain.value_objects import (
    CAPACIDAD_MAXIMA,
    CAPACIDAD_POR_DEFECTO,
    EstadoSala,
)
from modules.shared.domain.base_entity import BaseEntity
from modules.shared.domain.exceptions import BusinessRuleViolationError, ValidationError
from modules.shared.domain.tiempo import ahora_utc

_NOMBRE_REQUERIDO_MSG = "La sala necesita un nombre."
_NOMBRE_LARGO_MSG = "El nombre de la sala admite hasta 120 caracteres."
_CAPACIDAD_MSG = f"La capacidad de una sala va de 1 a {CAPACIDAD_MAXIMA} personas."
_FINALIZADA_MSG = "Esta sala ya finalizó: no se puede reabrir."


@dataclass(eq=False)
class Sala(BaseEntity):
    """
    Sala privada: un instructor o admin la abre sobre un laboratorio publicado
    y comparte un código; cada estudiante que entra recibe su propia
    asignación (y su propio contenedor al practicar). El anfitrión ve el
    progreso de todos en un tablero en vivo. `laboratorio_id`/`anfitrion_id`
    son id sueltos (Arquitectura §8).
    """

    nombre: str
    laboratorio_id: uuid.UUID
    anfitrion_id: uuid.UUID
    codigo: str
    descripcion: str = ""
    capacidad: int = CAPACIDAD_POR_DEFECTO
    estado: EstadoSala = EstadoSala.ABIERTA
    fecha_fin: datetime | None = None
    created_at: datetime = field(default_factory=ahora_utc)
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        BaseEntity.__init__(self, id=self.id)
        self.nombre = (self.nombre or "").strip()
        if not self.nombre:
            raise ValidationError(_NOMBRE_REQUERIDO_MSG)
        if len(self.nombre) > 120:
            raise ValidationError(_NOMBRE_LARGO_MSG)
        if not 1 <= int(self.capacidad) <= CAPACIDAD_MAXIMA:
            raise ValidationError(_CAPACIDAD_MSG)

    def acepta_ingresos(self, ahora: datetime | None = None) -> bool:
        ahora = ahora or ahora_utc()
        return self.estado == EstadoSala.ABIERTA and (self.fecha_fin is None or self.fecha_fin > ahora)

    def cambiar_estado(self, nuevo: EstadoSala) -> None:
        if self.estado == EstadoSala.FINALIZADA and nuevo != EstadoSala.FINALIZADA:
            raise BusinessRuleViolationError(_FINALIZADA_MSG)
        self.estado = nuevo


@dataclass(eq=False)
class ParticipanteSala(BaseEntity):
    """
    Un estudiante dentro de una sala, ligado a la asignación con la que
    trabaja el laboratorio. `completado_antes`: ya había terminado ese
    laboratorio con esa misma asignación antes de entrar, así que no compite
    por los puestos del tablero (si no, ganaría el primer lugar al instante).
    """

    sala_id: uuid.UUID
    estudiante_id: uuid.UUID
    asignacion_id: uuid.UUID
    completado_antes: bool = False
    posicion_final: int | None = None
    fecha_completado: datetime | None = None
    unido_en: datetime = field(default_factory=ahora_utc)
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        BaseEntity.__init__(self, id=self.id)

    @property
    def compite(self) -> bool:
        return not self.completado_antes and self.posicion_final is None
