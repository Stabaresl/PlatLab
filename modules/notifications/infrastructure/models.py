import uuid

from django.db import models


class NotificacionModel(models.Model):
    """base-de-datos.md "notifications_notificacion"."""

    class Tipo(models.TextChoices):
        INVITACION = "invitacion", "Invitación"
        VENCIMIENTO_PROXIMO = "vencimiento_proximo", "Vencimiento próximo"
        REPORTE_RESUELTO = "reporte_resuelto", "Reporte resuelto"
        LABORATORIO_PUBLICADO = "laboratorio_publicado", "Laboratorio publicado"
        ACCESO_VENCIDO = "acceso_vencido", "Acceso vencido"

    class Canal(models.TextChoices):
        IN_APP = "in_app", "In-app"
        EMAIL = "email", "Email"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # user_id: id suelto (Arquitectura §8) — Notifications no depende de Users.
    user_id = models.UUIDField()
    tipo = models.CharField(max_length=30, choices=Tipo.choices)
    mensaje = models.TextField()
    canal = models.CharField(max_length=10, choices=Canal.choices, default=Canal.IN_APP)
    leida = models.BooleanField(default=False)
    entidad_tipo = models.CharField(max_length=50, null=True, blank=True)
    entidad_id = models.UUIDField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications_notificacion"
        indexes = [
            models.Index(fields=["user_id", "leida"], name="idx_notif_user_leida"),
        ]

    def __str__(self) -> str:
        return f"Notificacion({self.user_id}, {self.tipo})"
