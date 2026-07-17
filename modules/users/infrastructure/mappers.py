from modules.users.domain.entities import ProveedorAutenticacion, ProveedorTipo, User
from modules.users.domain.value_objects import Email, Rol
from modules.users.infrastructure.models import (
    ProveedorAutenticacionModel,
    UserModel,
)


def user_to_entity(model: UserModel) -> User:
    return User(
        id=model.id,
        email=Email(model.email),
        nombre_completo=model.nombre_completo,
        rol=Rol(model.rol),
        username=model.username,
        password_hash=model.password_hash,
        is_active=model.is_active,
        date_joined=model.date_joined,
        last_login=model.last_login,
    )


def user_to_model(entity: User) -> UserModel:
    return UserModel(
        id=entity.id,
        email=str(entity.email),
        nombre_completo=entity.nombre_completo,
        rol=entity.rol.value,
        username=entity.username,
        password_hash=entity.password_hash,
        is_active=entity.is_active,
        last_login=entity.last_login,
    )


def proveedor_to_entity(model: ProveedorAutenticacionModel) -> ProveedorAutenticacion:
    return ProveedorAutenticacion(
        id=model.id,
        user_id=model.user_id,
        proveedor=ProveedorTipo(model.proveedor),
        proveedor_uid=model.proveedor_uid,
        created_at=model.created_at,
    )


def proveedor_to_model(entity: ProveedorAutenticacion) -> ProveedorAutenticacionModel:
    return ProveedorAutenticacionModel(
        id=entity.id,
        user_id=entity.user_id,
        proveedor=entity.proveedor.value,
        proveedor_uid=entity.proveedor_uid,
    )
