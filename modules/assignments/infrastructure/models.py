import uuid

from django.db import models


class AsignacionModel(models.Model):
    """
    base-de-datos.md "assignments_asignacion". `estudiante_id`/
    `laboratorio_id`/`instructor_id` son "id suelto" (Arquitectura §8) —
    sin FK hacia Users/Laboratories.
    """

    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        ACEPTADA = "aceptada", "Aceptada"
        RECHAZADA = "rechazada", "Rechazada"
        ACTIVA = "activa", "Activa"
        VENCIDA = "vencida", "Vencida"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    estudiante_id = models.UUIDField()
    laboratorio_id = models.UUIDField()
    instructor_id = models.UUIDField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    fecha_invitacion = models.DateTimeField(auto_now_add=True)
    fecha_vencimiento = models.DateTimeField(null=True, blank=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "assignments_asignacion"
        indexes = [
            models.Index(
                fields=["estado", "fecha_vencimiento"], name="idx_asig_estado_vencimiento"
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(fecha_vencimiento__isnull=True)
                | models.Q(fecha_vencimiento__gt=models.F("fecha_invitacion")),
                name="ck_asig_vencimiento_posterior",
            ),
            # base-de-datos.md: "único (estudiante_id, laboratorio_id) con
            # estado activo" (UC-06 E2) — parcial, solo bloquea mientras la
            # asignación sigue vigente (pendiente/activa); una rechazada o
            # vencida no impide una nueva invitación al mismo par.
            models.UniqueConstraint(
                fields=["estudiante_id", "laboratorio_id"],
                condition=models.Q(estado__in=["pendiente", "activa"]),
                name="uq_asig_est_lab_vigente",
            ),
        ]

    def __str__(self) -> str:
        return f"Asignacion({self.estudiante_id} -> {self.laboratorio_id}, {self.estado})"
