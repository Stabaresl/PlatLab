from dataclasses import dataclass
from enum import Enum
from typing import ClassVar

from modules.shared.domain.exceptions import ValidationError

_ESCALA_INVALIDA_MSG = "La escala máxima de un puntaje debe ser mayor a cero."
_VALOR_FUERA_DE_RANGO_MSG = "El valor obtenido no puede ser negativo ni superar la escala máxima."


class EstadoProgresoSeccion(str, Enum):
    BLOQUEADA = "bloqueada"
    EN_PROGRESO = "en_progreso"
    COMPLETADA = "completada"


@dataclass(frozen=True)
class ContadorFallos:
    """
    dominio.md §2: valor incremental por flag — dispara la pista a los 5
    fallos y el paso a paso a los 15 (5 + 10 adicionales, UC-02 A1). El
    total es el número de `IntentoFlag` fallidos ya persistidos para esa
    sección (Infrastructure lo cuenta, `IProgresoRepository.contar_fallos`);
    este VO es inmutable, `incrementar()` devuelve una nueva instancia.
    """

    total: int = 0

    UMBRAL_PISTA: ClassVar[int] = 5
    UMBRAL_PASO_A_PASO: ClassVar[int] = 15

    def incrementar(self) -> "ContadorFallos":
        return ContadorFallos(total=self.total + 1)

    @property
    def debe_mostrar_pista(self) -> bool:
        return self.total >= self.UMBRAL_PISTA

    @property
    def debe_mostrar_paso_a_paso(self) -> bool:
        return self.total >= self.UMBRAL_PASO_A_PASO


@dataclass(frozen=True)
class Puntaje:
    """
    HE-09/HI-08, dominio.md §2: valor obtenido + escala máxima, usado en
    `ResultadoExamen` e `HistorialCompletitud`. Se persiste como el
    porcentaje resultante (numeric(5,2), base-de-datos.md) — este VO
    solo existe para el cálculo, no se embebe en la entidad.
    """

    correctas: int
    total: int

    def __post_init__(self):
        if self.total <= 0:
            raise ValidationError(_ESCALA_INVALIDA_MSG)
        if self.correctas < 0 or self.correctas > self.total:
            raise ValidationError(_VALOR_FUERA_DE_RANGO_MSG)

    @property
    def porcentaje(self) -> float:
        return round(self.correctas / self.total * 100, 2)
