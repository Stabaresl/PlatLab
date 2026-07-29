import uuid

from django.db import models


class ProgresoModel(models.Model):
    """
    base-de-datos.md "progress_progreso" + `estudiante_id` denormalizado
    (decisión aprobada: Assignments todavía no existe en Sprint 3, ver
    `modules.progress.domain.entities.Progreso`).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asignacion_id = models.UUIDField(unique=True)
    estudiante_id = models.UUIDField()
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    ultima_actividad = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "progress_progreso"
        indexes = [
            models.Index(fields=["estudiante_id"], name="idx_progreso_estudiante"),
        ]

    def __str__(self) -> str:
        return f"Progreso(asignacion={self.asignacion_id})"


class ProgresoSeccionModel(models.Model):
    class Estado(models.TextChoices):
        BLOQUEADA = "bloqueada", "Bloqueada"
        EN_PROGRESO = "en_progreso", "En progreso"
        COMPLETADA = "completada", "Completada"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    progreso = models.ForeignKey(
        ProgresoModel, on_delete=models.CASCADE, related_name="secciones"
    )
    # seccion_id: id suelto a laboratories_seccion (Arquitectura §8).
    seccion_id = models.UUIDField()
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.BLOQUEADA)
    fecha_completado = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "progress_progresoseccion"
        constraints = [
            models.UniqueConstraint(
                fields=["progreso", "seccion_id"], name="uq_progsec_progreso_seccion"
            ),
        ]
        indexes = [
            models.Index(
                fields=["progreso", "estado"], name="idx_progsec_progreso_estado"
            ),
        ]

    def __str__(self) -> str:
        return f"ProgresoSeccion(seccion={self.seccion_id}, estado={self.estado})"


class IntentoFlagModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    progreso = models.ForeignKey(ProgresoModel, on_delete=models.CASCADE, related_name="intentos")
    seccion_id = models.UUIDField()
    resultado = models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "progress_intentoflag"
        indexes = [
            models.Index(
                fields=["progreso", "seccion_id", "timestamp"], name="idx_intentoflag_prog_sec_ts"
            ),
        ]

    def __str__(self) -> str:
        return f"IntentoFlag(seccion={self.seccion_id}, resultado={self.resultado})"


class HistorialCompletitudModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    progreso = models.ForeignKey(ProgresoModel, on_delete=models.CASCADE, related_name="historial")
    numero_intento = models.PositiveIntegerField()
    fecha_completado = models.DateTimeField(auto_now_add=True)
    puntaje = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "progress_historialcompletitud"
        constraints = [
            models.UniqueConstraint(
                fields=["progreso", "numero_intento"], name="uq_historial_progreso_intento"
            ),
        ]

    def __str__(self) -> str:
        return f"HistorialCompletitud(progreso={self.progreso_id}, intento={self.numero_intento})"
