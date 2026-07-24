import uuid

from modules.users.domain.entities import ProveedorAutenticacion, User
from modules.users.infrastructure.mappers import (
    proveedor_to_entity,
    proveedor_to_model,
    user_to_entity,
    user_to_model,
)
from modules.users.infrastructure.models import (
    ProveedorAutenticacionModel,
    UserModel,
)


class UserRepository:
    """
    Implementación de `IUserRepository` (modules.users.domain.repositories)
    sobre PostgreSQL vía el ORM de Django. Traduce entidad <-> modelo con
    `mappers.py` en cada operación — el resto del sistema nunca ve
    `UserModel` directamente, solo la entidad `User`.
    """

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        model = UserModel.objects.filter(id=user_id).first()
        return user_to_entity(model) if model else None

    def get_by_email(self, email: str) -> User | None:
        model = UserModel.objects.filter(email=email).first()
        return user_to_entity(model) if model else None

    def get_by_username(self, username: str) -> User | None:
        model = UserModel.objects.filter(username=username).first()
        return user_to_entity(model) if model else None

    def exists_by_email(self, email: str) -> bool:
        return UserModel.objects.filter(email=email).exists()

    def add(self, user: User) -> User:
        model = user_to_model(user)
        model.save()
        return user_to_entity(model)

    def update(self, user: User) -> User:
        model = UserModel.objects.get(id=user.id)
        model.email = str(user.email)
        model.nombre_completo = user.nombre_completo
        model.rol = user.rol.value
        model.username = user.username
        model.password_hash = user.password_hash
        model.is_active = user.is_active
        model.last_login = user.last_login
        model.save()
        return user_to_entity(model)

    def add_proveedor(self, proveedor: ProveedorAutenticacion) -> ProveedorAutenticacion:
        model = proveedor_to_model(proveedor)
        model.save()
        return proveedor_to_entity(model)

    def get_proveedores_by_user_id(self, user_id: uuid.UUID) -> list[ProveedorAutenticacion]:
        models = ProveedorAutenticacionModel.objects.filter(user_id=user_id)
        return [proveedor_to_entity(m) for m in models]

    def get_by_proveedor(self, proveedor: str, proveedor_uid: str) -> User | None:
        vinculo = ProveedorAutenticacionModel.objects.filter(
            proveedor=proveedor, proveedor_uid=proveedor_uid
        ).first()
        if not vinculo:
            return None
        return self.get_by_id(vinculo.user_id)
