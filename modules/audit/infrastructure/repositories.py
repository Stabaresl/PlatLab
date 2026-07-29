import uuid
from datetime import datetime

from modules.audit.domain.entities import RegistroAuditoria
from modules.audit.infrastructure.mappers import registro_to_entity
from modules.audit.infrastructure.models import RegistroAuditoriaModel


class AuditoriaRepository:
    """
    Implementación de `IAuditoriaRepository`
    (modules.audit.domain.repositories) sobre PostgreSQL vía el ORM de
    Django — traduce entidad <-> modelo con `mappers.py`. Solo `add` y
    lecturas: append-only (UC-12).
    """

    def add(self, registro: RegistroAuditoria) -> RegistroAuditoria:
        model = RegistroAuditoriaModel.objects.create(
            id=registro.id,
            actor_id=registro.actor_id,
            accion=registro.accion,
            entidad_tipo=registro.entidad_tipo,
            entidad_id=registro.entidad_id,
            ip=registro.ip,
        )
        return registro_to_entity(model)

    def find_todos(
        self,
        actor_id: uuid.UUID | None = None,
        accion: str | None = None,
        desde: datetime | None = None,
        hasta: datetime | None = None,
    ) -> list[RegistroAuditoria]:
        queryset = RegistroAuditoriaModel.objects.all()
        if actor_id is not None:
            queryset = queryset.filter(actor_id=actor_id)
        if accion is not None:
            queryset = queryset.filter(accion=accion)
        if desde is not None:
            queryset = queryset.filter(timestamp__gte=desde)
        if hasta is not None:
            queryset = queryset.filter(timestamp__lte=hasta)

        queryset = queryset.order_by("-timestamp")
        return [registro_to_entity(m) for m in queryset]
