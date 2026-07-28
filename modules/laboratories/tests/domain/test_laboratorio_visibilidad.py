import uuid

from modules.laboratories.domain.entities import Laboratorio
from modules.laboratories.domain.value_objects import (
    EstadoLaboratorio,
    NivelDificultad,
    TipoLaboratorio,
)


def _lab(**overrides) -> Laboratorio:
    defaults = dict(
        nombre="Lab Test",
        descripcion="desc",
        nivel_dificultad=NivelDificultad.BASICO,
        estado=EstadoLaboratorio.PUBLICADO,
        tipo=TipoLaboratorio.PREDETERMINADO,
    )
    defaults.update(overrides)
    return Laboratorio(**defaults)


def test_predeterminado_publicado_es_visible_para_cualquiera():
    lab = _lab()

    assert lab.es_visible_para(None) is True
    assert lab.es_visible_para(uuid.uuid4()) is True


def test_predeterminado_borrador_no_es_visible_para_nadie():
    lab = _lab(estado=EstadoLaboratorio.BORRADOR)

    assert lab.es_visible_para(None) is False
    assert lab.es_visible_para(uuid.uuid4()) is False


def test_personalizado_borrador_visible_solo_para_su_instructor():
    instructor_id = uuid.uuid4()
    lab = _lab(
        estado=EstadoLaboratorio.BORRADOR,
        tipo=TipoLaboratorio.PERSONALIZADO,
        instructor_id=instructor_id,
    )

    assert lab.es_visible_para(instructor_id) is True
    assert lab.es_visible_para(uuid.uuid4()) is False
    assert lab.es_visible_para(None) is False


def test_personalizado_publicado_no_es_visible_para_publico():
    lab = _lab(
        estado=EstadoLaboratorio.PUBLICADO,
        tipo=TipoLaboratorio.PERSONALIZADO,
        instructor_id=uuid.uuid4(),
    )

    assert lab.es_visible_para(None) is False
