from enum import Enum


class TipoCriterioLogro(str, Enum):
    """
    Cómo se evalúa si un `Logro` se desbloquea —
    ver `application/procesar_completitud.py::ProcesarCompletitudLaboratorio`.
    """

    PRIMER_LABORATORIO = "primer_laboratorio"
    N_LABORATORIOS = "n_laboratorios"
    CATEGORIA_ROADMAP_COMPLETA = "categoria_roadmap_completa"


class RarezaCosmetico(str, Enum):
    COMUN = "comun"
    POCO_COMUN = "poco_comun"
    RARO = "raro"
    EPICO = "epico"
    LEGENDARIO = "legendario"
    MITICO = "mitico"


class TipoCosmetico(str, Enum):
    """
    Slot de equipamiento — uno equipado a la vez por tipo, salvo
    `INSIGNIA` (admite varias equipadas simultáneamente, como badges).
    """

    HOODIE = "hoodie"
    GAFAS = "gafas"
    MASCARA = "mascara"
    AURA = "aura"
    INSIGNIA = "insignia"
    MOCHILA = "mochila"
    GUANTES = "guantes"
    ZAPATOS = "zapatos"
    GORRA = "gorra"
    AUDIFONOS = "audifonos"
    MARCO = "marco"


class AvatarTipo(str, Enum):
    """De dónde sale la identidad visual del avatar — ver `PerfilJugador.avatar_tipo`."""

    PRESET = "preset"
    SUBIDO = "subido"
