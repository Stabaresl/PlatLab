import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="RegistroAuditoriaModel",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("actor_id", models.UUIDField(blank=True, null=True)),
                ("accion", models.CharField(max_length=100)),
                ("entidad_tipo", models.CharField(blank=True, max_length=50, null=True)),
                ("entidad_id", models.UUIDField(blank=True, null=True)),
                ("ip", models.GenericIPAddressField(blank=True, null=True)),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "audit_registroauditoria",
            },
        ),
        migrations.AddIndex(
            model_name="registroauditoriamodel",
            index=models.Index(fields=["actor_id"], name="idx_audit_actor"),
        ),
        migrations.AddIndex(
            model_name="registroauditoriamodel",
            index=models.Index(fields=["accion"], name="idx_audit_accion"),
        ),
        migrations.AddIndex(
            model_name="registroauditoriamodel",
            index=models.Index(fields=["timestamp"], name="idx_audit_timestamp"),
        ),
    ]
