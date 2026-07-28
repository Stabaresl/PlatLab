from modules.progress.domain.value_objects import ContadorFallos


def test_contador_fallos_inicial_no_muestra_ayuda():
    contador = ContadorFallos()

    assert contador.total == 0
    assert contador.debe_mostrar_pista is False
    assert contador.debe_mostrar_paso_a_paso is False


def test_contador_fallos_incrementar_es_inmutable():
    contador = ContadorFallos(total=2)

    siguiente = contador.incrementar()

    assert contador.total == 2
    assert siguiente.total == 3


def test_contador_fallos_desbloquea_pista_a_los_5():
    assert ContadorFallos(total=4).debe_mostrar_pista is False
    assert ContadorFallos(total=5).debe_mostrar_pista is True
    assert ContadorFallos(total=10).debe_mostrar_pista is True


def test_contador_fallos_desbloquea_paso_a_paso_a_los_15():
    assert ContadorFallos(total=14).debe_mostrar_paso_a_paso is False
    assert ContadorFallos(total=15).debe_mostrar_paso_a_paso is True
