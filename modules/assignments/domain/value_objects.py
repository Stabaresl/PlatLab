from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from modules.shared.domain.exceptions import ValidationError

_FECHA_SIN_TIMEZONE_MSG = "La fecha de vencimiento debe incluir zona horaria."


class EstadoAsignacion(str, Enum):
    PENDIENTE = "pendiente"
    ACEPTADA = "aceptada"
    RECHAZADA = "rechazada"
    ACTIVA = "activa"
    VENCIDA = "vencida"


@dataclass(frozen=True)
class VentanaVencimiento:
    """
    HI-07, dominio.md §2: fecha/hora límite de acceso de una
    `Asignación`. Se exige zona horaria explícita (UC-06 E3: "el sistema
    normaliza y almacena en UTC, mostrando conversión local en la UI")
    — con `USE_TZ=True` Django persiste en UTC cualquier datetime
    consciente de zona horaria, así que esta validación solo asegura que
    llegue una zona horaria, sin reconvertir aquí. Se reutiliza en
    `InvitarEstudiantesUseCase` (validar que no venga ya vencida) y en
    `GestorDeVencimientos` (RF-32, decidir si ya venció).
    """

    fecha: datetime

    def __post_init__(self):
        if self.fecha.tzinfo is None:
            raise ValidationError(_FECHA_SIN_TIMEZONE_MSG)

    def ya_vencio(self, ahora: datetime | None = None) -> bool:
        return self.fecha <= (ahora or datetime.now(timezone.utc))
