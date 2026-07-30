import time
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from django.contrib.auth.hashers import make_password

from modules.assignments.domain.entities import Asignacion
from modules.assignments.domain.value_objects import EstadoAsignacion
from modules.assignments.infrastructure.repositories import AsignacionRepository
from modules.laboratories.domain.entities import Flag, Laboratorio, Seccion
from modules.laboratories.domain.value_objects import (
    EstadoLaboratorio,
    NivelDificultad,
    TipoLaboratorio,
)
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.progress.application.dtos import (
    CompletarSeccionTeoricaDTO,
    EnviarExamenDTO,
    ObtenerProgresoDTO,
    ValidarFlagDTO,
)
from modules.progress.application.queries.obtener_progreso import ObtenerProgresoQuery
from modules.progress.application.use_cases.completar_seccion_teorica import (
    CompletarSeccionTeoricaUseCase,
)
from modules.progress.application.use_cases.enviar_examen import EnviarExamenUseCase
from modules.progress.application.use_cases.validar_flag import ValidarFlagUseCase
from modules.progress.domain.entities import Progreso, ProgresoSeccion
from modules.progress.domain.exceptions import AsignacionVencidaError
from modules.progress.domain.value_objects import EstadoProgresoSeccion
from modules.progress.infrastructure.asignacion_estado_provider import AsignacionEstadoProvider
from modules.progress.infrastructure.repositories import ProgresoRepository
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


def _crear_asignacion_vencida(estudiante_id: uuid.UUID, laboratorio_id: uuid.UUID) -> Asignacion:
    # `fecha_invitacion` es `auto_now_add` (siempre "ahora" al insertar) y
    # ck_asig_vencimiento_posterior exige vencimiento > invitación — para
    # simular una asignación ya vencida sin violar ese constraint, se crea
    # con vencimiento apenas en el futuro y se espera a que quede atrás
    # (mismo patrón que test_cerrar_asignaciones_vencidas.py).
    creada = AsignacionRepository().add(
        Asignacion(
            estudiante_id=estudiante_id,
            laboratorio_id=laboratorio_id,
            estado=EstadoAsignacion.ACTIVA,
            fecha_vencimiento=datetime.now(timezone.utc) + timedelta(milliseconds=200),
        )
    )
    time.sleep(0.3)
    return creada


def _crear_lab_con_seccion_practica(valor_flag: str = "FLAG{correcta}"):
    lab_repo = LaboratorioRepository()
    lab = lab_repo.add(
        Laboratorio(
            nombre=f"Lab Vencido {uuid.uuid4()}",
            descripcion="desc",
            nivel_dificultad=NivelDificultad.BASICO,
            estado=EstadoLaboratorio.PUBLICADO,
            tipo=TipoLaboratorio.PREDETERMINADO,
        )
    )
    seccion = lab_repo.add_seccion(
        Seccion(
            laboratorio_id=lab.id, titulo="Practica", contenido_teorico="...", orden=1,
            tiene_practica=True,
        )
    )
    lab_repo.save_flag(Flag(seccion_id=seccion.id, hash=make_password(valor_flag)))
    return lab, seccion


def _crear_progreso_para(asignacion: Asignacion, seccion, estado=EstadoProgresoSeccion.EN_PROGRESO):
    progreso_repo = ProgresoRepository()
    progreso = progreso_repo.add(
        Progreso(asignacion_id=asignacion.id, estudiante_id=asignacion.estudiante_id)
    )
    progreso_repo.add_secciones(
        [ProgresoSeccion(progreso_id=progreso.id, seccion_id=seccion.id, estado=estado)]
    )
    return progreso


@pytest.mark.django_db
def test_validar_flag_bloqueado_si_asignacion_vencida():
    lab, seccion = _crear_lab_con_seccion_practica()
    estudiante_id = uuid.uuid4()
    asignacion = _crear_asignacion_vencida(estudiante_id, lab.id)
    _crear_progreso_para(asignacion, seccion)

    uc = ValidarFlagUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        progreso_repository=ProgresoRepository(),
        laboratorio_repository=LaboratorioRepository(),
        estado_asignacion_provider=AsignacionEstadoProvider(),
    )

    with pytest.raises(AsignacionVencidaError):
        uc.execute(
            ValidarFlagDTO(
                asignacion_id=asignacion.id,
                seccion_id=seccion.id,
                valor="FLAG{correcta}",
                estudiante_id=estudiante_id,
            )
        )


@pytest.mark.django_db
def test_completar_seccion_teorica_bloqueado_si_asignacion_vencida():
    lab_repo = LaboratorioRepository()
    lab = lab_repo.add(
        Laboratorio(
            nombre=f"Lab Vencido Teorico {uuid.uuid4()}",
            descripcion="desc",
            nivel_dificultad=NivelDificultad.BASICO,
            estado=EstadoLaboratorio.PUBLICADO,
            tipo=TipoLaboratorio.PREDETERMINADO,
        )
    )
    seccion = lab_repo.add_seccion(
        Seccion(laboratorio_id=lab.id, titulo="Intro", contenido_teorico="...", orden=1)
    )
    estudiante_id = uuid.uuid4()
    asignacion = _crear_asignacion_vencida(estudiante_id, lab.id)
    _crear_progreso_para(asignacion, seccion)

    uc = CompletarSeccionTeoricaUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        progreso_repository=ProgresoRepository(),
        laboratorio_repository=LaboratorioRepository(),
        estado_asignacion_provider=AsignacionEstadoProvider(),
    )

    with pytest.raises(AsignacionVencidaError):
        uc.execute(
            CompletarSeccionTeoricaDTO(
                asignacion_id=asignacion.id, seccion_id=seccion.id, estudiante_id=estudiante_id
            )
        )


@pytest.mark.django_db
def test_enviar_examen_bloqueado_si_asignacion_vencida():
    lab, seccion = _crear_lab_con_seccion_practica()
    estudiante_id = uuid.uuid4()
    asignacion = _crear_asignacion_vencida(estudiante_id, lab.id)
    _crear_progreso_para(asignacion, seccion, estado=EstadoProgresoSeccion.COMPLETADA)

    uc = EnviarExamenUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        progreso_repository=ProgresoRepository(),
        laboratorio_repository=LaboratorioRepository(),
        estado_asignacion_provider=AsignacionEstadoProvider(),
    )

    with pytest.raises(AsignacionVencidaError):
        uc.execute(
            EnviarExamenDTO(asignacion_id=asignacion.id, estudiante_id=estudiante_id, respuestas={})
        )


@pytest.mark.django_db
def test_asignacion_estado_provider_detecta_vencimiento_por_fecha_sin_job():
    """
    RF-32: aunque `CerrarAsignacionesVencidasJob` (Celery Beat) todavía no
    haya corrido y el `estado` persistido siga en `activa`, el provider
    debe detectar el vencimiento comparando `fecha_vencimiento` contra
    "ahora" — no confiar solo en el estado ya persistido.
    """
    estudiante_id = uuid.uuid4()
    laboratorio_id = uuid.uuid4()
    asignacion = _crear_asignacion_vencida(estudiante_id, laboratorio_id)
    assert asignacion.estado == EstadoAsignacion.ACTIVA  # el job no corrió

    estado = AsignacionEstadoProvider().obtener_estado(asignacion.id)

    assert estado.vencida is True


@pytest.mark.django_db
def test_obtener_progreso_expone_vencido_y_fecha_vencimiento():
    lab, seccion = _crear_lab_con_seccion_practica()
    estudiante_id = uuid.uuid4()
    asignacion = _crear_asignacion_vencida(estudiante_id, lab.id)
    _crear_progreso_para(asignacion, seccion)

    resultado = ObtenerProgresoQuery(
        progreso_repository=ProgresoRepository(),
        laboratorio_repository=LaboratorioRepository(),
        estado_asignacion_provider=AsignacionEstadoProvider(),
    ).execute(ObtenerProgresoDTO(asignacion_id=asignacion.id, estudiante_id=estudiante_id))

    assert resultado.vencido is True
    assert resultado.fecha_vencimiento == asignacion.fecha_vencimiento
