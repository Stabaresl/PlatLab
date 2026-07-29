import uuid

from django.db import models


class RegistroAuditoriaModel(models.Model):
    """UC-12/RF-33: registro append-only — no se edita ni se borra tras crearse."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # actor_id/entidad_id: id suelto (Arquitectura §8) — Audit no depende
    # de ningún otro módulo, solo escucha eventos de dominio.
    actor_id = models.UUIDField(null=True, blank=True)
    accion = models.CharField(max_length=100)
    entidad_tipo = models.CharField(max_length=50, null=True, blank=True)
    entidad_id = models.UUIDField(null=True, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_registroauditoria"
        indexes = [
            models.Index(fields=["actor_id"], name="idx_audit_actor"),
            models.Index(fields=["accion"], name="idx_audit_accion"),
            models.Index(fields=["timestamp"], name="idx_audit_timestamp"),
        ]

    def __str__(self) -> str:
        return f"RegistroAuditoria({self.accion}, {self.timestamp})"
