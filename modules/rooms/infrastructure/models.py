import uuid

from django.db import models


class SalaModel(models.Model):
    """Sala privada sobre un laboratorio. `laboratorio_id`/`anfitrion_id`: id sueltos (Arquitectura §8)."""

    class Estado(models.TextChoices):
        ABIERTA = "abierta", "Abierta"
        CERRADA = "cerrada", "Cerrada"
        FINALIZADA = "finalizada", "Finalizada"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True, default="")
    laboratorio_id = models.UUIDField()
    anfitrion_id = models.UUIDField()
    codigo = models.CharField(max_length=12, unique=True)
    capacidad = models.PositiveSmallIntegerField(default=30)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.ABIERTA)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "rooms_sala"
        indexes = [models.Index(fields=["anfitrion_id", "created_at"], name="idx_sala_anfitrion")]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(capacidad__gte=1) & models.Q(capacidad__lte=100),
                name="ck_sala_capacidad_1_100",
            ),
        ]

    def __str__(self) -> str:
        return f"Sala({self.codigo}, {self.nombre})"


class ParticipanteSalaModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sala = models.ForeignKey(SalaModel, on_delete=models.CASCADE, related_name="participantes")
    estudiante_id = models.UUIDField()
    asignacion_id = models.UUIDField()
    completado_antes = models.BooleanField(default=False)
    posicion_final = models.PositiveSmallIntegerField(null=True, blank=True)
    fecha_completado = models.DateTimeField(null=True, blank=True)
    unido_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "rooms_participante"
        constraints = [
            models.UniqueConstraint(fields=["sala", "estudiante_id"], name="uq_participante_sala_estudiante"),
        ]
        indexes = [
            models.Index(fields=["asignacion_id"], name="idx_participante_asignacion"),
            models.Index(fields=["estudiante_id"], name="idx_participante_estudiante"),
        ]

    def __str__(self) -> str:
        return f"Participante({self.estudiante_id} en {self.sala_id})"
