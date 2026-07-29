import uuid

import pytest

from modules.laboratories.domain.entities import Flag, Laboratorio, Seccion
from modules.laboratories.domain.exceptions import OrigenInvalidoParaDuplicarError
from modules.laboratories.domain.services import DuplicadorDeLaboratorio
from modules.laboratories.domain.value_objects import (
    EstadoLaboratorio,
    NivelDificultad,
    TipoLaboratorio,
)


def test_duplicar_predeterminado_crea_copia_personalizado():
    original = Laboratorio(
        nombre="Original",
        descripcion="desc",
        nivel_dificultad=NivelDificultad.BASICO,
        estado=EstadoLaboratorio.PUBLICADO,
        tipo=TipoLaboratorio.PREDETERMINADO,
        temas=["red team"],
    )
    seccion = Seccion(
        laboratorio_id=original.id,
        titulo="Practica",
        contenido_teorico="...",
        orden=1,
        tiene_practica=True,
    )
    flag = Flag(seccion_id=seccion.id, hash="hash-x")
    instructor_id = uuid.uuid4()

    copia, secciones_copiadas, flags_copiadas = DuplicadorDeLaboratorio().duplicar(
        original, [seccion], {seccion.id: flag}, instructor_id
    )

    assert copia.tipo == TipoLaboratorio.PERSONALIZADO
    assert copia.estado == EstadoLaboratorio.BORRADOR
    assert copia.instructor_id == instructor_id
    assert copia.origen_id == original.id
    assert copia.temas == original.temas
    assert len(secciones_copiadas) == 1
    assert secciones_copiadas[0].laboratorio_id == copia.id
    assert secciones_copiadas[0].id != seccion.id
    assert len(flags_copiadas) == 1
    assert flags_copiadas[0].seccion_id == secciones_copiadas[0].id
    assert flags_copiadas[0].hash == flag.hash


def test_duplicar_personalizado_lanza_origen_invalido():
    original = Laboratorio(
        nombre="Personalizado",
        descripcion="desc",
        nivel_dificultad=NivelDificultad.BASICO,
        estado=EstadoLaboratorio.BORRADOR,
        tipo=TipoLaboratorio.PERSONALIZADO,
        instructor_id=uuid.uuid4(),
    )

    with pytest.raises(OrigenInvalidoParaDuplicarError):
        DuplicadorDeLaboratorio().duplicar(original, [], {}, uuid.uuid4())
