import uuid

import pytest

from modules.roadmap.domain.entities import NodoRoadmap
from modules.roadmap.domain.exceptions import PosicionInvalidaError


def test_nodo_se_crea_con_posicion_valida():
    nodo = NodoRoadmap(categoria_id=uuid.uuid4(), laboratorio_id=uuid.uuid4(), posicion=0)

    assert nodo.posicion == 0
    assert nodo.id is not None


def test_nodo_con_posicion_negativa_lanza_error():
    with pytest.raises(PosicionInvalidaError):
        NodoRoadmap(categoria_id=uuid.uuid4(), laboratorio_id=uuid.uuid4(), posicion=-1)
