import uuid

from modules.users.domain.value_objects import Rol
from modules.users.infrastructure.repositories import UserRepository


class AdministradoresProvider:
    """
    Adaptador hacia Users para avisos dirigidos a un rol, no a una persona
    (ej. "hay una solicitud de instructor por revisar"). Notifications sigue
    guardando solo `user_id` sueltos — esta clase es el único punto que
    consulta Users, igual que los providers de otros módulos.
    """

    def ids_activos(self) -> list[uuid.UUID]:
        return [
            u.id
            for u in UserRepository().find_all(rol=Rol.ADMINISTRADOR.value, activo=True, limit=50)
        ]
