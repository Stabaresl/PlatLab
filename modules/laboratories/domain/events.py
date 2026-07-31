import uuid
from dataclasses import dataclass

from modules.shared.domain.domain_event import DomainEvent


@dataclass(frozen=True, kw_only=True)
class LaboratoryPublished(DomainEvent):
    """Se dispara al publicar un laboratorio (UC-04) — insumo de auditoría (UC-12)."""

    laboratorio_id: uuid.UUID
    instructor_id: uuid.UUID | None


@dataclass(frozen=True, kw_only=True)
class LaboratoryDuplicated(DomainEvent):
    """Se dispara al duplicar un laboratorio predeterminado (UC-05)."""

    laboratorio_id: uuid.UUID
    origen_id: uuid.UUID
    instructor_id: uuid.UUID


@dataclass(frozen=True, kw_only=True)
class LaboratoryReviewRequested(DomainEvent):
    """Se dispara cuando un instructor manda su laboratorio a revisión."""

    laboratorio_id: uuid.UUID
    instructor_id: uuid.UUID


@dataclass(frozen=True, kw_only=True)
class LaboratoryApproved(DomainEvent):
    """
    Se dispara cuando un admin aprueba un laboratorio en revisión (pasa a
    publicado). `admin_id` es quien tomó la decisión — distinto de
    `instructor_id` (el dueño del laboratorio), necesario para que
    auditoría le atribuya la acción a la persona correcta.
    """

    laboratorio_id: uuid.UUID
    instructor_id: uuid.UUID
    admin_id: uuid.UUID


@dataclass(frozen=True, kw_only=True)
class LaboratoryRejected(DomainEvent):
    """Se dispara cuando un admin rechaza un laboratorio en revisión (vuelve a borrador)."""

    laboratorio_id: uuid.UUID
    instructor_id: uuid.UUID
    admin_id: uuid.UUID
    motivo: str


@dataclass(frozen=True, kw_only=True)
class LaboratoryCatalogVisibilityChanged(DomainEvent):
    """
    Se dispara cuando alguien activa/desactiva la visibilidad de un
    `personalizado` en el catálogo público (`CambiarVisibilidadCatalogoUseCase`).
    `actor_id` es quien tomó la decisión — el instructor dueño o un admin,
    distinto de `instructor_id` (el dueño) en el segundo caso.
    """

    laboratorio_id: uuid.UUID
    instructor_id: uuid.UUID
    actor_id: uuid.UUID
    visible: bool
