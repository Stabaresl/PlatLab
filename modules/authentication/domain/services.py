from modules.authentication.domain.exceptions import (
    AccountLinkingRequiresConfirmationError,
)
from modules.users.domain.entities import User


class VinculadorDeCuenta:
    """
    Servicio de dominio (dominio.md §5): decide si un nuevo
    `ProveedorAutenticacion` puede asociarse automáticamente a un `User` o
    si requiere confirmación explícita — no vive en la entidad `User`
    porque cruza una decisión de negocio ("¿es seguro asumir que quien
    llega por OAuth es la misma persona dueña de esta cuenta?") que no es
    responsabilidad del agregado.

    Regla (UC-01 E4, seguridad.md §3): si ya existe un `User` con ese
    email — creado por password o por otro proveedor — jamás se vincula
    sin que el usuario confirme explícitamente. Esto evita que alguien se
    apropie de una cuenta ajena simplemente autenticándose con OAuth con
    un email que el proveedor ya verificó pero que no controla realmente
    (ej. correo institucional reasignado).
    """

    def validar_vinculacion(self, usuario_existente: User | None) -> None:
        if usuario_existente is not None:
            raise AccountLinkingRequiresConfirmationError(
                "Ya existe una cuenta con este correo. Confirma tu "
                "contraseña actual para vincular este proveedor."
            )
