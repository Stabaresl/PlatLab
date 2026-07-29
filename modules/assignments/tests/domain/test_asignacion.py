import uuid

from modules.assignments.domain.entities import Asignacion
from modules.assignments.domain.value_objects import EstadoAsignacion


def _nueva_asignacion() -> Asignacion:
    return Asignacion(estudiante_id=uuid.uuid4(), laboratorio_id=uuid.uuid4())


def test_asignacion_nace_pendiente_y_vigente():
    asignacion = _nueva_asignacion()

    assert asignacion.estado == EstadoAsignacion.PENDIENTE
    assert asignacion.esta_vigente() is True


def test_aceptar_transiciona_directo_a_activa():
    asignacion = _nueva_asignacion()

    asignacion.aceptar()

    assert asignacion.estado == EstadoAsignacion.ACTIVA
    assert asignacion.fecha_respuesta is not None
    assert asignacion.esta_vigente() is True


def test_rechazar_transiciona_a_rechazada_y_deja_de_ser_vigente():
    asignacion = _nueva_asignacion()

    asignacion.rechazar()

    assert asignacion.estado == EstadoAsignacion.RECHAZADA
    assert asignacion.fecha_respuesta is not None
    assert asignacion.esta_vigente() is False
