import uuid

import pytest

from modules.assignments.domain.entities import Asignacion
from modules.assignments.infrastructure.repositories import AsignacionRepository
from modules.laboratories.domain.entities import Laboratorio
from modules.laboratories.domain.value_objects import (
    EstadoLaboratorio,
    NivelDificultad,
    TipoLaboratorio,
)
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.progress.domain.entities import HistorialCompletitud, Progreso
from modules.progress.infrastructure.repositories import ProgresoRepository
from modules.roadmap.application.dtos import AgregarNodoDTO, InscribirseRoadmapDTO
from modules.roadmap.application.use_cases.agregar_nodo import AgregarNodoUseCase
from modules.roadmap.application.use_cases.inscribirse_roadmap import InscribirseRoadmapUseCase
from modules.roadmap.domain.entities import CategoriaRoadmap
from modules.roadmap.infrastructure.repositories import (
    CategoriaRoadmapRepository,
    NodoRoadmapRepository,
)
from modules.shared.domain.exceptions import (
    BusinessRuleViolationError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


def _agregar_uc():
    return AgregarNodoUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        categoria_repository=CategoriaRoadmapRepository(),
        nodo_repository=NodoRoadmapRepository(),
        laboratorio_repository=LaboratorioRepository(),
    )


def _uc():
    return InscribirseRoadmapUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        nodo_repository=NodoRoadmapRepository(),
        asignacion_repository=AsignacionRepository(),
        laboratorio_repository=LaboratorioRepository(),
        progreso_repository=ProgresoRepository(),
    )


def _crear_categoria():
    return CategoriaRoadmapRepository().add(CategoriaRoadmap(nombre=f"Cat {uuid.uuid4()}"))


def _crear_lab(**overrides) -> Laboratorio:
    defaults = dict(
        nombre=f"Lab {uuid.uuid4()}",
        descripcion="desc",
        nivel_dificultad=NivelDificultad.BASICO,
        estado=EstadoLaboratorio.PUBLICADO,
        tipo=TipoLaboratorio.PREDETERMINADO,
    )
    defaults.update(overrides)
    return LaboratorioRepository().add(Laboratorio(**defaults))


def _completar_laboratorio_para(estudiante_id, laboratorio_id):
    """Simula que el estudiante ya completó `laboratorio_id` (fuera del roadmap, ej. vía catálogo)."""
    asignacion_repo = AsignacionRepository()
    progreso_repo = ProgresoRepository()
    asignacion = asignacion_repo.add(
        Asignacion(estudiante_id=estudiante_id, laboratorio_id=laboratorio_id)
    )
    asignacion.aceptar()
    asignacion_repo.update(asignacion)
    progreso = progreso_repo.add(
        Progreso(asignacion_id=asignacion.id, estudiante_id=estudiante_id)
    )
    progreso_repo.registrar_historial(
        HistorialCompletitud(progreso_id=progreso.id, numero_intento=1, puntaje=90.0)
    )


@pytest.mark.django_db
def test_primer_nodo_de_la_pista_no_tiene_prerequisitos():
    categoria = _crear_categoria()
    lab = _crear_lab()
    nodo = _agregar_uc().execute(
        AgregarNodoDTO(categoria.id, lab.id, 0, uuid.uuid4(), "administrador")
    )
    estudiante_id = uuid.uuid4()

    resultado = _uc().execute(
        InscribirseRoadmapDTO(nodo.id, estudiante_id, "estudiante")
    )

    assert resultado.estado == "activa"
    assert resultado.laboratorio_id == lab.id


@pytest.mark.django_db
def test_segundo_nodo_bloqueado_si_no_completo_el_primero():
    categoria = _crear_categoria()
    lab_a, lab_b = _crear_lab(), _crear_lab()
    _agregar_uc().execute(AgregarNodoDTO(categoria.id, lab_a.id, 0, uuid.uuid4(), "administrador"))
    nodo_b = _agregar_uc().execute(
        AgregarNodoDTO(categoria.id, lab_b.id, 1, uuid.uuid4(), "administrador")
    )
    estudiante_id = uuid.uuid4()

    with pytest.raises(BusinessRuleViolationError):
        _uc().execute(InscribirseRoadmapDTO(nodo_b.id, estudiante_id, "estudiante"))


@pytest.mark.django_db
def test_segundo_nodo_disponible_tras_completar_el_primero():
    categoria = _crear_categoria()
    lab_a, lab_b = _crear_lab(), _crear_lab()
    _agregar_uc().execute(AgregarNodoDTO(categoria.id, lab_a.id, 0, uuid.uuid4(), "administrador"))
    nodo_b = _agregar_uc().execute(
        AgregarNodoDTO(categoria.id, lab_b.id, 1, uuid.uuid4(), "administrador")
    )
    estudiante_id = uuid.uuid4()
    _completar_laboratorio_para(estudiante_id, lab_a.id)

    resultado = _uc().execute(InscribirseRoadmapDTO(nodo_b.id, estudiante_id, "estudiante"))

    assert resultado.estado == "activa"


@pytest.mark.django_db
def test_tercer_nodo_requiere_los_dos_anteriores_completos():
    categoria = _crear_categoria()
    lab_a, lab_b, lab_c = _crear_lab(), _crear_lab(), _crear_lab()
    _agregar_uc().execute(AgregarNodoDTO(categoria.id, lab_a.id, 0, uuid.uuid4(), "administrador"))
    _agregar_uc().execute(AgregarNodoDTO(categoria.id, lab_b.id, 1, uuid.uuid4(), "administrador"))
    nodo_c = _agregar_uc().execute(
        AgregarNodoDTO(categoria.id, lab_c.id, 2, uuid.uuid4(), "administrador")
    )
    estudiante_id = uuid.uuid4()
    _completar_laboratorio_para(estudiante_id, lab_a.id)
    # Solo completó el primero, falta el segundo -> el tercero sigue bloqueado.

    with pytest.raises(BusinessRuleViolationError):
        _uc().execute(InscribirseRoadmapDTO(nodo_c.id, estudiante_id, "estudiante"))

    _completar_laboratorio_para(estudiante_id, lab_b.id)
    resultado = _uc().execute(InscribirseRoadmapDTO(nodo_c.id, estudiante_id, "estudiante"))
    assert resultado.estado == "activa"


@pytest.mark.django_db
def test_no_aplica_limite_de_un_solo_laboratorio_en_curso():
    """A diferencia del catálogo viejo, el roadmap no bloquea por tener otro lab activo."""
    categoria = _crear_categoria()
    lab_a, lab_b = _crear_lab(), _crear_lab()
    nodo_a = _agregar_uc().execute(
        AgregarNodoDTO(categoria.id, lab_a.id, 0, uuid.uuid4(), "administrador")
    )
    nodo_b_categoria = _crear_categoria()
    nodo_b = _agregar_uc().execute(
        AgregarNodoDTO(nodo_b_categoria.id, lab_b.id, 0, uuid.uuid4(), "administrador")
    )
    estudiante_id = uuid.uuid4()

    _uc().execute(InscribirseRoadmapDTO(nodo_a.id, estudiante_id, "estudiante"))
    # Todavía no terminó lab_a, pero lab_b es el primer nodo de OTRA pista -> igual debe poder.
    resultado = _uc().execute(InscribirseRoadmapDTO(nodo_b.id, estudiante_id, "estudiante"))

    assert resultado.estado == "activa"


@pytest.mark.django_db
def test_instructor_no_puede_inscribirse():
    categoria = _crear_categoria()
    lab = _crear_lab()
    nodo = _agregar_uc().execute(
        AgregarNodoDTO(categoria.id, lab.id, 0, uuid.uuid4(), "administrador")
    )

    with pytest.raises(ForbiddenError):
        _uc().execute(InscribirseRoadmapDTO(nodo.id, uuid.uuid4(), "instructor"))


@pytest.mark.django_db
def test_nodo_inexistente_lanza_not_found():
    with pytest.raises(NotFoundError):
        _uc().execute(InscribirseRoadmapDTO(uuid.uuid4(), uuid.uuid4(), "estudiante"))


@pytest.mark.django_db
def test_inscripcion_duplicada_lanza_conflict():
    categoria = _crear_categoria()
    lab = _crear_lab()
    nodo = _agregar_uc().execute(
        AgregarNodoDTO(categoria.id, lab.id, 0, uuid.uuid4(), "administrador")
    )
    estudiante_id = uuid.uuid4()
    _uc().execute(InscribirseRoadmapDTO(nodo.id, estudiante_id, "estudiante"))

    with pytest.raises(ConflictError):
        _uc().execute(InscribirseRoadmapDTO(nodo.id, estudiante_id, "estudiante"))
