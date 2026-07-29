import uuid

import pytest

from modules.shared.domain.exceptions import ForbiddenError, NotFoundError, ValidationError
from modules.shared.infrastructure.event_dispatcher import EventDispatcher
from modules.shared.infrastructure.unit_of_work import BaseUnitOfWork
from modules.users.application.dtos import (
    ActualizarUsuarioDTO,
    DeshabilitarUsuarioDTO,
    HabilitarUsuarioDTO,
    ListarUsuariosDTO,
)
from modules.users.application.queries.listar_usuarios import ListarUsuariosQuery
from modules.users.application.queries.obtener_usuario import ObtenerUsuarioQuery
from modules.users.application.use_cases.actualizar_usuario import ActualizarUsuarioUseCase
from modules.users.application.use_cases.deshabilitar_usuario import DeshabilitarUsuarioUseCase
from modules.users.application.use_cases.habilitar_usuario import HabilitarUsuarioUseCase
from modules.users.domain.entities import User
from modules.users.domain.exceptions import SelfDisableNotAllowedError
from modules.users.domain.value_objects import Email, Rol
from modules.users.infrastructure.repositories import UserRepository


def _crear_usuario(email: str, rol: Rol = Rol.ESTUDIANTE, is_active: bool = True) -> User:
    return UserRepository().add(
        User(email=Email(email), nombre_completo="Usuario Test", rol=rol, is_active=is_active)
    )


@pytest.mark.django_db
def test_listar_usuarios_filtra_por_nombre_rol_activo():
    _crear_usuario("listar1@uni.edu", rol=Rol.INSTRUCTOR)
    _crear_usuario("listar2@uni.edu", rol=Rol.ESTUDIANTE)

    resultado = ListarUsuariosQuery(UserRepository()).execute(
        ListarUsuariosDTO(actor_rol="administrador", rol="instructor")
    )

    assert all(item.rol == "instructor" for item in resultado)


@pytest.mark.django_db
def test_listar_usuarios_no_admin_lanza_forbidden():
    with pytest.raises(ForbiddenError):
        ListarUsuariosQuery(UserRepository()).execute(ListarUsuariosDTO(actor_rol="instructor"))


@pytest.mark.django_db
def test_obtener_usuario_admin_ve_detalle():
    usuario = _crear_usuario("detalle@uni.edu")

    resultado = ObtenerUsuarioQuery(UserRepository()).execute(
        usuario_id=usuario.id, actor_rol="administrador"
    )

    assert resultado.id == usuario.id
    assert resultado.email == "detalle@uni.edu"


@pytest.mark.django_db
def test_obtener_usuario_no_admin_lanza_forbidden():
    usuario = _crear_usuario("detalle2@uni.edu")

    with pytest.raises(ForbiddenError):
        ObtenerUsuarioQuery(UserRepository()).execute(
            usuario_id=usuario.id, actor_rol="estudiante"
        )


@pytest.mark.django_db
def test_obtener_usuario_inexistente_lanza_not_found():
    with pytest.raises(NotFoundError):
        ObtenerUsuarioQuery(UserRepository()).execute(
            usuario_id=uuid.uuid4(), actor_rol="administrador"
        )


def _actualizar_uc():
    return ActualizarUsuarioUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        user_repository=UserRepository(),
    )


@pytest.mark.django_db
def test_actualizar_usuario_admin_edita_rol():
    admin_id = uuid.uuid4()
    usuario = _crear_usuario("editar@uni.edu")

    resultado = _actualizar_uc().execute(
        ActualizarUsuarioDTO(
            usuario_id=usuario.id,
            actor_id=admin_id,
            actor_rol="administrador",
            rol="instructor",
        )
    )

    assert resultado.rol == "instructor"


@pytest.mark.django_db
def test_actualizar_usuario_no_admin_lanza_forbidden():
    usuario = _crear_usuario("editar2@uni.edu")

    with pytest.raises(ForbiddenError):
        _actualizar_uc().execute(
            ActualizarUsuarioDTO(
                usuario_id=usuario.id,
                actor_id=uuid.uuid4(),
                actor_rol="instructor",
                nombre_completo="x",
            )
        )


@pytest.mark.django_db
def test_actualizar_usuario_rol_invalido_lanza_validation_error():
    usuario = _crear_usuario("editar3@uni.edu")

    with pytest.raises(ValidationError):
        _actualizar_uc().execute(
            ActualizarUsuarioDTO(
                usuario_id=usuario.id,
                actor_id=uuid.uuid4(),
                actor_rol="administrador",
                rol="rol_invalido",
            )
        )


@pytest.mark.django_db
def test_actualizar_usuario_admin_no_puede_quitarse_su_propio_rol():
    admin = _crear_usuario("admin_self@uni.edu", rol=Rol.ADMINISTRADOR)

    with pytest.raises(SelfDisableNotAllowedError):
        _actualizar_uc().execute(
            ActualizarUsuarioDTO(
                usuario_id=admin.id,
                actor_id=admin.id,
                actor_rol="administrador",
                rol="instructor",
            )
        )


def _deshabilitar_uc():
    return DeshabilitarUsuarioUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        user_repository=UserRepository(),
    )


def _habilitar_uc():
    return HabilitarUsuarioUseCase(
        unit_of_work=BaseUnitOfWork(),
        event_dispatcher=EventDispatcher(),
        user_repository=UserRepository(),
    )


@pytest.mark.django_db
def test_deshabilitar_usuario_admin_exitoso():
    admin_id = uuid.uuid4()
    usuario = _crear_usuario("deshabilitar@uni.edu")

    resultado = _deshabilitar_uc().execute(
        DeshabilitarUsuarioDTO(usuario_id=usuario.id, actor_id=admin_id, actor_rol="administrador")
    )

    assert resultado.is_active is False


@pytest.mark.django_db
def test_deshabilitar_usuario_no_puede_deshabilitarse_a_si_mismo():
    admin = _crear_usuario("admin_self2@uni.edu", rol=Rol.ADMINISTRADOR)

    with pytest.raises(SelfDisableNotAllowedError):
        _deshabilitar_uc().execute(
            DeshabilitarUsuarioDTO(
                usuario_id=admin.id, actor_id=admin.id, actor_rol="administrador"
            )
        )


@pytest.mark.django_db
def test_deshabilitar_usuario_no_admin_lanza_forbidden():
    usuario = _crear_usuario("deshabilitar2@uni.edu")

    with pytest.raises(ForbiddenError):
        _deshabilitar_uc().execute(
            DeshabilitarUsuarioDTO(
                usuario_id=usuario.id, actor_id=uuid.uuid4(), actor_rol="estudiante"
            )
        )


@pytest.mark.django_db
def test_habilitar_usuario_admin_reactiva():
    usuario = _crear_usuario("habilitar@uni.edu", is_active=False)

    resultado = _habilitar_uc().execute(
        HabilitarUsuarioDTO(usuario_id=usuario.id, actor_id=uuid.uuid4(), actor_rol="administrador")
    )

    assert resultado.is_active is True


@pytest.mark.django_db
def test_habilitar_usuario_inexistente_lanza_not_found():
    with pytest.raises(NotFoundError):
        _habilitar_uc().execute(
            HabilitarUsuarioDTO(
                usuario_id=uuid.uuid4(), actor_id=uuid.uuid4(), actor_rol="administrador"
            )
        )
