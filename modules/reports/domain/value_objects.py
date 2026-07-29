from enum import Enum


class EstadoReporte(str, Enum):
    """HE-12/HA-05, base-de-datos.md "reports_reporte" (nombres sin tilde, fuente de verdad)."""

    ABIERTO = "abierto"
    EN_REVISION = "en_revision"
    RESUELTO = "resuelto"
    NO_REPRODUCIBLE = "no_reproducible"
