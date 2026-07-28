import pytest

from modules.authentication.domain.exceptions import AccountLinkingRequiresConfirmationError
from modules.authentication.domain.services import VinculadorDeCuenta
from modules.users.domain.entities import User
from modules.users.domain.value_objects import Email


def test_permite_vincular_si_no_existe_usuario_previo():
    VinculadorDeCuenta().validar_vinculacion(usuario_existente=None)  # no lanza


def test_rechaza_vinculacion_automatica_si_ya_existe_usuario_con_ese_email():
    usuario = User(email=Email("colision@uni.edu"), nombre_completo="Colision Test")

    with pytest.raises(AccountLinkingRequiresConfirmationError):
        VinculadorDeCuenta().validar_vinculacion(usuario_existente=usuario)
