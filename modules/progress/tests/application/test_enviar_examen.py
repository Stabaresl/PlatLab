import uuid

import pytest
from django.contrib.auth.hashers import make_password

from modules.laboratories.domain.entities import Examen, Laboratorio, Pregunta, Seccion
from modules.laboratories.domain.value_objects import (
    EstadoLaboratorio,
    NivelDificultad,
    TipoLaboratorio,
    TipoPregunta,
)
from modules.laboratories.infrastructure.repositories import LaboratorioRepository
from modules.progress.application.dtos import EnviarExamenDTO
from modules.progress.application.use_cases.enviar_examen import EnviarExamenUseCase
from modules.progress.domain.entities import Progreso, ProgresoSeccion
from modules.progress.domain.value_objects import EstadoProgresoSeccion
from modules.progress.infrastructure.repositories import ProgresoRepository
from modules.shared.domain.exceptions import BusinessRuleViolationError, NotFoundError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork


def _crear_lab_con_examen(respuesta_opcion="a", respuesta_abierta="xss"):
    lab_repo = LaboratorioRepository()
    lab = lab_repo.add(
        Laboratorio(
            nombre=f"Lab Examen {uuid.uuid4()}",
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
    examen = lab_repo.add_examen(Examen(laboratorio_id=lab.id))
    pregunta_opcion = lab_repo.add_pregunta(
        Pregunta(
            examen_id=examen.id,
            enunciado="pregunta opcion",
            tipo=TipoPregunta.OPCION_MULTIPLE,
            respuesta_hash=make_password(respuesta_opcion),
            opciones=["a", "b"],
        )
    )
    pregunta_abierta = lab_repo.add_pregunta(
        Pregunta(
            examen_id=examen.id,
            enunciado="pregunta abierta",
            tipo=TipoPregunta.ABIERTA,
            respuesta_hash=make_password(respuesta_abierta),
        )
    )
    return lab, seccion, examen, pregunta_opcion, pregunta_abierta


def _crear_progreso_completado(seccion, estudiante_id=None):
    estudiante_id = estudiante_id or uuid.uuid4()
    progreso_repo = ProgresoRepository()
    asignacion_id = uuid.uuid4()
    progreso = progreso_repo.add(
        Progreso(asignacion_id=asignacion_id, estudiante_id=estudiante_id)
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
    return progreso, estudiante_id


def _build_use_case():
    return EnviarExamenUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        progreso_repository=ProgresoRepository(),
        laboratorio_repository=LaboratorioRepository(),
    )


@pytest.mark.django_db
def test_enviar_examen_calificacion_correcta_100():
    lab, seccion, examen, pregunta_opcion, pregunta_abierta = _crear_lab_con_examen()
    progreso, estudiante_id = _crear_progreso_completado(seccion)

    resultado = _build_use_case().execute(
        EnviarExamenDTO(
            asignacion_id=progreso.asignacion_id,
            estudiante_id=estudiante_id,
            respuestas={
                str(pregunta_opcion.id): "a",
                str(pregunta_abierta.id): "XSS",  # normalizado a lower antes de comparar
            },
        )
    )

    assert resultado.puntaje == 100.0
    assert resultado.correctas == 2
    assert resultado.total == 2
    assert resultado.numero_intento == 1


@pytest.mark.django_db
def test_enviar_examen_calificacion_parcial():
    lab, seccion, examen, pregunta_opcion, pregunta_abierta = _crear_lab_con_examen()
    progreso, estudiante_id = _crear_progreso_completado(seccion)

    resultado = _build_use_case().execute(
        EnviarExamenDTO(
            asignacion_id=progreso.asignacion_id,
            estudiante_id=estudiante_id,
            respuestas={
                str(pregunta_opcion.id): "b",  # incorrecta
                str(pregunta_abierta.id): "xss",
            },
        )
    )

    assert resultado.puntaje == 50.0
    assert resultado.correctas == 1


@pytest.mark.django_db
def test_enviar_examen_reintento_crea_nuevo_intento_sin_perder_historico():
    lab, seccion, examen, pregunta_opcion, pregunta_abierta = _crear_lab_con_examen()
    progreso, estudiante_id = _crear_progreso_completado(seccion)
    dto = EnviarExamenDTO(
        asignacion_id=progreso.asignacion_id,
        estudiante_id=estudiante_id,
        respuestas={str(pregunta_opcion.id): "a", str(pregunta_abierta.id): "xss"},
    )

    primero = _build_use_case().execute(dto)
    segundo = _build_use_case().execute(dto)

    assert primero.numero_intento == 1
    assert segundo.numero_intento == 2

    historial = ProgresoRepository().get_historial(progreso.id)
    resultados = ProgresoRepository().get_resultados_examen(progreso.id)
    assert len(historial) == 2
    assert len(resultados) == 2
    assert historial[0].numero_intento == 1
    assert historial[1].numero_intento == 2


@pytest.mark.django_db
def test_enviar_examen_secciones_incompletas_lanza_business_rule_error():
    lab_repo = LaboratorioRepository()
    lab = lab_repo.add(
        Laboratorio(
            nombre=f"Lab Incompleto {uuid.uuid4()}",
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
    progreso_repo = ProgresoRepository()
    estudiante_id = uuid.uuid4()
    progreso = progreso_repo.add(
        Progreso(asignacion_id=uuid.uuid4(), estudiante_id=estudiante_id)
    )
    progreso_repo.add_secciones(
        [
            ProgresoSeccion(
                progreso_id=progreso.id,
                seccion_id=seccion.id,
                estado=EstadoProgresoSeccion.EN_PROGRESO,
            )
        ]
    )

    with pytest.raises(BusinessRuleViolationError):
        _build_use_case().execute(
            EnviarExamenDTO(
                asignacion_id=progreso.asignacion_id,
                estudiante_id=estudiante_id,
                respuestas={},
            )
        )


@pytest.mark.django_db
def test_enviar_examen_progreso_inexistente_lanza_not_found():
    with pytest.raises(NotFoundError):
        _build_use_case().execute(
            EnviarExamenDTO(
                asignacion_id=uuid.uuid4(),
                estudiante_id=uuid.uuid4(),
                respuestas={},
            )
        )
