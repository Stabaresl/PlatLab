from dataclasses import dataclass
from enum import Enum
from typing import ClassVar


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
