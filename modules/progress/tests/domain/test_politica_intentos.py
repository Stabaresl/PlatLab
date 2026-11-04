from datetime import datetime, timedelta, timezone

from modules.progress.domain.services import PoliticaDeIntentosExamen

T0 = datetime(2026, 11, 4, 10, 0, tzinfo=timezone.utc)


def _evaluar(puntajes_y_minutos, ahora):
    intentos = [(T0 + timedelta(minutes=m), p) for p, m in puntajes_y_minutos]
    return PoliticaDeIntentosExamen().evaluar(intentos, ahora)


def test_sin_intentos_quedan_tres():
    estado = _evaluar([], T0)
    assert estado.intentos_restantes == 3
    assert estado.bloqueado_hasta is None
    assert estado.aprobado is False
    assert estado.mejor_puntaje is None


def test_dos_reprobados_dejan_uno():
    estado = _evaluar([(20, 0), (40, 5)], T0 + timedelta(minutes=10))
    assert estado.intentos_restantes == 1
    assert estado.bloqueado_hasta is None


def test_tres_reprobados_bloquean_24_horas_desde_el_ultimo():
    estado = _evaluar([(20, 0), (40, 5), (59.9, 10)], T0 + timedelta(minutes=11))
    assert estado.intentos_restantes == 0
    assert estado.bloqueado_hasta == T0 + timedelta(minutes=10, hours=24)
    assert estado.bloqueado


def test_cumplida_la_espera_vuelven_tres():
    estado = _evaluar([(20, 0), (40, 5), (50, 10)], T0 + timedelta(hours=24, minutes=10))
    assert estado.intentos_restantes == 3
    assert estado.bloqueado_hasta is None


def test_tras_la_espera_el_ciclo_nuevo_cuenta_desde_cero():
    # 3 reprobados, espera cumplida, 1 reprobado más: quedan 2 (no se arrastra el ciclo viejo).
    estado = _evaluar([(20, 0), (40, 5), (50, 10), (10, 60 * 25)], T0 + timedelta(hours=26))
    assert estado.intentos_restantes == 2
    assert estado.bloqueado_hasta is None


def test_aprobar_reinicia_la_cuenta():
    estado = _evaluar([(20, 0), (40, 5), (60, 10), (30, 15)], T0 + timedelta(minutes=20))
    assert estado.aprobado is True
    assert estado.intentos_restantes == 2
    assert estado.mejor_puntaje == 60
