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
