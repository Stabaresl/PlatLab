import uuid

from django.db import models


class EntornoActivoModel(models.Model):
    class Estado(models.TextChoices):
        INICIANDO = "iniciando", "Iniciando"
        ACTIVO = "activo", "Activo"
        DETENIDO = "detenido", "Detenido"
        ERROR = "error", "Error"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # ids sueltos hacia Progress/Laboratories (Arquitectura §8) — sin FK real.
    seccion_id = models.UUIDField()
    progreso_id = models.UUIDField()
    estudiante_id = models.UUIDField()
    container_id = models.CharField(max_length=64)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.INICIANDO)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    ultima_actividad = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "lab_environments_entornoactivo"
        indexes = [
            models.Index(fields=["estado", "ultima_actividad"], name="idx_entorno_estado_actividad"),
            models.Index(fields=["progreso_id", "seccion_id"], name="idx_entorno_progreso_seccion"),
        ]

    def __str__(self) -> str:
        return f"EntornoActivo(seccion={self.seccion_id}, estado={self.estado})"
