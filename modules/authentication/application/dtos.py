import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class RegistroDTO:
    email: str
    password: str
    password_confirm: str
    nombre_completo: str


@dataclass(frozen=True)
class LoginDTO:
    email: str
    password: str


@dataclass(frozen=True)
class RegistroResultDTO:
    id: uuid.UUID
    email: str
    rol: str
    email_verificado: bool


@dataclass(frozen=True)
class TokenPairDTO:
    access: str
    refresh: str
    expires_in: int
    rol: str
