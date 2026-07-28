import uuid
from typing import Protocol


class IEstadoInscripcionProvider(Protocol):
    """
    Puerto para resolver si un estudiante está inscrito en un laboratorio
    (HE-02: "mostrando estado de inscripción por card"). La implementación
    real depende del agregado `Asignación` (módulo Assignments, Sprint 4)
    — todavía no existe, mismo criterio que `UserRegistered` en
    Authentication (evento/puerto disponible desde ya, sin bloquear este
    sprint por un módulo que se construye después).
    """

    def esta_inscrito(self, estudiante_id: uuid.UUID, laboratorio_id: uuid.UUID) -> bool: ...


class SinInscripcionProvider:
    """
    Implementación null-object de `IEstadoInscripcionProvider`, usada
    mientras Assignments no existe — siempre responde `False`. Se
    reemplaza por la implementación real (consultando `Asignación`) en
    Sprint 4, sin tocar `ListarLaboratoriosQuery`.
    """

    def esta_inscrito(self, estudiante_id: uuid.UUID, laboratorio_id: uuid.UUID) -> bool:
        return False
