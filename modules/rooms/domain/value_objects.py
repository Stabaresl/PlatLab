import secrets
from enum import Enum

from modules.progress.domain.value_objects import PUNTAJE_APROBACION  # noqa: F401 (re-export)

CAPACIDAD_MAXIMA = 100
CAPACIDAD_POR_DEFECTO = 30
LONGITUD_CODIGO = 6
# Sin 0/O ni 1/I/L: el código se dicta en voz alta en el aula o se copia del
# tablero, y esos caracteres se confunden.
_ALFABETO_CODIGO = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
# PUNTAJE_APROBACION (importado arriba): una sola fuente para el umbral con
# el que la sala, la gamificación y el examen cuentan un laboratorio terminado.


class EstadoSala(str, Enum):
    ABIERTA = "abierta"  # acepta nuevos participantes
    CERRADA = "cerrada"  # sin nuevos ingresos; quienes ya entraron siguen trabajando
    FINALIZADA = "finalizada"  # terminó: el tablero queda de solo lectura y no da recompensas


def generar_codigo() -> str:
    return "".join(secrets.choice(_ALFABETO_CODIGO) for _ in range(LONGITUD_CODIGO))


def normalizar_codigo(valor: str) -> str:
    """Acepta el código como lo escriba la persona: minúsculas, espacios o guion ("abc-123")."""
    return "".join(c for c in (valor or "").upper() if c.isalnum())
