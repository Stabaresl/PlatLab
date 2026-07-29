import uuid

import pytest

from modules.assignments.application.dtos import InscribirseLaboratorioDTO
from modules.assignments.application.use_cases.inscribirse_laboratorio import (
    InscribirseLaboratorioUseCase,
)
from modules.assignments.infrastructure.repositories import AsignacionRepository
from modules.laboratories.domain.entities import Laboratorio, Seccion
from modules.laboratories.domain.value_objects import (
    EstadoLaboratorio,
    NivelDificultad,
    TipoLaboratorio,
)
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.progress.domain.entities import HistorialCompletitud
from modules.progress.infrastructure.repositories import ProgresoRepository
from modules.shared.domain.exceptions import (
    BusinessRuleViolationError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


def _uc():
    return InscribirseLaboratorioUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        asignacion_repository=AsignacionRepository(),
        laboratorio_repository=LaboratorioRepository(),
        progreso_repository=ProgresoRepository(),
    )


def _crear_lab(repo: LaboratorioRepository, **overrides) -> Laboratorio:
    defaults = dict(
        nombre="Lab Catalogo Inscribible",
        descripcion="desc",
        nivel_dificultad=NivelDificultad.BASICO,
        estado=EstadoLaboratorio.PUBLICADO,
        tipo=TipoLaboratorio.PREDETERMINADO,
        temas=[],
    )
    defaults.update(overrides)
    lab = repo.add(Laboratorio(**defaults))
    repo.add_seccion(Seccion(laboratorio_id=lab.id, titulo="Uno", contenido_teorico="...", orden=1))
    repo.add_seccion(Seccion(laboratorio_id=lab.id, titulo="Dos", contenido_teorico="...", orden=2))
    return lab


@pytest.mark.django_db
def test_inscripcion_exitosa_crea_asignacion_activa_y_progreso():
    repo = LaboratorioRepository()
    lab = _crear_lab(repo)
    estudiante_id = uuid.uuid4()

    resultado = _uc().execute(
        InscribirseLaboratorioDTO(
            laboratorio_id=lab.id, actor_id=estudiante_id, actor_rol="estudiante"
        )
    )

    assert resultado.estado == "activa"
    progreso = ProgresoRepository().get_by_asignacion(resultado.id)
    assert progreso is not None
    assert progreso.estudiante_id == estudiante_id


@pytest.mark.django_db
def test_inscripcion_a_lab_personalizado_lanza_not_found():
    repo = LaboratorioRepository()
    lab = _crear_lab(repo, tipo=TipoLaboratorio.PERSONALIZADO, instructor_id=uuid.uuid4())

    with pytest.raises(NotFoundError):
        _uc().execute(
            InscribirseLaboratorioDTO(
                laboratorio_id=lab.id, actor_id=uuid.uuid4(), actor_rol="estudiante"
            )
        )


@pytest.mark.django_db
def test_inscripcion_a_lab_borrador_lanza_not_found():
    repo = LaboratorioRepository()
    lab = _crear_lab(repo, estado=EstadoLaboratorio.BORRADOR)

    with pytest.raises(NotFoundError):
        _uc().execute(
            InscribirseLaboratorioDTO(
                laboratorio_id=lab.id, actor_id=uuid.uuid4(), actor_rol="estudiante"
            )
        )


@pytest.mark.django_db
def test_inscripcion_actor_no_estudiante_lanza_forbidden():
    repo = LaboratorioRepository()
    lab = _crear_lab(repo)

    with pytest.raises(ForbiddenError):
        _uc().execute(
            InscribirseLaboratorioDTO(
                laboratorio_id=lab.id, actor_id=uuid.uuid4(), actor_rol="instructor"
            )
        )


@pytest.mark.django_db
def test_inscripcion_duplicada_lanza_conflict():
    repo = LaboratorioRepository()
    lab = _crear_lab(repo)
    estudiante_id = uuid.uuid4()
    _uc().execute(
        InscribirseLaboratorioDTO(
            laboratorio_id=lab.id, actor_id=estudiante_id, actor_rol="estudiante"
        )
    )

    with pytest.raises(ConflictError):
        _uc().execute(
            InscribirseLaboratorioDTO(
                laboratorio_id=lab.id, actor_id=estudiante_id, actor_rol="estudiante"
            )
        )


@pytest.mark.django_db
def test_inscripcion_bloqueada_si_tiene_lab_sin_terminar():
    repo = LaboratorioRepository()
    lab_actual = _crear_lab(repo, nombre="Lab En Curso")
    lab_nuevo = _crear_lab(repo, nombre="Lab Nuevo")
    estudiante_id = uuid.uuid4()
    _uc().execute(
        InscribirseLaboratorioDTO(
            laboratorio_id=lab_actual.id, actor_id=estudiante_id, actor_rol="estudiante"
        )
    )

    with pytest.raises(BusinessRuleViolationError):
        _uc().execute(
            InscribirseLaboratorioDTO(
                laboratorio_id=lab_nuevo.id, actor_id=estudiante_id, actor_rol="estudiante"
            )
        )


@pytest.mark.django_db
def test_inscripcion_permitida_si_el_lab_anterior_ya_fue_terminado():
    repo = LaboratorioRepository()
    lab_actual = _crear_lab(repo, nombre="Lab Terminado")
    lab_nuevo = _crear_lab(repo, nombre="Lab Siguiente")
    estudiante_id = uuid.uuid4()
    anterior = _uc().execute(
        InscribirseLaboratorioDTO(
            laboratorio_id=lab_actual.id, actor_id=estudiante_id, actor_rol="estudiante"
        )
    )
    progreso_repo = ProgresoRepository()
    progreso_anterior = progreso_repo.get_by_asignacion(anterior.id)
    progreso_repo.registrar_historial(
        HistorialCompletitud(progreso_id=progreso_anterior.id, numero_intento=1, puntaje=80.0)
    )

    resultado = _uc().execute(
        InscribirseLaboratorioDTO(
            laboratorio_id=lab_nuevo.id, actor_id=estudiante_id, actor_rol="estudiante"
        )
    )

    assert resultado.estado == "activa"
