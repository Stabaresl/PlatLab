import uuid

import pytest

from modules.assignments.application.dtos import (
    FiltrarEstudiantesDTO,
    ListarAsignacionesDTO,
    ObtenerDashboardDTO,
)
from modules.assignments.application.queries.filtrar_estudiantes import FiltrarEstudiantesQuery
from modules.assignments.application.queries.listar_asignaciones import ListarAsignacionesQuery
from modules.assignments.application.queries.obtener_dashboard import ObtenerDashboardQuery
from modules.assignments.domain.entities import Asignacion
from modules.assignments.domain.value_objects import EstadoAsignacion
from modules.assignments.infrastructure.repositories import AsignacionRepository
from modules.laboratories.domain.entities import Laboratorio, Seccion
from modules.laboratories.domain.value_objects import (
    EstadoLaboratorio,
    NivelDificultad,
    TipoLaboratorio,
)
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.progress.domain.entities import Progreso, ProgresoSeccion
from modules.progress.domain.value_objects import EstadoProgresoSeccion
from modules.progress.infrastructure.repositories import ProgresoRepository
from modules.shared.domain.exceptions import ForbiddenError
from modules.users.domain.entities import User
from modules.users.domain.value_objects import Email
from modules.users.infrastructure.repositories import UserRepository


def _crear_lab(instructor_id: uuid.UUID) -> Laboratorio:
    return LaboratorioRepository().add(
        Laboratorio(
            nombre="Lab Query",
            descripcion="desc",
            nivel_dificultad=NivelDificultad.BASICO,
            estado=EstadoLaboratorio.PUBLICADO,
            tipo=TipoLaboratorio.PERSONALIZADO,
            instructor_id=instructor_id,
        )
    )


@pytest.mark.django_db
def test_listar_asignaciones_instructor_ve_las_que_creo():
    instructor_id = uuid.uuid4()
    lab = _crear_lab(instructor_id)
    AsignacionRepository().add(
        Asignacion(estudiante_id=uuid.uuid4(), laboratorio_id=lab.id, instructor_id=instructor_id)
    )

    resultado = ListarAsignacionesQuery(AsignacionRepository()).execute(
        ListarAsignacionesDTO(actor_id=instructor_id, actor_rol="instructor")
    )

    assert len(resultado) == 1


@pytest.mark.django_db
def test_listar_asignaciones_estudiante_ve_las_suyas():
    instructor_id = uuid.uuid4()
    estudiante_id = uuid.uuid4()
    lab = _crear_lab(instructor_id)
    AsignacionRepository().add(
        Asignacion(estudiante_id=estudiante_id, laboratorio_id=lab.id, instructor_id=instructor_id)
    )
    AsignacionRepository().add(
        Asignacion(estudiante_id=uuid.uuid4(), laboratorio_id=lab.id, instructor_id=instructor_id)
    )

    resultado = ListarAsignacionesQuery(AsignacionRepository()).execute(
        ListarAsignacionesDTO(actor_id=estudiante_id, actor_rol="estudiante")
    )

    assert len(resultado) == 1
    assert resultado[0].estudiante_id == estudiante_id


@pytest.mark.django_db
def test_filtrar_estudiantes_calcula_porcentaje_completitud():
    instructor_id = uuid.uuid4()
    estudiante = UserRepository().add(
        User(email=Email("filtrado@uni.edu"), nombre_completo="Estudiante Filtrado")
    )
    lab = _crear_lab(instructor_id)
    seccion = LaboratorioRepository().add_seccion(
        Seccion(laboratorio_id=lab.id, titulo="Uno", contenido_teorico="...", orden=1)
    )
    asignacion = AsignacionRepository().add(
        Asignacion(
            estudiante_id=estudiante.id,
            laboratorio_id=lab.id,
            instructor_id=instructor_id,
            estado=EstadoAsignacion.ACTIVA,
        )
    )
    progreso_repo = ProgresoRepository()
    progreso = progreso_repo.add(
        Progreso(asignacion_id=asignacion.id, estudiante_id=estudiante.id)
    )
    progreso_repo.add_secciones(
        [
            ProgresoSeccion(
                progreso_id=progreso.id,
                seccion_id=seccion.id,
                estado=EstadoProgresoSeccion.COMPLETADA,
            )
        ]
    )

    resultado = FiltrarEstudiantesQuery(
        asignacion_repository=AsignacionRepository(),
        user_repository=UserRepository(),
        progreso_repository=progreso_repo,
    ).execute(FiltrarEstudiantesDTO(instructor_id=instructor_id, actor_rol="instructor"))

    assert len(resultado) == 1
    assert resultado[0].porcentaje_completitud == 100.0


@pytest.mark.django_db
def test_filtrar_estudiantes_rol_no_instructor_lanza_forbidden():
    with pytest.raises(ForbiddenError):
        FiltrarEstudiantesQuery(
            asignacion_repository=AsignacionRepository(),
            user_repository=UserRepository(),
            progreso_repository=ProgresoRepository(),
        ).execute(FiltrarEstudiantesDTO(instructor_id=uuid.uuid4(), actor_rol="estudiante"))


@pytest.mark.django_db
def test_obtener_dashboard_solo_labs_propios_con_metricas():
    instructor_id = uuid.uuid4()
    lab_propio = _crear_lab(instructor_id)
    seccion = LaboratorioRepository().add_seccion(
        Seccion(laboratorio_id=lab_propio.id, titulo="Uno", contenido_teorico="...", orden=1)
    )
    estudiante_id = uuid.uuid4()
    asignacion = AsignacionRepository().add(
        Asignacion(
            estudiante_id=estudiante_id,
            laboratorio_id=lab_propio.id,
            instructor_id=instructor_id,
            estado=EstadoAsignacion.ACTIVA,
        )
    )
    progreso_repo = ProgresoRepository()
    progreso = progreso_repo.add(
        Progreso(asignacion_id=asignacion.id, estudiante_id=estudiante_id)
    )
    progreso_repo.add_secciones(
        [
            ProgresoSeccion(
                progreso_id=progreso.id,
                seccion_id=seccion.id,
                estado=EstadoProgresoSeccion.COMPLETADA,
            )
        ]
    )

    resultado = ObtenerDashboardQuery(
        laboratorio_repository=LaboratorioRepository(),
        asignacion_repository=AsignacionRepository(),
        progreso_repository=progreso_repo,
    ).execute(ObtenerDashboardDTO(instructor_id=instructor_id, actor_rol="instructor"))

    assert len(resultado) == 1
    item = resultado[0]
    assert item.laboratorio_id == lab_propio.id
    assert item.estudiantes_inscritos == 1
    assert item.porcentaje_completitud_promedio == 100.0


@pytest.mark.django_db
def test_obtener_dashboard_rol_no_instructor_lanza_forbidden():
    with pytest.raises(ForbiddenError):
        ObtenerDashboardQuery(
            laboratorio_repository=LaboratorioRepository(),
            asignacion_repository=AsignacionRepository(),
            progreso_repository=ProgresoRepository(),
        ).execute(ObtenerDashboardDTO(instructor_id=uuid.uuid4(), actor_rol="administrador"))
