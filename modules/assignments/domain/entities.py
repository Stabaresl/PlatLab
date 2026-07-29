import uuid
from dataclasses import dataclass, field
from datetime import datetime

from modules.assignments.domain.value_objects import EstadoAsignacion
from modules.shared.domain.base_entity import BaseEntity


@dataclass(eq=False)
class Asignacion(BaseEntity):
    """
    Agregado raíz de Assignments (dominio.md §4): vínculo
    Estudiante↔Laboratorio con ciclo de vida propio
    (invitación→aceptación→vencimiento), independiente del contenido del
    laboratorio — separado de `Progreso` para evitar contención de
    escritura (dominio.md §4). `estudiante_id`/`laboratorio_id`/
    `instructor_id` son "id suelto" (Arquitectura §8): sin FK a otros
    módulos.
    """

    estudiante_id: uuid.UUID
    laboratorio_id: uuid.UUID
    instructor_id: uuid.UUID | None = None
    estado: EstadoAsignacion = EstadoAsignacion.PENDIENTE
    fecha_invitacion: datetime = field(default_factory=datetime.utcnow)
    fecha_vencimiento: datetime | None = None
    fecha_respuesta: datetime | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        BaseEntity.__init__(self, id=self.id)

    def aceptar(self) -> None:
        """
        UC-06 paso 4-5: aceptar y otorgar acceso son el mismo instante
        (el sistema "otorga acceso... y comienza a contar el plazo"
        inmediatamente después de aceptar) — se persiste directo como
        `activa`, no como `aceptada` intermedio, para que
        `GestorDeVencimientos` (Sprint 5) solo tenga que mirar ese
        estado al evaluar vencimientos.
        """
        self.estado = EstadoAsignacion.ACTIVA
        self.fecha_respuesta = datetime.utcnow()

    def rechazar(self) -> None:
        self.estado = EstadoAsignacion.RECHAZADA
        self.fecha_respuesta = datetime.utcnow()

    def vencer(self) -> None:
        """RF-32, UC-07: revoca el acceso al llegar la `VentanaVencimiento`."""
        self.estado = EstadoAsignacion.VENCIDA

    def esta_vigente(self) -> bool:
        """UC-06 E2: usado para detectar duplicados — pendiente o activa cuentan como vigente."""
        return self.estado in (EstadoAsignacion.PENDIENTE, EstadoAsignacion.ACTIVA)
