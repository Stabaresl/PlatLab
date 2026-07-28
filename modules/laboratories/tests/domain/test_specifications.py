from modules.laboratories.domain.specifications import PorDificultad, PorTema


def test_por_dificultad_agrega_filtro():
    filtros = PorDificultad("avanzado").aplicar({})
    assert filtros == {"nivel_dificultad": "avanzado"}


def test_por_tema_agrega_filtro():
    filtros = PorTema("redes").aplicar({})
    assert filtros == {"tema": "redes"}


def test_especificaciones_combinables_con_and():
    especificacion = PorDificultad("avanzado") & PorTema("redes")

    filtros = especificacion.aplicar({})

    assert filtros == {"nivel_dificultad": "avanzado", "tema": "redes"}
