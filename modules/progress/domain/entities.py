import uuid
from dataclasses import dataclass, field
from datetime import datetime

from modules.progress.domain.value_objects import EstadoProgresoSeccion
from modules.shared.domain.base_entity import BaseEntity


@dataclass(eq=False)
class Progreso(BaseEntity):
    """
    Agregado raíz del módulo Progress (dominio.md §4): cambia con alta
    frecuencia (cada intento de flag) y se mantiene separado de
    Asignación para evitar contención de escritura.

    `estudiante_id` es una denormalización deliberada frente a
    base-de-datos.md (que solo define `asignacion_id`): Assignments
    (Sprint 4) todavía no existe, y la regla de propiedad "Estudiante
    (propio)" (seguridad.md §1) debe poder validarse sin depender de ese
    módulo. Es el mismo patrón de "id suelto" ya usado en
    `instructor_id`/`origen_id` de `Laboratorio` — una referencia cruzada
    resuelta en Application, nunca una FK de base de datos.
    """

    asignacion_id: uuid.UUID
    estudiante_id: uuid.UUID
    fecha_inicio: datetime = field(default_factory=datetime.utcnow)
    ultima_actividad: datetime = field(default_factory=datetime.utcnow)
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        BaseEntity.__init__(self, id=self.id)

    def es_propio_de(self, estudiante_id: uuid.UUID) -> bool:
        return self.estudiante_id == estudiante_id


@dataclass(eq=False)
class ProgresoSeccion(BaseEntity):
    """
    Estado de una `Seccion` (id suelto a `laboratories_seccion`) dentro
    de un `Progreso` (dominio.md §3): máquina de estados
    `bloqueada -> en_progreso -> completada`, secuencialidad
    obligatoria — solo la entidad misma decide sus propias transiciones,
    coordinar dos instancias (desbloquear la siguiente) es
    responsabilidad de `GestorDeSecuencia` (dominio.md §5).
    """

    progreso_id: uuid.UUID
    seccion_id: uuid.UUID
    estado: EstadoProgresoSeccion = EstadoProgresoSeccion.BLOQUEADA
    fecha_completado: datetime | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        BaseEntity.__init__(self, id=self.id)

    def desbloquear(self) -> None:
        if self.estado == EstadoProgresoSeccion.BLOQUEADA:
            self.estado = EstadoProgresoSeccion.EN_PROGRESO

    def completar(self) -> None:
        self.estado = EstadoProgresoSeccion.COMPLETADA
        self.fecha_completado = datetime.utcnow()


@dataclass(eq=False)
class IntentoFlag(BaseEntity):
    """
    Registro de un intento sobre una flag (dominio.md §1,
    base-de-datos.md "progress_intentoflag").
    """

    progreso_id: uuid.UUID
    seccion_id: uuid.UUID
    resultado: bool
    timestamp: datetime = field(default_factory=datetime.utcnow)
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        BaseEntity.__init__(self, id=self.id)


@dataclass(eq=False)
class HistorialCompletitud(BaseEntity):
    """
    Registro append-only de cada completitud del laboratorio (dominio.md
    §1: "soporta repetición sin perder histórico", HE-10/HE-11).
    """

    progreso_id: uuid.UUID
    numero_intento: int
    fecha_completado: datetime = field(default_factory=datetime.utcnow)
    puntaje: float | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        BaseEntity.__init__(self, id=self.id)
