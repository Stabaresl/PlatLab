import uuid
from dataclasses import dataclass, field
from datetime import datetime

from modules.laboratories.domain.value_objects import (
    AyudaProgresiva,
    EstadoLaboratorio,
    NivelDificultad,
    TipoLaboratorio,
    TipoPregunta,
)
from modules.shared.domain.base_entity import BaseEntity
from modules.shared.domain.exceptions import ValidationError

_OPCIONES_REQUERIDAS_MSG = "Las preguntas de opción múltiple requieren al menos dos opciones."
_OPCIONES_NO_PERMITIDAS_MSG = "Las preguntas abiertas no llevan opciones."


@dataclass(eq=False)
class Laboratorio(BaseEntity):
    """
    Entidad raíz del agregado Laboratorio (dominio.md §4: "se edita/publica
    como unidad atómica"). `Sección` (y, en sprints posteriores, `Flag` y
    `Examen`) son parte del mismo agregado. `temas` es una lista de
    nombres — `Tema` es un value object (dominio.md §2), no una entidad
    propia; la normalización en tabla aparte es un detalle de
    `infrastructure/models.py`, invisible aquí.
    """

    nombre: str
    descripcion: str
    nivel_dificultad: NivelDificultad
    estado: EstadoLaboratorio = EstadoLaboratorio.BORRADOR
    tipo: TipoLaboratorio = TipoLaboratorio.PREDETERMINADO
    temas: list[str] = field(default_factory=list)
    origen_id: uuid.UUID | None = None
    instructor_id: uuid.UUID | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        BaseEntity.__init__(self, id=self.id)

    def es_visible_para(self, instructor_id: uuid.UUID | None = None) -> bool:
        """
        HV-02/HI-01: el catálogo público (y el de estudiante, HE-02) solo
        muestra laboratorios `predeterminado` + `publicado`. Un instructor
        además ve sus propios laboratorios `personalizado`, sin importar
        el estado (borrador incluido) — nunca los de otro instructor.
        """
        if (
            self.estado == EstadoLaboratorio.PUBLICADO
            and self.tipo == TipoLaboratorio.PREDETERMINADO
        ):
            return True
        return instructor_id is not None and self.instructor_id == instructor_id


@dataclass(eq=False)
class Seccion(BaseEntity):
    """
    Unidad de contenido de un `Laboratorio` (dominio.md §1). En Sprint 2
    solo se modela el esqueleto — `Flag` (relación 1:1) se agrega en
    Sprint 3 (HE-05), no antes.
    """

    laboratorio_id: uuid.UUID
    titulo: str
    contenido_teorico: str
    orden: int
    tiene_practica: bool = False
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        BaseEntity.__init__(self, id=self.id)


@dataclass(eq=False)
class Flag(BaseEntity):
    """
    Flag de una Sección práctica (dominio.md §1/§3, base-de-datos.md
    "laboratories_flag"): relación 1:1 con `Seccion`, solo si
    `tiene_practica`. El valor real nunca se persiste ni se expone en
    claro — únicamente su `hash` (bcrypt/argon2, misma utilidad que
    `password_hash` de User), comparado en tiempo constante al validar
    un intento (seguridad.md §4). Hashear y comparar es responsabilidad
    de Application (`DefinirFlagUseCase`/`ValidarFlagUseCase`), no de
    esta entidad.
    """

    seccion_id: uuid.UUID
    hash: str
    ayuda: AyudaProgresiva = field(default_factory=AyudaProgresiva)
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        BaseEntity.__init__(self, id=self.id)


@dataclass(eq=False)
class Examen(BaseEntity):
    """
    HE-09/HI-08, dominio.md §1: agregado interno de `Laboratorio`,
    relación 1:1 (base-de-datos.md "laboratories_examen"). Opcional en
    laboratorios `personalizado` (UC-03 A2) — si no existe, el
    laboratorio se marca completo directamente al terminar las
    secciones, sin bloquear al estudiante.
    """

    laboratorio_id: uuid.UUID
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        BaseEntity.__init__(self, id=self.id)


@dataclass(eq=False)
class Pregunta(BaseEntity):
    """
    dominio.md §1, base-de-datos.md "laboratories_pregunta". `tipo`
    determina la estrategia de calificación en `CalificadorDeExamen`
    (Progress, Strategy). `respuesta_hash` nunca expone la respuesta
    correcta en claro (mismo patrón que `Flag.hash`) — para `abierta` se
    hashea el texto normalizado (trim + lower), para `opcion_multiple`
    se hashea el identificador de la opción correcta.
    """

    examen_id: uuid.UUID
    enunciado: str
    tipo: TipoPregunta
    respuesta_hash: str
    opciones: list[str] | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        BaseEntity.__init__(self, id=self.id)
        if self.tipo == TipoPregunta.OPCION_MULTIPLE:
            if not self.opciones or len(self.opciones) < 2:
                raise ValidationError(_OPCIONES_REQUERIDAS_MSG)
        elif self.opciones:
            raise ValidationError(_OPCIONES_NO_PERMITIDAS_MSG)
