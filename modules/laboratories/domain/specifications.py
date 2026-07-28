from abc import ABC, abstractmethod


class Specification(ABC):
    """
    Traduce un criterio de filtro de catálogo (HV-02/HE-02) a los
    parámetros con nombre que espera `ILaboratorioRepository.find_catalogo`
    — mantiene en Domain la regla de "qué filtros existen y cómo se
    combinan", sin que Application conozca los nombres exactos de
    columnas/kwargs del repositorio salvo a través de esta traducción.
    Combinable con `&` (ej. `PorDificultad(...) & PorTema(...)`).
    """

    @abstractmethod
    def aplicar(self, filtros: dict) -> dict:
        raise NotImplementedError

    def __and__(self, other: "Specification") -> "Specification":
        return _EspecificacionCompuesta(self, other)


class _EspecificacionCompuesta(Specification):
    def __init__(self, izquierda: Specification, derecha: Specification):
        self._izquierda = izquierda
        self._derecha = derecha

    def aplicar(self, filtros: dict) -> dict:
        return self._derecha.aplicar(self._izquierda.aplicar(filtros))


class PorDificultad(Specification):
    """Filtra el catálogo por `NivelDificultad` (HV-02, RF-06)."""

    def __init__(self, nivel_dificultad: str):
        self._nivel_dificultad = nivel_dificultad

    def aplicar(self, filtros: dict) -> dict:
        filtros["nivel_dificultad"] = self._nivel_dificultad
        return filtros


class PorTema(Specification):
    """Filtra el catálogo por nombre de `Tema` (HV-02, RF-06)."""

    def __init__(self, tema: str):
        self._tema = tema

    def aplicar(self, filtros: dict) -> dict:
        filtros["tema"] = self._tema
        return filtros
