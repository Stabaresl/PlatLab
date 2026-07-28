import uuid

import pytest

from modules.progress.domain.entities import ProgresoSeccion
from modules.progress.domain.exceptions import SeccionNoPerteneceAProgresoError
from modules.progress.domain.services import GestorDeSecuencia, ValidadorDeFlag
from modules.progress.domain.value_objects import ContadorFallos, EstadoProgresoSeccion


def _seccion(progreso_id, estado=EstadoProgresoSeccion.BLOQUEADA):
    return ProgresoSeccion(progreso_id=progreso_id, seccion_id=uuid.uuid4(), estado=estado)


def test_gestor_completa_seccion_y_desbloquea_siguiente():
    progreso_id = uuid.uuid4()
    actual = _seccion(progreso_id, EstadoProgresoSeccion.EN_PROGRESO)
    siguiente = _seccion(progreso_id, EstadoProgresoSeccion.BLOQUEADA)
    secciones = [actual, siguiente]

    modificadas = GestorDeSecuencia().completar_y_desbloquear_siguiente(
        secciones, actual.seccion_id
    )

    assert actual.estado == EstadoProgresoSeccion.COMPLETADA
    assert actual.fecha_completado is not None
    assert siguiente.estado == EstadoProgresoSeccion.EN_PROGRESO
    assert modificadas == [actual, siguiente]


def test_gestor_completa_ultima_seccion_sin_siguiente():
    progreso_id = uuid.uuid4()
    unica = _seccion(progreso_id, EstadoProgresoSeccion.EN_PROGRESO)

    modificadas = GestorDeSecuencia().completar_y_desbloquear_siguiente(
        [unica], unica.seccion_id
    )

    assert unica.estado == EstadoProgresoSeccion.COMPLETADA
    assert modificadas == [unica]


def test_gestor_seccion_inexistente_lanza_error():
    progreso_id = uuid.uuid4()
    secciones = [_seccion(progreso_id)]

    with pytest.raises(SeccionNoPerteneceAProgresoError):
        GestorDeSecuencia().completar_y_desbloquear_siguiente(secciones, uuid.uuid4())


def test_gestor_laboratorio_completado_solo_si_todas_completadas():
    progreso_id = uuid.uuid4()
    todas_completadas = [
        _seccion(progreso_id, EstadoProgresoSeccion.COMPLETADA),
        _seccion(progreso_id, EstadoProgresoSeccion.COMPLETADA),
    ]
    una_pendiente = [
        _seccion(progreso_id, EstadoProgresoSeccion.COMPLETADA),
        _seccion(progreso_id, EstadoProgresoSeccion.EN_PROGRESO),
    ]

    assert GestorDeSecuencia().laboratorio_completado(todas_completadas) is True
    assert GestorDeSecuencia().laboratorio_completado(una_pendiente) is False


def test_validador_intento_correcto_no_incrementa_contador():
    resultado = ValidadorDeFlag().procesar_intento(True, ContadorFallos(total=3))

    assert resultado.correcta is True
    assert resultado.contador.total == 3


def test_validador_intento_fallido_incrementa_contador():
    resultado = ValidadorDeFlag().procesar_intento(False, ContadorFallos(total=3))

    assert resultado.correcta is False
    assert resultado.contador.total == 4


def test_validador_desbloquea_pista_al_quinto_fallo():
    resultado = ValidadorDeFlag().procesar_intento(False, ContadorFallos(total=4))

    assert resultado.contador.total == 5
    assert resultado.pista_desbloqueada is True
    assert resultado.paso_a_paso_desbloqueado is False


def test_validador_desbloquea_paso_a_paso_al_intento_15():
    resultado = ValidadorDeFlag().procesar_intento(False, ContadorFallos(total=14))

    assert resultado.contador.total == 15
    assert resultado.pista_desbloqueada is True
    assert resultado.paso_a_paso_desbloqueado is True
