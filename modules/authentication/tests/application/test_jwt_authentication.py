import uuid

import pytest
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from modules.authentication.infrastructure.authentication import (
    AuthenticatedUser,
    JWTAuthentication,
)
from modules.authentication.infrastructure.jwt_service import JWTService

_factory = APIRequestFactory()


def _request_with_header(header_value: str | None) -> Request:
    extra = {"HTTP_AUTHORIZATION": header_value} if header_value else {}
    django_request = _factory.get("/", **extra)
    return Request(django_request)


def test_authenticate_returns_none_without_header():
    auth = JWTAuthentication()

    result = auth.authenticate(_request_with_header(None))

    assert result is None


def test_authenticate_returns_none_for_malformed_header():
    auth = JWTAuthentication()

    assert auth.authenticate(_request_with_header("TotalmenteInvalido")) is None
    assert auth.authenticate(_request_with_header("Basic algo")) is None


def test_authenticate_resolves_user_from_valid_token():
    user_id = uuid.uuid4()
    tokens = JWTService().generate_token_pair(user_id=user_id, rol="instructor")
    auth = JWTAuthentication()

    user, token = auth.authenticate(_request_with_header(f"Bearer {tokens.access}"))

    assert isinstance(user, AuthenticatedUser)
    assert user.id == user_id
    assert user.rol == "instructor"
    assert user.is_authenticated is True
    assert token == tokens.access


def test_authenticate_rejects_invalid_token():
    auth = JWTAuthentication()

    with pytest.raises(AuthenticationFailed):
        auth.authenticate(_request_with_header("Bearer token-invalido"))


def test_authenticate_rejects_refresh_token_used_as_access():
    tokens = JWTService().generate_token_pair(user_id=uuid.uuid4(), rol="estudiante")
    auth = JWTAuthentication()

    with pytest.raises(AuthenticationFailed):
        auth.authenticate(_request_with_header(f"Bearer {tokens.refresh}"))
