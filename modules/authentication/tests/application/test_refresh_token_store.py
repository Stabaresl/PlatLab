import uuid

import pytest

from modules.authentication.domain.exceptions import (
    InvalidCredentialsError,
    TokenReuseDetectedError,
)
from modules.authentication.infrastructure.refresh_token_store import RefreshTokenStore


@pytest.fixture
def store():
    return RefreshTokenStore()


def test_register_family_returns_family_id(store):
    family_id = store.register_family(user_id=uuid.uuid4(), jti="jti-1")

    assert family_id is not None


def test_validate_and_rotate_with_current_jti_succeeds(store):
    user_id = uuid.uuid4()
    family_id = store.register_family(user_id=user_id, jti="jti-1")

    result_family_id = store.validate_and_rotate(jti="jti-1", new_jti="jti-2")

    assert result_family_id == family_id


def test_after_rotation_new_jti_is_the_valid_one(store):
    user_id = uuid.uuid4()
    store.register_family(user_id=user_id, jti="jti-1")
    store.validate_and_rotate(jti="jti-1", new_jti="jti-2")

    # jti-2 (el nuevo) debe poder rotar de nuevo sin problema
    store.validate_and_rotate(jti="jti-2", new_jti="jti-3")


def test_reusing_rotated_jti_raises_token_reuse_detected(store):
    user_id = uuid.uuid4()
    store.register_family(user_id=user_id, jti="jti-1")
    store.validate_and_rotate(jti="jti-1", new_jti="jti-2")

    # jti-1 ya fue rotado (reemplazado por jti-2); reusarlo es un robo/replay
    with pytest.raises(TokenReuseDetectedError):
        store.validate_and_rotate(jti="jti-1", new_jti="jti-attacker")


def test_reuse_detection_revokes_the_entire_family(store):
    user_id = uuid.uuid4()
    store.register_family(user_id=user_id, jti="jti-1")
    store.validate_and_rotate(jti="jti-1", new_jti="jti-2")

    with pytest.raises(TokenReuseDetectedError):
        store.validate_and_rotate(jti="jti-1", new_jti="jti-attacker")

    # jti-2 era el legitimo, pero la familia entera quedo revocada
    with pytest.raises(InvalidCredentialsError):
        store.validate_and_rotate(jti="jti-2", new_jti="jti-3")


def test_unknown_jti_raises_invalid_credentials(store):
    with pytest.raises(InvalidCredentialsError):
        store.validate_and_rotate(jti="jti-nunca-existio", new_jti="jti-x")


def test_revoke_all_for_user_invalidates_every_family(store):
    user_id = uuid.uuid4()
    store.register_family(user_id=user_id, jti="jti-a")
    store.register_family(user_id=user_id, jti="jti-b")

    store.revoke_all_for_user(user_id)

    with pytest.raises(InvalidCredentialsError):
        store.validate_and_rotate(jti="jti-a", new_jti="jti-a2")
    with pytest.raises(InvalidCredentialsError):
        store.validate_and_rotate(jti="jti-b", new_jti="jti-b2")
