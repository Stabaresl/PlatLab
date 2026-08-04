from dataclasses import dataclass, field
from enum import Enum


IMAGENES_PRACTICA_PERMITIDAS: frozenset[str] = frozenset(
    {
        "platlab-target-sqli:latest",
    }
)
"""
seguridad.md — allowlist de las únicas imágenes que una `Seccion` puede
usar como `imagen_practica`. No es una tabla en base de datos a propósito
(mismo criterio que `NIVEL_UMBRALES` en gamification): agregar una imagen
nueva implica construir y publicar el Dockerfile en `docker/targets/`
primero, así que su disponibilidad ya es un cambio de código, no un dato
de negocio que un instructor deba poder tocar. Ver
`ImagenPracticaNoPermitidaError` y `validar_imagen_practica_permitida`
(domain/services.py) — sin esto, `imagen_practica` era texto libre pasado
directo a `containers.run()`.
"""


class NivelDificultad(str, Enum):
    BASICO = "basico"
    INTERMEDIO = "intermedio"
    AVANZADO = "avanzado"


class EstadoLaboratorio(str, Enum):
    BORRADOR = "borrador"
    EN_REVISION = "en_revision"
    PUBLICADO = "publicado"


class TipoLaboratorio(str, Enum):
    PREDETERMINADO = "predeterminado"
    PERSONALIZADO = "personalizado"


class TipoPregunta(str, Enum):
    """dominio.md/base-de-datos.md "laboratories_pregunta": Strategy de calificación (HE-09)."""

    OPCION_MULTIPLE = "opcion_multiple"
    ABIERTA = "abierta"


@dataclass(frozen=True)
class AyudaProgresiva:
    """
    dominio.md §2: pista y paso a paso, siempre asociados a una `Flag`.
    Ambos opcionales (el instructor puede omitir la ayuda progresiva).
    Esta ayuda se DESBLOQUEA progresivamente (5/15 intentos fallidos,
    HE-06) — es distinta de `Seccion.pasos_guia`, que está disponible
    desde el arranque, sin gatillo.
    """

    pista: str | None = None
    paso_a_paso: str | None = None


@dataclass(frozen=True)
class ComandoSimulado:
    """
    Un par comando/salida de la consola simulada de una `Seccion`
    práctica (`Seccion.entorno_practica`). No ejecuta nada real: el
    instructor autoría el guion completo (estilo HackerRank/TryHackMe
    "salas" con terminal embebida pero controlada) y el frontend solo
    compara el texto tipeado contra `comando` para mostrar `salida`.
    """

    comando: str
    salida: str


@dataclass(frozen=True)
class EntornoPractica:
    """
    Consola simulada opcional de una `Seccion` práctica — le da la
    sensación de "tener una VM" sin ejecutar comandos reales contra
    ningún sistema (eso requeriría una infraestructura de aislamiento
    aparte, fuera de alcance). `comandos` es el guion completo que
    autoría el instructor; el frontend resuelve cualquier comando no
    listado con un mensaje genérico de "comando no encontrado".
    """

    prompt: str = "root@lab:~#"
    banner: str = ""
    comandos: list[ComandoSimulado] = field(default_factory=list)


@dataclass(frozen=True)
class PasoGuia:
    """
    Un paso numerado de la guía de una `Seccion` (estilo AWS Academy: tarea
    1, tarea 2, ...) — reemplaza el bloque único `guia_paso_a_paso` por
    pasos discretos, cada uno con su propio título e instrucciones, y
    opcionalmente el comando exacto sugerido para ese paso.
    """

    orden: int
    titulo: str
    instrucciones: str
    comando_sugerido: str | None = None
