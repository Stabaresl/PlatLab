"""Comandos que usa el instalador (platlab.ps1 / platlab.sh) en modo red / aula."""

import io

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from modules.users.domain.value_objects import Rol
from modules.users.infrastructure.repositories import UserRepository

_DEMO = ["admin@platlab.demo", "instructor@platlab.demo", "estudiante@platlab.demo"]


@pytest.mark.django_db
def test_seed_demo_con_cuentas_desactivadas_crea_contenido_pero_no_deja_entrar():
    call_command("seed_demo_data", stdout=io.StringIO())
    call_command("seed_demo_data", "--desactivar-cuentas-demo", stdout=io.StringIO())

    repo = UserRepository()
    for email in _DEMO:
        usuario = repo.get_by_email(email)
        assert usuario is not None
        assert usuario.is_active is False
        assert usuario.password_hash.startswith("!")

    login = APIClient().post("/api/v1/auth/login/", {"email": "admin@platlab.demo", "password": "Admin1234"})
    assert login.status_code in (401, 403)


@pytest.mark.django_db
def test_create_production_users_solo_admin():
    salida = io.StringIO()

    call_command(
        "create_production_users", "--admin-email", "profe@uni.edu.co", "--admin-nombre", "Profe", stdout=salida
    )

    admin = UserRepository().get_by_email("profe@uni.edu.co")
    assert admin.rol == Rol.ADMINISTRADOR
    assert "contraseña:" in salida.getvalue()
    assert UserRepository().contar(rol=Rol.INSTRUCTOR.value) == 0
