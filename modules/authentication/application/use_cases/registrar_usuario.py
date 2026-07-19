import re

from django.contrib.auth.hashers import make_password

from modules.authentication.application.dtos import RegistroDTO, RegistroResultDTO
from modules.authentication.domain.events import UserRegistered
from modules.shared.application.base_use_case import BaseUseCase
from modules.shared.domain.domain_event import DomainEvent
from modules.shared.domain.exceptions import ConflictError, ValidationError
from modules.users.domain.entities import User
from modules.users.domain.repositories import IUserRepository
from modules.users.domain.value_objects import Email, Rol

_PASSWORD_MIN_LENGTH = 8
_PASSWORD_UPPERCASE_REGEX = re.compile(r"[A-Z]")
_PASSWORD_DIGIT_REGEX = re.compile(r"\d")


class RegistrarUsuarioUseCase(BaseUseCase[RegistroDTO, RegistroResultDTO]):
    """
    UC-01, flujo principal (registro con email). Valida unicidad de correo
    (con mensaje genérico anti-enumeración, UC-01 E1) y política de
    contraseña (RF-01), hashea la contraseña (RNF-01.2) y persiste el
    usuario con rol Estudiante por defecto y estado activo.
    """

    def __init__(self, unit_of_work, event_dispatcher, user_repository: IUserRepository):
        super().__init__(unit_of_work, event_dispatcher)
        self._user_repository = user_repository

    def _validate(self, input_dto: RegistroDTO) -> None:
        Email(input_dto.email)  # lanza ValidationError si el formato es inválido

        if input_dto.password != input_dto.password_confirm:
            raise ValidationError(
                "Las contraseñas no coinciden.",
                details=[{"field": "password_confirm", "message": "Las contraseñas no coinciden."}],
            )

        self._validate_password_policy(input_dto.password)

        if self._user_repository.exists_by_email(input_dto.email):
            # Mensaje genérico a propósito: evita confirmar si el email ya
            # existe con otro proveedor (UC-01 E1, anti-enumeración).
            raise ConflictError(
                "Este correo ya está registrado.",
                details=[{"field": "email", "message": "Este correo ya está registrado."}],
            )

    def _validate_password_policy(self, password: str) -> None:
        errors = []
        if len(password) < _PASSWORD_MIN_LENGTH:
            errors.append(f"Debe tener al menos {_PASSWORD_MIN_LENGTH} caracteres.")
        if not _PASSWORD_UPPERCASE_REGEX.search(password):
            errors.append("Debe incluir al menos una mayúscula.")
        if not _PASSWORD_DIGIT_REGEX.search(password):
            errors.append("Debe incluir al menos un número.")

        if errors:
            raise ValidationError(
                "La contraseña no cumple la política de seguridad.",
                details=[{"field": "password", "message": msg} for msg in errors],
            )

    def _execute_domain_logic(
        self, input_dto: RegistroDTO
    ) -> tuple[RegistroResultDTO, list[DomainEvent]]:
        user = User(
            email=Email(input_dto.email),
            nombre_completo=input_dto.nombre_completo,
            rol=Rol.ESTUDIANTE,
            password_hash=make_password(input_dto.password),
            is_active=True,
        )
        saved_user = self._user_repository.add(user)

        result = RegistroResultDTO(
            id=saved_user.id,
            email=str(saved_user.email),
            rol=saved_user.rol.value,
            email_verificado=False,
        )
        event = UserRegistered(
            user_id=saved_user.id,
            email=str(saved_user.email),
            nombre_completo=saved_user.nombre_completo,
        )
        return result, [event]
