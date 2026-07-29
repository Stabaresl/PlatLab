import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AsignacionModel",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("estudiante_id", models.UUIDField()),
                ("laboratorio_id", models.UUIDField()),
                ("instructor_id", models.UUIDField(blank=True, null=True)),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("pendiente", "Pendiente"),
                            ("aceptada", "Aceptada"),
                            ("rechazada", "Rechazada"),
                            ("activa", "Activa"),
                            ("vencida", "Vencida"),
                        ],
                        default="pendiente",
                        max_length=20,
                    ),
                ),
                ("fecha_invitacion", models.DateTimeField(auto_now_add=True)),
                ("fecha_vencimiento", models.DateTimeField(blank=True, null=True)),
                ("fecha_respuesta", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "db_table": "assignments_asignacion",
            },
        ),
        migrations.AddIndex(
            model_name="asignacionmodel",
            index=models.Index(
                fields=["estado", "fecha_vencimiento"], name="idx_asig_estado_vencimiento"
            ),
        ),
        migrations.AddConstraint(
            model_name="asignacionmodel",
            constraint=models.CheckConstraint(
                condition=models.Q(("fecha_vencimiento__isnull", True))
                | models.Q(("fecha_vencimiento__gt", models.F("fecha_invitacion"))),
                name="ck_asig_vencimiento_posterior",
            ),
        ),
        migrations.AddConstraint(
            model_name="asignacionmodel",
            constraint=models.UniqueConstraint(
                condition=models.Q(("estado__in", ["pendiente", "activa"])),
                fields=("estudiante_id", "laboratorio_id"),
                name="uq_asig_est_lab_vigente",
            ),
        ),
    ]
