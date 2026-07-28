import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ProgresoModel",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("asignacion_id", models.UUIDField(unique=True)),
                ("estudiante_id", models.UUIDField()),
                ("fecha_inicio", models.DateTimeField(auto_now_add=True)),
                ("ultima_actividad", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "progress_progreso",
            },
        ),
        migrations.CreateModel(
            name="ProgresoSeccionModel",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("seccion_id", models.UUIDField()),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("bloqueada", "Bloqueada"),
                            ("en_progreso", "En progreso"),
                            ("completada", "Completada"),
                        ],
                        default="bloqueada",
                        max_length=20,
                    ),
                ),
                ("fecha_completado", models.DateTimeField(blank=True, null=True)),
                (
                    "progreso",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="secciones",
                        to="progress.progresomodel",
                    ),
                ),
            ],
            options={
                "db_table": "progress_progresoseccion",
            },
        ),
        migrations.CreateModel(
            name="IntentoFlagModel",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("seccion_id", models.UUIDField()),
                ("resultado", models.BooleanField()),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                (
                    "progreso",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="intentos",
                        to="progress.progresomodel",
                    ),
                ),
            ],
            options={
                "db_table": "progress_intentoflag",
            },
        ),
        migrations.CreateModel(
            name="HistorialCompletitudModel",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("numero_intento", models.PositiveIntegerField()),
                ("fecha_completado", models.DateTimeField(auto_now_add=True)),
                (
                    "puntaje",
                    models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
                ),
                (
                    "progreso",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="historial",
                        to="progress.progresomodel",
                    ),
                ),
            ],
            options={
                "db_table": "progress_historialcompletitud",
            },
        ),
        migrations.AddIndex(
            model_name="progresomodel",
            index=models.Index(fields=["estudiante_id"], name="idx_progreso_estudiante"),
        ),
        migrations.AddIndex(
            model_name="progresoseccionmodel",
            index=models.Index(
                fields=["progreso", "estado"], name="idx_progresoseccion_progreso_estado"
            ),
        ),
        migrations.AddConstraint(
            model_name="progresoseccionmodel",
            constraint=models.UniqueConstraint(
                fields=("progreso", "seccion_id"), name="uq_progresoseccion_progreso_seccion"
            ),
        ),
        migrations.AddIndex(
            model_name="intentoflagmodel",
            index=models.Index(
                fields=["progreso", "seccion_id", "timestamp"], name="idx_intentoflag_prog_sec_ts"
            ),
        ),
        migrations.AddConstraint(
            model_name="historialcompletitudmodel",
            constraint=models.UniqueConstraint(
                fields=("progreso", "numero_intento"), name="uq_historial_progreso_intento"
            ),
        ),
    ]
