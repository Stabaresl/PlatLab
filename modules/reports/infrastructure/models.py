import uuid

from django.db import models


class ReporteModel(models.Model):
    """base-de-datos.md "reports_reporte"."""

    class Estado(models.TextChoices):
        ABIERTO = "abierto", "Abierto"
        EN_REVISION = "en_revision", "En revisión"
        RESUELTO = "resuelto", "Resuelto"
        NO_REPRODUCIBLE = "no_reproducible", "No reproducible"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # estudiante_id/laboratorio_id/seccion_id: id suelto (Arquitectura §8).
    estudiante_id = models.UUIDField()
    laboratorio_id = models.UUIDField()
    seccion_id = models.UUIDField(null=True, blank=True)
    descripcion = models.TextField()
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ABIERTO)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_resolucion = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "reports_reporte"
        # UC-09 E1 (descripción mínima 10 caracteres) se valida en
        # `Reporte.__post_init__` (Domain) — Django no soporta `__length`
        # como lookup portable para un CheckConstraint, así que no se
        # duplica aquí a nivel de base de datos.
        indexes = [
            models.Index(fields=["estado"], name="idx_reporte_estado"),
            models.Index(fields=["estudiante_id"], name="idx_reporte_estudiante"),
        ]

    def __str__(self) -> str:
        return f"Reporte({self.laboratorio_id}, {self.estado})"


class AdjuntoReporteModel(models.Model):
    """
    base-de-datos.md "reports_adjunto": 1:0..1 con `ReporteModel` (un
    solo adjunto por reporte, seguridad.md §4).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reporte = models.OneToOneField(
        ReporteModel, on_delete=models.CASCADE, related_name="adjunto"
    )
    archivo_url = models.CharField(max_length=500)
    nombre_archivo = models.CharField(max_length=255)
    tamano_kb = models.PositiveIntegerField()

    class Meta:
        db_table = "reports_adjunto"

    def __str__(self) -> str:
        return f"AdjuntoReporte(reporte={self.reporte_id}, {self.nombre_archivo})"
