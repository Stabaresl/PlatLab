import uuid

from modules.reports.domain.entities import AdjuntoReporte, Reporte
from modules.reports.infrastructure.mappers import adjunto_to_entity, reporte_to_entity
from modules.reports.infrastructure.models import AdjuntoReporteModel, ReporteModel


class ReporteRepository:
    """
    Implementación de `IReporteRepository`
    (modules.reports.domain.repositories) sobre PostgreSQL vía el ORM de
    Django — traduce entidad <-> modelo con `mappers.py`.
    """

    def get_by_id(self, reporte_id: uuid.UUID) -> Reporte | None:
        model = ReporteModel.objects.filter(id=reporte_id).first()
        return reporte_to_entity(model) if model else None

    def add(self, reporte: Reporte) -> Reporte:
        model = ReporteModel.objects.create(
            id=reporte.id,
            estudiante_id=reporte.estudiante_id,
            laboratorio_id=reporte.laboratorio_id,
            seccion_id=reporte.seccion_id,
            descripcion=reporte.descripcion,
            estado=reporte.estado.value,
        )
        return reporte_to_entity(model)

    def update(self, reporte: Reporte) -> Reporte:
        model = ReporteModel.objects.get(id=reporte.id)
        model.estado = reporte.estado.value
        model.fecha_resolucion = reporte.fecha_resolucion
        model.save()
        return reporte_to_entity(model)

    def add_adjunto(self, adjunto: AdjuntoReporte) -> AdjuntoReporte:
        model = AdjuntoReporteModel.objects.create(
            id=adjunto.id,
            reporte_id=adjunto.reporte_id,
            archivo_url=adjunto.archivo_url,
            nombre_archivo=adjunto.nombre_archivo,
            tamano_kb=adjunto.tamano_kb,
        )
        return adjunto_to_entity(model)

    def get_adjunto(self, reporte_id: uuid.UUID) -> AdjuntoReporte | None:
        model = AdjuntoReporteModel.objects.filter(reporte_id=reporte_id).first()
        return adjunto_to_entity(model) if model else None

    def find_por_estudiante(self, estudiante_id: uuid.UUID) -> list[Reporte]:
        modelos = ReporteModel.objects.filter(estudiante_id=estudiante_id).order_by(
            "-fecha_creacion"
        )
        return [reporte_to_entity(m) for m in modelos]

    def find_todos(
        self,
        estado: str | None = None,
        laboratorio_id: uuid.UUID | None = None,
    ) -> list[Reporte]:
        queryset = ReporteModel.objects.all()
        if estado is not None:
            queryset = queryset.filter(estado=estado)
        if laboratorio_id is not None:
            queryset = queryset.filter(laboratorio_id=laboratorio_id)

        queryset = queryset.order_by("-fecha_creacion")
        return [reporte_to_entity(m) for m in queryset]
