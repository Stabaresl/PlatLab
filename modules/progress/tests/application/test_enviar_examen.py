import uuid
from datetime import timedelta

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
from modules.progress.application.dtos import EnviarExamenDTO, IniciarExamenDTO, ObtenerExamenDTO
from modules.progress.application.queries.obtener_examen import ObtenerExamenQuery
from modules.progress.application.use_cases.enviar_examen import EnviarExamenUseCase
from modules.progress.application.use_cases.iniciar_examen import IniciarExamenUseCase
from modules.progress.domain.entities import Progreso, ProgresoSeccion
from modules.progress.domain.exceptions import ExamenNoIniciadoError
from modules.progress.domain.value_objects import EstadoProgresoSeccion
from modules.progress.infrastructure.models import ProgresoModel, ResultadoExamenModel
from modules.progress.infrastructure.repositories import ProgresoRepository
from modules.shared.domain.exceptions import BusinessRuleViolationError, NotFoundError
from modules.shared.domain.tiempo import ahora_utc
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


def _iniciar(progreso, estudiante_id):
    return IniciarExamenUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        progreso_repository=ProgresoRepository(),
        laboratorio_repository=LaboratorioRepository(),
    ).execute(IniciarExamenDTO(asignacion_id=progreso.asignacion_id, estudiante_id=estudiante_id))


def _estado(progreso, estudiante_id):
    return ObtenerExamenQuery(ProgresoRepository(), LaboratorioRepository()).execute(
        ObtenerExamenDTO(asignacion_id=progreso.asignacion_id, estudiante_id=estudiante_id)
    )


def _presentar(progreso, estudiante_id, respuestas):
    _iniciar(progreso, estudiante_id)
    return _build_use_case().execute(
        EnviarExamenDTO(asignacion_id=progreso.asignacion_id, estudiante_id=estudiante_id, respuestas=respuestas)
    )


@pytest.mark.django_db
def test_enviar_examen_calificacion_correcta_100():
    lab, seccion, examen, pregunta_opcion, pregunta_abierta = _crear_lab_con_examen()
    progreso, estudiante_id = _crear_progreso_completado(seccion)

    resultado = _presentar(
        progreso,
        estudiante_id,
        {
            str(pregunta_opcion.id): "a",
            str(pregunta_abierta.id): "XSS",  # normalizado a lower antes de comparar
        },
    )

    assert resultado.puntaje == 100.0
    assert resultado.correctas == 2
    assert resultado.total == 2
    assert resultado.numero_intento == 1
    assert resultado.aprobado is True
    assert resultado.estado.aprobado is True
    assert resultado.estado.intento_abierto is False


@pytest.mark.django_db
def test_enviar_examen_calificacion_parcial():
    lab, seccion, examen, pregunta_opcion, pregunta_abierta = _crear_lab_con_examen()
    progreso, estudiante_id = _crear_progreso_completado(seccion)

    resultado = _presentar(
        progreso,
        estudiante_id,
        {str(pregunta_opcion.id): "b", str(pregunta_abierta.id): "xss"},  # una incorrecta
    )

    assert resultado.puntaje == 50.0
    assert resultado.correctas == 1
    assert resultado.aprobado is False
    assert resultado.estado.intentos_restantes == 2


@pytest.mark.django_db
def test_enviar_examen_reintento_crea_nuevo_intento_sin_perder_historico():
    lab, seccion, examen, pregunta_opcion, pregunta_abierta = _crear_lab_con_examen()
    progreso, estudiante_id = _crear_progreso_completado(seccion)
    respuestas = {str(pregunta_opcion.id): "a", str(pregunta_abierta.id): "xss"}

    primero = _presentar(progreso, estudiante_id, respuestas)
    segundo = _presentar(progreso, estudiante_id, respuestas)

    assert primero.numero_intento == 1
    assert segundo.numero_intento == 2

    historial = ProgresoRepository().get_historial(progreso.id)
    resultados = ProgresoRepository().get_resultados_examen(progreso.id)
    assert len(historial) == 2
    assert len(resultados) == 2
    assert historial[0].numero_intento == 1
    assert historial[1].numero_intento == 2


@pytest.mark.django_db
def test_enviar_sin_iniciar_el_examen_no_se_acepta():
    lab, seccion, examen, pregunta_opcion, pregunta_abierta = _crear_lab_con_examen()
    progreso, estudiante_id = _crear_progreso_completado(seccion)

    with pytest.raises(ExamenNoIniciadoError):
        _build_use_case().execute(
            EnviarExamenDTO(asignacion_id=progreso.asignacion_id, estudiante_id=estudiante_id, respuestas={})
        )


@pytest.mark.django_db
def test_entregar_dos_veces_el_mismo_intento_no_cuenta_doble():
    lab, seccion, examen, pregunta_opcion, pregunta_abierta = _crear_lab_con_examen()
    progreso, estudiante_id = _crear_progreso_completado(seccion)
    _presentar(progreso, estudiante_id, {str(pregunta_opcion.id): "a"})

    with pytest.raises(ExamenNoIniciadoError):
        _build_use_case().execute(
            EnviarExamenDTO(asignacion_id=progreso.asignacion_id, estudiante_id=estudiante_id, respuestas={})
        )
    assert len(ProgresoRepository().get_resultados_examen(progreso.id)) == 1


@pytest.mark.django_db
def test_iniciar_entrega_preguntas_sin_respuesta():
    lab, seccion, examen, pregunta_opcion, pregunta_abierta = _crear_lab_con_examen()
    progreso, estudiante_id = _crear_progreso_completado(seccion)

    inicio = _iniciar(progreso, estudiante_id)

    assert inicio.iniciado is True
    assert {p.id for p in inicio.preguntas} == {pregunta_opcion.id, pregunta_abierta.id}
    assert not any(hasattr(p, "respuesta_hash") for p in inicio.preguntas)
    assert inicio.estado.intentos_restantes == 3
    assert ProgresoModel.objects.get(id=progreso.id).examen_iniciado_en is not None


@pytest.mark.django_db
def test_salir_sin_entregar_cuenta_como_intento_reprobado():
    lab, seccion, examen, pregunta_opcion, pregunta_abierta = _crear_lab_con_examen()
    progreso, estudiante_id = _crear_progreso_completado(seccion)
    _iniciar(progreso, estudiante_id)

    # Al volver (recargó, cerró la pestaña…), el estado ya cuenta ese intento.
    estado = _estado(progreso, estudiante_id)
    assert estado.intento_abierto is True
    assert estado.intentos_restantes == 2

    reinicio = _iniciar(progreso, estudiante_id)
    assert reinicio.abandono_cerrado is True
    assert reinicio.iniciado is True
    resultados = ProgresoRepository().get_resultados_examen(progreso.id)
    assert [float(r.puntaje) for r in resultados] == [0.0]


@pytest.mark.django_db
def test_tres_reprobados_bloquean_24_horas():
    lab, seccion, examen, pregunta_opcion, pregunta_abierta = _crear_lab_con_examen()
    progreso, estudiante_id = _crear_progreso_completado(seccion)
    mal = {str(pregunta_opcion.id): "b"}

    _presentar(progreso, estudiante_id, mal)
    _presentar(progreso, estudiante_id, mal)
    tercero = _presentar(progreso, estudiante_id, mal)

    assert tercero.estado.intentos_restantes == 0
    bloqueado_hasta = tercero.estado.bloqueado_hasta
    assert bloqueado_hasta is not None
    assert timedelta(hours=23, minutes=59) < bloqueado_hasta - ahora_utc() <= timedelta(hours=24)

    cuarto = _iniciar(progreso, estudiante_id)
    assert cuarto.iniciado is False
    assert cuarto.preguntas == []
    assert ProgresoModel.objects.get(id=progreso.id).examen_iniciado_en is None


@pytest.mark.django_db
def test_pasadas_24_horas_vuelven_los_tres_intentos():
    lab, seccion, examen, pregunta_opcion, pregunta_abierta = _crear_lab_con_examen()
    progreso, estudiante_id = _crear_progreso_completado(seccion)
    mal = {str(pregunta_opcion.id): "b"}
    for _ in range(3):
        _presentar(progreso, estudiante_id, mal)

    ResultadoExamenModel.objects.filter(progreso_id=progreso.id).update(fecha=ahora_utc() - timedelta(hours=25))

    inicio = _iniciar(progreso, estudiante_id)
    assert inicio.iniciado is True
    assert inicio.estado.intentos_restantes == 3


@pytest.mark.django_db
def test_aprobar_reinicia_la_cuenta_de_intentos():
    lab, seccion, examen, pregunta_opcion, pregunta_abierta = _crear_lab_con_examen()
    progreso, estudiante_id = _crear_progreso_completado(seccion)
    mal = {str(pregunta_opcion.id): "b"}
    bien = {str(pregunta_opcion.id): "a", str(pregunta_abierta.id): "xss"}

    _presentar(progreso, estudiante_id, mal)
    _presentar(progreso, estudiante_id, mal)
    aprobado = _presentar(progreso, estudiante_id, bien)

    assert aprobado.estado.aprobado is True
    assert aprobado.estado.intentos_restantes == 3
    assert aprobado.estado.bloqueado_hasta is None


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
    with pytest.raises(BusinessRuleViolationError):
        _iniciar(progreso, estudiante_id)


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
