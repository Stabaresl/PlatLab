import uuid
from dataclasses import dataclass, field
from datetime import datetime

from modules.laboratories.domain.value_objects import (
    EstadoLaboratorio,
    NivelDificultad,
    TipoLaboratorio,
)
from modules.shared.domain.base_entity import BaseEntity


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
