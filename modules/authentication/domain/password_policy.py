import re

from modules.shared.domain.exceptions import ValidationError

_PASSWORD_MIN_LENGTH = 8
_PASSWORD_UPPERCASE_REGEX = re.compile(r"[A-Z]")
_PASSWORD_DIGIT_REGEX = re.compile(r"\d")


def validate_password_policy(password: str) -> None:
    """
    RF-01: mínimo 8 caracteres, 1 mayúscula, 1 número. Compartida entre
    `RegistrarUsuarioUseCase` y `ConfirmarRecuperacionUseCase` — una
    contraseña nueva debe cumplir la misma regla sin importar si viene de
    un registro o de un reseteo.
    """
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
