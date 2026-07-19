import uuid

import pytest

from modules.authentication.infrastructure.jwt_service import JWTService
from modules.shared.domain.exceptions import UnauthenticatedError


def test_generate_token_pair_returns_access_and_refresh():
    service = JWTService()
    user_id = uuid.uuid4()

    tokens = service.generate_token_pair(user_id=user_id, rol="estudiante")

    assert tokens.access
    assert tokens.refresh
    assert tokens.access != tokens.refresh
    assert tokens.expires_in == 15 * 60
    assert tokens.rol == "estudiante"


def test_decode_access_token_returns_expected_claims():
    service = JWTService()
    user_id = uuid.uuid4()

    tokens = service.generate_token_pair(user_id=user_id, rol="instructor")
    claims = service.decode_access_token(tokens.access)

    assert claims["sub"] == str(user_id)
    assert claims["rol"] == "instructor"
    assert "jti" in claims
    assert "exp" in claims


def test_decode_refresh_token_returns_expected_claims():
    service = JWTService()
    user_id = uuid.uuid4()

    tokens = service.generate_token_pair(user_id=user_id, rol="administrador")
    claims = service.decode_refresh_token(tokens.refresh)

    assert claims["sub"] == str(user_id)
    assert claims["rol"] == "administrador"


def test_decode_access_token_rejects_garbage_token():
    service = JWTService()

    with pytest.raises(UnauthenticatedError):
        service.decode_access_token("esto-no-es-un-jwt-valido")


def test_decode_access_token_rejects_refresh_token_used_as_access():
    """Un refresh token no debe pasar como access token (distinto tipo de token)."""
    service = JWTService()
    tokens = service.generate_token_pair(user_id=uuid.uuid4(), rol="estudiante")

    with pytest.raises(UnauthenticatedError):
        service.decode_access_token(tokens.refresh)
