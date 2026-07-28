from dataclasses import dataclass
from enum import Enum


class NivelDificultad(str, Enum):
    BASICO = "basico"
    INTERMEDIO = "intermedio"
    AVANZADO = "avanzado"


class EstadoLaboratorio(str, Enum):
    BORRADOR = "borrador"
    PUBLICADO = "publicado"


class TipoLaboratorio(str, Enum):
    PREDETERMINADO = "predeterminado"
    PERSONALIZADO = "personalizado"


@dataclass(frozen=True)
class AyudaProgresiva:
    """
    dominio.md §2: pista y paso a paso, siempre asociados a una `Flag`.
    Ambos opcionales (el instructor puede omitir la ayuda progresiva).
    """

    pista: str | None = None
    paso_a_paso: str | None = None
