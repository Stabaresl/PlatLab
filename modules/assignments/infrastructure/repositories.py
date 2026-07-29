import uuid

from modules.assignments.domain.entities import Asignacion
from modules.assignments.domain.value_objects import EstadoAsignacion
from modules.assignments.infrastructure.mappers import asignacion_to_entity
from modules.assignments.infrastructure.models import AsignacionModel

_ESTADOS_VIGENTES = [EstadoAsignacion.PENDIENTE.value, EstadoAsignacion.ACTIVA.value]


class AsignacionRepository:
    """
    Implementación de `IAsignacionRepository`
    (modules.assignments.domain.repositories) sobre PostgreSQL vía el
    ORM de Django — traduce entidad <-> modelo con `mappers.py`.
    """

    def get_by_id(self, asignacion_id: uuid.UUID) -> Asignacion | None:
        model = AsignacionModel.objects.filter(id=asignacion_id).first()
        return asignacion_to_entity(model) if model else None

    def add(self, asignacion: Asignacion) -> Asignacion:
        model = AsignacionModel.objects.create(
            id=asignacion.id,
            estudiante_id=asignacion.estudiante_id,
            laboratorio_id=asignacion.laboratorio_id,
            instructor_id=asignacion.instructor_id,
            estado=asignacion.estado.value,
            fecha_vencimiento=asignacion.fecha_vencimiento,
        )
        return asignacion_to_entity(model)

    def update(self, asignacion: Asignacion) -> Asignacion:
        model = AsignacionModel.objects.get(id=asignacion.id)
        model.estado = asignacion.estado.value
        model.fecha_respuesta = asignacion.fecha_respuesta
        model.fecha_vencimiento = asignacion.fecha_vencimiento
        model.save()
        return asignacion_to_entity(model)

    def existe_vigente(self, estudiante_id: uuid.UUID, laboratorio_id: uuid.UUID) -> bool:
        return AsignacionModel.objects.filter(
            estudiante_id=estudiante_id,
            laboratorio_id=laboratorio_id,
            estado__in=_ESTADOS_VIGENTES,
        ).exists()

    def find_por_instructor(self, instructor_id: uuid.UUID) -> list[Asignacion]:
        modelos = AsignacionModel.objects.filter(instructor_id=instructor_id).order_by(
            "-fecha_invitacion"
        )
        return [asignacion_to_entity(m) for m in modelos]

    def find_por_estudiante(self, estudiante_id: uuid.UUID) -> list[Asignacion]:
        modelos = AsignacionModel.objects.filter(estudiante_id=estudiante_id).order_by(
            "-fecha_invitacion"
        )
        return [asignacion_to_entity(m) for m in modelos]

    def find_activas_con_vencimiento(self) -> list[Asignacion]:
        modelos = AsignacionModel.objects.filter(
            estado=EstadoAsignacion.ACTIVA.value, fecha_vencimiento__isnull=False
        )
        return [asignacion_to_entity(m) for m in modelos]

    def find_todas_activas(self) -> list[Asignacion]:
        modelos = AsignacionModel.objects.filter(estado=EstadoAsignacion.ACTIVA.value)
        return [asignacion_to_entity(m) for m in modelos]
