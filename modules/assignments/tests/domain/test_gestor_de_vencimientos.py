import uuid
from datetime import datetime, timedelta, timezone

import pytest

from modules.assignments.domain.entities import Asignacion
from modules.assignments.domain.services import GestorDeVencimientos
from modules.assignments.domain.value_objects import EstadoAsignacion, VentanaVencimiento
from modules.shared.domain.exceptions import ValidationError


def _asignacion_activa(fecha_vencimiento=None):
    return Asignacion(
        estudiante_id=uuid.uuid4(),
        laboratorio_id=uuid.uuid4(),
        estado=EstadoAsignacion.ACTIVA,
        fecha_vencimiento=fecha_vencimiento,
    )


def test_ventana_vencimiento_sin_timezone_lanza_validation_error():
    with pytest.raises(ValidationError):
        VentanaVencimiento(fecha=datetime.now())


def test_ventana_vencimiento_ya_vencio_true_si_fecha_pasada():
    ventana = VentanaVencimiento(fecha=datetime.now(timezone.utc) - timedelta(days=1))
    assert ventana.ya_vencio() is True


def test_ventana_vencimiento_ya_vencio_false_si_fecha_futura():
    ventana = VentanaVencimiento(fecha=datetime.now(timezone.utc) + timedelta(days=1))
    assert ventana.ya_vencio() is False


def test_gestor_identifica_vencidas_y_las_marca():
    ahora = datetime.now(timezone.utc)
    vencida = _asignacion_activa(fecha_vencimiento=ahora - timedelta(minutes=1))
    vigente = _asignacion_activa(fecha_vencimiento=ahora + timedelta(days=1))
    sin_vencimiento = _asignacion_activa(fecha_vencimiento=None)

    resultado = GestorDeVencimientos().identificar_vencidas(
        [vencida, vigente, sin_vencimiento], ahora=ahora
    )

    assert resultado == [vencida]
    assert vencida.estado == EstadoAsignacion.VENCIDA
    assert vigente.estado == EstadoAsignacion.ACTIVA
    assert sin_vencimiento.estado == EstadoAsignacion.ACTIVA


def test_gestor_no_identifica_nada_si_ninguna_vencio():
    ahora = datetime.now(timezone.utc)
    vigente = _asignacion_activa(fecha_vencimiento=ahora + timedelta(days=1))

    resultado = GestorDeVencimientos().identificar_vencidas([vigente], ahora=ahora)

    assert resultado == []
