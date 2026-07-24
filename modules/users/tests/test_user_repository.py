import pytest

from modules.users.domain.entities import ProveedorAutenticacion, ProveedorTipo, User
from modules.users.domain.value_objects import Email, Rol
from modules.users.infrastructure.repositories import UserRepository


@pytest.mark.django_db
def test_add_and_get_by_id():
    repo = UserRepository()
    user = User(email=Email("repo_test1@uni.edu"), nombre_completo="Repo Test 1")

    saved = repo.add(user)
    found = repo.get_by_id(saved.id)

    assert found is not None
    assert found.id == saved.id
    assert found.email.value == "repo_test1@uni.edu"


@pytest.mark.django_db
def test_get_by_email_returns_none_when_not_found():
    repo = UserRepository()

    assert repo.get_by_email("no_existe@uni.edu") is None


@pytest.mark.django_db
def test_exists_by_email():
    repo = UserRepository()
    repo.add(User(email=Email("repo_test2@uni.edu"), nombre_completo="Repo Test 2"))

    assert repo.exists_by_email("repo_test2@uni.edu") is True
    assert repo.exists_by_email("otro@uni.edu") is False


@pytest.mark.django_db
def test_update_persists_changes():
    repo = UserRepository()
    user = repo.add(User(email=Email("repo_test3@uni.edu"), nombre_completo="Original"))

    user.nombre_completo = "Actualizado"
    user.rol = Rol.INSTRUCTOR
    repo.update(user)

    found = repo.get_by_id(user.id)
    assert found.nombre_completo == "Actualizado"
    assert found.rol == Rol.INSTRUCTOR


@pytest.mark.django_db
def test_add_proveedor_and_get_by_proveedor():
    repo = UserRepository()
    user = repo.add(User(email=Email("repo_test4@uni.edu"), nombre_completo="Repo Test 4"))

    repo.add_proveedor(
        ProveedorAutenticacion(
            user_id=user.id, proveedor=ProveedorTipo.GOOGLE, proveedor_uid="google-uid-123"
        )
    )

    found = repo.get_by_proveedor("google", "google-uid-123")
    assert found is not None
    assert found.id == user.id

    proveedores = repo.get_proveedores_by_user_id(user.id)
    assert len(proveedores) == 1
    assert proveedores[0].proveedor == ProveedorTipo.GOOGLE
