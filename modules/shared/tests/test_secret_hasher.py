from django.contrib.auth.hashers import make_password

from modules.shared.infrastructure.secret_hasher import hashear_secreto, verificar_secreto


def test_hash_nuevo_verifica_valor_correcto_y_rechaza_incorrecto():
    hash_flag = hashear_secreto("FLAG{correcta}")

    assert hash_flag.startswith("hmac_sha256$")
    assert "FLAG{correcta}" not in hash_flag
    assert verificar_secreto("FLAG{correcta}", hash_flag)
    assert not verificar_secreto("FLAG{incorrecta}", hash_flag)


def test_hash_es_deterministico_para_poder_copiar_flags_al_duplicar():
    assert hashear_secreto("x") == hashear_secreto("x")


def test_sigue_verificando_hashes_pbkdf2_legados():
    """Flags guardadas antes del cambio (make_password) siguen funcionando sin migrar datos."""
    legado = make_password("FLAG{vieja}")

    assert verificar_secreto("FLAG{vieja}", legado)
    assert not verificar_secreto("FLAG{otra}", legado)
