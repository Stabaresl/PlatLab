import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="NotificacionModel",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("user_id", models.UUIDField()),
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("invitacion", "Invitación"),
                            ("vencimiento_proximo", "Vencimiento próximo"),
                            ("reporte_resuelto", "Reporte resuelto"),
                            ("laboratorio_publicado", "Laboratorio publicado"),
                            ("acceso_vencido", "Acceso vencido"),
                        ],
                        max_length=30,
                    ),
                ),
                ("mensaje", models.TextField()),
                (
                    "canal",
                    models.CharField(
                        choices=[("in_app", "In-app"), ("email", "Email")],
                        default="in_app",
                        max_length=10,
                    ),
                ),
                ("leida", models.BooleanField(default=False)),
                ("entidad_tipo", models.CharField(blank=True, max_length=50, null=True)),
                ("entidad_id", models.UUIDField(blank=True, null=True)),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "notifications_notificacion",
            },
        ),
        migrations.AddIndex(
            model_name="notificacionmodel",
            index=models.Index(fields=["user_id", "leida"], name="idx_notif_user_leida"),
        ),
    ]
