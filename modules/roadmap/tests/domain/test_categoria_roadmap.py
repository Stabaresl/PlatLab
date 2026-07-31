from modules.roadmap.domain.entities import CategoriaRoadmap


def test_categoria_se_crea_con_orden_por_defecto():
    categoria = CategoriaRoadmap(nombre="Seguridad Web")

    assert categoria.nombre == "Seguridad Web"
    assert categoria.orden == 0
    assert categoria.id is not None


def test_dos_categorias_son_iguales_si_tienen_el_mismo_id():
    import uuid

    id_compartido = uuid.uuid4()
    a = CategoriaRoadmap(id=id_compartido, nombre="A")
    b = CategoriaRoadmap(id=id_compartido, nombre="B")

    assert a == b
