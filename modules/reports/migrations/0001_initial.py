import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ReporteModel",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("estudiante_id", models.UUIDField()),
                ("laboratorio_id", models.UUIDField()),
                ("seccion_id", models.UUIDField(blank=True, null=True)),
                ("descripcion", models.TextField()),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("abierto", "Abierto"),
                            ("en_revision", "En revisión"),
                            ("resuelto", "Resuelto"),
                            ("no_reproducible", "No reproducible"),
                        ],
                        default="abierto",
                        max_length=20,
                    ),
                ),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                ("fecha_resolucion", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "db_table": "reports_reporte",
            },
        ),
        migrations.CreateModel(
            name="AdjuntoReporteModel",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("archivo_url", models.CharField(max_length=500)),
                ("nombre_archivo", models.CharField(max_length=255)),
                ("tamano_kb", models.PositiveIntegerField()),
                (
                    "reporte",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="adjunto",
                        to="reports.reportemodel",
                    ),
                ),
            ],
            options={
                "db_table": "reports_adjunto",
            },
        ),
        migrations.AddIndex(
            model_name="reportemodel",
            index=models.Index(fields=["estado"], name="idx_reporte_estado"),
        ),
        migrations.AddIndex(
            model_name="reportemodel",
            index=models.Index(fields=["estudiante_id"], name="idx_reporte_estudiante"),
        ),
    ]
