import uuid

from modules.lab_environments.domain.entities import EntornoActivo
from modules.lab_environments.domain.value_objects import EstadoEntorno
from modules.lab_environments.infrastructure.mappers import entorno_to_entity
from modules.lab_environments.infrastructure.models import EntornoActivoModel

_ESTADOS_ACTIVOS = [EstadoEntorno.INICIANDO.value, EstadoEntorno.ACTIVO.value]


class EntornoRepository:
    """Implementación de `IEntornoRepository` sobre PostgreSQL vía el ORM de Django."""

    def add(self, entorno: EntornoActivo) -> EntornoActivo:
        model = EntornoActivoModel.objects.create(
            id=entorno.id,
            seccion_id=entorno.seccion_id,
            progreso_id=entorno.progreso_id,
            estudiante_id=entorno.estudiante_id,
            container_id=entorno.container_id,
            estado=entorno.estado.value,
        )
        return entorno_to_entity(model)

    def get_by_id(self, entorno_id: uuid.UUID) -> EntornoActivo | None:
        model = EntornoActivoModel.objects.filter(id=entorno_id).first()
        return entorno_to_entity(model) if model else None

    def get_activo_por_seccion(
        self, progreso_id: uuid.UUID, seccion_id: uuid.UUID
    ) -> EntornoActivo | None:
        model = (
            EntornoActivoModel.objects.filter(
                progreso_id=progreso_id, seccion_id=seccion_id, estado__in=_ESTADOS_ACTIVOS
            )
            .order_by("-fecha_inicio")
            .first()
        )
        return entorno_to_entity(model) if model else None

    def update(self, entorno: EntornoActivo) -> EntornoActivo:
        model = EntornoActivoModel.objects.get(id=entorno.id)
        model.estado = entorno.estado.value
        model.save()
        return entorno_to_entity(model)

    def contar_activos(self) -> int:
        return EntornoActivoModel.objects.filter(estado__in=_ESTADOS_ACTIVOS).count()

    def get_todos_activos(self) -> list[EntornoActivo]:
        modelos = EntornoActivoModel.objects.filter(estado__in=_ESTADOS_ACTIVOS)
        return [entorno_to_entity(m) for m in modelos]
