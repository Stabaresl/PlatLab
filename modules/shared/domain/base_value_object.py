from dataclasses import dataclass


@dataclass(frozen=True)
class BaseValueObject:
    """
    Value Object base del dominio. Inmutable y se compara por valor: dos
    instancias con los mismos atributos son iguales, sin importar identidad.
    Los VOs concretos (Email, Rol, NivelDificultad, etc.) heredan de esta
    clase como @dataclass(frozen=True) también.
    """
    pass
