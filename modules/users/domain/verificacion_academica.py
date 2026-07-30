from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ResultadoVerificacionAcademica:
    """Snapshot del resultado de comparar una solicitud contra OpenAlex."""

    encontrado: bool
    coincide_nombre: bool
    works_count: int
    nombre_openalex: str | None


class IVerificadorAcademicoProvider(Protocol):
    """
    Puerto para verificar la identidad académica de quien solicita
    convertirse en instructor. La implementación real (`OpenAlexAdapter`,
    Infrastructure) llama la API pública de OpenAlex — el dominio no conoce
    `requests` ni la forma del JSON de un proveedor externo.
    """

    def verificar(self, orcid: str, nombre_declarado: str) -> ResultadoVerificacionAcademica: ...
