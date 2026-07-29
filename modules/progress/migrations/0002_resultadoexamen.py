import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("progress", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ResultadoExamenModel",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("examen_id", models.UUIDField()),
                ("respuestas", models.JSONField()),
                ("puntaje", models.DecimalField(decimal_places=2, max_digits=5)),
                ("fecha", models.DateTimeField(auto_now_add=True)),
                (
                    "progreso",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="resultados_examen",
                        to="progress.progresomodel",
                    ),
                ),
            ],
            options={
                "db_table": "progress_resultadoexamen",
            },
        ),
        migrations.AddIndex(
            model_name="resultadoexamenmodel",
            index=models.Index(fields=["progreso", "fecha"], name="idx_resex_progreso_fecha"),
        ),
    ]
