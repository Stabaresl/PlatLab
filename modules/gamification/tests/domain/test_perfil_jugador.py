import uuid

from modules.gamification.domain.entities import PerfilJugador


def test_perfil_nuevo_empieza_en_nivel_1_con_0_xp():
    perfil = PerfilJugador(estudiante_id=uuid.uuid4())

    assert perfil.xp == 0
    assert perfil.nivel == 1
    assert perfil.xp_para_siguiente_nivel() == 100


def test_agregar_xp_bajo_el_primer_umbral_no_sube_de_nivel():
    perfil = PerfilJugador(estudiante_id=uuid.uuid4())

    perfil.agregar_xp(50)

    assert perfil.xp == 50
    assert perfil.nivel == 1


def test_agregar_xp_que_alcanza_un_umbral_sube_de_nivel():
    perfil = PerfilJugador(estudiante_id=uuid.uuid4())

    perfil.agregar_xp(100)

    assert perfil.xp == 100
    assert perfil.nivel == 2
    assert perfil.xp_para_siguiente_nivel() == 250


def test_agregar_xp_acumula_a_traves_de_varias_llamadas():
    perfil = PerfilJugador(estudiante_id=uuid.uuid4())

    perfil.agregar_xp(60)
    perfil.agregar_xp(60)

    assert perfil.xp == 120
    assert perfil.nivel == 2


def test_xp_en_el_umbral_maximo_no_tiene_siguiente_nivel():
    perfil = PerfilJugador(estudiante_id=uuid.uuid4())

    perfil.agregar_xp(4000)

    assert perfil.xp_para_siguiente_nivel() is None
