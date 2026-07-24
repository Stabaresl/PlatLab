import uuid


class BaseEntity:
    """
    Entidad base del dominio. Se identifica por su `id`, no por sus atributos.
    Dos entidades son iguales si tienen el mismo id, aunque el resto de sus
    datos difiera.
    """

    def __init__(self, id: uuid.UUID | None = None):
        self.id = id or uuid.uuid4()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BaseEntity):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id})"
