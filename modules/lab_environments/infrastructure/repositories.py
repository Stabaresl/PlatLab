import uuid

from django.utils import timezone

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
        # `container_id` nace vacío (`iniciando`, ver IniciarEntornoUseCase)
        # y lo completa AprovisionarEntornoUseCase una vez que Docker
        # responde — a diferencia de `estado`, antes era inmutable después
        # de crear el registro, por eso `update()` nunca lo tocaba.
        model.container_id = entorno.container_id
        model.save()
        return entorno_to_entity(model)

    def contar_activos(self) -> int:
        return EntornoActivoModel.objects.filter(estado__in=_ESTADOS_ACTIVOS).count()

    def contar_activos_por_estudiante(self, estudiante_id: uuid.UUID) -> int:
        return EntornoActivoModel.objects.filter(
            estudiante_id=estudiante_id, estado__in=_ESTADOS_ACTIVOS
        ).count()

    def tocar_actividad(self, entorno_id: uuid.UUID) -> bool:
        """
        Actualiza SOLO `ultima_actividad`, y solo si el entorno sigue vivo.
        Antes el consumer del WebSocket hacía `update()` con la entidad que
        leyó al conectar: si mientras tanto el reaper o el estudiante lo
        habían detenido, ese `update()` volvía a escribir `estado=activo`
        sobre un contenedor ya borrado (entorno "fantasma" ocupando cupo).
        Devuelve False si el entorno ya no está activo.
        """
        return bool(
            EntornoActivoModel.objects.filter(id=entorno_id, estado__in=_ESTADOS_ACTIVOS).update(
                ultima_actividad=timezone.now()
            )
        )

    def get_todos_activos(self) -> list[EntornoActivo]:
        modelos = EntornoActivoModel.objects.filter(estado__in=_ESTADOS_ACTIVOS)
        return [entorno_to_entity(m) for m in modelos]
