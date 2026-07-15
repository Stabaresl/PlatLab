import re
from dataclasses import dataclass
from enum import Enum

from modules.shared.domain.base_value_object import BaseValueObject
from modules.shared.domain.exceptions import ValidationError

_EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Rol(str, Enum):
    ESTUDIANTE = "estudiante"
    INSTRUCTOR = "instructor"
    ADMINISTRADOR = "administrador"


@dataclass(frozen=True)
class Email(BaseValueObject):
    value: str

    def __post_init__(self):
        if not _EMAIL_REGEX.match(self.value):
            raise ValidationError(
                "Formato de correo inválido.",
                details=[{"field": "email", "message": "Formato de correo inválido."}],
            )

    def __str__(self) -> str:
        return self.value
