import uuid
from dataclasses import dataclass, field
from datetime import datetime

from modules.laboratories.domain.value_objects import (
    AyudaProgresiva,
    EntornoPractica,
    EstadoLaboratorio,
    NivelDificultad,
    PasoGuia,
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
    # Cierre estilo "Conclusion" de AWS Academy — se muestra al estudiante
    # una vez completadas todas las secciones (dominio.md, ver
    # ProgresoOverviewDTO en Progress).
    resumen_cierre: str = ""
    # Motivo del último rechazo de un admin (`RechazarLaboratorioUseCase`) —
    # visible para el instructor, se limpia al reenviar a revisión
    # (`SolicitarRevisionLaboratorioUseCase`). No hay un estado `rechazado`
    # separado: un rechazo vuelve a `borrador` con este campo poblado.
    motivo_rechazo: str | None = None
    # Opt-in de un `personalizado` al catálogo público (`CambiarVisibilidadCatalogoUseCase`)
    # — lo activa su instructor dueño o un admin, nunca por defecto (un
    # `personalizado` sigue siendo privado/por invitación salvo que alguien
    # decida exponerlo). Sin efecto en un `predeterminado`, que ya es
    # público apenas se publica.
    visible_en_catalogo: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        BaseEntity.__init__(self, id=self.id)

    def es_visible_para(self, instructor_id: uuid.UUID | None = None) -> bool:
        """
        HV-02/HI-01: el catálogo público (y el de estudiante, HE-02)
        muestra laboratorios `predeterminado` + `publicado` siempre, y un
        `personalizado` + `publicado` cuando su instructor (o un admin) lo
        marcó explícitamente como `visible_en_catalogo` — de lo contrario
        sigue siendo privado, solo asignable por invitación. Un instructor
        además ve sus propios laboratorios `personalizado`, sin importar
        el estado (borrador incluido) ni `visible_en_catalogo` — nunca los
        de otro instructor.
        """
        if self.estado == EstadoLaboratorio.PUBLICADO and (
            self.tipo == TipoLaboratorio.PREDETERMINADO or self.visible_en_catalogo
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
    # Objetivos de aprendizaje de la sección (lista corta, estilo AWS
    # Academy) y duración estimada — se muestran como encabezado antes del
    # contenido.
    objetivos: list[str] = field(default_factory=list)
    duracion_estimada_minutos: int = 15
    # Guía paso a paso SIEMPRE disponible (no gatillada por intentos
    # fallidos, a diferencia de `Flag.ayuda.paso_a_paso`) — tareas
    # numeradas discretas en vez de un bloque único de texto, el material
    # de referencia que el estudiante puede dejar abierto mientras
    # resuelve la práctica.
    pasos_guia: list[PasoGuia] = field(default_factory=list)
    entorno_practica: EntornoPractica | None = None
    # Referencia de imagen Docker (ej. "platlab-target-sqli:latest") para el
    # entorno de práctica REAL (lab_environments) — opcional, distinto de
    # `entorno_practica` (consola simulada, siempre disponible sin infra).
    imagen_practica: str | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        BaseEntity.__init__(self, id=self.id)


@dataclass(eq=False)
class DockerfileSeccion(BaseEntity):
    """
    Dockerfile/contexto de build subido por el instructor para el entorno
    real de una `Seccion` práctica — relación 1:1. Nunca se construye
    automáticamente (ver `infrastructure/dockerfile_storage.py`): un admin
    lo revisa y, si confía en el contenido, hace `docker build`/`docker tag`
    a mano fuera de la app y referencia la imagen resultante en
    `Seccion.imagen_practica`.
    """

    seccion_id: uuid.UUID
    archivo_url: str
    nombre_archivo: str
    tamano_kb: int
    created_at: datetime = field(default_factory=datetime.utcnow)
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
