import uuid
from dataclasses import dataclass, field
from datetime import datetime

from modules.lab_environments.domain.value_objects import EstadoEntorno
from modules.shared.domain.base_entity import BaseEntity


@dataclass(eq=False)
class EntornoActivo(BaseEntity):
    """
    Agregado raíz de lab_environments: una instancia de contenedor Docker
    descartable, aislada de red, asociada 1:1 a (Progreso, Sección) —
    dominio.md-style "id suelto" hacia Progress/Laboratories, sin FK real
    (mismo patrón que `Progreso.asignacion_id`). Separado de `Progreso`
    porque tiene un ciclo de vida propio y mucho más corto (minutos/horas,
    no la duración completa del laboratorio).
    """

    seccion_id: uuid.UUID
    progreso_id: uuid.UUID
    estudiante_id: uuid.UUID
    container_id: str
    estado: EstadoEntorno = EstadoEntorno.INICIANDO
    fecha_inicio: datetime = field(default_factory=datetime.utcnow)
    ultima_actividad: datetime = field(default_factory=datetime.utcnow)
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        BaseEntity.__init__(self, id=self.id)

    def es_propio_de(self, estudiante_id: uuid.UUID) -> bool:
        return self.estudiante_id == estudiante_id

    def marcar_activo(self) -> None:
        self.estado = EstadoEntorno.ACTIVO

    def marcar_detenido(self) -> None:
        self.estado = EstadoEntorno.DETENIDO

    def marcar_error(self) -> None:
        self.estado = EstadoEntorno.ERROR

    def tocar_actividad(self) -> None:
        self.ultima_actividad = datetime.utcnow()

    def esta_activo(self) -> bool:
        return self.estado in (EstadoEntorno.INICIANDO, EstadoEntorno.ACTIVO)
