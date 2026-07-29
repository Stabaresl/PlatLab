import uuid

import pytest

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
from modules.users.application.dtos import ObtenerDashboardAdminDTO
from modules.users.application.queries.obtener_dashboard_admin import ObtenerDashboardAdminQuery
from modules.users.domain.entities import User
from modules.users.domain.value_objects import Email, Rol
from modules.users.infrastructure.repositories import UserRepository


def _build_query():
    return ObtenerDashboardAdminQuery(
        user_repository=UserRepository(),
        laboratorio_repository=LaboratorioRepository(),
        asignacion_repository=AsignacionRepository(),
        progreso_repository=ProgresoRepository(),
    )


@pytest.mark.django_db
def test_dashboard_admin_agrega_usuarios_por_rol():
    UserRepository().add(
        User(email=Email("inst@uni.edu"), nombre_completo="Inst", rol=Rol.INSTRUCTOR)
    )
    UserRepository().add(
        User(email=Email("est@uni.edu"), nombre_completo="Est", rol=Rol.ESTUDIANTE)
    )

    resultado = _build_query().execute(ObtenerDashboardAdminDTO(actor_rol="administrador"))

    assert resultado.usuarios_por_rol.get("instructor") == 1
    assert resultado.usuarios_por_rol.get("estudiante") == 1


@pytest.mark.django_db
def test_dashboard_admin_cuenta_labs_publicados_y_populares():
    lab_repo = LaboratorioRepository()
    lab = lab_repo.add(
        Laboratorio(
            nombre=f"Lab Dashboard {uuid.uuid4()}",
            descripcion="desc",
            nivel_dificultad=NivelDificultad.BASICO,
            estado=EstadoLaboratorio.PUBLICADO,
            tipo=TipoLaboratorio.PREDETERMINADO,
        )
    )
    seccion = lab_repo.add_seccion(
        Seccion(
            laboratorio_id=lab.id,
            titulo="Seccion 1",
            contenido_teorico="contenido",
            orden=1,
            tiene_practica=True,
        )
    )
    estudiante_id = uuid.uuid4()
    asignacion = AsignacionRepository().add(
        Asignacion(
            estudiante_id=estudiante_id,
            laboratorio_id=lab.id,
            estado=EstadoAsignacion.ACTIVA,
        )
    )
    progreso = ProgresoRepository().add(
        Progreso(asignacion_id=asignacion.id, estudiante_id=estudiante_id)
    )
    ProgresoRepository().add_secciones(
        [
            ProgresoSeccion(
                progreso_id=progreso.id,
                seccion_id=seccion.id,
                estado=EstadoProgresoSeccion.COMPLETADA,
            )
        ]
    )

    resultado = _build_query().execute(ObtenerDashboardAdminDTO(actor_rol="administrador"))

    assert resultado.laboratorios_activos >= 1
    populares = [item for item in resultado.labs_mas_populares if item.laboratorio_id == lab.id]
    assert len(populares) == 1
    assert populares[0].estudiantes_inscritos == 1
    assert resultado.tasa_completitud_promedio == 100.0


@pytest.mark.django_db
def test_dashboard_admin_no_admin_lanza_forbidden():
    with pytest.raises(ForbiddenError):
        _build_query().execute(ObtenerDashboardAdminDTO(actor_rol="instructor"))
